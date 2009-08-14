#!/usr/bin/python

def positive_ints(x): # Return only positive ints, or None
	try:
		foo = int(x)
		assert str(foo) == str(x), "The tagid was numeric but non-int"
		assert foo > 0, "The tagid was integer but not greater-than-zero"
	except Exception, data:
		return None
	return foo


def int_or_none(x):
	try:
		foo = int(x)
		assert str(foo) == str(x), "The tagid was numeric but non-int"
	except Exception, data:
		return
	return foo


def compare_by(fieldname):
	def compare_two_dicts(a, b):
		return cmp(a[fieldname], b[fieldname])
	return compare_two_dicts


def colour_gen():
	colours = ['#ffaaaa', '#ffffaa', '#aaffaa']
	num_colours = len(colours)
	index = 0
	while True:
		pointer = colours[index]
		index = (index + 1) % num_colours
		yield pointer

def get_value_from_cookie(cookie_name):
	import os
	import Cookie
	if os.environ.has_key('HTTP_COOKIE'):
		c = Cookie.SimpleCookie()
		c.load(os.environ['HTTP_COOKIE'])
		if c.has_key(cookie_name):
			return c[cookie_name].value
	return ''


def space_to_under(string):
	import re
	if isinstance(string, str):
		return re.sub(r'[^A-Za-z0-9-]', r'_', string)
	else:
		return re.sub(r'[^A-Za-z0-9-]', r'_', string.group(1))
def under_to_space(string):
	import re
	return re.sub(r'_+', r' ', string)


def double_quote_string(string):
	if ' ' in string:
		return '''"%s"''' % (string)
	else:
		return string
