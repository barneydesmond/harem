--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: plpgsql; Type: PROCEDURAL LANGUAGE; Schema: -; Owner: postgres
--

CREATE PROCEDURAL LANGUAGE plpgsql;


ALTER PROCEDURAL LANGUAGE plpgsql OWNER TO postgres;

SET search_path = public, pg_catalog;

--
-- Name: tag_plus_parent; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE tag_plus_parent AS (
	tagid bigint,
	name character varying(100),
	gloss character varying(200),
	type character varying(30),
	parent bigint
);


ALTER TYPE public.tag_plus_parent OWNER TO postgres;

--
-- Name: delete_file(character varying); Type: FUNCTION; Schema: public; Owner: meidokon_admin
--

CREATE FUNCTION delete_file(character varying) RETURNS integer
    AS $_$DECLARE
  hashlen INTEGER := (SELECT CHAR_LENGTH("hash") FROM "files" LIMIT 1);
  sha1 ALIAS FOR $1;
BEGIN
  IF sha1 IS NULL THEN
    RETURN 0;
  END IF;

  IF CHAR_LENGTH(sha1) != hashlen THEN
    RETURN 0;
  END IF;

  DELETE FROM "files" WHERE "hash"=sha1;
  RETURN 1;
END;$_$
    LANGUAGE plpgsql STABLE;


ALTER FUNCTION public.delete_file(character varying) OWNER TO meidokon_admin;

--
-- Name: get_all_tags(character varying, character varying); Type: FUNCTION; Schema: public; Owner: meidokon_admin
--

CREATE FUNCTION get_all_tags(character varying, character varying) RETURNS SETOF tag_plus_parent
    AS $_$DECLARE
  type_string ALIAS FOR $1;
  parent_string VARCHAR;
  where_string VARCHAR := 'true';
  new_tagid BIGINT;
  tag_line tag_plus_parent;
  type_line VARCHAR := '';
  query VARCHAR;
