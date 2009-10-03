#!/usr/bin/python

# Sometimes files don't get released properly. This takes the necessary hash and signature
# and calls the datastore's release function for you.
#
# The hash and signature are computed from manage_probation.py and sent here via a GET.
# There's no reason we couldn't have done it here, I jus felt like doing it this way.


# General imports
import cgi
import cgitb; cgitb.enable()

from util_html import meidokon_html_headers
from util_html import meidokon_html_footers
from conf import *

# Automatically close the HTML cleanly, whether we finish normally, or halfway through something
import atexit
atexit.register(meidokon_html_footers)



# First stdout output
print """Content-Type: text/html; charset=utf-8
P3P: policyref="/w3c/privacy.p3p", CP=""
"""

meidokon_html_headers()



form = cgi.FieldStorage()

if form.has_key('hash') and form.has_key('signature'):
	# hit it!
	hash = form.getfirst('hash', '')
	signature = form.getfirst('signature', '')
	import xmlrpclib
	xmlrpc_server = xmlrpclib.ServerProxy("http://datastore.meidokon.net/xmlrpc.py")
	result = xmlrpc_server.release(hash, signature)
	if result['success']:
		print "Success! File released -- " + result['explanation']
	else:
		print "Failed! File not released -- " + result['explanation']

	# Finish up
	print '''<br /><a href="%s%s">Edit tags</a>''' % (EDIT_PAGE_PATH, hash)
else:
	print """Nothing to do, please supply a hash and signature"""

