#!/usr/bin/python2.4 -u

import pgdb
import sys
import os.path
#import sha
import xmlrpclib

from util_html import meidokon_http_headers
from util_html import meidokon_html_headers
from util_html import meidokon_html_footers
from conf import *
from util_errors import gen_error

# Automatically close the HTML cleanly, whether we finish normally, or halfway through something
import atexit
atexit.register(meidokon_html_footers)

# Prep the XMLRPC server for queries
xs = xmlrpclib.ServerProxy("http://xmlrpc.meidokon.net/RPC2")


# First stdout output
meidokon_http_headers()
meidokon_html_headers()


# Get the probationary files
try:
	conn = pgdb.connect(host=db_hostname, database=db_dbname, user=db_username, password=db_password)
	cur = conn.cursor()
except Exception, data:
	gen_error('GENERIC', "Couldn't connect to upload_tracking database")

try:
	cur.execute('''SELECT "hash","width","height","ext","initial_tagids","filename" FROM ''' + tbl_uploads)
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
</tr>
'''


for img in listing:
	img[5:5] = [PROBATION_DIR, img[5]]
	try:
		img.append(str(xs.get_filedata(str(img[0]))["success"]))
	except:
		img.append('ERR')
	print '''<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td> <a href="%s%s">%s</a> </td><td>%s</td></tr>''' % tuple(img)


print '''</table>'''


