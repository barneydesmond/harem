from util_regexes import *

BASE10_DIGITS = "0123456789"
BASE16_DIGITS = "0123456789abcdef"
BASE32_DIGITS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

def convert(number, fromdigits, todigits):
	"""Convert between arbitrary base systems

	Written by Drew Pettula
	Stolen from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/111286

	The input number is assumed to be a string of digits from the
	fromdigits string (which is in order of smallest to largest
	digit). The return value is a string of elements from todigits
	(ordered in the same way). The input and output bases are
	determined from the lengths of the digit strings. Negative 
	signs are passed through.

	decimal to binary
	>>> baseconvert(555,BASE10,BASE2)
	'1000101011'

	binary to decimal
	>>> baseconvert('1000101011',BASE2,BASE10)
	'555'

	integer interpreted as binary and converted to decimal (!)
	>>> baseconvert(1000101011,BASE2,BASE10)
	'555'

	base10 to base4
	>>> baseconvert(99,BASE10,"0123")
	'1203'

	base4 to base5 (with alphabetic digits)
	>>> baseconvert(1203,"0123","abcde")
	'dee'

	base5, alpha digits back to base 10
	>>> baseconvert('dee',"abcde",BASE10)
	'99'

	decimal to a base that uses A-Z0-9a-z for its digits
	>>> baseconvert(257938572394L,BASE10,BASE62)
	'E78Lxik'

	..convert back
	>>> baseconvert('E78Lxik',BASE62,BASE10)
	'257938572394'

	binary to a base with words for digits (the function cannot convert this back)
	>>> baseconvert('1101',BASE2,('Zero','One'))
	'OneOneZeroOne'
	"""

	neg = False
	if str(number)[0]=='-':
		number = str(number)[1:]
		neg = True
	x=long(0)
	for digit in str(number):
		x = x*len(fromdigits) + fromdigits.index(digit)

	res=""
	while x>0:
		digit = x % len(todigits)
		res = todigits[digit] + res
		x /= len(todigits)

	if neg:
		reg = '-' + res
	return res

def base32_to_base16(hash):
	if not base16_or_32.search(hash):
		return None
	if base16.search(hash):
		return hash.lower()

	# Because convert() treats things as numbers, we need to pad things out
	# manually to make it legal as a hash
	return convert(hash.upper(), BASE32_DIGITS, BASE16_DIGITS).rjust(40, '0')

def base16_to_base32(hash):
	if not base16_or_32.search(hash):
		return None
	if base32.search(hash):
		return hash.upper()

	return convert(hash.lower(), BASE16_DIGITS, BASE32_DIGITS).rjust(32, 'A')

