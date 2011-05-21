#!/usr/bin/python

import os
import xmlrpclib
import cgi
import cgitb; cgitb.enable()
from hashlib import sha1
import hmac

import util_regexes
from util_baseconvert import base32_to_base16
from util_baseconvert import base16_to_base32
from util_errors import http_error
from util_errors import gen_error
from util_errors import HOMEPAGE_LINK
from util_html import meidokon_html_headers
from util_html import meidokon_html_footers

# New-style config
import frontend_config
config = frontend_config.get_config_for_hostname(os.environ.get('SERVER_NAME', 'NO_HOSTNAME'))

# Automatically close the HTML cleanly, whether we finish normally, or halfway through something
import atexit
atexit.register(meidokon_html_footers)


form = cgi.FieldStorage()
hashes = set([base32_to_base16(x) for x in form.getlist("hashes") if util_regexes.base16_or_32.search(x)])
hashes = list(hashes)
password = form.getfirst("password", "")

if len(hashes) == 0:
        http_error(400, "No valid hashes were supplied")


print "Content-Type: text/html"
print '''P3P: policyref="/w3c/privacy.p3p", CP=""'''
print ""
meidokon_html_headers("File deletion")

print """<div style="position:fixed; left:1em; top:1em; border:1px dotted"><a href="%s">Go home</a></div>""" % HOMEPAGE_LINK

print """<h3>Deleting:</h3><div><ul class="tag_tree">"""
for hash in hashes:
	print """<li>%s</li>""" % hash
print """</ul></div>"""


for hash in hashes:
	print """<div style="border:2px red solid;">"""
	print "Retrieving file data... "
	filedata = config.xmlrpc_server.get_filedata(hash)
	if not filedata['success']:
		print "Failed! -- " + filedata['explanation'] + "<br />"
		print "</div>"
		continue
	print "OK<br />"

	print """<table style="border:2px solid black;" class="metadata">"""
	for x in filedata['data']:
		print """<tr><th>%s</th><td>%s</td></tr>""" % (str(x), str(filedata['data'][x]))
	print """</table>"""

	print "Deleting file..."
	hmac_password = hmac.new(password, hash, sha1).hexdigest()
	result = config.xmlrpc_server.delete_file(hash, hmac_password)
	if not result['success']:
		print "Failed! -- " + str(result['explanation']) + "<br />"
	else:
		print "OK<br />"

	print "</div>"


import sys
sys.exit()

