import os
import sys

def application(environ, start_response):
	# cwd gets set to /, which is annoying :(
	cwd = os.path.dirname(__file__)
	sys.path.insert(0, cwd)
	import util_regexes
	from util_baseconvert import base32_to_base16
	from util_baseconvert import base16_to_base32
	from util_http import http_response
	import conf

	# Setup our output
	output = http_response(environ, start_response)
	sys.stdout = output
	wsgi_errors = environ['wsgi.errors']

	# Get the hash
	QUERY = environ.get('QUERY_STRING', '')
	if not util_regexes.base16_or_32.match(QUERY):
		return output.user_failure("No hash supplied, or invalid hash format. hash=%s" % QUERY)

	# Send a redirection header
	# We just dumbly assume jpeg
	return output.redirect("%sm%s.jpg" % (conf.MID_URLBASE, base32_to_base16(QUERY)))

