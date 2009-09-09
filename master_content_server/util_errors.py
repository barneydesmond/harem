#!/usr/bin/python

import sys

from util_html import meidokon_html_headers
from util_html import meidokon_html_footers

DEFAULT_LANG = 'EN'
DEFAULT_ERR = 'Status: 500 Internal Server Error'
DEFAULT_MSG = 'Something Went Boom, Sorry'
HOMEPAGE_LINK = 'index.py'

# Start the HTTP errors
HTTP_ERRORS = {}

# English, mothafucker, do you speak it?!
HTTP_ERRORS['EN'] = {}
HTTP_ERRORS['EN'][400] = 'Status: 400 Bad Request'
HTTP_ERRORS['EN'][403] = 'Status: 403 Forbidden'
HTTP_ERRORS['EN'][404] = 'Status: 404 Not found'
HTTP_ERRORS['EN'][500] = 'Status: 500 Internal Server Error'



GEN_ERRORS = {}
GEN_ERRORS['EN'] = {}
GEN_ERRORS['EN']['ERR_NO_SUCH_FILE'] = 'FAILED! There is no such file with that hash'
GEN_ERRORS['EN']['XMLRPC_TAG_LIST_GET'] = 'Failure while retrieving a list of all tags for display'
GEN_ERRORS['EN']['FAIL_WRITING_UPLOAD'] = 'Failure while attempting to write uploaded file to disk'
GEN_ERRORS['EN']['UNRECOGNISED_MODE'] = 'Unknown tagging mode was given'
GEN_ERRORS['EN']['GENERIC'] = 'An error occurred, of an unknown type'


def http_error(error_code, msg=DEFAULT_MSG, lang=DEFAULT_LANG):
	if lang not in HTTP_ERRORS.keys():
		lang = DEFAULT_LANG
	err = HTTP_ERRORS[lang].get(error_code, DEFAULT_ERR)
	print err
	print
	meidokon_html_headers()
	print msg
	sys.exit(msg)

def gen_error(error_code, msg=DEFAULT_MSG, lang=DEFAULT_LANG):
	if lang not in GEN_ERRORS.keys():
		lang = DEFAULT_LANG
	err = GEN_ERRORS[lang].get(error_code, DEFAULT_ERR)
	print '<div style="border:1px black dotted;">'
	print err, "<br />"
	print "Further data from error site: ", msg, "<br />"
	print """<a href="%s">Go home</a><br />\n""" % HOMEPAGE_LINK
	print '</div>'
	sys.exit(msg)
