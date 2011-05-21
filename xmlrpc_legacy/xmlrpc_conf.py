class Production(object):
	# General parameters for running the XMLRPC server
	bind_ip = '127.0.0.1'
	bind_port = 8002
	db_hostname = 'localhost'
	db_dbname = 'db_name'
	db_username = 'db_user'
	db_password = 'db_pass'
	syslog_name = 'meidokon_xmlrpc'

	# No authentication, just used to verify deletion requests
	deletion_password = 'delete_password'

	# Threshold when looking for matching tags, sort of a paranoia safety
	MAX_LEVENSHTEIN_DISTANCE = 20

	# Old code, theoretically allows you to run >1 instance in a single DB
	tbl_files = "files"
	tbl_assoc = "assoc"
	tbl_tags = "tags"
	tbl_types = "types"
	tbl_inherit = "inheritances"
	tbl_aliases = "aliases"

	# Parameters for connecting to your content server
	import xmlrpclib
	master_content_xmlrpc_server = xmlrpclib.ServerProxy("http://datastore.meidokon.net/xmlrpc.py")
	INSERTION_SHARED_SECRET = "513f401462da13ef997644832767f383b0afe8f4"
	RELEASE_SHARED_SECRET = "6dbf1c362e11af68ae0e99999e83ad84cfb5e58c"
	DELETION_SHARED_SECRET = "11c72e42e8f85dee27e52fab7a07b818d1a0905f"


class Development(Production):
	bind_port = 8003
	syslog_name = 'meidokon_xmlrpc_devmode'



config_sets = {}
config_sets['production'] = Production
config_sets['development'] = Development

