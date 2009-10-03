#!/usr/bin/python

# DEPENDENCIES
# * DB API 2.0 provider
#  * python-psycopg
#  * python-psycopg2
#  * python-pygresql


import psycopg2
import sys
import xmlrpclib
import hashlib
import hmac

from util_html import meidokon_http_headers
from util_html import meidokon_html_headers
from util_html import meidokon_html_footers
from conf import *
from util_errors import gen_error

# Automatically close the HTML cleanly, whether we finish normally, or halfway through something
import atexit
atexit.register(meidokon_html_footers)

# First stdout output
meidokon_http_headers()
meidokon_html_headers()

# Prep the XMLRPC server for queries
xs = xmlrpclib.ServerProxy("http://xmlrpc.meidokon.net/RPC2")


# Get the probationary files
try:
	conn = psycopg2.connect(host=db_hostname, database=db_dbname, user=db_username, password=db_password)
	cur = conn.cursor()
except Exception, data:
	gen_error('GENERIC', "Couldn't connect to upload_tracking database")

try:
	cur.execute('''SELECT "hash","width","height","ext","initial_tagids","filename" FROM %s''' % tbl_uploads)
	listing = cur.fetchall()
except Exception, data:
	gen_error('GENERIC', "Failure reading list from database")


print '''
<table border="2">
<tr>
<th>Hash</th>
<th>Width</th>
<th>Height</th>
<th>Ext.</th>
<th>tagids</th>
<th>filename</th>
<th>Already in system</th>
<th>Release</th>
</tr>
'''


# ['e8be8ab09cd35d09ef9a95e970e51d8e2538f257', 1680, 1050, 'jpg', '47,375', 'e8be8ab09cd35d09ef9a95e970e51d8e2538f257.jpg']
keys = ['hash', 'width', 'height', 'ext', 'tags', 'filename']
for img in listing:
	img = dict(zip(keys,img))
	img['dir'] = PROBATION_DIR
	try:
		img['success'] = str(xs.get_filedata(img['hash'])["success"])
	except:
		img['success'] = 'ERR'

	img['release_signature'] = hmac.new(RELEASE_SHARED_SECRET, img['hash'], hashlib.sha1).hexdigest()

	print '''<tr><td>%(hash)s</td><td>%(width)s</td><td>%(height)s</td><td>%(ext)s</td><td>%(tags)s</td><td> <a href="%(dir)s%(filename)s">%(filename)s</a> </td><td>%(success)s</td><td><a href="release.py?hash=%(hash)s&signature=%(release_signature)s">Attempt release</a></td></tr>''' % img


print '''</table>'''


