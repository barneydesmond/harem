#!/usr/bin/python2.4 -u

import os
import sys

import util_regexes
from util_baseconvert import base32_to_base16
from util_baseconvert import base16_to_base32
from util_errors import http_error
#from util_errors import gen_error
from util_html import meidokon_html_headers
from util_html import meidokon_html_footers

from conf import *

# Automatically close the HTML cleanly, whether we finish normally, or halfway through something
import atexit
#atexit.register(meidokon_html_footers)


# Get the hash
QUERY = os.environ.get('QUERY_STRING', '')
if not util_regexes.base16_or_32.match(QUERY):
	http_error(400, "No valid hashes were supplied")



# Send a redirection header
# FIND ANOTHER MECHANISM TO DO FILE EXTENSIONS
# ASSUME JPG FOR NOW
print "Status: 302 Redirecting..."
print "Location: %sm%s.jpg" % (MID_DIR, base32_to_base16(QUERY))
print
