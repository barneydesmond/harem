#!/usr/bin/python

# Developed on Python 2.6

# DEPENDENCIES
# * DB API 2.0 provider
#  * python-psycopg
#  * python-psycopg2
#  * python-pygresql
# * DBUtils - http://pypi.python.org/pypi/DBUtils/


import sys
import time
import optparse
import DocXMLRPCServer
import SocketServer
import xmlrpclib
from hashlib import sha1
import hmac
import syslog

import psycopg2
from DBUtils.PooledDB import PooledDB
from hash_manipulation import *
from xmlrpc_conf import config_sets


def prepare_syslog(syslog_name):
	syslog.openlog(syslog_name, syslog.LOG_PID, syslog.LOG_DAEMON)

def logmsg(message):
	syslog.syslog(syslog.LOG_INFO, message)


class CustomXMLRPCRequestHandler(DocXMLRPCServer.DocXMLRPCRequestHandler):
	server_version = "Meidokon XML-RPC Service"
	sys_version = "XML-RPC/2.0"

class NoWaitXMLRPCServer(DocXMLRPCServer.DocXMLRPCServer):
	allow_reuse_address = True

class SimpleThreadedXMLRPCServer(SocketServer.ThreadingMixIn, NoWaitXMLRPCServer):
	pass


class Error(Exception):
	pass


