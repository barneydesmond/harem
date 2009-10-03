import re

base16 =	re.compile('^[0-9a-f]{40}$', re.I)
base32 =	re.compile('^[2-7A-Z]{32}$', re.I)
base16_or_32 =	re.compile('^[0-9a-f]{40}$|^[2-7A-Z]{32}$', re.I)

safe_space_quotes =	re.compile("""[^a-zA-Z0-9_\s'"]+""", re.I)
quoted_string =		re.compile("""['"]([^'"]*?)['"]""")
alphanum =		re.compile("""[^a-zA-Z0-9]+""", re.I)
whitespace =		re.compile("""\s+""")
only_digits =		re.compile("""^\d+$""")

def chunkify_tag_input(tag_string):
	tag_string = tag_string.lower()
	tag_string = safe_space_quotes.sub('', tag_string)
	tag_string = quoted_string.sub(lambda x: alphanum.sub('_', x.group(1)), tag_string)

	# I originally did underscore->space, but now realise it's easier to match
	# when it's just underscore->nothing
	chunks = [re.sub('_', '', x) for x in whitespace.split(tag_string) if x != '']

	return chunks

