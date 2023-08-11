--
-- PostgreSQL database dump
--

-- Dumped from database version 15.2 (Debian 15.2-1.pgdg110+1)
-- Dumped by pg_dump version 15.1

-- Started on 2023-03-20 15:21:26 UTC

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
-- TOC entry 843 (class 1247 OID 28549)
-- Name: comissioner; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.comissioner AS ENUM (
    'UKAEA',
    'EuroFusion'
);


ALTER TYPE public.comissioner OWNER TO root;

--
-- TOC entry 846 (class 1247 OID 28554)
-- Name: current_range; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.current_range AS ENUM (
    '400 kA',
    '450 kA',
    '600 kA',
    '700 kA',
    '750 kA',
    '1000 kA',
    '1300 kA',
    '1600 kA',
    '2000 kA'
);


ALTER TYPE public.current_range OWNER TO root;

--
-- TOC entry 852 (class 1247 OID 28576)
-- Name: divertor_config; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.divertor_config AS ENUM (
    'Conventional',
    'Super-X',
    'Super-X (Inner Leg)',
    'Snowflake',
    'Vertical Target',
    'X Divertor',
    'Limiter'
);


ALTER TYPE public.divertor_config OWNER TO root;

--
-- TOC entry 855 (class 1247 OID 28590)
-- Name: facility; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.facility AS ENUM (
    'MAST',
    'MAST-U'
);


ALTER TYPE public.facility OWNER TO root;

--
-- TOC entry 858 (class 1247 OID 28596)
-- Name: plasma_shape; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.plasma_shape AS ENUM (
    'Connected Double Null',
    'Lower Single Null',
    'Upper Single Null',
    'Limiter'
);


ALTER TYPE public.plasma_shape OWNER TO root;

--
-- TOC entry 861 (class 1247 OID 28606)
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
-- TOC entry 3642 (class 0 OID 0)
-- Dependencies: 861
-- Name: TYPE quality; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TYPE public.quality IS 'A number indicating the status of the signal:
-1 Poor Data: do not use (Very Bad)
0 Something is wrong in the Data (Bad)
1 either Raw data not checked or Analysed data quality is Unknown (Not Checked)
2 Data has been checked - no known problems (Checked)
3 Data was validated" (Validated)';


--
-- TOC entry 864 (class 1247 OID 28618)
-- Name: signal_type; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.signal_type AS ENUM (
    'Raw',
    'Analysed',
    'Image'
);

--
-- Name: source_format; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.source_format AS ENUM (
    'IDA3', 
    'NIDA', 
    'CDF', 
    'ASCII', 
    'IPX', 
    'TIF', 
    'NCDF'
);


ALTER TYPE public.signal_type OWNER TO root;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 214 (class 1259 OID 28623)
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
-- TOC entry 215 (class 1259 OID 28628)
-- Name: scenarios; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.scenarios (
    id smallint NOT NULL,
    name character varying(20) NOT NULL
);


ALTER TABLE public.scenarios OWNER TO root;

--
-- TOC entry 216 (class 1259 OID 28631)
-- Name: signals; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.signals (
    id integer NOT NULL,
    signal_dataset_id integer NOT NULL,
    shot_id integer NOT NULL,
    quality public.quality NOT NULL,
    shape integer[] NOT NULL
);


ALTER TABLE public.signals OWNER TO root;

--
-- TOC entry 220 (class 1259 OID 30034)
-- Name: signals_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

ALTER TABLE public.signals ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.signals_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- TOC entry 216 (class 1259 OID 28631)
-- Name: shot_source_link; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.shot_source_link (
    id integer NOT NULL,
    source text NOT NULL,
    shot_id integer NOT NULL,
    quality public.quality NOT NULL,
    pass integer NOT NULL,
    format public.source_format NOT NULL
);


ALTER TABLE public.shot_source_link OWNER TO root;

--
-- TOC entry 220 (class 1259 OID 30034)
-- Name: shot_source_link_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

