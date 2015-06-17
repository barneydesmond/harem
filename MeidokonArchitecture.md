# Introduction #

Meidokon started as a horrible project in PHP and later became a horrible project in Python. Along the way it was reworked to be scalable and potentially somewhat distributable.



# Details #

## Goals ##

  * Meidokon was intended to work with images, typically JPG, PNG and GIF.
  * Zero or more named "tags" can be applied to an image to indicate that the image shows the named feature.
  * One can search for images based on the presence of specified tags
    * Later modified to allow searching based on the lack of a specified tag

At its core, Meidokon is all about maintaining image metadata. An image is represented by its SHA1 hash, a unique identifier for all intents and purposes. The metadata is in the form of tags. If an image has a given feature, there's an association between the hash and the tag.


## About tags ##
  * Unlike other systems like Danbooru, metadata for a given tag is a core feature of Meidokon.
    * Parent-child tag relationships
    * URLs
    * Free-form text Description
    * Alternate names/spellings (aliases)
  * While Meidokon retains a "canonical" name for a tag, the association is much weaker than Danbooru, which imposes a restrictive set of characters for naming tags
    * Depending on your point of view this is a great boon, or a particularly hairy bit of evil
  * Tags have an associated **type**, used for presentation and grouping - artist, character, series, etc
    * This is something else Danbooru didn't have to begin with :)


## Components (or Tiers if you want to think of it that way) ##

Meidokon has a few distinct interlinked services that provide the eventual user experience. While web-centric, the design allows the hypothetical possibility of a standalone client application.

Each component is (should be) independent of the others, and doesn't rely on implicit relationships to function. The implementation is security-concious.

XML-RPC is used for most inter-component communication.
  * It's a nice protocol
  * The Python API is good


### Database backend ###

**Postgres** was chosen for its:
  * Sanity
  * Rich set of features
  * Performance
  * Popularity

The DB stores **tags**, **files** (more correctly, the SHA1 hashes of files), and the **associations** between them. Non-tag metadata about each file is also kept in the DB, as well as all tag metadata and relationships.

Because tags exist entirely within the DB, a lot of processing logic has been pushed to the DB, for performance and convenience. Tag constraints (cardinality and referentiality) are also implemented in the DB.

### App server ###

Connects to the DB and provides an XML-RPC interface for querying by a web/standalone frontend. Designed primarily with a web frontend in mind, it will do a lot of processing to relieve the frontend of the work. An example of this is `get_tags()` returning ready-to-use tag data, instead of a trivial list of tagids (which would necessitate another API call from a stateless web UI).

The XML-RPC API is (roughly) self-documented:
http://xmlrpc.meidokon.net/RPC2

A planned addition would be the use of an API key, for accountability and access control.

The app server is implemented in ` xmlrpc_legacy/ `

### Web frontend ###

Currently all written in CGI-Python, should be moved to WSGI for sanity and performance.

The obvious stuff:
  * Issues queries against the XML-RPC interface
  * Accepts queries via GET parameters and presents results based on the lookups
  * Provides an interface for editing tag->image associations
  * Provides an interface for uploading new images

Less-obvious stuff:
  * The newer `text.py` frontpage takes freeform text input for searching, rather than presenting an exhaustive list of all tags - this should really be made the default
    * This would be ripe for some suggest-as-you-type AJAX
  * The input processor is "smart" - if it couldn't match an existing tag unambiguously, it'll do its best to find results, but also suggest _"Did you mean..?"_
    * It uses Levenshtein for string comparisons, with a user-configurable threshold
  * The web frontend trivially supports having more than one content server. The default is defined as a config parameter, but if the client wants to specify their own servers for thumbnails and full-size images then they can pass it in a cookie, and it'll get written into the page.
  * Image uploads are handled by sending them over to the master content server. The frontend _never_ receives uploads, they go to the content server, which then informs the app-server and bounces the user back to the frontend.

The **Suggestions** stuff should really be moved to the app-server - it's currently implemented in `text.py` by directly querying the DB.


### Content server ###

  * Serves files based on hash
  * Receives new uploads and adds them by talking XML-RPC to the app-server
  * Even cooler, can be passed a URL and it'll fetch it for you

Currently written in CGI-Python, should be moved to WSGI for sanity and performance.

`hash_{full,mid,thumb}.py` take the hash as the query string and issue a 302 redirect to the real file. This is amazingly ugly, but was deemed necessary as a workaround for content types and file extensions, etc.

The upload process is funky and asyncronous.

When a new upload is received:
  1. Attempt to sanity-check it with ImageMagick
  1. Dump it to disk in a _probation_ directory, converting from BMP if needed
  1. Gather metadata about the file
  1. Note the file in the local tracking DB (this should be really lightweight)
  1. Notify the app-server that we want to insert a new file

When the app-server hears about a new file:
  1. It checks that the file isn't already in the DB
  1. Inserts the new entry
  1. Notifies the content server that it can go ahead and release the file from probation

When the content server gets a release authorisation:
  1. It deletes it from the local tracking database
  1. Creates the mid-size and thumbnail images
  1. Moves the full-size file into place


Deletions are handled in a similar manner, with the app-server requesting a deletion (as a consequence of a deletion request from the frontend), and the content server complying.

The app-server currently assume a single master content server. It's up to this master content server to replicate new files to any hypothetical read-only slaves. Something like MogileFS could be used I supppose.


### Content server caching proxy ###

Entirely optional. As mentioned, the frontend can take user-specified content servers. It's assumed a user may maintain a local proxy for speed and bandwidth savings.

Such a content server has similar `hash_{full,mid,thumb}` scripts and a local store. If the file doesn't exist, it fetches it from the upstream first (the user if of course free to specify this however they want). The file is then served up by usual 302 redirect.

Because a proxy is so trivial and needs no API access, this is easiest to implement in PHP and just make dumb assumptions about local filenames.