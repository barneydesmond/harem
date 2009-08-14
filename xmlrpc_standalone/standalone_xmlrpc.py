#!/usr/bin/python2.4

import os
import sys
import time
import xmlrpclib
import pgdb
import SimpleXMLRPCServer
import SocketServer

from hash_manipulation import *
from db_params import *
from xmlrpc_conf import *



class CustomXMLRPCRequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
	server_version = "Meidokon XML-RPC Service"
	sys_version = "XML-RPC/2.0"


class SimpleThreadedXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):
	def serve_forever(self):
		self.stop = False
		while not self.stop:
			self.handle_request()

class StandaloneXMLRPC(object):
	def __init__(self):
		self.connection = pgdb.connect(host=db_hostname, database=db_dbname, user=db_username, password=db_password)

	def open_connection():
		pass

	def none_to_empty_string(foo):
		if foo == None:
			return ''
		return foo

	def return_error(explanation='An unknown error has occurred'):
		response = {}
		response['success'] = False
		response['explanation'] = explanation
		return response

	def return_success(explanation='SUCCESS', data={}):
		response = {}
		response['success'] = True
		response['explanation'] = explanation
		if data:
			response['data'] = data
		return response

	def get_filedata(hash):
		"""Takes a base16 or base32 hash and returns the file's metadata in a struct.

		Function is expected to retrieve a single tuple from the DB and return that data.
		The data is returned in an XMLRPC struct, containing param->value mappings.
		If there is no data for that file, then return a failure, and an according message.
		"""
		try:
			hash = base32_to_base16(hash)
		except:
			return return_error("File hash was in an invalid format. File metadata could not be retrieved.")

		try:
			open_connection()
		except Exception, data:
			return return_error("There was a problem connecting to the database. -- %s" % str(data))

		cursor = self.connection.cursor()
		cursor.execute('SELECT * FROM "'+tbl_files+'" WHERE "hash"=%(hash)s', {'hash':hash})
		if not cursor.rowcount:
			return return_error("No image was found with that hash")
		column_names = [x[0] for x in cursor.description]
		filetuple = cursor.fetchone()
		filedata = dict(zip(column_names, filetuple))
		return return_success("Found image data", filedata)


	def get_tags_on_file(hash):
		"""Takes a base16 or base32 hash and returns the tags on a file as an array of tagids(integers)."""
		try:
			hash = base32_to_base16(hash)
		except:
			return return_error("File hash was in an invalid format. Could not retrieve tags.")

		try:
			open_connection()
		except Exception, data:
			return return_error("There was a problem connecting to the database. -- %s" % str(data))

		cursor = self.connection.cursor()
		cursor.execute('SELECT "tagid" FROM get_tags_on_file(%(hash)s)', {'hash':hash})
		if not cursor.rowcount:
			return return_error("No tags set on image")
		tagids_on_file = [x[0] for x in cursor.fetchall()]
		return return_success("Found tags on file", tagids_on_file)



	def get_taglist():
		"""Retrieves a full list of tags from the server.

		It'll be returned pretty much verbatim from the server as a list of lists (an array of arrays, in XMLRPC).
		As this data is pretty big, the client is expected to keep this data unless there's a newer copy.
		A standalone app might retrieve a new copy once a day."""
		start = time.time()
		try:
			open_connection()
		except Exception, data:
			return return_error("There was a problem connecting to the database. -- %s" % str(data))

		try:
			cursor = self.connection.cursor()
			cursor.execute('SELECT * FROM "%s"' % tbl_tags)
			tags = [[none_to_empty_string(x) for x in y] for y in cursor.fetchall()]
			fin = time.time()
			dif = str(1000*(fin-start))
			return return_success("Got taglist -- %s ms"%dif, tags)
		except Exception, data:
			return return_error("There was a problem getting the taglist. -- %s" % str(data))


	def get_tag_types():
		"""Retrieve a simple list of tag-types available in the system"""
		try:
			open_connection()
		except:
			return return_error("There was a problem connecting to the database.")
		cursor = self.connection.cursor()

		cursor.execute("""SELECT display_order,type,COALESCE("display_depends",'') AS "display_depends",COALESCE("contingent",0) AS "contingent" FROM """ + '"' + tbl_types + '"' + """ ORDER BY "display_order" """)
		if not cursor.rowcount:
			return return_error("No tag types defined in database.")
		column_names = [x[0] for x in cursor.description]
		types = cursor.fetchall()
		return_tuples = {}
		for x in types:
			return_tuples[str(x[0])] = dict(zip(column_names, x))
		for key in return_tuples:
			return_tuples[key]['contingent'] = ''
		return return_success("Found tag types available", return_tuples)


	def run(self):
		# Import Psyco if available
		try:
			import psyco
			psyco.full()
		except ImportError:
			pass
		else:
			print 'Loaded psyco...'

		server = SimpleThreadedXMLRPCServer(("202.4.232.68", 8001), CustomXMLRPCRequestHandler, 0)

		#server.register_introspection_functions()
		server.register_function(self.get_filedata)
		server.register_function(self.get_tags_on_file)
		server.register_function(self.get_taglist)
		server.register_function(self.get_tag_types)

		print "IP: ", server.server_address[0]
		print "Port: ", server.server_address[1]
		print "Now serving requests"
		try:
			server.serve_forever()
		except Exception, data:
			print "Exiting for exception -- %s" % str(data)
			sys.exit(0)



if __name__ == "__main__":
	s = StandaloneXMLRPC()
	s.run()