ALTER TABLE public.shot_source_link ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.shot_source_link_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 217 (class 1259 OID 28634)
-- Name: shots; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.shots (
    shot_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    reference_shot integer,
    scenario smallint,
    current_range public.current_range,
    heating character varying(30),
    divertor_config public.divertor_config,
    pellets boolean,
    plasma_shape public.plasma_shape,
    rmp_coil boolean,
    preshot_description text NOT NULL,
    postshot_description text NOT NULL,
    comissioner public.comissioner,
    campaign character varying(4),
    facility public.facility NOT NULL,
    cpf_p03249 real,

    cpf_p04673 real,

    cpf_p04674 real,

    cpf_p04675 real,

    cpf_p04676 real,

    cpf_p04677 real,

    cpf_p04678 real,

    cpf_p04679 real,

    cpf_p04680 real,

    cpf_p04681 real,

    cpf_p04833 real,

    cpf_p04993 real,

    cpf_p05007 real,

    cpf_p05008 real,

    cpf_p05009 real,

    cpf_p05010 real,

    cpf_p05011 real,

    cpf_p05015 real,

    cpf_p05016 real,

    cpf_p05017 real,

    cpf_p05025 real,

    cpf_p05027 real,

    cpf_p05028 real,

    cpf_p05029 real,

    cpf_p05030 real,

    cpf_p05032 real,

    cpf_p05033 real,

    cpf_p05153 real,

    cpf_p06000 real,

    cpf_p06001 real,

    cpf_p06002 real,

    cpf_p06003 real,

    cpf_p06004 real,

    cpf_p10963 real,

    cpf_p10964 real,

    cpf_p12441 real,

    cpf_p12450 real,

    cpf_p12451 real,

    cpf_p12452 real,

    cpf_p15202 real,

    cpf_p15203 real,

    cpf_p15209 real,

    cpf_p15659 real,

    cpf_p15660 real,

    cpf_p15661 real,

    cpf_p20000 real,

    cpf_p20204 real,

    cpf_p20205 real,

    cpf_p20206 real,

    cpf_p20207 real,

    cpf_p20208 real,

    cpf_p21010 real,

    cpf_p21011 real,

    cpf_p21012 real,

    cpf_p21021 real,

    cpf_p21022 real,

    cpf_p21029 real,

    cpf_p21035 real,

    cpf_p21037 real,

    cpf_p21041 real,

    cpf_p21042 real,

    cpf_p21043 real,

    cpf_p21044 real,

    cpf_p21045 real,

    cpf_p21046 real,

    cpf_p21047 real,

    cpf_p21048 real,

    cpf_p21051 real,

    cpf_p21052 real,

    cpf_p21053 real,

    cpf_p21054 real,

    cpf_p21055 real,

    cpf_p21056 real,

    cpf_p21075 real,

    cpf_p21076 real,

    cpf_p21077 real,

    cpf_p21078 real,

    cpf_p21079 real,

    cpf_p21080 real,

    cpf_p21081 real,

    cpf_p21082 real,

    cpf_p21083 real,

    cpf_p21084 real,

    cpf_p21085 real,

    cpf_p21086 real,

    cpf_p21087 real,

    cpf_p21088 real,

    cpf_p21089 real,

    cpf_p21092 real,

    cpf_p21093 real,

    cpf_abort real,

    cpf_amin_ipmax real,

    cpf_amin_max real,

    cpf_amin_truby real,

    cpf_area_ipmax real,

    cpf_area_max real,

    cpf_area_truby real,

    cpf_bepmhd_ipmax real,

    cpf_bepmhd_max real,

    cpf_bepmhd_truby real,

    cpf_betmhd_ipmax real,

    cpf_betmhd_max real,

    cpf_betmhd_truby real,

    cpf_bt_ipmax real,

    cpf_bt_max real,

    cpf_bt_truby real,

    cpf_c2ratio real,

    cpf_column_temp_in real,

    cpf_column_temp_out real,

    cpf_creation date,

    cpf_dwmhd_ipmax real,

    cpf_dwmhd_max real,

    cpf_dwmhd_truby real,

    cpf_enbi_max_ss real,

    cpf_enbi_max_sw real,

    cpf_exp_date date,

    cpf_exp_number integer,

    cpf_exp_time time,

    cpf_gdc_duration real,

    cpf_gdc_time real,

    cpf_ibgas_pressure real,

    cpf_ip_av real,

    cpf_ip_max real,

    cpf_jnbi_ipmax real,

    cpf_jnbi_ipmax_ss real,

    cpf_jnbi_ipmax_sw real,

    cpf_jnbi_max real,

    cpf_jnbi_max_ss real,

    cpf_jnbi_max_sw real,

    cpf_jnbi_total real,

    cpf_jnbi_total_ss real,

    cpf_jnbi_total_sw real,

    cpf_jnbi_truby real,

    cpf_jnbi_truby_ss real,

    cpf_jnbi_truby_sw real,

    cpf_johm_ipmax real,

    cpf_johm_max real,

    cpf_johm_total real,

    cpf_johm_truby real,

    cpf_kappa_ipmax real,

    cpf_kappa_max real,

    cpf_kappa_truby real,

    cpf_li_2_ipmax real,

    cpf_li_2_max real,

    cpf_li_2_truby real,

    cpf_li_3_ipmax real,

    cpf_li_3_max real,

    cpf_li_3_truby real,

    cpf_log_base_pressure real,

    cpf_ndl_co2_ipmax real,

    cpf_ndl_co2_max real,

    cpf_ndl_co2_truby real,

    cpf_ne0_ipmax real,

    cpf_ne0_max real,

    cpf_ne0_truby real,

    cpf_ne0ratio_ipmax real,

    cpf_ne0ruby real,

    cpf_ne_bar_ipmax real,

    cpf_ne_yag_bar_ipmax real,

    cpf_ngreenwald_ipmax real,

    cpf_ngreenwaldratio_ipmax real,

    cpf_o2ratio real,

    cpf_objective text,

    cpf_pe0_ipmax real,

    cpf_pe0_max real,

    cpf_pe0_truby real,

    cpf_pe0ruby real,

    cpf_pic text,

    cpf_pnbi_ipmax real,

    cpf_pnbi_ipmax_ss real,

    cpf_pnbi_ipmax_sw real,

    cpf_pnbi_max real,

    cpf_pnbi_max_ss real,

    cpf_pnbi_max_sw real,

    cpf_pnbi_truby real,

    cpf_pnbi_truby_ss real,

    cpf_pnbi_truby_sw real,

    cpf_pohm_ipmax real,

    cpf_pohm_max real,

    cpf_pohm_truby real,

    cpf_postshot text,

    cpf_prad_ipmax real,

    cpf_prad_max real,

    cpf_prad_truby real,

    cpf_pradne2 real,

    cpf_preshot text,

    cpf_program text,

    cpf_pulno real,

    cpf_q95_ipmax real,

    cpf_q95_min real,

    cpf_q95_truby real,

    cpf_reference real,

    cpf_rgeo_ipmax real,

    cpf_rgeo_max real,

    cpf_rgeo_truby real,

    cpf_rinner_da real,

    cpf_rinner_efit real,

    cpf_rmag_efit real,

    cpf_router_da real,

    cpf_router_efit real,

    cpf_sarea_ipmax real,

    cpf_sarea_max real,

    cpf_sarea_truby real,

    cpf_sl text,

    cpf_summary text,

    cpf_tamin_max real,

    cpf_tarea_max real,

    cpf_tautot_ipmax real,

    cpf_tautot_max real,

    cpf_tautot_truby real,

    cpf_tbepmhd_max real,

    cpf_tbetmhd_max real,

    cpf_tbt_max real,

    cpf_tdwmhd_max real,

    cpf_te0_ipmax real,

    cpf_te0_max real,

    cpf_te0_truby real,

    cpf_te0ratio_ipmax real,

    cpf_te0ruby real,

    cpf_te_yag_bar_ipmax real,

    cpf_tend real,

    cpf_tend_ibgas real,

    cpf_tend_nbi real,

    cpf_tend_nbi_ss real,

    cpf_tend_nbi_sw real,

    cpf_term_code real,

    cpf_tftend real,

    cpf_tftstart real,

    cpf_tipmax real,

    cpf_tkappa_max real,

    cpf_tli_2_max real,

    cpf_tli_3_max real,

    cpf_tndl_co2_max real,

    cpf_tne0_max real,

    cpf_tpe0_max real,

    cpf_tpnbi_max real,

    cpf_tpnbi_max_ss real,

    cpf_tpnbi_max_sw real,

    cpf_tpohm_max real,

    cpf_tprad_max real,

    cpf_tq95_min real,

    cpf_trgeo_max real,

    cpf_truby real,

    cpf_tsarea_max real,

    cpf_tstart real,

    cpf_tstart_ibgas real,

    cpf_tstart_nbi real,

    cpf_tstart_nbi_ss real,

    cpf_tstart_nbi_sw real,

    cpf_ttautot_max real,

    cpf_tte0_max real,

    cpf_tvol_max real,

    cpf_twmhd_max real,

    cpf_tzeff_max real,

    cpf_useful real,

    cpf_vol_ipmax real,

    cpf_vol_max real,

    cpf_vol_truby real,

    cpf_wmhd_ipmax real,

    cpf_wmhd_max real,

    cpf_wmhd_truby real,

    cpf_zeff_ipmax real,

    cpf_zeff_max real,

    cpf_zeff_truby real,

    cpf_zmag_efit real
);


