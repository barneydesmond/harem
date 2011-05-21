#!/usr/bin/python -u

#import cgi_buffer
import xmlrpclib
import cgi
import cgitb; cgitb.enable()
import os
import sys
import re

import util_regexes
from util_general import *
from util_printing import *
from util_baseconvert import base32_to_base16
from util_baseconvert import base16_to_base32
from util_errors import http_error
from util_errors import gen_error
from util_errors import HOMEPAGE_LINK
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
# Expects util_general to be imported as `from X import Y`
full_resolver = get_value_from_cookie('full_resolver')
mid_resolver = get_value_from_cookie('mid_resolver')
thumb_resolver = get_value_from_cookie('thumb_resolver')


# Deal with POSTed hashes, which are the result of mark-and-tag from the index page
form = cgi.FieldStorage()
hashes = set()
for one_hash in form.getlist("hashes"):
	if util_regexes.base16_or_32.search(one_hash):
		hashes.add(base32_to_base16(one_hash))
# Throw in a hash sent as the QUERY_STRING
query_string = os.environ.get('QUERY_STRING', '')
if util_regexes.base16_or_32.search(query_string):
	hashes.add(base32_to_base16(query_string))
# It's now more convenient to index into hashes
hashes = list(hashes)


if len(hashes) == 0:
	http_error(400, "No valid hashes were supplied")

if len(hashes) == 1:
	page_title = "Edit tags for %s" % hashes[0]
else:
	page_title = "Edit tags for multiple files"


meidokon_http_headers()
meidokon_html_headers(page_title)


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


print """<div style="position:fixed; left:1em; top:1em; border:1px dotted"><a href="%s">Go home</a></div>""" % HOMEPAGE_LINK
tags_on_files = {}

# Collect data on 1 or many files
if len(hashes) == 1:
	metadata = config.xmlrpc_server.get_filedata(hashes[0])
	if not metadata['success']:
		gen_error("ERR_NO_SUCH_FILE", metadata['explanation'])
	# metadata will only be used/available if len(hashes)==1
	metadata = metadata['data']
else:
	pass

for a_hash in hashes:
	tags_on_file = config.xmlrpc_server.get_tags(a_hash)
	if not tags_on_file['success']:
		continue
	tags_on_file = tags_on_file['data']
	for tagid in tags_on_file:
		if tagid not in tags_on_files:
			tags_on_files[int(tagid)] = tags_on_file[tagid]



# Present data

print """<table style="margin-left:auto; margin-right:auto; width:90%;">"""
print """<tr><td style="width:50%; border:2px black solid;">"""

if full_resolver:
	config.FULL_VER_PATH = full_resolver
if mid_resolver:
	config.MID_VER_PATH = mid_resolver
if thumb_resolver:
	config.THUMB_VER_PATH = thumb_resolver

if len(hashes) == 1:
	# Print thumbnail and metadata
	print '<a href="' + config.FULL_VER_PATH + hashes[0] + '"><img src="' + config.MID_VER_PATH + hashes[0] + '" alt="' + hashes[0] + '" /></a><br />'
	print '<table class="metadata">'
	for element in metadata:
		print '\t<tr><th>' + element.capitalize() + '</th><td>' + str(metadata[element]) + '</td></tr>'
	print '</table>'
	print print_tag_set(tags_on_files.values())
else:
	# Print the hashes
	print '<strong>Files being affected</strong><br />'
	print '<ul class="tag_tree">'
	for file_hash in hashes:
		print '<li>%s</li>' % file_hash
	print '</ul>'

print '<form id="delete_file" method="post" action="delete_file.py"><div>'
for file_hash in hashes:
	print '<input type="hidden" name="hashes" value="%s" />' % file_hash
print """Deletion password: <input type="password" name="password" /><br />
<input type="submit" value="Delete File/s" /><br />
</div></form>"""

print '</td>'




print '<td style="width:50%; border:2px black solid;">'

# Get and sort the tag-types
tag_types = config.xmlrpc_server.get_tag_types()
if not tag_types['success']:
	gen_error("GENERIC", tag_types['explanation'])
tag_types = tag_types['data'].values()
tag_types.sort(key=lambda x: x['display_order'])


# Print header bar showing all tag-types
colours = colour_gen()
script_buffer = []
print '<table><tr>'
for tag_type in tag_types:
	print """<td style="border:2px dotted; margin:1em; background-color:%s;" onclick="showOnly('%s')">%s</td>""" % (colours.next(), tag_type['type'], tag_type['type'])
	script_buffer.append("""tabs[tabs.length] = "%s";""" % tag_type['type'])
print '</tr></table>'

# Print all the javascript snippets at once, for efficiency
print '<script type="text/javascript">'
for line in script_buffer:
	print '\t' + line
print '</script>'


# ### OPEN FORM HERE
print """<form method="post" action="set_tags.py">"""

