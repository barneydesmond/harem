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

	# Get metadata
	filedata = conf.xmlrpc_server.get_filedata(QUERY)
	if not filedata['success']:
		return output.not_found("Hash not found")

	# Send a redirection header
	return output.redirect("%s%s.%s" % (conf.FULL_URLBASE, base16_to_base32(QUERY), filedata['data']['ext']))