ALTER TABLE public.shots OWNER TO root;

--
-- TOC entry 3643 (class 0 OID 0)
-- Dependencies: 217
-- Name: COLUMN shots.heating; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.shots.heating IS 'First bit: Ohmic 
Second bit: One Beam (South / On Axis) 
Third bit: One Beam (South-West / Off Axis) ';

--
-- TOC entry 218 (class 1259 OID 28639)
-- Name: sources; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sources (
    name text NOT NULL,
    description text NOT NULL,
    source_type public.signal_type NOT NULL,
    annotations jsonb
);


ALTER TABLE public.sources OWNER TO root;

--
-- TOC entry 218 (class 1259 OID 28639)
-- Name: signals; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.signal_datasets (
    signal_dataset_id integer NOT NULL,
    name text NOT NULL,
    units character varying(20) NOT NULL,
    rank smallint NOT NULL,
    uri text,
    description text NOT NULL,
    signal_type public.signal_type NOT NULL,
    quality public.quality NOT NULL,
    doi text NOT NULL,
    dimensions text[],
    camera_metadata integer,
    camera integer
);


ALTER TABLE public.signal_datasets OWNER TO root;

--
-- TOC entry 219 (class 1259 OID 29997)
-- Name: signals_signal_dataset_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

ALTER TABLE public.signal_datasets ALTER COLUMN signal_dataset_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.signal_datasets_signal_dataset_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- TOC entry 3218 (class 2606 OID 28645)
-- Name: cpf_summary cpf_summary_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.cpf_summary
    ADD CONSTRAINT cpf_summary_pkey PRIMARY KEY (id);


