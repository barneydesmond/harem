#!/usr/bin/python

# General imports
import cgi
import cgitb; cgitb.enable()
import os
import sha
import hmac
import StringIO
import urllib2
import pgdb

# For upload preparsing
import Image
try:
	from mod_autotag import functions as autotag_functions
except:
	pass

from util_html import meidokon_html_headers
from util_html import meidokon_html_footers
from conf import *
from util_errors import gen_error

# Automatically close the HTML cleanly, whether we finish normally, or halfway through something
import atexit
atexit.register(meidokon_html_footers)


FILE_FIELD_NAME = "files"
URL_FIELD_NAME = "urls"
LOCALFILE_FIELD_NAME = "fname"
FORMAT_TO_EXT = {	"JPEG":	".jpg",
			"GIF":	".gif",
			"BMP":	".png",
			"PNG":	".png" }


# First stdout output
print """Content-Type: text/html; charset=utf-8
P3P: policyref="/w3c/privacy.p3p", CP=""
"""

meidokon_html_headers()


# This is a self-posting form, because such things are nice
form = cgi.FieldStorage()

# This "interesting" coding style lets us get the easy case out of the way,
# which is sorta cleaner
if not form.has_key(FILE_FIELD_NAME) and not form.has_key(URL_FIELD_NAME) and not form.has_key(LOCALFILE_FIELD_NAME):
	# Not a form submission, so present a form
	print """<form action="%s" method="post" enctype="multipart/form-data">""" % os.environ['SCRIPT_NAME']
	print """	<div>
		<strong>Upload a file</strong><br />
		<input type="file" name="files" /><br />
		<input type="submit" value="Upload File" />
	</div>
	</form>"""

else:
	metadata = {}

	# Accept uploads
	if form.has_key(FILE_FIELD_NAME):
		if type(form[FILE_FIELD_NAME]) is list:
			items = form[FILE_FIELD_NAME]
		else:
			items = [form[FILE_FIELD_NAME]]
		# Can code it to accept more, but accepting a lot at once could be a problem
		if len(items) != 1:
			gen_error('GENERIC', "Attempting to upload too many files (or no files); one at a time please (by POST)")
		# Catch other stupid errors
		item = items[0]
		if not item.file or not item.filename:
			gen_error('GENERIC', "Couldn't get file upload data for some reason")
		file_data = item.value
		metadata["source"] = ''
	# Or snarf it via HTTP
	elif form.has_key(URL_FIELD_NAME):
		# Can code it to accept more, but accepting a lot at once could be a problem
		if len(form.getlist(URL_FIELD_NAME)) != 1:
			gen_error('GENERIC', "Attempting to upload too many files (or no files); one at a time please (by URL)")
		# Catch other stupid stuff
		url = form.getlist(URL_FIELD_NAME)[0]
		url_file = urllib2.urlopen(urllib2.Request(url,headers={'User-Agent':'MSIE LOL'}))
		file_data = url_file.read()
		url_file.close()
		metadata["source"] = url
	# Or find a file we manually injected into the probation directory
	elif form.has_key(LOCALFILE_FIELD_NAME):
		if len(form.getlist(LOCALFILE_FIELD_NAME)) != 1:
			gen_error('GENERIC', "Attempting to upload too many files (or no files); one at a time please (by filename)")
		# Catch other stupid stuff
		filename = form.getlist(LOCALFILE_FIELD_NAME)[0]
		filepath = os.path.join(PROBATION_DIR, filename)
		f = open(filepath, 'rb')
		file_data = f.read()
		f.close()
		metadata["source"] = ''
	else:
		gen_error('GENERIC', "Something bad happened, got neither URL nor POST upload")


	# Check for allowed filetypes
	try:
		img = Image.open(StringIO.StringIO(file_data))
		img.verify()
		img = Image.open(StringIO.StringIO(file_data))
	except:
		gen_error('GENERIC', "Not an image file, or the image is corrupt<br />")

	if img.format not in FORMAT_TO_EXT:
		gen_error('GENERIC', "Format `%s` is not allowed<br />" % img.format)
	else:
		print "Got file of type `%s`, okay...<br />" % img.format


	# Dump the file to disk, converting from BMP as needed
	try:
		tmp_name = sha.new(file_data).hexdigest() + FORMAT_TO_EXT[img.format]
		tmp_path = os.path.join(PROBATION_DIR, tmp_name)
		if img.format == 'BMP':
			print "bmp"
			img.save(tmp_path)
			print "did save"
			f = open(tmp_path, 'rb')
			correct_hash = sha.new(f.read()).hexdigest()
			f.close()
			correct_name = correct_hash + FORMAT_TO_EXT[img.format]
			correct_path = os.path.join(PROBATION_DIR, correct_name)
			os.rename(tmp_path, correct_path)
		else:
			tmp_file = open(tmp_path, 'wb')
			tmp_file.write(file_data)
			tmp_file.flush()
			tmp_file.close()
		print "File dumped to disk...<br />"
		del(img)
		del(file_data)
	except Exception, data:
		gen_error('FAIL_WRITING_UPLOAD', "Try checking permissions on the probation directory, and that there is free space on the drive.<br />")


	# Gather image metadata
	try:
		metadata["filename"] = tmp_name
		f = open(tmp_path, 'rb')
		metadata["hash"] = sha.new(f.read()).hexdigest()
		f.close()

		img = Image.open(tmp_path)
		img.verify()
		img = Image.open(tmp_path)
		metadata["format"] = img.format
		# This conversion line seems to be problematic. See if it's only needed on some formats or something
		img = img.convert("RGB")
		(metadata["width"], metadata["height"]) = img.size
		metadata["ext"] = FORMAT_TO_EXT[metadata["format"]][1:]
		del(img)
	except Exception, data:
		gen_error('GENERIC', "Could not read image metadata -- " + str(data))


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






