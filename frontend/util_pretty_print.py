__tabout = "\t"

def pretty(object, depth=0):
	if depth > 10:
		return

	if type(object) == dict:
		print "Dictionary"
		print __tabout * depth + "{"
		for key in object:
			print __tabout * (depth+1) + "[%s] => " % key,
			pretty(object[key], depth+1)
		print __tabout * depth + "}"

	elif type(object) == list:
		print "List"
		print __tabout * depth + "["
		num_width = len(str(len(object)))
		for i in range(len(object)):
			print __tabout * (depth+1) + "[%s%s] => " % ( ' '*(num_width-len(str(i))), str(i) ),
			pretty(object[i], depth+1)
		print __tabout * depth + "]"

	elif type(object) == set:
		print "Set"
		print __tabout * depth + "<"
		for x in object:
			print __tabout * (depth+1),
			print "[*] => ",
			pretty(x)
		print __tabout * depth + ">"

	else:
		print object

def html_pretty(object):
	global __tabout
	__tabout = "    "
	print "<pre>"
	pretty(object)
	print "</pre>"
