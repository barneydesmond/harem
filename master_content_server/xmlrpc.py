#!/usr/bin/python2.4 -u

# General imports
import SimpleXMLRPCServer
import os
import os.path
import sha
import hmac
import pgdb

# For upload preparsing
import Image

from util_baseconvert import base32_to_base16
from util_baseconvert import base16_to_base32
from conf import *



def release(hash, signature):
	h = hmac.new(RELEASE_SHARED_SECRET, hash, sha)
	if h.hexdigest() == signature:
		retval = {"success":False}
		try:
			conn = pgdb.connect(host=db_hostname, database=db_dbname, user=db_username, password=db_password)
			cur = conn.cursor()
		except Exception, data:
			retval["explanation"] = "Failed to connect to DB"
			return retval

		try:
			cur.execute('''SELECT filename,ext from uploads WHERE hash=%(h)s''', {"h":hash} )
			d = cur.fetchall()
			filename, ext = d[0][0], d[0][1]
			cur.execute('''DELETE FROM uploads WHERE hash=%(h)s''', {"h":hash} )
			conn.commit()
		except:
			retval["explanation"] = "No such file to release"
			return retval

		tmp_full	= os.path.join(PROBATION_DIR, filename)
		tmp_mid		= os.path.join(PROBATION_DIR, 'm' + hash + '.jpg')
		tmp_thumb	= os.path.join(PROBATION_DIR, 't' + hash + '.jpg')
		final_full	= os.path.join(FULL_DIR, base16_to_base32(hash) + '.' + ext)
		final_mid	= os.path.join(MID_DIR, 'm' + hash + '.jpg')
		final_thumb	= os.path.join(THUMB_DIR, 't' + hash + '.jpg')

		if not os.path.exists(tmp_full):
			retval["explanation"] = "Cannot find file to release"
			return retval

		try:
			img = Image.open(tmp_full).convert()
			img.thumbnail((400,400), Image.ANTIALIAS)

			try:
				os.unlink(tmp_mid)
			except:
				pass
			img.save(tmp_mid)
		except:
			retval["explanation"] = "Failed creating mid-size tempfile"
			return retval

		try:
			img = Image.open(tmp_full).convert()
			img.thumbnail((120,120), Image.ANTIALIAS)
			try:
				os.unlink(tmp_thumb)
			except:
				pass
			img.save(tmp_thumb)
		except:
			retval["explanation"] = "Failed creating thumbnail tempfile"
			return retval

		try:
			try:
				os.unlink(final_full)
			except:
				pass
			os.rename(tmp_full, final_full)
		except:
			retval["explanation"] = "Failed to move file into place"
			return retval

		try:
			try:
				os.unlink(final_mid)
			except:
				pass
			os.rename(tmp_mid, final_mid)
		except:
			retval["explanation"] = "Failed to move mid-size into place"
			return retval

		try:
			try:
				os.unlink(final_thumb)
			except:
				pass
			os.rename(tmp_thumb, final_thumb)
		except:
			retval["explanation"] = "Failed to move thumbnail into place"
			return retval

		retval["success"] = True
		retval["explanation"] = "Success"
		return retval
	else:
		retval["success"] = False
		retval["explanation"] = "Bad signature"
		return retval



def delete(hash, signature):
	h = hmac.new(DELETION_SHARED_SECRET, hash, sha)
	if h.hexdigest() == signature:
		final_full	= os.path.join(FULL_DIR, base16_to_base32(hash) + '.' + ext)
		final_mid	= os.path.join(MID_DIR, 'm' + hash + '.jpg')
		final_thumb	= os.path.join(THUMB_DIR, 't' + hash + '.jpg')

		retval = {"success":False}
		progress = ""
		try:
			progress = progress + "Starting..."
			os.unlink(final_thumb)
			progress = progress + "Deleted thumbnail..."
			os.unlink(final_mid)
			progress = progress + "Deleted mid-size..."
			os.unlink(final_full)
			progress = progress + "Deleted full-size..."
		except:
			pass
		retval["success"] = True
		retval["explanation"] = "Success -- " + progress
	else:
		retval["success"] = False
		retval["explanation"] = "Bad signature"
		return retval


if __name__ == '__main__':
	handler = SimpleXMLRPCServer.CGIXMLRPCRequestHandler()
	handler.register_function(release)
	handler.register_function(delete)
	handler.handle_request()
