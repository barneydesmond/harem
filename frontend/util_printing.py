#!/usr/bin/python

import os
import re

# New-style config
import frontend_config
config = frontend_config.get_config_for_hostname(os.environ.get('SERVER_NAME', 'NO_HOSTNAME'))


def display_image_list(list, checkall=False, **kargs):
	row_counter = 0
	print """<table border="2" id="results">\n"""
	for image in list:
		if row_counter == 0:
			print "<tr>\n"
		display_image_cell(image, checked=checkall, **kargs)
		row_counter = row_counter + 1
		if row_counter == config.IMAGES_PER_ROW:
			print "</tr>\n"
			row_counter = 0
	for x in range((config.IMAGES_PER_ROW - row_counter) % config.IMAGES_PER_ROW):
		print "<td></td>\n"
	if row_counter != 0:
		print "</tr>\n"
	print "</table>\n"


def print_tag_set(tags):
	"""Takes a set or list of tags, where each tag is a dict (attrib->value).

	Each dict representing a tag will have keys 'name' and 'type' as a bare
	minimum. Display tag names grouped by type, sorted of course.
	"""

	output_buffer = ''
	tag_types = list(set([x['type'] for x in tags]))
	tag_types.sort()
	output_buffer += """<ul class="tag_tree">"""
	for type in tag_types:
		output_buffer += "<li>%s</li>" % type
		tags_of_type = [x for x in tags if x['type']==type]
		tags_of_type.sort(key=lambda x: re.sub(r'[\*_]', r'', x['name']).lower())	# Sort, ignoring formatting characters
		output_buffer += """<li><ul class="tag_tree">"""
		for tag_name in [x['name'] for x in tags_of_type]:
			output_buffer += "<li>%s</li>" % tag_name
		output_buffer += "</ul></li>"
	output_buffer += "</ul>"

	return output_buffer


def display_image_cell(image, **kargs):
	print """<td id="cell_%s" ondblclick="document.getElementById('checkbox_%s').click();">""" % (image['hash'], image['hash'])
	path = config.EDIT_PAGE_PATH + image['hash']
	thumb = config.THUMBNAIL_PATH + image['hash']
	full = config.FULL_VER_PATH + image['hash']

	if kargs.get('full_resolver', ''):
		full  = kargs['full_resolver'] + image['hash']
	if kargs.get('thumb_resolver', ''):
		thumb = kargs['thumb_resolver'] + image['hash']

	# Get the tags on the file
	tags_on_file = config.xmlrpc_server.get_tags(image['hash'])
	tag_set = print_tag_set(tags_on_file['data'].values())

	metadata = """<ul style="margin-top: 0em; padding-left:0em; list-style: none inside; font-size: smaller;">
<li>Width: %s</li>
<li>Height: %s</li>
</ul>
%s
""" % (image['width'], image['height'], tag_set)

	print """<div class="cell">\n\t<a href="%s"><img src="%s" alt="%s" /></a><br /><div>%s</div></div>\n""" % (path, thumb, thumb, metadata)
	print """<a href="%s">Full-size</a>&nbsp;|&nbsp;<a href="%s">Edit tags</a><br />\n""" % (full, path)
	if kargs.get('checked', False):
		print """<input type="checkbox" CHECKED id="checkbox_%s" name="hashes" value="%s" onclick="markFile('%s')" />Mark\n""" % (image['hash'], image['hash'], image['hash'])
	else:
		print """<input type="checkbox" id="checkbox_%s" name="hashes" value="%s" onclick="markFile('%s')" />Mark\n""" % (image['hash'], image['hash'], image['hash'])

	print "</td>\n"


def print_tag_tree(taglist, marked_tagids, parent_tagid, current_depth, printing_function, print_prefix, print_suffix):
	"""Print the listing of tags, giving special treatment to "already selected tags.

	The taglist is every tag we want to print, each tag is a dictionary. Each tag
	has a 'parent' key which should be zero if we want to indicate the top level.
	By default, the first call to print_tag_tree is with parent_tagid of 0, a
	magic number. The marked_tagids is a raw collection of positive ints which
	in this case means that tagid doesn't need to be hyperlinked if it's printed.
	The current_depth needs to be incremented manually each time this function is
	called recursively. The printing_function is a callback that we'll call iff a
	tag, need printing, taking the tag(dictionary) and a flag(boolean) indicating
	whether to "mark" it or not (ie. if tag is member of marked_tagids). The
	print_pre/suffix is given to the printing_function as spare material to use.
	"""

	assert parent_tagid is not None
	if current_depth >= 10:
		# Just a paranoid safety stop
		return

	tags_to_print = [tag for tag in taglist if tag.get('parent', None) == parent_tagid]
	if len(tags_to_print):
		print """<ul class="tag_tree">"""
		for tag in tags_to_print:
			print "<li>", printing_function(tag, tag.get('tagid', None) in marked_tagids, print_prefix, print_suffix), "</li>"
			# As an efficiency measure, only recurse deeper if there are children to deal with
			if len([x for x in taglist if x.get('parent', None)==tag.get('tagid', None)]):
				# Still need to pass the full taglist so children will be found at lower levels
				print "<li>"
				print_tag_tree(taglist, marked_tagids, tag.get('tagid', None), current_depth+1, printing_function, print_prefix, print_suffix)
				print "</li>"
		print "</ul>"



