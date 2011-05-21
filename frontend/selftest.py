#!/usr/bin/python

import sys
import os


class output(object):
	'''Build the output in a piecemeal fashion as tests pass/fail'''
	def __init__(self):
		self.output_buffer = ''

	def __str__(self):
		return "Content-Type: text/plain\r\n\r\n" + self.output_buffer

	def append(self, line):
		self.output_buffer += line+'\n'

	def append_and_finish(self, line):
		self.output_buffer += line+'\n'
		print self
		sys.exit(0)

page_output = output()


# 1. check http auth
# no need for this now
USERNAME = os.environ.get('REMOTE_USER', 'NOUSER')
#if not USERNAME:
#	page_output.append_and_finish("* FAIL HTTP auth")
#page_output.append("* PASS HTTP auth for %s" % USERNAME)
import pwd
page_output.append("* user is %s" % pwd.getpwuid(os.getuid())[0])
#for i in os.environ:
#	page_output.append("%s: %s" % (i, os.environ[i]))


# 2. session handling
import session
try:
	sess = session.Session(expires='', cookie_path='/')
	sess.data['lastvisit'] = repr("this is a string")
	sess.close()
except Exception, data:
	page_output.append_and_finish("* FAIL starting the session: %s" % str(data))
page_output.append("* PASS started a session")


# 3. read a file
#### test commented out as the test file has been removed.
#test_filename = 'master.jpg'
#try:
#	f = open(test_filename, 'rb')
#	data = f.read()
#	f.close()
#	del(data) # free up the memory we just used
#except Exception, data:
#	page_output.append_and_finish("* FAIL couldn't read the testfile %s: %s" % (test_filename, str(data)))
#page_output.append("* PASS read the testfile %s" % test_filename)
#

# 4. write a file
import time
timestamp = repr(time.time())
test_filename = 'aTestFile'+timestamp
try:
	f = open(test_filename, 'w')
	f.write("this is a test file")
	f.close()
except Exception, data:
	page_output.append_and_finish("* FAIL couldn't write the testfile %s: %s" % (test_filename, str(data)))
page_output.append("* PASS wrote the testfile %s" % test_filename)
# 4a. delete the file
try:
	os.unlink(test_filename)
except Exception, data:
	page_output.append_and_finish("* FAIL couldn't delete the testfile %s: %s" % (test_filename, str(data)))
page_output.append("* PASS deleted the testfile %s" % test_filename)


# 6. XML-RPC
try:
	import xmlrpclib
	xmlrpc_server = xmlrpclib.ServerProxy("http://xmlrpc.meidokon.net/RPC2")
	taglist = xmlrpc_server.get_all_tags('')['data'].values()
except Exception, data:
	page_output.append_and_finish("* FAIL XMLRPC call: %s" % str(data))
page_output.append("* PASS XMLRPC call returned data (truncated sample): %s" % str(taglist)[:50])



page_output.append("")
page_output.append_and_finish("Hello %s everything is great!" % USERNAME)

