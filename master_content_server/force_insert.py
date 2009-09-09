#!/usr/bin/python2.4 -u

import pgdb
import sys
import os.path
import sha
import hmac
import Image
from conf import *

# For upload preparsing
import Image
try:
	from mod_autotag import functions as autotag_functions
except:
	pass


filename = sys.argv[1]
filepath = os.path.join("_probation", filename)

metadata = {}
FORMAT_TO_EXT = {	"JPEG": ".jpg",
			"GIF":  ".gif",
			"BMP":  ".png",
			"PNG":  ".png" }


f = open(filepath, 'rb')
metadata["hash"] = sha.new(f.read()).hexdigest()
f.close()
metadata["filename"] = filename

img = Image.open(filepath)
img.verify()
img = Image.open(filepath)
metadata["format"] = img.format
#img = img.convert("RGB")
(metadata["width"], metadata["height"]) = img.size
metadata["ext"] = FORMAT_TO_EXT[metadata["format"]][1:]
del(img)


print "hash is: " + metadata["hash"]
print "width x height is: %s,%s" % (metadata["width"], metadata["height"])
print "type is: " + metadata["format"]

# Enqueue the files in the local tracking database
try:
	conn = pgdb.connect(host=db_hostname, database=db_dbname, user=db_username, password=db_password)
	cur = conn.cursor()
except Exception, data:
	gen_error('GENERIC', "Couldn't connect to upload_tracking database")


tagids = set()
for x in autotag_functions:
	tagids.update([y for y in x(metadata) if type(y)==int])
metadata["array"] = ','.join([str(x) for x in tagids])

try:
	cur.execute('''INSERT INTO uploads VALUES (%(hash)s, %(width)s, %(height)s, %(ext)s, %(array)s, %(filename)s)''', metadata)
	conn.commit()
except Exception, data:
	print "Failed to insert local metadata, maybe a duplicate file -- " + str(data) + "<br />"


# Submit for insertion
msg = metadata["hash"] + str(metadata["width"]) + str(metadata["height"]) + str(metadata["ext"])
metadata["signature"] = hmac.new(INSERTION_SHARED_SECRET, msg, sha).hexdigest()

result = xmlrpc_server.add_file(metadata)
if result['success']:
	print "Success! File added -- " + result['explanation']
else:
	print "Failed! File not added -- " + result['explanation']

# Autotag the file if possible
if result['success']:
	param_tags = dict(zip([str(x) for x in tagids], tagids))
	param_items = {str(metadata["hash"]):metadata["hash"]}
	query_params = {	"tags_to_set":  param_tags,
				"items_to_tag": param_items,
				"mode":         'replace' }

	result = xmlrpc_server.set_tags(query_params)
	if result['success']:
		print "Success, applied auto-tags<br />"
	else:
	        print "Failed to apply auto-tags<br />"
		print result['explanation']

# Finish up
print '''<br /><a href="%s%s">Edit tags</a>''' % (EDIT_PAGE_PATH, metadata["hash"])

