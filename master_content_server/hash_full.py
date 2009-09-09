#!/usr/bin/python2.4 -u

import os
import sys

import util_regexes
from util_baseconvert import base32_to_base16
from util_baseconvert import base16_to_base32
from util_errors import http_error
#from util_errors import gen_error
from util_html import meidokon_http_headers
from util_html import meidokon_html_headers
from util_html import meidokon_html_footers

from conf import *


# Get the hash
QUERY = os.environ.get('QUERY_STRING', '')
if not util_regexes.base16_or_32.match(QUERY):
	http_error(400, "No valid hashes were supplied")



# Send a redirection header
filedata = xmlrpc_server.get_filedata(QUERY)
if not filedata['success']:
	http_error(404, "Hash not found")
print "Status: 302 Redirecting..."
print "Location: %s%s.%s" % (FULL_DIR, base16_to_base32(QUERY), filedata['data']['ext'])
print