def linking_tag_print(tag, flagged, prefix, suffix):
	"""Used on the main page, has gloss and links but no checkboxes"""

	tag_name = tag.get('name', '$NAME')
	tag_name = re.sub(r'\*(.*?)\*', r'<strong>\1</strong>', tag_name)
	tag_name = retval = re.sub(r'_(.*?)_', r'<em>\1</em>', tag_name)
	if flagged:
		if tag.get('gloss', None):		# Glossy, unlinked
			##retval = """<abbr title="%s">%s (%s)</abbr>""" % (tag.get('gloss', ''), tag.get('name', '$NAME'), str(tag.get('count', '$COUNT')))
			retval = """<abbr title="%s">%s (%s)</abbr>""" % (tag.get('gloss', ''), tag_name, str(tag.get('count', '$COUNT')))
		else:					# No gloss, unlinked
			retval = """%s (%s)""" % (tag.get('name', 'NO NAME'), str(tag.get('count', '$COUNT')))
	else:
		if tag.get('gloss', None):		# Glossy, linked
			##retval = """<abbr title="%s"><a href="%s&amp;tag=%s&amp;limit=%s">%s (%s)</a></abbr>""" % (tag.get('gloss', ''), prefix, tag.get('tagid', '$TAGID'), suffix, tag.get('name', '$NAME'), str(tag.get('count', '$COUNT')))
			retval = """<abbr title="%s"><a href="%s&amp;tag=%s&amp;limit=%s">%s (%s)</a></abbr>""" % (tag.get('gloss', ''), prefix, tag.get('tagid', '$TAGID'), suffix, tag_name, str(tag.get('count', '$COUNT')))
		else:					# No gloss, linked
			retval = """<a href="%s&amp;tag=%s&amp;limit=%s">%s (%s)</a>""" % (prefix, tag.get('tagid', '$TAGID'), suffix, tag.get('name', '$NAME'), str(tag.get('count', '$COUNT')))
	return retval


def nonlinking_tag_print(tag, flagged, prefix, suffix):
	"""Used on the edit_tags page, has no links, but checkboxes instead; gloss as well"""

	# <input id="box14" type="checkbox" name="tags[]" value="14"><span onClick="toggleCbox(14)">Cosplaying</span><br>
	tag_name = tag.get('name', '$NAME')
	tag_name = re.sub(r'\*(.*?)\*', r'<strong>\1</strong>', tag_name)
	tag_name = retval = re.sub(r'_(.*?)_', r'<em>\1</em>', tag_name)
	if flagged:
		if tag.get('gloss', None):
			retval = """<input id="box%s" type="checkbox" name="tags" value="%s" checked="checked" /><span onclick="toggleCbox(%s)"><abbr title="%s">%s (%s)</abbr></span>""" % (tag['tagid'], tag['tagid'], tag['tagid'], tag.get('gloss', ''), tag_name, str(tag.get('count', '$COUNT')))
		else:
			retval = """<input id="box%s" type="checkbox" name="tags" value="%s" checked="checked" /><span onclick="toggleCbox(%s)">%s (%s)</span>""" % (tag['tagid'], tag['tagid'], tag['tagid'], tag.get('name', 'NO NAME'), str(tag.get('count', '$COUNT')))
	else:
		if tag.get('gloss', None):
			retval = """<input id="box%s" type="checkbox" name="tags" value="%s" /><span onclick="toggleCbox(%s)"><abbr title="%s">%s (%s)</abbr></span>""" % (tag['tagid'], tag['tagid'], tag['tagid'], tag.get('gloss', ''), tag_name, str(tag.get('count', '$COUNT')))
		else:
			retval = """<input id="box%s" type="checkbox" name="tags" value="%s" /><span onclick="toggleCbox(%s)">%s (%s)</span>""" % (tag['tagid'], tag['tagid'], tag['tagid'], tag.get('name', 'NO NAME'), str(tag.get('count', '$COUNT')))

	return retval