BEGIN
  IF type_string != '' THEN
    IF type_string NOT IN (SELECT "type" FROM "types") THEN
      RETURN;
    END IF;
    type_line := 'AND "type"=''' || type_string || '''';
  END IF;

  parent_string := $2;
  IF parent_string !~ '^([0-9]+(,[0-9]+)*)?$' THEN
    RAISE NOTICE 'BAD PARENT STRING';
    RETURN;
  END IF;

  -- Parent string handling
  IF parent_string != '' THEN
    IF parent_string !~ '^[0-9]+(,[0-9]+)*$' THEN
      RAISE NOTICE 'BAD PARENT STRING';
      RETURN;
    END IF;

    -- Process first parent in string
    where_string := '';
    new_tagid := CAST(SUBSTRING(parent_string FROM '^[0-9]+') AS bigint);
    parent_string := trim(leading '0123456789' FROM parent_string);
    parent_string := trim(leading ',' FROM parent_string);
    where_string := where_string || '"parent"=' || new_tagid;

    -- Handle other parents from here
    LOOP
      IF parent_string = '' THEN
        EXIT;
      END IF;

      new_tagid := CAST(SUBSTRING(parent_string FROM '^[0-9]+') AS bigint);
      where_string := where_string || ' OR "parent"=' || new_tagid;

      parent_string := trim(leading '0123456789' FROM parent_string);
      parent_string := trim(leading ',' FROM parent_string);
    END LOOP;
  END IF;
  -- Parent string is done

  query := 'SELECT "tags".*,COALESCE("parent", ''0'') AS "parent" FROM "tags" LEFT OUTER JOIN "inheritances" ON ("tags"."tagid"="inheritances"."tagid") WHERE (' || where_string || ') '|| type_line || ' ORDER BY "parent","name"';
  -- RAISE NOTICE '%',query;

  FOR tag_line IN
    EXECUTE query
  LOOP
    RETURN NEXT tag_line;
  END LOOP;

  RETURN;

END;$_$
    LANGUAGE plpgsql STABLE;


ALTER FUNCTION public.get_all_tags(character varying, character varying) OWNER TO meidokon_admin;

--
-- Name: get_child_tags_from_string(character varying); Type: FUNCTION; Schema: public; Owner: meidokon_admin
--

CREATE FUNCTION get_child_tags_from_string(character varying) RETURNS SETOF bigint
    AS $_$DECLARE
  parents VARCHAR;
  new_tagid BIGINT;
  process_tagid RECORD;
BEGIN
  parents := $1;
  IF parents !~ '^[0-9]+(,[0-9]+)*$' THEN
    RAISE NOTICE 'FOO!';
    RETURN;
  END IF;
  -- RAISE NOTICE 'All''s Good';


  LOOP
    IF parents = '' THEN
      EXIT;
    END IF;
    new_tagid := CAST(SUBSTRING(parents FROM '^[0-9]+') AS bigint);

    FOR process_tagid IN
      SELECT DISTINCT get_child_tags_from_tag FROM get_child_tags_from_tag(new_tagid)
    LOOP
      RETURN NEXT process_tagid.get_child_tags_from_tag;
    END LOOP;

    parents := trim(leading '0123456789' FROM parents);
    parents := trim(leading ',' FROM parents);
  END LOOP;

  RETURN;
END;$_$
    LANGUAGE plpgsql STABLE;


ALTER FUNCTION public.get_child_tags_from_string(character varying) OWNER TO meidokon_admin;

--
-- Name: get_child_tags_from_tag(bigint); Type: FUNCTION; Schema: public; Owner: meidokon_admin
--

CREATE FUNCTION get_child_tags_from_tag(bigint) RETURNS SETOF bigint
    AS $_$DECLARE
  parent_in ALIAS FOR $1;
  child_out RECORD;
  child_in RECORD;
BEGIN
  IF parent_in IS NULL THEN
    RETURN;
  END IF;

  RETURN NEXT parent_in;
  FOR child_out IN
    SELECT "tagid" FROM "tags" NATURAL JOIN "inheritances" WHERE "parent"=parent_in AND "type"=(SELECT "type" FROM "tags" WHERE "tagid"=parent_in)
  LOOP
    RETURN NEXT "child_out"."tagid";
    FOR child_in IN
      SELECT DISTINCT "get_child_tags_from_tag" FROM get_child_tags_from_tag("child_out"."tagid")
    LOOP
      RETURN NEXT "child_in"."get_child_tags_from_tag";
    END LOOP;
  END LOOP;

  RETURN;
END;$_$
    LANGUAGE plpgsql STABLE;


ALTER FUNCTION public.get_child_tags_from_tag(bigint) OWNER TO meidokon_admin;

--
-- Name: get_related_tagids(bigint); Type: FUNCTION; Schema: public; Owner: meidokon_admin
--

CREATE FUNCTION get_related_tagids(bigint) RETURNS SETOF bigint
    AS $_$DECLARE
  ret RECORD;
BEGIN
  IF $1 IS NULL THEN
    RETURN;
  END IF;

  FOR ret IN
    SELECT DISTINCT "tagid" FROM "assoc" WHERE "hash" IN (SELECT "hash" FROM "assoc" WHERE "tagid"=$1) AND "tagid" <> $1
  LOOP
    RETURN NEXT ret.tagid;
  END LOOP;

  RETURN;
END;$_$
    LANGUAGE plpgsql;


ALTER FUNCTION public.get_related_tagids(bigint) OWNER TO meidokon_admin;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: tags; Type: TABLE; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE TABLE tags (
    tagid bigint NOT NULL,
    name character varying(100) NOT NULL,
    gloss character varying(200),
    type character varying(30) NOT NULL
);


ALTER TABLE public.tags OWNER TO meidokon_admin;

--
-- Name: get_tags_on_file(character varying); Type: FUNCTION; Schema: public; Owner: meidokon_admin
--

CREATE FUNCTION get_tags_on_file(character varying) RETURNS SETOF tags
    AS $_$DECLARE
  the_hash ALIAS FOR $1;
  my_row "tags"%ROWTYPE;
BEGIN
  IF (looks_like_base16(the_hash) = false) THEN
    RETURN;
  END IF;

  FOR my_row IN
    SELECT "tags".* FROM "tags" NATURAL JOIN "assoc" WHERE "hash"=the_hash ORDER BY "type","name"
  LOOP
    RETURN NEXT my_row;
  END LOOP;

  RETURN;
END;$_$
    LANGUAGE plpgsql STABLE;


ALTER FUNCTION public.get_tags_on_file(character varying) OWNER TO meidokon_admin;

--
-- Name: looks_like_base16(character varying); Type: FUNCTION; Schema: public; Owner: meidokon_admin
--

CREATE FUNCTION looks_like_base16(character varying) RETURNS boolean
    AS $_$DECLARE
  candidate ALIAS FOR $1;
BEGIN
  IF candidate ~ '^[0-9A-Fa-f]{40}$' THEN
    RETURN 1;
  END IF;

  RETURN 0;
END;$_$
    LANGUAGE plpgsql STABLE;


ALTER FUNCTION public.looks_like_base16(character varying) OWNER TO meidokon_admin;

--
-- Name: looks_like_base32(character varying); Type: FUNCTION; Schema: public; Owner: meidokon_admin
--

CREATE FUNCTION looks_like_base32(character varying) RETURNS boolean
    AS $_$DECLARE
  candidate ALIAS FOR $1;
BEGIN
  IF candidate ~ '^[2-7A-Za-z]{32}$' THEN
    RETURN 1;
  END IF;

  RETURN 0;
END;$_$
    LANGUAGE plpgsql STABLE;


ALTER FUNCTION public.looks_like_base32(character varying) OWNER TO meidokon_admin;

--
-- Name: aliases; Type: TABLE; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE TABLE aliases (
    shorthand character varying(32) NOT NULL,
    tagid bigint NOT NULL
);


ALTER TABLE public.aliases OWNER TO meidokon_admin;

--
-- Name: assoc; Type: TABLE; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE TABLE assoc (
    hash character varying(40) NOT NULL,
    tagid bigint NOT NULL
);


ALTER TABLE public.assoc OWNER TO meidokon_admin;

--
-- Name: files; Type: TABLE; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE TABLE files (
    hash character varying(40) NOT NULL,
    date_added timestamp without time zone DEFAULT now() NOT NULL,
    width integer NOT NULL,
    height integer NOT NULL,
    ext character varying(4) DEFAULT ''::character varying NOT NULL
);


ALTER TABLE public.files OWNER TO meidokon_admin;

--
-- Name: inheritances; Type: TABLE; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE TABLE inheritances (
    tagid bigint NOT NULL,
    parent bigint NOT NULL
);


ALTER TABLE public.inheritances OWNER TO meidokon_admin;

--
-- Name: tags_tagid_seq; Type: SEQUENCE; Schema: public; Owner: meidokon_admin
--

CREATE SEQUENCE tags_tagid_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.tags_tagid_seq OWNER TO meidokon_admin;

--
-- Name: tags_tagid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: meidokon_admin
--

ALTER SEQUENCE tags_tagid_seq OWNED BY tags.tagid;


--
-- Name: types; Type: TABLE; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE TABLE types (
    type character varying(30) NOT NULL,
    display_order smallint NOT NULL,
    display_depends character varying(30),
    contingent bigint
);


ALTER TABLE public.types OWNER TO meidokon_admin;

--
-- Name: tagid; Type: DEFAULT; Schema: public; Owner: meidokon_admin
--

ALTER TABLE tags ALTER COLUMN tagid SET DEFAULT nextval('tags_tagid_seq'::regclass);


--
-- Name: aliases_pkey; Type: CONSTRAINT; Schema: public; Owner: meidokon_admin; Tablespace: 
--

ALTER TABLE ONLY aliases
    ADD CONSTRAINT aliases_pkey PRIMARY KEY (shorthand);


--
-- Name: assoc_pkey; Type: CONSTRAINT; Schema: public; Owner: meidokon_admin; Tablespace: 
--

ALTER TABLE ONLY assoc
    ADD CONSTRAINT assoc_pkey PRIMARY KEY (hash, tagid);


--
-- Name: files_pkey; Type: CONSTRAINT; Schema: public; Owner: meidokon_admin; Tablespace: 
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_pkey PRIMARY KEY (hash);


--
-- Name: inheritances_pkey; Type: CONSTRAINT; Schema: public; Owner: meidokon_admin; Tablespace: 
--

ALTER TABLE ONLY inheritances
    ADD CONSTRAINT inheritances_pkey PRIMARY KEY (tagid);


--
-- Name: tags_pkey; Type: CONSTRAINT; Schema: public; Owner: meidokon_admin; Tablespace: 
--

ALTER TABLE ONLY tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (tagid);

ALTER TABLE tags CLUSTER ON tags_pkey;


--
-- Name: types_display_order_key; Type: CONSTRAINT; Schema: public; Owner: meidokon_admin; Tablespace: 
--

ALTER TABLE ONLY types
    ADD CONSTRAINT types_display_order_key UNIQUE (display_order);


--
-- Name: types_pkey; Type: CONSTRAINT; Schema: public; Owner: meidokon_admin; Tablespace: 
--

ALTER TABLE ONLY types
    ADD CONSTRAINT types_pkey PRIMARY KEY (type);


--
-- Name: aliases_tagid_idx; Type: INDEX; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE INDEX aliases_tagid_idx ON aliases USING btree (tagid);


--
-- Name: assoc_hash_idx; Type: INDEX; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE INDEX assoc_hash_idx ON assoc USING btree (hash);


--
-- Name: assoc_tagid_idx; Type: INDEX; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE INDEX assoc_tagid_idx ON assoc USING btree (tagid);


--
-- Name: date_added_idx; Type: INDEX; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE INDEX date_added_idx ON files USING btree (date_added);

ALTER TABLE files CLUSTER ON date_added_idx;


--
-- Name: fki_assoc_tagid_fkey; Type: INDEX; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE INDEX fki_assoc_tagid_fkey ON assoc USING btree (tagid);


--
-- Name: inheritances_parent_idx; Type: INDEX; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE INDEX inheritances_parent_idx ON inheritances USING btree (parent);

ALTER TABLE inheritances CLUSTER ON inheritances_parent_idx;


--
-- Name: tags_auto-shorthand; Type: INDEX; Schema: public; Owner: meidokon_admin; Tablespace: 
--

CREATE INDEX "tags_auto-shorthand" ON tags USING btree (lower(replace(replace(rtrim((name)::text, '&#;0123456789/ '::text), '-'::text, ''::text), ' '::text, ''::text)));


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: meidokon_admin
--

ALTER TABLE ONLY types
    ADD CONSTRAINT "$1" FOREIGN KEY (display_depends) REFERENCES types(type) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: meidokon_admin
--

ALTER TABLE ONLY tags
    ADD CONSTRAINT "$1" FOREIGN KEY (type) REFERENCES types(type) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: aliases_tagid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: meidokon_admin
--

ALTER TABLE ONLY aliases
    ADD CONSTRAINT aliases_tagid_fkey FOREIGN KEY (tagid) REFERENCES tags(tagid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: assoc_hash_fkey; Type: FK CONSTRAINT; Schema: public; Owner: meidokon_admin
--

ALTER TABLE ONLY assoc
    ADD CONSTRAINT assoc_hash_fkey FOREIGN KEY (hash) REFERENCES files(hash) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: assoc_tagid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: meidokon_admin
--

ALTER TABLE ONLY assoc
    ADD CONSTRAINT assoc_tagid_fkey FOREIGN KEY (tagid) REFERENCES tags(tagid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: inheritances_parent_fkey; Type: FK CONSTRAINT; Schema: public; Owner: meidokon_admin
--

ALTER TABLE ONLY inheritances
    ADD CONSTRAINT inheritances_parent_fkey FOREIGN KEY (parent) REFERENCES tags(tagid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: inheritances_tagid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: meidokon_admin
--

ALTER TABLE ONLY inheritances
    ADD CONSTRAINT inheritances_tagid_fkey FOREIGN KEY (tagid) REFERENCES tags(tagid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: tags; Type: ACL; Schema: public; Owner: meidokon_admin
--

REVOKE ALL ON TABLE tags FROM PUBLIC;
REVOKE ALL ON TABLE tags FROM meidokon_admin;
GRANT ALL ON TABLE tags TO meidokon_admin;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE tags TO PUBLIC;


--
-- Name: aliases; Type: ACL; Schema: public; Owner: meidokon_admin
--

REVOKE ALL ON TABLE aliases FROM PUBLIC;
REVOKE ALL ON TABLE aliases FROM meidokon_admin;
GRANT ALL ON TABLE aliases TO meidokon_admin;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE aliases TO PUBLIC;


--
-- Name: assoc; Type: ACL; Schema: public; Owner: meidokon_admin
--

REVOKE ALL ON TABLE assoc FROM PUBLIC;
REVOKE ALL ON TABLE assoc FROM meidokon_admin;
GRANT ALL ON TABLE assoc TO meidokon_admin;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE assoc TO PUBLIC;


--
-- Name: files; Type: ACL; Schema: public; Owner: meidokon_admin
--

REVOKE ALL ON TABLE files FROM PUBLIC;
REVOKE ALL ON TABLE files FROM meidokon_admin;
GRANT ALL ON TABLE files TO meidokon_admin;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE files TO PUBLIC;


--
-- Name: inheritances; Type: ACL; Schema: public; Owner: meidokon_admin
--

REVOKE ALL ON TABLE inheritances FROM PUBLIC;
REVOKE ALL ON TABLE inheritances FROM meidokon_admin;
GRANT ALL ON TABLE inheritances TO meidokon_admin;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE inheritances TO PUBLIC;


--
-- Name: types; Type: ACL; Schema: public; Owner: meidokon_admin
--

REVOKE ALL ON TABLE types FROM PUBLIC;
REVOKE ALL ON TABLE types FROM meidokon_admin;
GRANT ALL ON TABLE types TO meidokon_admin;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE types TO PUBLIC;


--
-- PostgreSQL database dump complete
--

