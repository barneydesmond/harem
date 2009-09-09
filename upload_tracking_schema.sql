-- holds metadata about new uploads
CREATE TABLE uploads (
    hash character varying(40) NOT NULL,
    width integer NOT NULL,
    height integer NOT NULL,
    ext character varying(4) DEFAULT ''::character varying NOT NULL,
    initial_tagids text DEFAULT ''::text NOT NULL,
    filename text NOT NULL,
    CONSTRAINT tagids_format CHECK ((initial_tagids ~ '^$|^[0-9]+(,[0-9]+)*$'::text))
);

ALTER TABLE ONLY uploads ADD CONSTRAINT upload_tracking_pkey PRIMARY KEY (hash);
