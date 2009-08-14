import os
import re
import psycopg2

### WARNING: REPLACE THIS DIRECT DB ACCESS
import frontend_config
config = frontend_config.get_config_for_hostname(os.environ.get('SERVER_NAME', 'NO_HOSTNAME'))

# DEPENDENCIES
# * python-levenshtein
# * python-psycopg2

from Levenshtein import distance
from Levenshtein import ratio

from util_regexes import *
from util_general import compare_by

class Suggestions(object):
	"""We keep a mapping from input keywords to possibilities. Because we keep a
	list of levenshtein matches and substring matches, we map
	keyword->dict(alike_matches[], lev_matches[])

	Alike matches are fundamentally different to levenshtein matches, so handle
	them separately.
	"""

	def __init__(self):
		self.listing = {}


	def init_keyword(self, keyword):
		if keyword not in self.listing:
			self.listing[keyword] = {}
			self.listing[keyword]['like'] = []
			self.listing[keyword]['lev'] = []


	def add_alike(self, keyword, tag_data):
		"""The tag_tuple has a shorthand for the tag (when it exists), the pretty
		name that we can display to the user, and the tagid (most important).
		Expected input for the tag_data is
		tag_data = {	"shorthand" :	"shortTagName",
				"name" : 	"The tag name",
				"tagid" : 	42 }
		"""

		self.init_keyword(keyword)

		if tag_data.get("tagid", 0) in [x['tagid'] for x in self.listing[keyword]['like']]:
			return
		if tag_data.get("tagid", 0) in [x['tagid'] for x in self.listing[keyword]['lev']]:
			return

		self.listing[keyword]['like'].append(tag_data)


	def add_lev(self, keyword, tag_data):
		"""Similar enough to add_alike, but we calculate a levenshtein ratio when
		you add. We use it later to provide ranked results.
		"""

		self.init_keyword(keyword)

		if tag_data.get("tagid", 0) in [x['tagid'] for x in self.listing[keyword]['like']]:
			return
		if tag_data.get("tagid", 0) in [x['tagid'] for x in self.listing[keyword]['lev']]:
			return

		tag_data['distance'] = distance(keyword, tag_data.get("shorthand", ""))
		tag_data['ratio'] = ratio(keyword, tag_data.get("shorthand", ""))

		self.listing[keyword]['lev'].append(tag_data)




