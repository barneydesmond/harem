#!/usr/bin/python

# Interface to the metadata server
import xmlrpclib
xmlrpc_server = xmlrpclib.ServerProxy("http://xmlrpc.meidokon.net/RPC2")


# These paths work by appending the hash, you can point them anywhere
EDIT_PAGE_PATH = "http://meidokon.net/edit_tags.py?"
THUMBNAIL_PATH = "hash_thumb.py?"
MID_VER_PATH = "hash_mid.py?"
FULL_VER_PATH = "hash_full.py?"

# Storage directories
PROBATION_DIR = "_probation/"
FULL_DIR = "_full/"
MID_DIR = "_mid/"
THUMB_DIR = "_thumb/"

# Allows the metadata server to request the content server to "release" a file for viewing (or delete a file)
INSERTION_SHARED_SECRET = "513f401462da13ef997644832767f383b0afe8f4"
RELEASE_SHARED_SECRET = "6dbf1c362e11af68ae0e99999e83ad84cfb5e58c"
DELETION_SHARED_SECRET = "11c72e42e8f85dee27e52fab7a07b818d1a0905f"

db_hostname = "local.db.host"
db_dbname = "upload_tracking"
db_username = "upload_tracking"
db_password = "XXXX"

tbl_uploads = "uploads"
