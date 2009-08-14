import xmlrpclib

class Production(object):
	## General parameters for connecting the frontend to the XMLRPC server
	xmlrpc_server = xmlrpclib.ServerProxy("http://xmlrpc.meidokon.net/RPC2")

	## Levenshtein match distance when doing text-based tag searches
	lev_threshold = 2

	## We have to deal with the master content server a little
	# This is where we send file uploads to
	file_upload_target = "http://tsutako.meidokon.net/file_upload.py"

	## Controls the rendered HTML output for the frontend
	# These paths work by appending the hash, you can point them anywhere
	EDIT_PAGE_PATH = "edit_tags.py?"
	THUMBNAIL_PATH = "http://tsutako.meidokon.net/hash_thumb.py?"
	MID_VER_PATH = "http://tsutako.meidokon.net/hash_mid.py?"
	FULL_VER_PATH = "http://tsutako.meidokon.net/hash_full.py?"
	# These parameters govern the display of thumbnails returned by a query
	DEFAULT_LIMIT = 50
	DEFAULT_OFFSET = 0
	IMAGES_PER_ROW = 5
	# Some silly fun for the front page
	headings = [
		'''How many roads must a maid walk down..?''',
		'''A match maid in heaven''',
		'''"So a maid walks into a bar..."''',
		'''In Maids We Trust''',
		'''One small step for a maid, one giant leap for maidkind.''',
		'''We can't stop here, this is maid country!''',
		'''Frankly my dear, I don't give a maid''',
		'''I love the smell of maid in the morning''',
		'''DID YOU ORDER THE CODE-MAID!?''',
		'''We need Maids. Lots of maids.''',
		'''Maid nano wa ikenai to omoimasu!''',
		'''May the Maid be with you''',
		'''Maid's a maid, but they call it Le Maid''',
		'''MAID, MOTHERFUCKER, DO YOU SPEAK IT!?''',
		'''Maids can fly because they can take themselves lightly''',
		'''The first rule of meidokon is - you do not talk about maids''',
		'''Nobody expects the maidish inquisition!''',
		'''You want the maid? You can't handle the maid!''',
		'''This is my maid. There are many like it, but this one is mine.''',
	]

	## Crufty old code we need to get rid of, the XMLRPC interface should handle giving suggestions
	MAX_LEVENSHTEIN_DISTANCE = 20
	db_hostname = "localhost"
	db_dbname = "db_name"
	db_username = "db_user"
	db_password = "db_password"
	tbl_files = "files"
	tbl_assoc = "assoc"
	tbl_tags = "tags"
	tbl_types = "types"
	tbl_inherit = "inheritances"
	tbl_aliases = "aliases"



class Development(Production):
	xmlrpc_server = xmlrpclib.ServerProxy("http://localhost:8003/RPC2")



# DEFAULT IS A MAGIC WORD THAT MUST EXIST
config_sets = {}
config_sets['DEFAULT'] = Production
config_sets['production'] = Production
config_sets['dev.meidokon.net'] = Development

def get_config_for_hostname(hostname):
	if hostname in config_sets.keys():
		return config_sets[hostname]
	else:
		return config_sets['DEFAULT']