def build_suggestions(suggestions, keyword_list):
	"""Take a list of keywords and throw them into a Suggestions object

	keyword_list is a list of strings which we will scan the taglists for
	These "strings" may also be str(int)'s
	PUT MORE WORDS HERE

	Because our lists are ordered, we add elements from greater->lower likelihood of match
	Likelihood hierarchy:
		Raw tagid -- Assume perfect, stop here after you get one
		Keyword is exact match to a tag -- eg. SAKURA
		Keyword appears at start of tag -- eg. SAKURAkinomoto
		Keyword appears at end of tag -- eg. nemuaSAKURA
		Keyword appears in middle of tag -- eg. aSAKURAryouko
		Levenshtein match is needed to find a tag -- eg. meganekKo->meganeko
	Levenshtein assumes that the user isn't completely braindead,
	ie. they can get the first two characters of the tag correct
		glasses -> glsses = MATCH
		glasses -> grasses = NO MATCH
	This should speed things up considerably, rather than trying to perform
	levenshtein against hundreds or thousands of names.
	If we assume even alphabetic distribution of tagnames, enforcing first
	character correctness presumably shrinks the search space by a factor of 26.
	With two characters, that should be 26^2, or 676? I think so.
	"""

	try:
		connection = psycopg2.connect(host=config.db_hostname, database=config.db_dbname, user=config.db_username, password=config.db_password)
		cursor = connection.cursor()
	except:
		gen_error('GENERIC', "Could not connect to the database")

	tag_keys = ["shorthand", "name", "tagid"]

	# These query strings get looped pretty heavily, so no point defining them every iteration down below
	primary_exact_query = 'SELECT "name" AS "shorthand","name" AS "name","tagid" FROM "' + config.tbl_tags + '" WHERE ' + \
		"""lower(replace(replace(trim(trailing '&#;0123456789/ ' from "name"), '-', ''), ' ', '')) = %(keyword)s"""
	secondary_exact_query = 'SELECT "shorthand","name","tagid" FROM "' + config.tbl_tags + '" NATURAL JOIN "' + config.tbl_aliases + '" WHERE "shorthand" = %(keyword)s'
	primary_query = 'SELECT "name" AS "shorthand","name" AS "name","tagid" FROM "' + config.tbl_tags + '" WHERE ' + \
		"""lower(replace(replace(trim(trailing '&#;0123456789/ ' from "name"), '-', ''), ' ', '')) LIKE %(keyword)s"""
	secondary_query = 'SELECT "shorthand","name","tagid" FROM "' + config.tbl_tags + '" NATURAL JOIN "' + config.tbl_aliases + '" WHERE "shorthand" LIKE %(keyword)s'
	levenshtein_query= 'SELECT "name" AS "shorthand","name" AS "name","tagid" FROM "' + config.tbl_tags + '" WHERE ' + \
		"""lower(replace(replace(trim(trailing '&#;0123456789/ ' from "name"), '-', ''), ' ', '')) LIKE %(keyword)s UNION """ + \
		'SELECT "shorthand","name","tagid" FROM "' + config.tbl_aliases + '" NATURAL JOIN "' + config.tbl_tags + '" WHERE "shorthand" LIKE %(keyword)s'

	for keyword in keyword_list:
		# Special case, we retrieve the tag and assume they entered the full name *exactly*
		if only_digits.match(keyword):
			tagid = int(keyword)
			cursor.execute('SELECT "name" AS "shorthand","name" AS "name","tagid" FROM "' + config.tbl_tags + '" WHERE "tagid"=%(tagid)s', {"tagid":tagid} )
			row = cursor.fetchone()
			if row is not None:
				suggestions.add_alike(row[0], dict(zip(tag_keys, row)))
			continue


		# Attempt EXACT MATCH for keyword->name
		cursor.execute(primary_exact_query, {"keyword":keyword} )
		resultset = cursor.fetchall()
		if resultset is not None:
			for row in resultset:
				suggestions.add_alike(keyword, dict(zip(tag_keys, row)))

		cursor.execute(secondary_exact_query, {"keyword":keyword} )
		resultset = cursor.fetchall()
		if resultset is not None:
			for row in resultset:
				suggestions.add_alike(keyword, dict(zip(tag_keys, row)))


		keyword_lists = [	[ {"keyword":keyword + r'_%'},		{"keyword":keyword + r'_%'} ],		# keyword at START
					[ {"keyword":r'%_' + keyword},		{"keyword":r'%_' + keyword} ],		# keyword at END
					[ {"keyword":r'%_' + keyword + r'_%'},	{"keyword":r'%_' + keyword + r'_%'}]	# keyword in MIDDLE
		]
		# The first query runs against the main tags table, and should catch most cases
		# The second query is against the tag-alias table
		# This pair of queries gets made three times, changing only the sql-based
		# string-matching stuff each time, so to save space and maybe be optimal,
		# we wrap in some loopage.
		for keyword_pair in keyword_lists:
			cursor.execute(primary_query, keyword_pair[0])
			resultset = cursor.fetchall()
			if resultset is not None:
				for row in resultset:
					suggestions.add_alike(keyword, dict(zip(tag_keys, row)))

			cursor.execute(secondary_query, keyword_pair[1])
			resultset = cursor.fetchall()
			if resultset is not None:
				for row in resultset:
					suggestions.add_alike(keyword, dict(zip(tag_keys, row)))


		# Levenshtein matching to account for typos
		# This is cool, as we can hit the tags table as well as the aliases, at once!
		cursor.execute(levenshtein_query, {"keyword":keyword[0:2] + r'%'} )
		resultset = cursor.fetchall()
		if resultset is not None:
			for row in resultset:
				if distance(keyword, alphanum.sub('', row[0])) > config.MAX_LEVENSHTEIN_DISTANCE:
					continue
				suggestions.add_lev(keyword, dict(zip(tag_keys, row)))

			# Sort the list of levenshtein hits
			if suggestions.listing.has_key(keyword):
				(suggestions.listing[keyword]['lev']).sort(key=lambda x: x['ratio'], reverse=True)







