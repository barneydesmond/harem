# Each function must return an iterable collection of integers



def animated_gif(file):
	"""Attempts to detect if the file is an animated GIF, and set the
	tagid accordingly
	"""

	import os.path
	import Image
	from conf import *
	from util_errors import gen_error
	ANIMGIF_TAGID = 2

	filepath = os.path.join(PROBATION_DIR, file["filename"])
	try:
		img = Image.open(filepath)
		try:
			img.seek(1)
		except:
			pass
		else:
			del(img)
			return [ANIMGIF_TAGID]
	except Exception, data:
		gen_error('GENERIC', "File couldn't be operated on, check perms -- " + str(data))

	del(img)
	return []


def wallpaper(file):
	"""Checks if the file is of wallpaper dimensions (predefined),
	and tags accordingly
	"""

	import os.path
	import Image
	from conf import *
	from util_errors import gen_error
	WALLPAPER_TAGID = 51
	WALLPAPER_RESOLUTIONS = [       (1024, 768),
					(1152, 864),
					(1280, 960),
					(1280, 1024),
					(1600, 1200) ]

	if (file["width"], file["height"]) in WALLPAPER_RESOLUTIONS:
		return [WALLPAPER_TAGID]
	else:
		return []


def defaults(file):
	"""A trivial case that always sets the no-series and uncategorised tags
	"""

	UNCAT_TAGID = 47
	NOSERIES_TAGID = 375

	return [NOSERIES_TAGID, UNCAT_TAGID]



functions = []
functions.append(animated_gif)
functions.append(wallpaper)
functions.append(defaults)



