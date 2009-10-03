Part of my work converting the content-serving from CGI to WSGI.

The content-serving is a bit mixed up with the upload-receiving, so I've dropped this in a separate directory. It can function entirely separately anyway.

The content-redirection is extremely thin. A few WSGI-served files and a handful of conf.

The content redirector would probably live on the same machine as the master content server, but need not. The redirector could easily discriminate between requests and balance them between content-servers.


TODO:
* could well roll hash_*.py into a single file and do URI-routing internally.


conf.py
hash_full.py
hash_mid.py
hash_thumb.py
util_baseconvert.py
util_http.py
util_regexes.py


1. For the sake of my own server-migration, I made a new subdomain, contentmaster.meidokon.net
2. The redirector will redirect to datastore.meidokon.net, a subdomain I happened to already have pointing to the right place
3. The frontend will then refer to contentmaster.meidokon.net
