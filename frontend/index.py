#!/usr/bin/python -u

import xmlrpclib
import cgi
import cgitb; cgitb.enable()
import os
import sys
import re

from util_general import *
from util_printing import *
from util_html import meidokon_http_headers
from util_html import meidokon_html_headers
from util_html import meidokon_html_footers

# New-style config
import frontend_config
config = frontend_config.get_config_for_hostname(os.environ.get('SERVER_NAME', 'NO_HOSTNAME'))


# Automatically close the HTML cleanly, whether we finish normally, or halfway through something
import atexit
atexit.register(meidokon_html_footers)

# If the user passes a cookie specifying another content server, use it
# Expects util_general to be imports as `from X import Y`
full_resolver = get_value_from_cookie('full_resolver')
mid_resolver = get_value_from_cookie('mid_resolver')
thumb_resolver = get_value_from_cookie('thumb_resolver')


meidokon_http_headers()
meidokon_html_headers()


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


# Get taglist
taglist = config.xmlrpc_server.get_all_tags('')['data'].values()
taglist.sort(compare_by('tagid'))
real_tagids = set([x['tagid'] for x in taglist])

# Get tag types
tag_types = config.xmlrpc_server.get_tag_types()['data'].values()
tag_types.sort(compare_by('display_order'))

# Get requested tagids and derive the types
form = cgi.FieldStorage()
query_tagids = set([int_or_none(x) for x in form.getlist("tag")])
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
index = "?" + "&amp;".join(['tag='+str(x) for x in query_tagids])


# ANNOUNCEMENTS
print '''
<h3>It's well overdue, but there's now a <a href="/kareha/">Kareha board</a> available for feedback, discussion and whatnot.<br />
- Shirley, 2007-04-06, 06:29 UTC
<br style="clear:both; font-size:1px; line-height:0; height:0;" />
</h3>
'''


# Print taglist by tagtype
for tag_type in tag_types:
	if not tag_type['display_depends'] in query_types and tag_type['display_depends']:
		continue	# Don't list a tag-type that's dependent on another type that isn't in the query


	print '''<div class="tagcontainer">'''
	print '''<h2>Search for %s</h2>''' % tag_type['type']

	tags_of_type = [x for x in taglist if x['type']==tag_type['type']]
	tags_of_type.sort(key=lambda x: re.sub(r'[\*_]', r'', x['name']).lower())	# Sort, ignoring formatting characters
	positive_query_tagids = set([abs(x) for x in query_tagids])

	print '''<div class="taglist">'''
	if tag_type['display_depends']:
		local_parents = [x for x in taglist if x['type']==tag_type['display_depends'] and x['tagid'] in positive_query_tagids]
		local_parents.sort(key=lambda x: x['name'])
		for parent in local_parents:
			print """Child tags of """ + tag_type['display_depends'] + """: <em>""" + parent['name'] + """</em><br />"""
			print_tag_tree(tags_of_type, positive_query_tagids, parent['tagid'], 0, linking_tag_print, index, limit)
	else:
		print_tag_tree(tags_of_type, positive_query_tagids, 0, 0, linking_tag_print, index, limit)
	print '''</div>'''

	print"</div>"

print '''<p style="clear:both;" />'''




# Easy link for a fresh search
print """<div style="text-align:center;"><h3><a href="?">New search</a></h3></div>
"""



# Handle uploads here
print """<form action="%s" method="post" enctype="multipart/form-data">""" % config.file_upload_target
print """<div>
	<strong>Upload a file</strong><br />
	<input type="file" name="files" /><br />
	<input type="submit" value="Upload File" />
</div>
</form>"""



# Prep the query
params_dict = {}
params_dict['limit'] = limit
params_dict['offset'] = offset
params_dict['query_tags'] = dict(zip([str(x) for x in query_tagids], query_tagids))
answer = config.xmlrpc_server.query(params_dict)



# Parse the results, re-sort due to conversion from dictionary
images = [answer['data'][str(x)] for x in sorted([int(y) for y in answer['data'].keys()])]
num_results_returned = len(images)




# Trim to fit limit
while len(images) > limit:
	images.pop()



# Display the results
if not len(images):
	print "Sorry, no images were found<br />\n"
	sys.exit(0)


print """<div style="text-align:center;">Images %d to %d shown</div>\n\n""" % (offset+1, offset+len(images))

print """<form id="selectImgs" method="post" action="edit_tags.py">\n"""
display_image_list(images, checkall=form.has_key('checkall'), thumb_resolver=thumb_resolver, mid_resolver=mid_resolver, full_resolver=full_resolver)
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


