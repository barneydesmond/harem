DOCTYPE_HTML_401_STRICT = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
   "http://www.w3.org/TR/html4/strict.dtd">"""
DOCTYPE_XHTML_11 = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
   "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">"""

TITLE = ": : meidokon.net : :"
STYLESHEET = """<link rel="stylesheet" href="meidokon_v1.css" type="text/css" title="meidokon.net v1" />"""
PRIVACY = """<link rel="P3Pv1" href="/w3c/p3p.xml" />"""
CONTENT_TYPE = """<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />"""
JAVASCRIPT = ''
IE7_FIX = """<!-- compliance patch for microsoft browsers -->
	<!--[if lt IE 7]>
	<script src="/ie7/ie7-standard-p.js" type="text/javascript"></script>
	<script src="/ie7/ie7-css-strict.js" type="text/javascript"></script>
	<![endif]-->"""


def meidokon_html_headers(title=TITLE, *head_items):
	print DOCTYPE_XHTML_11
	print """<html>\n<head>
	<title>%s</title>
	%s
	%s
	%s
	%s
	%s""" % (title, CONTENT_TYPE, STYLESHEET, PRIVACY, JAVASCRIPT, IE7_FIX)
	for item in head_items:
		print "\t%s" % item
	print "</head>\n<body>"


def meidokon_html_footers():
	print '<hr />'
	print '<div>'
	print """	<a href="http://validator.w3.org/check?uri=referer"><img
		class="borderless"
		src="w3c/valid-xhtml11"
		alt="Valid XHTML 1.1" height="31" width="88" /></a>"""
	print """This page just might be XHTML 1.1 compliant!"""
	print '</div>'
	print '</body>'
	print '</html>'


def meidokon_http_headers():
	headers = []
	headers.append("""Content-Type: text/html; charset=utf-8""")
	headers.append('P3P: policyref="/w3c/p3p.xml", CP="NOI NOR CURa OUR"')

	for x in headers:
		print x
	print