class LegacyXMLRPC(object):
	def __init__(self):
		# Because we're using the ThreadedMixIn, we need threadsafe DB connectivity.
		# DBUtils is awesome and provides thread-safe DB connections. This mattered
		# before switching from pgdb to psycopg, but DBUtils is nice anyway.
		# http://www.webwareforpython.org/DBUtils/Docs/UsersGuide.html
		self.pool = PooledDB(psycopg2, mincached=3, maxconnections=20, host=config.db_hostname, database=config.db_dbname, user=config.db_username, password=config.db_password)
		failcount = 0
		faillimit = 5
		while 1:
			try:
				self.server = SimpleThreadedXMLRPCServer((config.bind_ip, config.bind_port), CustomXMLRPCRequestHandler, 0)
				break
			except Exception, data:
				failcount += 1
				print "Failed to start"
				if failcount >= faillimit:
					raise Error("failed to start after %s attempts, dying" % failcount)
				time.sleep(1)

		self.server.set_server_title("Meidokon XML-RPC service")
		self.server.set_server_name("Meidokon XML-RPC API documentation")


	def return_error(self, explanation='An unknown error has occurred'):
		response = {}
		response['success'] = False
		response['explanation'] = explanation
		response['data'] = dict()
		logmsg("Error: %s, data=%s" % (str(explanation), str(dict)))
		return response

	def return_success(self, explanation='SUCCESS', data={}):
		response = {}
		response['success'] = True
		response['explanation'] = explanation
		response['data'] = data
		return response

	def int_or_none(self, x):
		try:
			foo = int(x)
			assert str(foo) == str(x), "The tagid was numeric but non-int"
		except Exception, data:
			return
		return foo

	def get_filedata(self, hash):
		"""Takes a base16 or base32 hash and returns the file's metadata in a struct.

		Function is expected to retrieve a single tuple from the DB and return that
		data. The data is returned in an XMLRPC struct, containing param->value
		mappings. If there is no data for that file, then return a failure, and
		empty data struct, and an according message.
		"""

		try:
			hash = base32_to_base16(hash)
		except:
			return self.return_error("File hash was in an invalid format. File metadata could not be retrieved.")

		try:
			connection = self.pool.connection()
			cursor = connection.cursor()
		except:
			return self.return_error("There was a problem connecting to the database.")

		try:
			cursor.execute('SELECT * FROM "'+config.tbl_files+'" WHERE "hash"=%(hash)s', {'hash':hash})
			if not cursor.rowcount:
				return self.return_error("No image was found with that hash")
			column_names = [x[0] for x in cursor.description]
			filetuple = cursor.fetchone()
		except:
			return self.return_error("Error while retriving file information from DB")

		cursor.close()
		connection.close()
		filedata = dict(zip(column_names, filetuple))
		filedata['date_added'] = str(filedata['date_added'])
		logmsg("Info: get_filedata(%s)" % hash)
		return self.return_success("Found image data", filedata)


	def get_tags(self, hash):
		"""Takes a base16 or base32 hash and returns the tags on a file as a
		struct of structs(one for each tag)
		"""

		try:
			hash = base32_to_base16(hash)
		except:
			return self.return_error("File hash was in an invalid format. Could not retrieve tags.")

		try:
			connection = self.pool.connection()
			cursor = connection.cursor()
		except:
			return self.return_error("There was a problem connecting to the database.")

		try:
			cursor.execute("""SELECT "tagid","name",COALESCE("gloss",'') AS "gloss","type" FROM get_tags_on_file(%(hash)s)""", {'hash':hash})
			if not cursor.rowcount:
				return self.return_error("No tags set on image %s" % hash)
			return_tuples = {}
			results = cursor.fetchall()
			column_names = [x[0] for x in cursor.description]
		except:
			return self.return_error("Error while retriving tags from DB")

		cursor.close()
		connection.close()
		for x in results:
			return_tuples[str(x[0])] = dict(zip(column_names, x))
		# this is quite verbose
		#logmsg("Info: get_tags(%s)" % hash)
		return self.return_success("Found tags on file", return_tuples)


	def get_child_tags(self, parent_tagids):
		"""We recieve a struct of tagids that are the "parents". We find and return
		their children.
		"""

		if not len(parent_tagids):
			return self.return_success("Found tags")

		try:
			connection = self.pool.connection()
			cursor = connection.cursor()
		except:
			return self.return_error("There was a problem connecting to the database.")

		tagid_string = ','.join([str(x) for x in parent_tagids.values()])
		try:
			cursor.execute('SELECT DISTINCT "tagid","name" FROM get_child_tags_from_string(%(parents)s) AS "tagid" NATURAL JOIN "'+config.tbl_tags+'"', {'parents':tagid_string})
			results = cursor.fetchall()
		except:
			return self.return_error("There was a problem while trying to find child tags")

		cursor.close()
		connection.close()
		return_tuples = dict(zip([str(x[0]) for x in results], [x[1] for x in results]))
		return self.return_success("Found tags", return_tuples)
		
		

	def get_all_tags(self, type, parents={}):
		"""Receive a type(string) and a struct of x->tagids, and return a
		struct of tagids->struct(full tuples from taglist).
		"""

		comma_parents = ','.join([str(x) for x in parents.values()])
		try:
			connection = self.pool.connection()
			cursor = connection.cursor()
		except:
			return self.return_error("There was a problem connecting to the database.")

		try:
			cursor.execute("""SELECT "tagid","name",COALESCE("gloss",'') AS "gloss","type","parent" FROM get_all_tags(%(type)s, %(parents)s)""", {'type':type, 'parents':comma_parents})
			tag_results = cursor.fetchall()
			column_names = [x[0] for x in cursor.description]

			cursor.execute('SELECT "'+config.tbl_tags+'"."tagid",COALESCE("r"."c", 0) FROM "'+config.tbl_tags+'" LEFT OUTER JOIN (SELECT "tagid",COUNT(*) AS "c" FROM "'+config.tbl_assoc+'" GROUP BY "tagid") AS "r" ON ("'+config.tbl_tags+'"."tagid"="r"."tagid")')
			tag_counts = cursor.fetchall()
		except:
			return self.return_error("Error while getting the list of tags")

		cursor.close()
		connection.close()
		return_tuples = {}
		for x in tag_results:
			tag_struct = dict(zip(column_names, x))
			return_tuples[str(x[0])] = tag_struct
		for x in tag_counts:
			if return_tuples.has_key(str(x[0])):
				return_tuples[str(x[0])]['count'] = x[1]
		return self.return_success("Found tags", return_tuples)



	def get_tag_types(self):
		"""Retrieve a simple list of tag-types available in the system
		"""

		try:
			connection = self.pool.connection()
			cursor = connection.cursor()
		except:
			return self.return_error("There was a problem connecting to the database.")

		try:
			cursor.execute("""SELECT display_order,type,COALESCE("display_depends",'') AS "display_depends",COALESCE("contingent",0) AS "contingent" FROM """ + '"' + config.tbl_types + '"' + """ ORDER BY "display_order" """)
			if not cursor.rowcount:
				return self.return_error("No tag types defined in database.")
			column_names = [x[0] for x in cursor.description]
			types = cursor.fetchall()
		except:
			return self.return_error("Error while retrieving list of tag types")

		cursor.close()
		connection.close()
		return_tuples = {}
		for x in types:
			return_tuples[str(x[0])] = dict(zip(column_names, x))
		for key in return_tuples:
			return_tuples[key]['contingent'] = ''
		return self.return_success("Found tag types available", return_tuples)



	def query(self, query_params):
		"""Issue a query as requested.

		This does a fair bit of processing on the query and turns it into some
		behemoth of SQL, but it works. Returns a bunch of tuples straight
		from the DB.
		"""

		try:
			limit = query_params['limit']
			offset = query_params['offset']
			query_tags = query_params['query_tags'].values()
		except KeyError:
			return self.return_error("Could not find named parameters in input for query")

		try:
			connection = self.pool.connection()
			cursor = connection.cursor()
		except:
			return self.return_error("There was a problem connecting to the database.")

		def expand_search_tags(expanded_set, base_tag, current_depth):
			max_recursion_depth = 4
			if current_depth > max_recursion_depth:
				return
			expanded_set.add(str(base_tag))

			try:
				cursor.execute('SELECT "tagid" FROM "'+config.tbl_inherit+'" WHERE "parent"=%(base)s', dict(base=base_tag))
				children_ids = [str(x[0]) for x in cursor.fetchall()]
				for child in children_ids:
					expanded_set.add(str(child))
					expand_search_tags(expanded_set, str(child), current_depth+1)
			except Exception, data:
				logmsg("Error: error during tag expansion of: %s; error was: %s" % (str(query_params), str(data)))
				return self.return_error("Error while expanding search tags at depth=%s" % current_depth)

		base = 'SELECT DISTINCT * FROM "' + config.tbl_files + '" '
		orderlimit = ' ORDER BY date_added DESC LIMIT ' + str(limit+1) + ' OFFSET ' + str(offset)


		def parse_query_logic_string(query):
			"""parse_query_logic_string will throw an exception if the query is
			malformed, so look out for it
			"""

			query_buffer = ''
			query_components = list(query)
			while len(query_components):
				# print query_buffer
				if query_components[0] == '%':
					del query_components[0] # Remove the opening '%'
					while query_components[0] != '%':
						query_buffer = query_buffer + str(query_components[0]) # Pass the enclosed characters directly
						del query_components[0]
					del query_components[0] # Remove the closing '%'
				elif query_components[0] == '!':
					if query_components[1] == '(':
						query_buffer = query_buffer + '(SELECT "hash" FROM "' + config.tbl_assoc + '" WHERE "hash" NOT IN ( '
						del query_components[0:2]
					else:
						raise QueryException, "! not followed by ( in query: " + str(query)
				elif query_components[0] == '(':
					query_buffer = query_buffer + '(SELECT "hash" FROM "' + config.tbl_assoc + '" WHERE "hash" IN ( '
					del query_components[0]
				elif query_components[0] == ')':
					query_buffer = query_buffer + ')) '
					del query_components[0]
				elif query_components[0] == '+':
					query_buffer = query_buffer + ' UNION '
					del query_components[0]
				elif query_components[0] == '*':
					query_buffer = query_buffer + ' INTERSECT '
					del query_components[0]
				elif str(query_components[0]) in '0123456789':
					query_buffer = query_buffer + '(SELECT "hash" FROM "' + config.tbl_assoc + '" WHERE "tagid"='
					while str(query_components[0]) in '0123456789':
						query_buffer = query_buffer + str(query_components[0])
						del query_components[0]
					query_buffer = query_buffer + ')'
				else:
					raise QueryException, "Unparseable character in query string: " + str(query)
			return query_buffer


		num_tags = len(query_tags)
		# print query_tags
		if num_tags:
			# Decide what's wanted and what isn't
			includes = set([self.int_or_none(x) for x in query_tags if x > 0])
			includes.discard(None)
			excludes = set([self.int_or_none(x) for x in query_tags if x < 0])
			excludes.discard(None)

			# Deal with potential query requesting inclusion and exclusion of the same tag
			includes.difference_update(excludes)

			# Now that they've been separated, flip all the excluded tags to +ve
			excludes = set([abs(x) for x in excludes])

			prepend_query = ' NATURAL JOIN ( '
			append_query = ' ) AS "foo" '
			logic_string = ''

			# Build the query string for inclusions
			if len(includes):
				include_strings = []
				for x in includes:
					included_set = set()
					# Basically a depth-first search of possible child-tags,
					# as deep as is specified in expand_search_tags
					expand_search_tags(included_set, x, 1)
					if len(included_set) == 1:
						include_strings.append(str(x))
					else:
						include_strings.append('(' + '+'.join(included_set) + ')')
				logic_string = logic_string + '(' + '*'.join(include_strings) + ')'

			if len(includes) and len(excludes):
				logic_string = logic_string + '*'

			if len(excludes):
				excluded_set = set()
				for x in excludes:
					# Another depth-first search to root out tags to exclude
					expand_search_tags(excluded_set, x, 1)
				logic_string = logic_string + '!(' + '+'.join([str(x) for x in excluded_set]) + ')'

			query_string = parse_query_logic_string(logic_string)
			q = base + prepend_query + query_string + append_query + orderlimit
		else:
			q = base + orderlimit

		try:
			cursor.execute(q)
			column_names = [x[0] for x in cursor.description]
			files = cursor.fetchall()
		except Exception, data:
			logmsg("Error: error while running query: %s; error was: %s" % (str(q), str(data)))
			return self.return_error("Error executing query")

		cursor.close()
		connection.close()
		return_tuples = {}
		file_count = 0
		for x in files:
			return_tuples[str(file_count)] = dict(zip(column_names, x))
			file_count = file_count + 1
		for x in return_tuples.values():
			x['date_added'] = str(x['date_added'])
		return self.return_success(q, return_tuples)



	def set_tags(self, params):
		"""Params is a struct containing a string, a struct of tagids,
		and a struct of hashes.
		"""

		try:
			mode = str(params['mode']).lower()
			tagids = params['tags_to_set']
			hashes = params['items_to_tag']
		except KeyError:
			return self.return_error("Could not find correct named parameters in request struct")

		if not mode in ('add', 'replace', 'remove'):
			return self.return_error("Incorrect mode specified")


		import os
		from hashlib import sha1
		import hmac
		def positive_ints(x): # Return only positive ints, or None
			try:
				foo = int(x)
				assert foo == x, "The tagid was numeric but non-int"
				assert foo > 0, "The tagid was integer but not greater-than-zero"
			except:
				return
			return foo

		def good_hashes(x): # Return only good hashes, or None
			try:
				foo = base32_to_base16(x)
			except:
				return
			return foo


		tagids = set([positive_ints(x) for x in tagids.values()])
		if None in tagids:
			tagids.remove(None)

		hashes = set([x for x in hashes.values()])
		if None in hashes:
			hashes.remove(None)

		# Defensive stuff here
		tripwires = set(['52cc75ff30cd0cb9230d10118e69a155372c33e9', 'ad11a26dda78498905e645ad7348b0fe8a1d5126'])
		if (tripwires & hashes):
			logmsg("Warning: tag modification denied")
			return self.return_error("Images blocked from modification due to abuse, your activities are unwelcome")

		if not len(hashes):
			return self.return_error("No files to tag, found this many: %s" % str(len(hashes)))


		# Prep DB connection
		try:
			connection = self.pool.connection()
			cursor = connection.cursor()
		except:
			return self.return_error("There was a problem connecting to the database.")


		# Start actually doing stuff now
		# Assets: mode(string), tagids(set), hashes(set)
		try:
			connection.commit() # Ensures we have a fresh transaction
		except:
			return self.return_error("Could not start database transaction")
		progress_string = "Opened database transaction with tagging mode &quot;%s&quot;...<br>\n" % mode
		logmsg("Info: setting tags {%s} on hashes {%s}" % (str(tagids), str(hashes)))

		if mode == 'remove':
			tagid_string = ' OR '.join(['"tagid"='+str(x) for x in tagids])
			try:
				cursor.executemany('DELETE FROM "'+config.tbl_assoc+'" WHERE "hash"=%(hash)s AND ('+tagid_string+')', [{'hash':str(x)} for x in hashes])
			except:
				connection.rollback()
				progress_string = progress_string + "Failed to delete tags.<br>\n"
				return self.return_error(progress_string)
			progress_string = progress_string + "Deleted tags...<br>\n"
		elif mode in ('replace', 'add'):
			if mode == 'replace': # Delete the old tags before setting up new ones, no way to ignore DB errors when doing this otherwise
				hash_string = ' OR '.join(['"hash"=\''+str(x)+'\'' for x in hashes])
				try:
					cursor.execute('DELETE FROM "'+config.tbl_assoc+'" WHERE '+hash_string)
				except Exception, data:
					connection.rollback()
					progress_string = progress_string + "Failed to delete old tags.<br>\n"
					return self.return_error(progress_string)
				progress_string = progress_string + "Deleted old tags...<br>\n"
			# Add or replace, this step is common to both
			for hash in hashes:
				for tagid in tagids:
					try:
						cursor.execute('DELETE FROM "'+config.tbl_assoc+'" WHERE "hash"=%(h)s and "tagid"=%(t)s', {'h':hash,'t':tagid})
					except:
						connection.rollback()
						progress_string = progress_string + "Failed to remove existing link with overlap %s and %s...<br />\n" % (hash, tagid)
						return self.return_error(progress_string)
					progress_string = progress_string + "Removed old tag %s and %s...<br />\n" % (hash, tagid)

					try:
						cursor.execute('INSERT INTO "'+config.tbl_assoc+'" VALUES ( %(h)s, '+str(tagid)+' )', {'h':hash})
					except:
						connection.rollback()
						progress_string = progress_string + "Failed adding link to attribute %s - %s<br />\n" % (hash, tagid)
						return self.return_error(progress_string)
					progress_string = progress_string + "Added association %s - %s<br />\n" % (hash, tagid)


		try:
			connection.commit()
		except:
			connection.rollback()
			progress_string = progress_string + "Could not commit database changes. Changes will be rolled back, files may have been deleted.<br />\n"
			return self.return_error(progress_string)

		cursor.close()
		connection.close()
		progress_string = progress_string + "Database updates completed!<br />\n"
		return self.return_success(progress_string)



	def add_file(self, params):
		"""Params is a struct containing a string(probation filepath) and
		a string(nice filename)
		"""

		msg = params["hash"] + str(params["width"]) + str(params["height"]) + str(params["ext"])
		digest = hmac.new(config.INSERTION_SHARED_SECRET, msg, sha1).hexdigest()
		if digest != params["signature"]:
			return self.return_error("Bad signature on request")

		progress_string = ""
		try:
			progress_string = progress_string + "Connecting to database..."
			connection = self.pool.connection()
			cursor = connection.cursor()
			progress_string = progress_string + "Inserting database entry... "
			cursor.execute('INSERT INTO "'+config.tbl_files+'" ("hash","width","height","ext") VALUES (%(hash)s, %(width)s, %(height)s, %(ext)s)', params)
			progress_string = progress_string + "Committing database modifications... "
			connection.commit()
			cursor.close()
			connection.close()
		except Exception, data:
			progress_string = progress_string + "FAILED! -- " + str(data) + "<br />\n"
			connection.rollback()
			return self.return_error(progress_string)
		else:
			progress_string = progress_string + "ALL DONE!<br /><br />\n"

		# Release the file at the content server
		try:
			progress_string = progress_string + "Requesting file release...<br />\n"
			h = hmac.new(config.RELEASE_SHARED_SECRET, params["hash"], sha1)
			progress_string = progress_string + "Calculated signature: " + h.hexdigest() + "<br />\n"
			retval = config.master_content_xmlrpc_server.release(params["hash"], h.hexdigest())
			if retval["success"]:
				progress_string = progress_string + "Success! File has been released"
			else:
				progress_string = progress_string + "Failure, file could not be released -- " + retval["explanation"]
		except Exception, data:
			progress_string = progress_string + "Failed to release file -- " + str(data) + "<br />\n"

	        return self.return_success(progress_string)



	def delete_file(self, hash, signature):
		"""Deletes entries from the database relating to the provided hash
		"""

		logmsg("Info: delete_file(%s, %s)" % (hash, signature))
		digest = hmac.new(config.deletion_password, hash, sha1).hexdigest()
		if digest != signature:
			return self.return_error("Bad signature on request")

		progress_string = ""
		try:
			progress_string = progress_string + "Connecting to database..."
			connection = self.pool.connection()
			cursor = connection.cursor()
			progress_string = progress_string + "Deleting database entry..."
			cursor.execute('DELETE FROM "'+config.tbl_files+'" WHERE "hash"=%(hash)s', {"hash":hash} )
			progress_string = progress_string + "Committing database modifications... "
			connection.commit()
			cursor.close()
			connection.close()
		except Exception, data:
			progress_string = progress_string + "FAILED! -- " + str(data) + "<br />\n"
			connection.rollback()
			return self.return_error(progress_string)
		else:
			progress_string = progress_string + "ALL DONE!<br /><br />\n"

		# Delete the file at the content server
		try:
			progress_string = progress_string + "Requesting file deletion...<br />\n"
			h = hmac.new(config.DELETION_SHARED_SECRET, hash, sha1)
			progress_string = progress_string + "Calculated signature: " + h.hexdigest() + "<br />\n"
			retval = config.master_content_xmlrpc_server.delete(hash, h.hexdigest())
			if retval["success"]:
				progress_string = progress_string + "Success! File has been deleted"
			else:
				progress_string = progress_string + "Failure, file could not be deleted -- " + retval["explanation"]
		except Exception, data:
			progress_string = progress_string + "Failed to delete file -- " + str(data) + "<br />\n"

		return self.return_success(progress_string)


	def run(self):
		#self.server.register_introspection_functions()
		self.server.register_function(self.get_filedata)
		self.server.register_function(self.get_tags)
		self.server.register_function(self.get_child_tags)
		self.server.register_function(self.get_all_tags)
		self.server.register_function(self.get_tag_types)
		self.server.register_function(self.query)
		self.server.register_function(self.set_tags)
		self.server.register_function(self.add_file)
		self.server.register_function(self.delete_file)

		logmsg("Info: listening on %s:%s" % (self.server.server_address[0], self.server.server_address[1]))
		try:
			self.server.serve_forever()
		except Exception, data:
			logmsg("Error: exiting for exception -- %s" % str(data))
			return 0



if __name__ == "__main__":
	parser = optparse.OptionParser()
	parser.add_option("-c", "--config", dest="config", help="Specify the Configuration mode to use, defaults to production mode", default='production')
	(options,args) = parser.parse_args()
	config = config_sets[options.config] # config is an object with attributes pertaining to config settings

	prepare_syslog(config.syslog_name)

	# Import Psyco if available - not the case on Ubuntu 9.04 (jaunty)
	try:
		import psyco
		psyco.full()
	except ImportError:
		logmsg('Info: starting up, did not load psyco optimiser')
	else:
		logmsg('Info: starting up, loaded psyco optimser')

	# We'll get an exception if the server can't be instantiated. A common reason for this is because the port is already in use, so we can't bind it
	try:
		s = LegacyXMLRPC()
	except Exception, data:
		logmsg(str(data))
		print str(data)
		sys.exit(1)

	sys.exit(s.run())




