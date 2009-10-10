# vim: syntax=python fileencoding=utf8

# DEPENDENCY: paste.exceptions.errormiddleware

import os
import sys
import cgi
from urllib import urlencode
from itertools import izip
from itertools import repeat

DEBUG = True
#DEBUG = False

def application(environ, start_response):
	# cwd gets set to /, which is annoying :(
	cwd = os.path.dirname(__file__)
	sys.path.insert(0, cwd)

	import util_regexes
	from util_http import http_response
	from util_general import get_value_from_cookie
	from util_general import space_to_under
	from util_general import under_to_space
	from util_general import compare_by
	from util_general import positive_ints
	from util_html import meidokon_html_headers
	from util_html import meidokon_html_footers
	from util_printing import display_image_list

	if DEBUG:
		from util_pretty_print import html_pretty
		from time import time
		timing_list = []
		timing_list.append( ('start', time()) )

	import Suggestions
	import frontend_config
	config = frontend_config.get_config_for_hostname(os.environ.get('SERVER_NAME', 'NO_HOSTNAME'))

	# Setup our output
	output = http_response(environ, start_response)
	sys.stdout = output
	wsgi_errors = environ['wsgi.errors']


	# If the user passes a cookie specifying another content server, use it
	# Expects util_general to be imports as `from X import Y`
	full_resolver = get_value_from_cookie('full_resolver')
	mid_resolver = get_value_from_cookie('mid_resolver')
	thumb_resolver = get_value_from_cookie('thumb_resolver')

	# Start content
	meidokon_html_headers()
	if DEBUG: timing_list.append( ('printed html headers', time()) )

	# Get all our form input
        form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)

	# q is our query string, whatever form it's in
	if form.has_key('q'):
		q = form.getlist('q')
		q = ' '.join([x.strip() for x in q if x])
	else:
		q = ''

	# User can set the levenshtein match distance
	try:
		lev_threshold = int(form.getfirst('lev_threshold', config.lev_threshold))
	except:
		# FIXME: what sort of exception am I guarding against here? casting to int?
		pass
	
	# Turn "quoted chunks" into underscore_separated_chunks
	q = util_regexes.double_quoted_string.sub(space_to_under, q)
	query_chunks = [ under_to_space(x).strip().lower() for x in util_regexes.alphanum_underscore_hyphen.split(q) if x ]


	# Get some matches now
	s = Suggestions.Suggestions()
	if q:
		Suggestions.build_suggestions(s, query_chunks)
	good_search_terms = s.listing.keys()
	failed_search_terms = set(query_chunks).difference(set(s.listing.keys()))
	# Account for the suggestions engine giving us data different to our original queries
	for term in good_search_terms:
		if len(s.listing[term]['like']) == 1 and len(s.listing[term]['lev']) == 0:
			failed_search_terms.discard(str(s.listing[term]['like'][0]['tagid']))
	failed_search_terms = list(failed_search_terms)

	# Put the search terms back in the input field for user's convenience
	# The /.* replacement is for tags which have a slash in them to split EN/JP, like Megane-ko/<kanji>
	# This might not be so awesome after all
	q_box = ''
	for term in good_search_terms:
		if ' ' in term:
			q_box += '%s ' % (space_to_under(util_regexes.slash_trailing.sub('', term).strip()))
		else:
			q_box += '%s ' % (term)
	for term in failed_search_terms:
		if ' ' in term:
			q_box += '%s ' % (space_to_under(util_regexes.slash_trailing.sub('', term).strip()))
		else:
			q_box += '%s ' % (term)
	q_box = q_box.strip()

	# Choose a random heading
	from random import choice
	chosen_heading = choice(config.headings)

	if DEBUG: timing_list.append( ('parsed all input', time()) )

	### START ACTUAL CONTENT HERE

	# Make it obvious if resolver overrides are in use
	if full_resolver or mid_resolver or thumb_resolver:
		print '''<div style="background:silver; border:3px double;">'''
	if full_resolver:
		print "<strong>Full-size resolver override:</strong> " + full_resolver + "<br />"
	if mid_resolver:
		print "<strong>Mid-size resolver override:</strong> " + mid_resolver + "<br />"
	if thumb_resolver:
		print "<strong>Thumbnail resolver override:</strong> " + thumb_resolver + "<br />"
	if full_resolver or mid_resolver or thumb_resolver:
		print '''</div>'''


	# Header block
	print '''<h1 style="text-align:center;">meidokon.net</h1>
	<h1 style="text-align:center;">&#12513;&#12452;&#12489;&#12467;&#12531;</h1>
	'''
	
	# Search box
	print '''<div style="text-align:center;">
		<form action="%s" method="get">
		<input type="text" name="q" size="60" value="%s">
		<input type="submit" value="Search!">
		</form>
	</div>
	''' % (environ['SCRIPT_NAME'], q_box)

	# News-box
	if not q_box:
		print '''<div class="center" style="background:DarkSlateGray; border:3px double black;">
		<h1>%s</h1>
		<p>News and stuff goes here</p>
	</div>
	''' % (cgi.escape(chosen_heading))
	
	# Dynamic content starts here
	print '''<div class="center" style="background:SteelBlue; border:3px double black;">'''

	if DEBUG: timing_list.append( ('boilerplate HTML printed', time()) )

	# Search suggestions
	if q_box:
		print '''<!-- BIGARSE TABLE STARTS HERE -->
		<h2 style="margin-bottom:0px;"><em>Did you mean..?</em></h2>
		<table class="suggestions">
		'''
	
		# First line of refinement form - original search terms
		print '''<tr>'''
		for term in good_search_terms:
			if len(s.listing[term]['like']) > 0:
				colour = 'green'
			elif len(s.listing[term]['lev']) > 0:
				colour = 'orange'
			else:
				colour = 'white'
	
			print '''<td style="background-color: %s;">
			<strong>%s</strong>
			</td>
			''' % (colour, term)
		for term in failed_search_terms:
			print '''<td style="background-color: red;">
			<strong>%s</strong>
			</td>
			''' % (term)
		
		print '''<td></td></tr>''' # Blank td for the search button next line
	
		# Second line of refinement - choices
		print '''<tr>
		<form method="get" action="%s">
		''' % (environ['SCRIPT_NAME'])
		for term in good_search_terms:
			print '''<td>
			<select name="q" style="background: silver;">
			<option value="" disabled style="color: firebrick;">== Substring matches==</option>"
			'''
			for hit in s.listing[term]['like']:
				print '''<option value="%s">%s</option>''' % (hit['tagid'], hit['name'])
			print '''<option value="" disabled></option>
			<option value="" disabled style="color: firebrick;">== Close matches ==</option>
			'''
			for hit in s.listing[term]['lev']:
				print '''<option value="%s">%s</option>''' % (hit['tagid'], hit['name'])
			print '''</select>
			</td>
			'''
		for term in failed_search_terms:
			print '''<td>NO MATCH</td>'''
		print '''<td><input type="submit" value="Revise search"></td>
		</form>
		</tr>'''
	
		# Third line of refinement - dump unwanted terms
		print '''<tr>'''
		for term in good_search_terms:
			other_terms = set(query_chunks)
			other_terms.discard(term)
			other_terms = [ space_to_under(x) for x in other_terms ]
			query_string = urlencode(list(izip(repeat('q'), other_terms)))
			print '''<td><a href="%s?%s">I don't want it</a></td>''' % (environ['SCRIPT_NAME'], query_string)
		for term in failed_search_terms:
			other_terms = set(query_chunks)
			other_terms.discard(term)
			other_terms = [ space_to_under(x) for x in other_terms ]
			query_string = urlencode(list(izip(repeat('q'), other_terms)))
			print '''<td><a href="%s?%s">I don't want it</a></td>''' % (environ['SCRIPT_NAME'], query_string)
		print '''<td></td></tr>''' # Blank td for the search button next line
	
		print '''</table>
		<!-- BIGARSE TABLE ENDS HERE -->
		'''
	
	
	
	print '''Lev threshold is %s<br />''' % (lev_threshold)
	if DEBUG: timing_list.append( ('printed search boxes', time()) )

	if DEBUG:
		html_pretty("SUGGESTIONS DICTIONARY")
		#html_pretty(s.listing)
		html_pretty(good_search_terms)
		html_pretty(failed_search_terms)

	query_tagids = set()
	for x in s.listing.values():
		if x['like']:
			query_tagids.add(x['like'][0]['tagid'])
		else:
			query_tagids.add(x['lev'][0]['tagid'])
	if DEBUG:
		html_pretty("Query tagids")
		html_pretty(query_tagids)

	####
	###
	##OLD CODE
	#
	# Get taglist
	taglist = config.xmlrpc_server.get_all_tags('')['data'].values() # FIXME: this is very slow
	real_tagids = set([ x['tagid'] for x in taglist ])
	if DEBUG: timing_list.append( ('got taglist', time()) )

	# Get tag types
	tag_types = config.xmlrpc_server.get_tag_types()['data'].values()
	tag_types.sort(compare_by('display_order'))
	if DEBUG: html_pretty(tag_types)
	if DEBUG: timing_list.append( ('got tag types', time()) )

	# Get requested tagids and derive the types
	# The following mess lets us keep the -ve tagids for exclusion but also check that they're legit
	query_tagids = query_tagids.intersection(real_tagids).union(set([x for x in query_tagids if abs(x) in real_tagids]))
	query_types = set([x['type'] for x in taglist if x['tagid'] in query_tagids])

	# Arrange limit and offset
	limit = positive_ints(form.getfirst("limit", config.DEFAULT_LIMIT))
	if not limit:
		limit = config.DEFAULT_LIMIT

	offset = positive_ints(form.getfirst("offset", config.DEFAULT_OFFSET))
	if not offset:
		offset = config.DEFAULT_OFFSET
	

	# Arrange index-base for href links
	index = "?" + "&amp;".join(['q='+str(x) for x in query_tagids])
	if DEBUG: html_pretty(index)




	# Handle uploads here
	print """<form action="%s" method="post" enctype="multipart/form-data">""" % config.file_upload_target
	print """<div>
		<strong>Upload a file</strong><br />
		<input type="file" name="files" /><br />
		<input type="submit" value="Upload File" />
	</div>
	</form>"""
	if DEBUG: timing_list.append( ('printed upload box', time()) )


	# Prep the query
	params_dict = {}
	params_dict['limit'] = limit
	params_dict['offset'] = offset
	params_dict['query_tags'] = dict(zip([ str(tagid) for tagid in query_tagids ], query_tagids))
	answer = config.xmlrpc_server.query(params_dict)
	if DEBUG: html_pretty(answer)
	if DEBUG: timing_list.append( ('ran query', time()) )

	# Parse the results, re-sort due to conversion from dictionary
	images = [ answer['data'][str(x)] for x in sorted([ int(y) for y in answer['data'].keys() ]) ]
	num_results_returned = len(images)
	if DEBUG: html_pretty(num_results_returned)

	# Trim to fit limit
	del(images[limit:])
	if DEBUG: timing_list.append( ('munged results', time()) )


	# Display the results
	if not len(images):
		print "Sorry, no images were found<br />\n"
		meidokon_html_footers()
		return output.finalise()

	print """<div style="text-align:center;">Images %d to %d shown</div>\n\n""" % (offset+1, offset+len(images))

	print """<form id="selectImgs" method="post" action="edit_tags.py">\n"""
	if DEBUG: timing_list.append( ('result header', time()) )
	display_image_list(images, checkall=form.has_key('checkall'), thumb_resolver=thumb_resolver, mid_resolver=mid_resolver, full_resolver=full_resolver)
	if DEBUG: timing_list.append( ('displayed image list', time()) )
	print """<div><input type="submit" value="Set tags on marked files" /></div>\n"""
	print "</form>\n"

	print "<div>&lt;"
	if offset > 0:
		temp_offset = max([offset-limit, 0])
		print """<a href="%s&amp;limit=%s&amp;offset=%s">Previous %d</a>""" % (index, limit, temp_offset, limit)
	else:
		print "Previous %d" % limit
	print "&nbsp;|&nbsp;"
	temp_offset = offset + limit
	if num_results_returned > limit:
		print """<a href="%s&amp;limit=%s&amp;offset=%s">Next %d</a>""" % (index, limit, temp_offset, limit)
	else:
		print "Next %d" % limit
	print "&gt;</div>"
	if DEBUG: timing_list.append( ('displayed results', time()) )


	if DEBUG:
		start_time = timing_list[0][1]
		timing_list = [ (x[0],x[1]-start_time) for x in timing_list ]
		html_pretty(timing_list)



	return output.finalise()


from paste.exceptions.errormiddleware import ErrorMiddleware
application = ErrorMiddleware(application, debug=True)