--
-- TOC entry 3220 (class 2606 OID 28647)
-- Name: scenarios scenarios_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.scenarios
    ADD CONSTRAINT scenarios_pkey PRIMARY KEY (id);


--
-- TOC entry 3222 (class 2606 OID 28649)
-- Name: signals signals_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.signals
    ADD CONSTRAINT signals_pkey PRIMARY KEY (id);

--
-- TOC entry 3224 (class 2606 OID 28651)
-- Name: shots shots_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT shots_pkey PRIMARY KEY (shot_id);


--
-- TOC entry 3226 (class 2606 OID 28653)
-- Name: signals signals_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.signal_datasets
    ADD CONSTRAINT signal_datasets_pkey PRIMARY KEY (signal_dataset_id);


ALTER TABLE ONLY public.sources
    ADD CONSTRAINT sources_pkey PRIMARY KEY (name);

--
-- TOC entry 3494 (class 2606 OID 28654)
-- Name: shots scenario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT scenario_fkey FOREIGN KEY (scenario) REFERENCES public.scenarios(id) NOT VALID;


--
-- TOC entry 3227 (class 2606 OID 28659)
-- Name: signals shot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.signals
    ADD CONSTRAINT shot_id_fkey FOREIGN KEY (shot_id) REFERENCES public.shots(shot_id) NOT VALID;


--
-- TOC entry 3228 (class 2606 OID 28664)
-- Name: signals signal_datasets_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.signals
    ADD CONSTRAINT signal_dataset_id_fkey FOREIGN KEY (signal_dataset_id) REFERENCES public.signal_datasets(signal_dataset_id) NOT VALID;

--
-- TOC entry 3227 (class 2606 OID 28659)
-- Name: shot_source_link shot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shot_source_link
    ADD CONSTRAINT shot_id_fkey FOREIGN KEY (shot_id) REFERENCES public.shots(shot_id) NOT VALID;


--
-- TOC entry 3228 (class 2606 OID 28664)
-- Name: shot_source_link signal_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shot_source_link
    ADD CONSTRAINT source_fkey FOREIGN KEY (source) REFERENCES public.sources(name) NOT VALID;

-- Completed on 2023-03-20 15:21:26 UTC

--
-- PostgreSQL database dump complete
--


-- Create reader user
DROP USER IF EXISTS dbreader;
CREATE USER dbreader WITH PASSWORD 'fairly-mast';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dbreader;