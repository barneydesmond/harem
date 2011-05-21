# DEPENDENCIES
# * python-levenshtein

from Levenshtein import distance
from Levenshtein import ratio


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

