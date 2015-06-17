# Introduction #

These are very rough instructions.

# Details #

## Pre-Requisites ##

  * Postgresql (sorry, no MySQL here).
  * Python
  * Various python libraries (listed below where needed)
  * CGI compatible web-server

## General ##

  1. Identify servers (and base URLs) for:
    * your content master
    * your frontend
    * your app server
  1. Generate random keys for Content Master operations (3 keys needed).
  1. Set up your databases
    * Content Master Database
      * should be close to the content master
      * execute schema ` upload_tracking_schema.sql `
    * App Server database
      * should be close to the app server and frontend
      * execute ` CREATE GROUP meidokon_admin; `
      * execute schema ` meidokon_schema.sql `
      * look at table ` types ` and ` tags ` and create a default tag and tag type (or several).

## Front-end ##

Nothing too special required here.

  * Install psycopg2, python-Levenshtein
  * Edit ` frontend/frontend_config.py `
    * set DB passwords.
    * set `file_upload_target`, `THUMBNAIL_PATH`, `MID_VER_PATH` and `FULL_VER_PATH` to reference the Content Master.
    * set the `xmlrpc_server` line(s) to reference your App Server.
    * At the bottom, make sure you have config\_sets for your host that select the right configuration.
  * Copy `frontend/` to your frontend's content directory, and make sure CGI execution is enabled.
  * Set your index document to either `index.py` (classic meidokon) or `text.py` (new-style text tag searching)

## App Server ##
  * Install psycopg2 + DBUtils.
  * Edit `xmlrpc_legacy/xmlrpc_conf.py`
    * set your bind address + port for the server, database details and shared secrets
    * set `master_content_xmlrpc_server` to reference your content server's URL
    * set `deletion_password` to something secret so you can delete images later.
  * Start with the `run` or `devrun` script in the `xmlrpc_legacy` directory.

## Content Server ##
  * Install psycopg2.
  * Edit `master_content_server/conf.py`
    * set `xmlrpc_server` to point to the app server.
    * set the shared secrets
    * set the database details for the content server's database
    * Set `EDIT_PAGE_PATH` to point to the frontend.
  * Edit `master_content_server/mod_autotag.py`
    * Edit `defaults` to return an array of the tag IDs you want assigned to new uploads by default.
    * Edit `animated_gif` and `wallpaper` to reference appropriate tag IDs or remove their `functions.append(...)` lines from the end of the file.
  * Deploy `master_content_server/` to your master content server web server.  Make sure CGI is enabled.
  * In the deployment, create directories `_probation`, `_full`, `_mid` and `_thumb`.  Make sure they're writable by the web server (or the CGI user if suexec or similar is in effect).