#!/usr/bin/python -u

import os
import cgi
import Cookie

form = cgi.FieldStorage()
full_resolver = form.getfirst("full_resolver", '')
mid_resolver = form.getfirst("mid_resolver", '')
thumb_resolver = form.getfirst("thumb_resolver", '')

print "Content-Type: text/plain"

if full_resolver or mid_resolver or thumb_resolver:
	c = Cookie.SimpleCookie()
	c['full_resolver'] = full_resolver
	c['mid_resolver'] = mid_resolver
	c['thumb_resolver'] = thumb_resolver
	print c
	print
	print
	print "OK"
	print c
else:
	f = Cookie.Morsel()
	m = Cookie.Morsel()
	t = Cookie.Morsel()

	f.key = 'full_resolver'
	f["max-age"] = 0
	print f.output()
	m.key = 'mid_resolver'
	m["max-age"] = 0
	print m.output()
	t.key = 'thumb_resolver'
	t["max-age"] = 0
	print t.output()

	print
	print
	print "OK"
	print f.output()
	print m.output()
	print t.output()