# Print each type of tags in a div
colours = colour_gen()
for tag_type in tag_types:
	# Establish tags to print
	if not tag_type['display_depends']:
		# Independent tag type does not depend on another tag_type
		tags_of_type = config.xmlrpc_server.get_all_tags(tag_type['type'])
		if not tags_of_type['success']:
			gen_error("XMLRPC_TAG_LIST_GET", 'Failed while trying to obtain tags of type' + tag_type['type'])
		tags_of_type = tags_of_type['data'].values()
		tags_of_type.sort(key=lambda x: re.sub(r'[\*_]', r'', x['name']).lower())	# Sort, ignoring formatting characters
	else:
		# Tag type depends on presence of other type in query

		# Expand the display_depends set of tags to include children in the dependee-type
		initial_parents = [x['tagid'] for x in tags_on_files.values() if x['type'] == tag_type['display_depends']]
		final_parents = config.xmlrpc_server.get_child_tags(dict(zip([str(x) for x in initial_parents], initial_parents)))
		if not final_parents['success']:
			gen_error("XMLRPC_TAG_LIST_GET", 'Failed while trying to expand parents for dependent tags of type' + tag_type['type'])
		# final_parents is a list of tuples of tagid,parent_name for use later; a hack
		final_parents = [tuple([int(x),final_parents['data'][x]]) for x in final_parents['data']]
		parent_tagids = [int(x[0]) for x in final_parents]

		# Get all tags of type with the full set of dependee-type tags
		tags_of_type = config.xmlrpc_server.get_all_tags(tag_type['type'], dict(zip([str(x) for x in parent_tagids], parent_tagids)))
		if not tags_of_type['success']:
			gen_error("XMLRPC_TAG_LIST_GET", 'Failed while trying to obtain tags of type' + tag_type['type'])
		tags_of_type = tags_of_type['data'].values()
		tags_of_type.sort(key=lambda x: re.sub(r'[\*_]', r'', x['name']).lower())       # Sort, ignoring formatting characters


	# Print the tags now
	print """<div id="%s" class="root" style="border:1px; text-align:left; padding:5px; height:30em; overflow:auto; background-color:%s;">""" % (tag_type['type'], colours.next())

	if not tag_type['display_depends']:
		if len(hashes) == 1:
			print_tag_tree(tags_of_type, tags_on_files.keys(), 0, 0, nonlinking_tag_print, None, None)
		else:
			print_tag_tree(tags_of_type, [], 0, 0, nonlinking_tag_print, None, None)
	else:
		final_parents.sort(key=lambda x: x[1])
		for parent in final_parents:
			print """<div style="margin-bottom:1em;">"""
			print """Child tags of %s: <em>%s</em><br />""" % ( tag_type['display_depends'], parent[1] )
			if len(hashes) == 1:
				print_tag_tree(tags_of_type, tags_on_files.keys(), int(parent[0]), 0, nonlinking_tag_print, None, None)
			else:
				print_tag_tree(tags_of_type, [], int(parent[0]), 0, nonlinking_tag_print, None, None)
			print """</div>"""

	print "</div>"


	# Do the JS here now to hide the other tabs
	print """<script type="text/javascript">"""
	print """if('%(type)s' != tabs[0]) document.getElementById('%(type)s').style.display = 'none';""" % tag_type
	print """</script>"""


print """<div style="margin:1em;">"""
for file_hash in hashes:
	print '<input type="hidden" name="hashes" value="%s" />' % file_hash

if len(hashes)==1:
	print '<input type="hidden" name="mode" value="replace" /><br />'
else:
	print """Add&nbsp;<input type="radio" name="mode" value="add" /><br />"""
	print """Replace&nbsp;<input type="radio" name="mode" value="replace" checked="checked" /><br />"""
	print """Remove&nbsp;<input type="radio" name="mode" value="remove" /><br />"""

print """<input type="submit" value="Set tags" style="margin-right:1em;" /> or <input type="submit" name="continue" value="Set tags and continue tagging" style="margin-left:1em;" /><br />"""
print """</div>"""

# ### CLOSE FORM HERE
print """</form>"""


# Free-text tag entry box
print """
<form method="post" action="revise_tags.py">
<div style="border: 1px dashed; padding:0.5em;">
Or, enter a list of tags to apply:<br /><input type="text" name="tag_string" size="60" accesskey="l" /><br />
"""
for file_hash in hashes:
	print '<input type="hidden" name="hashes" value="%s" />' % file_hash
print """
Add&nbsp;<input type="radio" name="mode" value="add" /><br />
Replace&nbsp;<input type="radio" name="mode" value="replace" checked="checked" /><br />
Remove&nbsp;<input type="radio" name="mode" value="remove" /><br />
<input type="submit" value="Submit list" accesskey="s" />
</div></form>
"""

print """
</td></tr>
</table>
"""

