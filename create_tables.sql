--
-- PostgreSQL database dump
--

-- Dumped from database version 15.2 (Debian 15.2-1.pgdg110+1)
-- Dumped by pg_dump version 15.1

-- Started on 2023-03-13 16:18:13 UTC

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 853 (class 1247 OID 16436)
-- Name: comissioner; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.comissioner AS ENUM (
    'UKAEA',
    'EuroFusion'
);


ALTER TYPE public.comissioner OWNER TO root;

--
-- TOC entry 844 (class 1247 OID 16396)
-- Name: current_range; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.current_range AS ENUM (
    '400 kA',
    '700 kA',
    '1000 kA',
    '1300 kA',
    '1600 kA',
    '2000 kA'
);


ALTER TYPE public.current_range OWNER TO root;

--
-- TOC entry 862 (class 1247 OID 16455)
-- Name: dimension; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.dimension AS ENUM (
    'Time',
    'X',
    'Y'
);


ALTER TYPE public.dimension OWNER TO root;

--
-- TOC entry 847 (class 1247 OID 16410)
-- Name: divertor_config; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.divertor_config AS ENUM (
    'Conventional',
    'Super-X',
    'Super-X (Inner Leg)',
    'Snowflake',
    'Vertical Target',
    'X Divertor'
);


ALTER TYPE public.divertor_config OWNER TO root;

--
-- TOC entry 856 (class 1247 OID 16442)
-- Name: facility; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.facility AS ENUM (
    'MAST',
    'MAST-U'
);


ALTER TYPE public.facility OWNER TO root;

--
-- TOC entry 850 (class 1247 OID 16424)
-- Name: plasma_shape; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.plasma_shape AS ENUM (
    'Double Null',
    'Lower Single Null',
    'Upper Single Null',
    'Limiter'
);


ALTER TYPE public.plasma_shape OWNER TO root;

--
-- TOC entry 865 (class 1247 OID 16462)
-- Name: quality; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.quality AS ENUM (
    'Very Bad',
    'Validated',
    'Checked',
    'Not Checked',
    'Bad'
);


ALTER TYPE public.quality OWNER TO root;

--
-- TOC entry 3381 (class 0 OID 0)
-- Dependencies: 865
-- Name: TYPE quality; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TYPE public.quality IS 'A number indicating the status of the signal:
-1 Poor Data: do not use (Very Bad)
0 Something is wrong in the Data (Bad)
1 either Raw data not checked or Analysed data quality is Unknown (Not Checked)
2 Data has been checked - no known problems (Checked)
3 Data was validated" (Validated)';


--
-- TOC entry 868 (class 1247 OID 16474)
-- Name: signal_type; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.signal_type AS ENUM (
    'Raw',
    'Analysed'
);


ALTER TYPE public.signal_type OWNER TO root;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 218 (class 1259 OID 16513)
-- Name: cpf_summary; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.cpf_summary (
    id integer NOT NULL,
    name character varying(20) NOT NULL,
    units character varying(10) NOT NULL,
    description text NOT NULL
);


ALTER TABLE public.cpf_summary OWNER TO root;

--
-- TOC entry 217 (class 1259 OID 16496)
-- Name: scenarios; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.scenarios (
    id smallint NOT NULL,
    name character varying(10) NOT NULL
);


ALTER TABLE public.scenarios OWNER TO root;

--
-- TOC entry 216 (class 1259 OID 16479)
-- Name: shot_signal_link; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.shot_signal_link (
    id integer NOT NULL,
    signal_id integer NOT NULL,
    shot_id integer NOT NULL
);


ALTER TABLE public.shot_signal_link OWNER TO root;

--
-- TOC entry 214 (class 1259 OID 16390)
-- Name: shots; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.shots (
    shot_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    reference_shot integer NOT NULL,
    scenario smallint NOT NULL,
    current_range public.current_range NOT NULL,
    heating bit(3) NOT NULL,
    divertor_config public.divertor_config NOT NULL,
    pellets boolean NOT NULL,
    plasma_shape public.plasma_shape NOT NULL,
    rpm_coil boolean,
    preshot_description text NOT NULL,
    postshot_description text NOT NULL,
    comissioner public.comissioner NOT NULL,
    campaign character varying(4) NOT NULL,
    facility public.facility NOT NULL
);


