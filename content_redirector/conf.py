# Interface to the metadata server
import xmlrpclib
xmlrpc_server = xmlrpclib.ServerProxy("http://xmlrpc.meidokon.net/RPC2")

# Various directories for the images, ALWAYS has a trailing slash
FULL_URLBASE = 'http://datastore.meidokon.net/_full/'
MID_URLBASE = 'http://datastore.meidokon.net/_mid/'
THUMB_URLBASE = 'http://datastore.meidokon.net/_thumb/'
