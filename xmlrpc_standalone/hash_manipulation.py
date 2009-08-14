#!/usr/bin/python

import re

# Index by `hex_bin[int('b', 16)]`
hex_bin = ['0000', '0001', '0010', '0011', '0100', '0101', '0110', '0111', '1000', '1001', '1010', '1011', '1100', '1101', '1110', '1111']
# Index by `bin_hex[int('1010', 2)]`
bin_hex = '0123456789abcdef'
# Index by `bin_to_32[int('10110', 2)]`
bin_to_32 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'

bin_from_32 = {}
bin_from_32['A'] = '00000'
bin_from_32['B'] = '00001'
bin_from_32['C'] = '00010'
bin_from_32['D'] = '00011'
bin_from_32['E'] = '00100'
bin_from_32['F'] = '00101'
bin_from_32['G'] = '00110'
bin_from_32['H'] = '00111'
bin_from_32['I'] = '01000'
bin_from_32['J'] = '01001'
bin_from_32['K'] = '01010'
bin_from_32['L'] = '01011'
bin_from_32['M'] = '01100'
bin_from_32['N'] = '01101'
bin_from_32['O'] = '01110'
bin_from_32['P'] = '01111'
bin_from_32['Q'] = '10000'
bin_from_32['R'] = '10001'
bin_from_32['S'] = '10010'
bin_from_32['T'] = '10011'
bin_from_32['U'] = '10100'
bin_from_32['V'] = '10101'
bin_from_32['W'] = '10110'
bin_from_32['X'] = '10111'
bin_from_32['Y'] = '11000'
bin_from_32['Z'] = '11001'
bin_from_32['2'] = '11010'
bin_from_32['3'] = '11011'
bin_from_32['4'] = '11100'
bin_from_32['5'] = '11101'
bin_from_32['6'] = '11110'
bin_from_32['7'] = '11111'

def valid_sha1(hash):
	if re.match(r"[a-fA-F0-9]{40}$|[2-7A-Za-z]{32}$", hash):
		return True
	return False

def base32_to_base16(hash):
	"""Takes a base32 SHA-1 hash and returns the base16 form. (both encoded as chars, not raw binary)

	If a base16 hash is passed in, it is returned as it was. This function is always safe to call.
	That is, unless you pass it something that doesn't look like a hash. Then you get an exception.
	For reference, a base32 hash is usually [2-7A-Z]{32}
	For reference, a base16 hash is usually [0-9a-f]{40}"""
	if not valid_sha1(hash):
		raise "MalformedHash", hash

	if re.match(r"[a-fA-F0-9]{40}$", hash):
		return hash.lower()
	hash = hash.upper()

	binary = ''
	for char in hash:
		binary = binary + bin_from_32[char]

	base16 = ''
	for i in range(0, 40):
		index = binary[(4*i):(4*i)+4]
		base16 = base16 + bin_hex[int(index, 2)]

	return base16


def base16_to_base32(hash):
	"""Takes a base16 SHA-1 hash and returns the base32 form. (both encoded as chars, not raw binary)

	If a base32 hash is passed in, it is returned as it was. This function is always safe to call.
	That is, unless you pass it something that doesn't look like a hash. Then you get an exception.
	For reference, a base16 hash is usually [0-9a-f]{40}
	For reference, a base32 hash is usually [2-7A-Z]{32}"""
	if not valid_sha1(hash):
		raise "MalformedHash", hash

	if re.match(r"[2-7A-Za-z]{32}$", hash):
		return hash.upper()
	hash = hash.lower()

	binary = ''
	for char in hash:
		binary = binary + hex_bin[int(str(char), 16)]

	base32 = ''
	for i in range(0,32):
		index = binary[(5*i):(5*i)+5]
		base32 = base32 + bin_to_32[int(index, 2)]

	return base32
