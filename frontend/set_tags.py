#!/usr/bin/python -u

import os
import xmlrpclib
import cgi
import cgitb; cgitb.enable()

import util_regexes
from util_general import *
from util_baseconvert import base32_to_base16
from util_baseconvert import base16_to_base32
from util_errors import http_error
from util_errors import gen_error
from util_html import meidokon_http_headers
from util_html import meidokon_html_headers
from util_html import meidokon_html_footers

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

tags_to_set = set([positive_ints(x) for x in form.getlist("tags")])
tags_to_set.discard(None)


# Handle adverse conditions
if len(items_to_tag) == 0:
	cgi.test()
        http_error(400, "No valid hashes were supplied")

if mode not in ["add", "replace", "remove"]:
        http_error(400, "`%s` is not an accepted tagging mode [add, replace, remove]" % mode)


# Preamble
if len(items_to_tag) == 1:
	page_title = "Setting tags for %s" % items_to_tag[0]
else:
	page_title = "Setting tags for multiple files"

meidokon_http_headers()
meidokon_html_headers(page_title)


print """<table class="metadata" style="border:2px solid black;">
<tr><th>Mode</th><td>%s</td></tr>""" % mode
print """<tr><th>Items to tag</th><td><ul class="tag_tree">"""
for x in items_to_tag:
	print """<li>%s</li>""" % x
print """</ul></td></tr>"""
print """<tr><th>Tags to set</th><td>%s</td></tr>
</table>""" % ', '.join([str(x) for x in tags_to_set])

param_tags = dict(zip([str(x) for x in tags_to_set], tags_to_set))
param_items = dict(zip([str(x) for x in items_to_tag], items_to_tag))
query_params = {	"tags_to_set":	param_tags,
			"items_to_tag":	param_items,
			"mode":		mode }

result = config.xmlrpc_server.set_tags(query_params)
print "<hr /><div>"
if result['success']:
	print "SUCCESS!<br />"
else:
	print "FAILED!<br />"
	print result['explanation']
	gen_error('GENERIC')
print "Links updated<br /><br />"
print "</div>"


print """<form id="hash_form" method="post" action="edit_tags.py">"""
print """<div>"""
for a_hash in items_to_tag:
	print """<input type="hidden" name="hashes" value="%s" />""" % a_hash

if len(items_to_tag) == 1:
	print """<input type="submit" value="Keep setting tags on this file" accesskey="k" />"""
else:
	print """<input type="submit" value="Keep setting tags on these files" accesskey="k" />"""

print """</div>
</form>"""
print """<div>or <a href="index.py">Go home</a></div>"""


if form.has_key("continue"):
	if len(items_to_tag) == 1:
		new_location = "edit_tags.py?" + items_to_tag[0]
		print """
REDIRECTING TO: `%s`...<br />
<script type="text/javascript">
// <![CDATA[
	location.href="%s";
// ]]>
</script>
<noscript><strong>Auto-return after tagging needs JavaScript. Please enable JavaScript, or do it manually</strong></noscript>
""" % (new_location, new_location)
	else:
		print """
<script type="text/javascript">
// <![CDATA[
	document.getElementById("hash_form").submit();
// ]]>
</script>
<noscript><strong>Auto-return after tagging needs JavaScript. Please enable JavaScript, or do it manually</strong></noscript>
"""
