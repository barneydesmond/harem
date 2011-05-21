#!/usr/bin/python -u

import os
import cgi
import cgitb; cgitb.enable()
import re

import util_regexes
from util_baseconvert import base32_to_base16
from util_baseconvert import base16_to_base32
from util_errors import http_error
from util_errors import gen_error
from util_html import meidokon_http_headers
from util_html import meidokon_html_headers
from util_html import meidokon_html_footers
from util_pretty_print import *

class DummySuggestions(object):
	'''Used to save rewriting too much code as a result of
	switching to XMLRPC lookups for suggestions now'''
	def __init__(self):
		self.listing = {}

# New-style config
import frontend_config
config = frontend_config.get_config_for_hostname(os.environ.get('SERVER_NAME', 'NO_HOSTNAME'))

# Automatically close the HTML cleanly, whether we finish normally, or halfway through something
import atexit
atexit.register(meidokon_html_footers)


# Import form data
form = cgi.FieldStorage()

mode = form.getfirst("mode", "").lower()

items_to_tag = set([base32_to_base16(x) for x in form.getlist("hashes") if util_regexes.base16_or_32.search(x)])
items_to_tag = list(items_to_tag)

tag_string = form.getfirst("tag_string", "")
keywords = util_regexes.chunkify_tag_input(tag_string)


# Handle adverse conditions
if len(items_to_tag) == 0:
	http_error(400, "No valid hashes were supplied")

if len(keywords) < 1:
	http_error(400, "No tags were given for revision")

if mode not in ["add", "replace", "remove"]:
	http_error(400, "`%s` is not an accepted tagging mode [add, replace, remove]" % mode)


# Preamble
if len(items_to_tag) == 1:
	page_title = "Revising tags for %s" % items_to_tag[0]
else:
	page_title = "Revising tags for multiple files"

meidokon_http_headers()
meidokon_html_headers(page_title)


# Anything that couldn't be matched won't have an entry in the suggestions, so
# extract them manually and deal with them. Turns out rather convenient.
s = DummySuggestions()
s.listing = config.xmlrpc_server.get_suggestions(keywords)['data']
unmatched_keywords = list(set(keywords).difference(set(s.listing.keys())))


# ### OPEN FORM HERE
print """<form method="post" action="set_tags.py">"""

print """<fieldset>"""
print """<legend>Tag confirmation</legend>"""
print """<table>"""

for keyword in s.listing.keys():
	if len(s.listing[keyword]['like']):
		print """<tr><td style="background:green;"><label for="%s">Attempted <strong>%s</strong></label></td>""" % (keyword, keyword)
	else:
		print """<tr><td style="background:orange;"><label for="%s">Attempted <strong>%s</strong></label></td>""" % (keyword, keyword)
	print """<td>"""

#####
	print """<select name="tags" id="%s" style="background:silver;">""" % keyword

	print """<option value="" disabled="disabled" style="color: firebrick;">== Substring matches ==</option>"""
	for tag in s.listing[keyword]['like']:	# "tag" is a dictionary
		print """<option value="%s">%s</option>""" % (tag.get("tagid", 0), tag.get("name", "Oops! Something broke!"))
	print """<option value="" disabled="disabled"></option>"""

	print """<option value="" disabled="disabled" style="color: firebrick;">== Close matches ==</option>"""
	for tag in s.listing[keyword]['lev']:	# "tag" is a dictionary
		print """<option value="%s">%s</option>""" % (tag.get("tagid", 0), tag.get("name", "Oops! Something broke!"))
	print """<option value="" disabled="disabled"></option>"""

	print """</select>"""
#####

	print """</td>"""
	print """</tr>"""

for keyword in unmatched_keywords:
	print """<tr><td style="background:red;">Attempted <strong>%s</strong></td><td>NO MATCH</td></tr>""" % keyword

print """</table>"""
print """</fieldset>"""


print """<fieldset>"""
print """<legend>Let's Go!</legend>"""
for hash in items_to_tag:
	print """<input type="text" name="hashes" size="50" value="%s" /><br />""" % hash
print """<input type="text" name="mode" value="%s" /><br />""" % mode
print """<input type="submit" value="Set tags" accesskey="s" style="margin-right:1em;" />"""
print """</fieldset>"""
print """</form>"""
# ### CLOSE FORM HERE


