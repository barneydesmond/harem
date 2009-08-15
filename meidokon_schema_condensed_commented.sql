-- used for internal processing and display
CREATE TYPE tag_plus_parent AS (
	tagid bigint,
	name character varying(100),
	gloss character varying(200),
	type character varying(30),
	parent bigint
);


-- returns 0 on failure, 1 on success
-- does not indicate whether any deletion actually occurred
CREATE FUNCTION delete_file(hash) RETURNS integer


-- get a list of all tags matching the requirements
-- type is an empty string, or one of the defined types
-- parent_string is a comma-separated list of one-or-more tagids
-- if the parent_string is specified, the returned tags must be an immediate child of at least one of the parent tags (ie. this does NOT descend recursively)
CREATE FUNCTION get_all_tags(type, parent_string) RETURNS SETOF tag_plus_parent


-- find the union of all child tagids of the specifed parents; this descends recursively
-- parents is a comma-separated list of one-or-more tagids
CREATE FUNCTION get_child_tags_from_string(parents) RETURNS SETOF tagid


-- find all child tagids of the specified tagid; this descends recursively
CREATE FUNCTION get_child_tags_from_tag(tagid) RETURNS SETOF tagid


-- take a tagid
-- find all images associated with that tagid
-- return all tagids associated with any of those images
CREATE FUNCTION get_related_tagids(tagid) RETURNS SETOF tagid


-- convenience functions for handling SHA1 hashes
CREATE FUNCTION looks_like_base16(character varying) RETURNS boolean
CREATE FUNCTION looks_like_base32(character varying) RETURNS boolean


-- return full tag records for all tags on a given file
CREATE FUNCTION get_tags_on_file(character varying) RETURNS SETOF tags




CREATE TABLE files (
    hash character varying(40) NOT NULL,
    date_added timestamp without time zone DEFAULT now() NOT NULL,
    width integer NOT NULL,
    height integer NOT NULL,
    ext character varying(4) DEFAULT ''::character varying NOT NULL
);


CREATE TABLE tags (
    tagid bigint NOT NULL,
    name character varying(100) NOT NULL,
    gloss character varying(200),
    type character varying(30) NOT NULL
);
CREATE TABLE aliases (
    shorthand character varying(32) NOT NULL,
    tagid bigint NOT NULL
);
CREATE TABLE inheritances (
    tagid bigint NOT NULL,
    parent bigint NOT NULL
);


CREATE TABLE assoc (
    hash character varying(40) NOT NULL,
    tagid bigint NOT NULL
);



CREATE TABLE types (
    type character varying(30) NOT NULL,
    display_order smallint NOT NULL,
    display_depends character varying(30),
    contingent bigint
);