ALTER TABLE public.shots OWNER TO root;

--
-- TOC entry 3382 (class 0 OID 0)
-- Dependencies: 214
-- Name: COLUMN shots.heating; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.shots.heating IS 'First bit: Ohmic 
Second bit: One Beam (South / On Axis) 
Third bit: One Beam (South-West / Off Axis) ';


--
-- TOC entry 215 (class 1259 OID 16447)
-- Name: signals; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.signals (
    signal_id integer NOT NULL,
    name text NOT NULL,
    units character varying(10) NOT NULL,
    dim_1_label public.dimension,
    dim_2_label public.dimension,
    dim_3_label public.dimension,
    uri text,
    description text NOT NULL,
    signal_type public.signal_type NOT NULL,
    quality public.quality NOT NULL,
    doi text NOT NULL,
    camera_metadata integer,
    camera integer,
    shot_link_id integer NOT NULL
);


ALTER TABLE public.signals OWNER TO root;

--
-- TOC entry 3375 (class 0 OID 16513)
-- Dependencies: 218
-- Data for Name: cpf_summary; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.cpf_summary (id, name, units, description) FROM stdin;
\.


--
-- TOC entry 3374 (class 0 OID 16496)
-- Dependencies: 217
-- Data for Name: scenarios; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.scenarios (id, name) FROM stdin;
\.


--
-- TOC entry 3373 (class 0 OID 16479)
-- Dependencies: 216
-- Data for Name: shot_signal_link; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.shot_signal_link (id, signal_id, shot_id) FROM stdin;
\.


--
-- TOC entry 3371 (class 0 OID 16390)
-- Dependencies: 214
-- Data for Name: shots; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.shots (shot_id, "timestamp", reference_shot, scenario, current_range, heating, divertor_config, pellets, plasma_shape, rpm_coil, preshot_description, postshot_description, comissioner, campaign, facility) FROM stdin;
\.


--
-- TOC entry 3372 (class 0 OID 16447)
-- Dependencies: 215
-- Data for Name: signals; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.signals (signal_id, name, units, dim_1_label, dim_2_label, dim_3_label, uri, description, signal_type, quality, doi, camera_metadata, camera, shot_link_id) FROM stdin;
\.


--
-- TOC entry 3224 (class 2606 OID 16519)
-- Name: cpf_summary cpf_summary_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.cpf_summary
    ADD CONSTRAINT cpf_summary_pkey PRIMARY KEY (id);


--
-- TOC entry 3222 (class 2606 OID 16500)
-- Name: scenarios scenarios_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.scenarios
    ADD CONSTRAINT scenarios_pkey PRIMARY KEY (id);


--
-- TOC entry 3220 (class 2606 OID 16483)
-- Name: shot_signal_link shot_signal_link_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shot_signal_link
    ADD CONSTRAINT shot_signal_link_pkey PRIMARY KEY (id);


--
-- TOC entry 3216 (class 2606 OID 16394)
-- Name: shots shots_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT shots_pkey PRIMARY KEY (shot_id);


--
-- TOC entry 3218 (class 2606 OID 16453)
-- Name: signals signals_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.signals
    ADD CONSTRAINT signals_pkey PRIMARY KEY (signal_id);


--
-- TOC entry 3226 (class 2606 OID 16501)
-- Name: shots scenario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT scenario_fkey FOREIGN KEY (scenario) REFERENCES public.scenarios(id) NOT VALID;


--
-- TOC entry 3227 (class 2606 OID 16491)
-- Name: shot_signal_link shot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shot_signal_link
    ADD CONSTRAINT shot_id_fkey FOREIGN KEY (shot_id) REFERENCES public.shots(shot_id) NOT VALID;


--
-- TOC entry 3228 (class 2606 OID 16486)
-- Name: shot_signal_link signal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shot_signal_link
    ADD CONSTRAINT signal_id_fkey FOREIGN KEY (signal_id) REFERENCES public.signals(signal_id) NOT VALID;


-- Completed on 2023-03-13 16:18:13 UTC

--
-- PostgreSQL database dump complete
--

