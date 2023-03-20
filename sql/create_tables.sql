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
    '700 kA',
    '1000 kA',
    '1300 kA',
    '1600 kA',
    '2000 kA'
);


ALTER TYPE public.current_range OWNER TO root;

--
-- TOC entry 849 (class 1247 OID 28568)
-- Name: dimension; Type: TYPE; Schema: public; Owner: root
--

CREATE TYPE public.dimension AS ENUM (
    'Time',
    'X',
    'Y'
);


ALTER TYPE public.dimension OWNER TO root;

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
    'X Divertor'
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
    'Double Null',
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
    'Analysed'
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
    name character varying(10) NOT NULL
);


ALTER TABLE public.scenarios OWNER TO root;

--
-- TOC entry 216 (class 1259 OID 28631)
-- Name: shot_signal_link; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.shot_signal_link (
    id integer NOT NULL,
    signal_id integer NOT NULL,
    shot_id integer NOT NULL
);


ALTER TABLE public.shot_signal_link OWNER TO root;

--
-- TOC entry 220 (class 1259 OID 30034)
-- Name: shot_signal_link_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

ALTER TABLE public.shot_signal_link ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.shot_signal_link_id_seq
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
    facility public.facility NOT NULL,
    cpf_p03249_value real,
    cpf_p03249_summary smallint,
    cpf_p04673_value real,
    cpf_p04673_summary smallint,
    cpf_p04674_value real,
    cpf_p04674_summary smallint,
    cpf_p04675_value real,
    cpf_p04675_summary smallint,
    cpf_p04676_value real,
    cpf_p04676_summary smallint,
    cpf_p04677_value real,
    cpf_p04677_summary smallint,
    cpf_p04678_value real,
    cpf_p04678_summary smallint,
    cpf_p04679_value real,
    cpf_p04679_summary smallint,
    cpf_p04680_value real,
    cpf_p04680_summary smallint,
    cpf_p04681_value real,
    cpf_p04681_summary smallint,
    cpf_p04833_value real,
    cpf_p04833_summary smallint,
    cpf_p04993_value real,
    cpf_p04993_summary smallint,
    cpf_p05007_value real,
    cpf_p05007_summary smallint,
    cpf_p05008_value real,
    cpf_p05008_summary smallint,
    cpf_p05009_value real,
    cpf_p05009_summary smallint,
    cpf_p05010_value real,
    cpf_p05010_summary smallint,
    cpf_p05011_value real,
    cpf_p05011_summary smallint,
    cpf_p05015_value real,
    cpf_p05015_summary smallint,
    cpf_p05016_value real,
    cpf_p05016_summary smallint,
    cpf_p05017_value real,
    cpf_p05017_summary smallint,
    cpf_p05025_value real,
    cpf_p05025_summary smallint,
    cpf_p05027_value real,
    cpf_p05027_summary smallint,
    cpf_p05028_value real,
    cpf_p05028_summary smallint,
    cpf_p05029_value real,
    cpf_p05029_summary smallint,
    cpf_p05030_value real,
    cpf_p05030_summary smallint,
    cpf_p05032_value real,
    cpf_p05032_summary smallint,
    cpf_p05033_value real,
    cpf_p05033_summary smallint,
    cpf_p05153_value real,
    cpf_p05153_summary smallint,
    cpf_p06000_value real,
    cpf_p06000_summary smallint,
    cpf_p06001_value real,
    cpf_p06001_summary smallint,
    cpf_p06002_value real,
    cpf_p06002_summary smallint,
    cpf_p06003_value real,
    cpf_p06003_summary smallint,
    cpf_p06004_value real,
    cpf_p06004_summary smallint,
    cpf_p10963_value real,
    cpf_p10963_summary smallint,
    cpf_p10964_value real,
    cpf_p10964_summary smallint,
    cpf_p12441_value real,
    cpf_p12441_summary smallint,
    cpf_p12450_value real,
    cpf_p12450_summary smallint,
    cpf_p12451_value real,
    cpf_p12451_summary smallint,
    cpf_p12452_value real,
    cpf_p12452_summary smallint,
    cpf_p15202_value real,
    cpf_p15202_summary smallint,
    cpf_p15203_value real,
    cpf_p15203_summary smallint,
    cpf_p15209_value real,
    cpf_p15209_summary smallint,
    cpf_p15659_value real,
    cpf_p15659_summary smallint,
    cpf_p15660_value real,
    cpf_p15660_summary smallint,
    cpf_p15661_value real,
    cpf_p15661_summary smallint,
    cpf_p20000_value real,
    cpf_p20000_summary smallint,
    cpf_p20204_value real,
    cpf_p20204_summary smallint,
    cpf_p20205_value real,
    cpf_p20205_summary smallint,
    cpf_p20206_value real,
    cpf_p20206_summary smallint,
    cpf_p20207_value real,
    cpf_p20207_summary smallint,
    cpf_p20208_value real,
    cpf_p20208_summary smallint,
    cpf_p21010_value real,
    cpf_p21010_summary smallint,
    cpf_p21011_value real,
    cpf_p21011_summary smallint,
    cpf_p21012_value real,
    cpf_p21012_summary smallint,
    cpf_p21021_value real,
    cpf_p21021_summary smallint,
    cpf_p21022_value real,
    cpf_p21022_summary smallint,
    cpf_p21029_value real,
    cpf_p21029_summary smallint,
    cpf_p21035_value real,
    cpf_p21035_summary smallint,
    cpf_p21037_value real,
    cpf_p21037_summary smallint,
    cpf_p21041_value real,
    cpf_p21041_summary smallint,
    cpf_p21042_value real,
    cpf_p21042_summary smallint,
    cpf_p21043_value real,
    cpf_p21043_summary smallint,
    cpf_p21044_value real,
    cpf_p21044_summary smallint,
    cpf_p21045_value real,
    cpf_p21045_summary smallint,
    cpf_p21046_value real,
    cpf_p21046_summary smallint,
    cpf_p21047_value real,
    cpf_p21047_summary smallint,
    cpf_p21048_value real,
    cpf_p21048_summary smallint,
    cpf_p21051_value real,
    cpf_p21051_summary smallint,
    cpf_p21052_value real,
    cpf_p21052_summary smallint,
    cpf_p21053_value real,
    cpf_p21053_summary smallint,
    cpf_p21054_value real,
    cpf_p21054_summary smallint,
    cpf_p21055_value real,
    cpf_p21055_summary smallint,
    cpf_p21056_value real,
    cpf_p21056_summary smallint,
    cpf_p21075_value real,
    cpf_p21075_summary smallint,
    cpf_p21076_value real,
    cpf_p21076_summary smallint,
    cpf_p21077_value real,
    cpf_p21077_summary smallint,
    cpf_p21078_value real,
    cpf_p21078_summary smallint,
    cpf_p21079_value real,
    cpf_p21079_summary smallint,
    cpf_p21080_value real,
    cpf_p21080_summary smallint,
    cpf_p21081_value real,
    cpf_p21081_summary smallint,
    cpf_p21082_value real,
    cpf_p21082_summary smallint,
    cpf_p21083_value real,
    cpf_p21083_summary smallint,
    cpf_p21084_value real,
    cpf_p21084_summary smallint,
    cpf_p21085_value real,
    cpf_p21085_summary smallint,
    cpf_p21086_value real,
    cpf_p21086_summary smallint,
    cpf_p21087_value real,
    cpf_p21087_summary smallint,
    cpf_p21088_value real,
    cpf_p21088_summary smallint,
    cpf_p21089_value real,
    cpf_p21089_summary smallint,
    cpf_p21092_value real,
    cpf_p21092_summary smallint,
    cpf_p21093_value real,
    cpf_p21093_summary smallint,
    cpf_abort_value real,
    cpf_abort_summary smallint,
    cpf_amin_ipmax_value real,
    cpf_amin_ipmax_summary smallint,
    cpf_amin_max_value real,
    cpf_amin_max_summary smallint,
    cpf_amin_truby_value real,
    cpf_amin_truby_summary smallint,
    cpf_area_ipmax_value real,
    cpf_area_ipmax_summary smallint,
    cpf_area_max_value real,
    cpf_area_max_summary smallint,
    cpf_area_truby_value real,
    cpf_area_truby_summary smallint,
    cpf_bepmhd_ipmax_value real,
    cpf_bepmhd_ipmax_summary smallint,
    cpf_bepmhd_max_value real,
    cpf_bepmhd_max_summary smallint,
    cpf_bepmhd_truby_value real,
    cpf_bepmhd_truby_summary smallint,
    cpf_betmhd_ipmax_value real,
    cpf_betmhd_ipmax_summary smallint,
    cpf_betmhd_max_value real,
    cpf_betmhd_max_summary smallint,
    cpf_betmhd_truby_value real,
    cpf_betmhd_truby_summary smallint,
    cpf_bt_ipmax_value real,
    cpf_bt_ipmax_summary smallint,
    cpf_bt_max_value real,
    cpf_bt_max_summary smallint,
    cpf_bt_truby_value real,
    cpf_bt_truby_summary smallint,
    cpf_c2ratio_value real,
    cpf_c2ratio_summary smallint,
    cpf_column_temp_in_value real,
    cpf_column_temp_in_summary smallint,
    cpf_column_temp_out_value real,
    cpf_column_temp_out_summary smallint,
    cpf_creation_value real,
    cpf_creation_summary smallint,
    cpf_dwmhd_ipmax_value real,
    cpf_dwmhd_ipmax_summary smallint,
    cpf_dwmhd_max_value real,
    cpf_dwmhd_max_summary smallint,
    cpf_dwmhd_truby_value real,
    cpf_dwmhd_truby_summary smallint,
    cpf_enbi_max_ss_value real,
    cpf_enbi_max_ss_summary smallint,
    cpf_enbi_max_sw_value real,
    cpf_enbi_max_sw_summary smallint,
    cpf_exp_date_value real,
    cpf_exp_date_summary smallint,
    cpf_exp_number_value real,
    cpf_exp_number_summary smallint,
    cpf_exp_time_value real,
    cpf_exp_time_summary smallint,
    cpf_gdc_duration_value real,
    cpf_gdc_duration_summary smallint,
    cpf_gdc_time_value real,
    cpf_gdc_time_summary smallint,
    cpf_ibgas_pressure_value real,
    cpf_ibgas_pressure_summary smallint,
    cpf_ip_av_value real,
    cpf_ip_av_summary smallint,
    cpf_ip_max_value real,
    cpf_ip_max_summary smallint,
    cpf_jnbi_ipmax_value real,
    cpf_jnbi_ipmax_summary smallint,
    cpf_jnbi_ipmax_ss_value real,
    cpf_jnbi_ipmax_ss_summary smallint,
    cpf_jnbi_ipmax_sw_value real,
    cpf_jnbi_ipmax_sw_summary smallint,
    cpf_jnbi_max_value real,
    cpf_jnbi_max_summary smallint,
    cpf_jnbi_max_ss_value real,
    cpf_jnbi_max_ss_summary smallint,
    cpf_jnbi_max_sw_value real,
    cpf_jnbi_max_sw_summary smallint,
    cpf_jnbi_total_value real,
    cpf_jnbi_total_summary smallint,
    cpf_jnbi_total_ss_value real,
    cpf_jnbi_total_ss_summary smallint,
    cpf_jnbi_total_sw_value real,
    cpf_jnbi_total_sw_summary smallint,
    cpf_jnbi_truby_value real,
    cpf_jnbi_truby_summary smallint,
    cpf_jnbi_truby_ss_value real,
    cpf_jnbi_truby_ss_summary smallint,
    cpf_jnbi_truby_sw_value real,
    cpf_jnbi_truby_sw_summary smallint,
    cpf_johm_ipmax_value real,
    cpf_johm_ipmax_summary smallint,
    cpf_johm_max_value real,
    cpf_johm_max_summary smallint,
    cpf_johm_total_value real,
    cpf_johm_total_summary smallint,
    cpf_johm_truby_value real,
    cpf_johm_truby_summary smallint,
    cpf_kappa_ipmax_value real,
    cpf_kappa_ipmax_summary smallint,
    cpf_kappa_max_value real,
    cpf_kappa_max_summary smallint,
    cpf_kappa_truby_value real,
    cpf_kappa_truby_summary smallint,
    cpf_li_2_ipmax_value real,
    cpf_li_2_ipmax_summary smallint,
    cpf_li_2_max_value real,
    cpf_li_2_max_summary smallint,
    cpf_li_2_truby_value real,
    cpf_li_2_truby_summary smallint,
    cpf_li_3_ipmax_value real,
    cpf_li_3_ipmax_summary smallint,
    cpf_li_3_max_value real,
    cpf_li_3_max_summary smallint,
    cpf_li_3_truby_value real,
    cpf_li_3_truby_summary smallint,
    cpf_log_base_pressure_value real,
    cpf_log_base_pressure_summary smallint,
    cpf_ndl_co2_ipmax_value real,
    cpf_ndl_co2_ipmax_summary smallint,
    cpf_ndl_co2_max_value real,
    cpf_ndl_co2_max_summary smallint,
    cpf_ndl_co2_truby_value real,
    cpf_ndl_co2_truby_summary smallint,
    cpf_ne0_ipmax_value real,
    cpf_ne0_ipmax_summary smallint,
    cpf_ne0_max_value real,
    cpf_ne0_max_summary smallint,
    cpf_ne0_truby_value real,
    cpf_ne0_truby_summary smallint,
    cpf_ne0ratio_ipmax_value real,
    cpf_ne0ratio_ipmax_summary smallint,
    cpf_ne0ruby_value real,
    cpf_ne0ruby_summary smallint,
    cpf_ne_bar_ipmax_value real,
    cpf_ne_bar_ipmax_summary smallint,
    cpf_ne_yag_bar_ipmax_value real,
    cpf_ne_yag_bar_ipmax_summary smallint,
    cpf_ngreenwald_ipmax_value real,
    cpf_ngreenwald_ipmax_summary smallint,
    cpf_ngreenwaldratio_ipmax_value real,
    cpf_ngreenwaldratio_ipmax_summary smallint,
    cpf_o2ratio_value real,
    cpf_o2ratio_summary smallint,
    cpf_objective_value real,
    cpf_objective_summary smallint,
    cpf_pe0_ipmax_value real,
    cpf_pe0_ipmax_summary smallint,
    cpf_pe0_max_value real,
    cpf_pe0_max_summary smallint,
    cpf_pe0_truby_value real,
    cpf_pe0_truby_summary smallint,
    cpf_pe0ruby_value real,
    cpf_pe0ruby_summary smallint,
    cpf_pic_value real,
    cpf_pic_summary smallint,
    cpf_pnbi_ipmax_value real,
    cpf_pnbi_ipmax_summary smallint,
    cpf_pnbi_ipmax_ss_value real,
    cpf_pnbi_ipmax_ss_summary smallint,
    cpf_pnbi_ipmax_sw_value real,
    cpf_pnbi_ipmax_sw_summary smallint,
    cpf_pnbi_max_value real,
    cpf_pnbi_max_summary smallint,
    cpf_pnbi_max_ss_value real,
    cpf_pnbi_max_ss_summary smallint,
    cpf_pnbi_max_sw_value real,
    cpf_pnbi_max_sw_summary smallint,
    cpf_pnbi_truby_value real,
    cpf_pnbi_truby_summary smallint,
    cpf_pnbi_truby_ss_value real,
    cpf_pnbi_truby_ss_summary smallint,
    cpf_pnbi_truby_sw_value real,
    cpf_pnbi_truby_sw_summary smallint,
    cpf_pohm_ipmax_value real,
    cpf_pohm_ipmax_summary smallint,
    cpf_pohm_max_value real,
    cpf_pohm_max_summary smallint,
    cpf_pohm_truby_value real,
    cpf_pohm_truby_summary smallint,
    cpf_postshot_value real,
    cpf_postshot_summary smallint,
    cpf_prad_ipmax_value real,
    cpf_prad_ipmax_summary smallint,
    cpf_prad_max_value real,
    cpf_prad_max_summary smallint,
    cpf_prad_truby_value real,
    cpf_prad_truby_summary smallint,
    cpf_pradne2_value real,
    cpf_pradne2_summary smallint,
    cpf_preshot_value real,
    cpf_preshot_summary smallint,
    cpf_program_value real,
    cpf_program_summary smallint,
    cpf_pulno_value real,
    cpf_pulno_summary smallint,
    cpf_q95_ipmax_value real,
    cpf_q95_ipmax_summary smallint,
    cpf_q95_min_value real,
    cpf_q95_min_summary smallint,
    cpf_q95_truby_value real,
    cpf_q95_truby_summary smallint,
    cpf_reference_value real,
    cpf_reference_summary smallint,
    cpf_rgeo_ipmax_value real,
    cpf_rgeo_ipmax_summary smallint,
    cpf_rgeo_max_value real,
    cpf_rgeo_max_summary smallint,
    cpf_rgeo_truby_value real,
    cpf_rgeo_truby_summary smallint,
    cpf_rinner_da_value real,
    cpf_rinner_da_summary smallint,
    cpf_rinner_efit_value real,
    cpf_rinner_efit_summary smallint,
    cpf_rmag_efit_value real,
    cpf_rmag_efit_summary smallint,
    cpf_router_da_value real,
    cpf_router_da_summary smallint,
    cpf_router_efit_value real,
    cpf_router_efit_summary smallint,
    cpf_sarea_ipmax_value real,
    cpf_sarea_ipmax_summary smallint,
    cpf_sarea_max_value real,
    cpf_sarea_max_summary smallint,
    cpf_sarea_truby_value real,
    cpf_sarea_truby_summary smallint,
    cpf_sl_value real,
    cpf_sl_summary smallint,
    cpf_summary_value real,
    cpf_summary_summary smallint,
    cpf_tamin_max_value real,
    cpf_tamin_max_summary smallint,
    cpf_tarea_max_value real,
    cpf_tarea_max_summary smallint,
    cpf_tautot_ipmax_value real,
    cpf_tautot_ipmax_summary smallint,
    cpf_tautot_max_value real,
    cpf_tautot_max_summary smallint,
    cpf_tautot_truby_value real,
    cpf_tautot_truby_summary smallint,
    cpf_tbepmhd_max_value real,
    cpf_tbepmhd_max_summary smallint,
    cpf_tbetmhd_max_value real,
    cpf_tbetmhd_max_summary smallint,
    cpf_tbt_max_value real,
    cpf_tbt_max_summary smallint,
    cpf_tdwmhd_max_value real,
    cpf_tdwmhd_max_summary smallint,
    cpf_te0_ipmax_value real,
    cpf_te0_ipmax_summary smallint,
    cpf_te0_max_value real,
    cpf_te0_max_summary smallint,
    cpf_te0_truby_value real,
    cpf_te0_truby_summary smallint,
    cpf_te0ratio_ipmax_value real,
    cpf_te0ratio_ipmax_summary smallint,
    cpf_te0ruby_value real,
    cpf_te0ruby_summary smallint,
    cpf_te_yag_bar_ipmax_value real,
    cpf_te_yag_bar_ipmax_summary smallint,
    cpf_tend_value real,
    cpf_tend_summary smallint,
    cpf_tend_ibgas_value real,
    cpf_tend_ibgas_summary smallint,
    cpf_tend_nbi_value real,
    cpf_tend_nbi_summary smallint,
    cpf_tend_nbi_ss_value real,
    cpf_tend_nbi_ss_summary smallint,
    cpf_tend_nbi_sw_value real,
    cpf_tend_nbi_sw_summary smallint,
    cpf_term_code_value real,
    cpf_term_code_summary smallint,
    cpf_tftend_value real,
    cpf_tftend_summary smallint,
    cpf_tftstart_value real,
    cpf_tftstart_summary smallint,
    cpf_tipmax_value real,
    cpf_tipmax_summary smallint,
    cpf_tkappa_max_value real,
    cpf_tkappa_max_summary smallint,
    cpf_tli_2_max_value real,
    cpf_tli_2_max_summary smallint,
    cpf_tli_3_max_value real,
    cpf_tli_3_max_summary smallint,
    cpf_tndl_co2_max_value real,
    cpf_tndl_co2_max_summary smallint,
    cpf_tne0_max_value real,
    cpf_tne0_max_summary smallint,
    cpf_tpe0_max_value real,
    cpf_tpe0_max_summary smallint,
    cpf_tpnbi_max_value real,
    cpf_tpnbi_max_summary smallint,
    cpf_tpnbi_max_ss_value real,
    cpf_tpnbi_max_ss_summary smallint,
    cpf_tpnbi_max_sw_value real,
    cpf_tpnbi_max_sw_summary smallint,
    cpf_tpohm_max_value real,
    cpf_tpohm_max_summary smallint,
    cpf_tprad_max_value real,
    cpf_tprad_max_summary smallint,
    cpf_tq95_min_value real,
    cpf_tq95_min_summary smallint,
    cpf_trgeo_max_value real,
    cpf_trgeo_max_summary smallint,
    cpf_truby_value real,
    cpf_truby_summary smallint,
    cpf_tsarea_max_value real,
    cpf_tsarea_max_summary smallint,
    cpf_tstart_value real,
    cpf_tstart_summary smallint,
    cpf_tstart_ibgas_value real,
    cpf_tstart_ibgas_summary smallint,
    cpf_tstart_nbi_value real,
    cpf_tstart_nbi_summary smallint,
    cpf_tstart_nbi_ss_value real,
    cpf_tstart_nbi_ss_summary smallint,
    cpf_tstart_nbi_sw_value real,
    cpf_tstart_nbi_sw_summary smallint,
    cpf_ttautot_max_value real,
    cpf_ttautot_max_summary smallint,
    cpf_tte0_max_value real,
    cpf_tte0_max_summary smallint,
    cpf_tvol_max_value real,
    cpf_tvol_max_summary smallint,
    cpf_twmhd_max_value real,
    cpf_twmhd_max_summary smallint,
    cpf_tzeff_max_value real,
    cpf_tzeff_max_summary smallint,
    cpf_useful_value real,
    cpf_useful_summary smallint,
    cpf_vol_ipmax_value real,
    cpf_vol_ipmax_summary smallint,
    cpf_vol_max_value real,
    cpf_vol_max_summary smallint,
    cpf_vol_truby_value real,
    cpf_vol_truby_summary smallint,
    cpf_wmhd_ipmax_value real,
    cpf_wmhd_ipmax_summary smallint,
    cpf_wmhd_max_value real,
    cpf_wmhd_max_summary smallint,
    cpf_wmhd_truby_value real,
    cpf_wmhd_truby_summary smallint,
    cpf_zeff_ipmax_value real,
    cpf_zeff_ipmax_summary smallint,
    cpf_zeff_max_value real,
    cpf_zeff_max_summary smallint,
    cpf_zeff_truby_value real,
    cpf_zeff_truby_summary smallint,
    cpf_zmag_efit_value real,
    cpf_zmag_efit_summary smallint
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
    camera integer
);


ALTER TABLE public.signals OWNER TO root;

--
-- TOC entry 219 (class 1259 OID 29997)
-- Name: signals_signal_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

ALTER TABLE public.signals ALTER COLUMN signal_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.signals_signal_id_seq
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
-- Name: shot_signal_link shot_signal_link_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shot_signal_link
    ADD CONSTRAINT shot_signal_link_pkey PRIMARY KEY (id);


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

ALTER TABLE ONLY public.signals
    ADD CONSTRAINT signals_pkey PRIMARY KEY (signal_id);


--
-- TOC entry 3229 (class 2606 OID 29119)
-- Name: shots cpf_abort_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_abort_fkey FOREIGN KEY (cpf_abort_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3230 (class 2606 OID 29124)
-- Name: shots cpf_amin_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_amin_ipmax_fkey FOREIGN KEY (cpf_amin_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3231 (class 2606 OID 29129)
-- Name: shots cpf_amin_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_amin_max_fkey FOREIGN KEY (cpf_amin_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3232 (class 2606 OID 29134)
-- Name: shots cpf_amin_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_amin_truby_fkey FOREIGN KEY (cpf_amin_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3233 (class 2606 OID 29139)
-- Name: shots cpf_area_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_area_ipmax_fkey FOREIGN KEY (cpf_area_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3234 (class 2606 OID 29144)
-- Name: shots cpf_area_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_area_max_fkey FOREIGN KEY (cpf_area_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3235 (class 2606 OID 29149)
-- Name: shots cpf_area_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_area_truby_fkey FOREIGN KEY (cpf_area_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3236 (class 2606 OID 29154)
-- Name: shots cpf_bepmhd_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_bepmhd_ipmax_fkey FOREIGN KEY (cpf_bepmhd_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3237 (class 2606 OID 29159)
-- Name: shots cpf_bepmhd_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_bepmhd_max_fkey FOREIGN KEY (cpf_bepmhd_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3238 (class 2606 OID 29164)
-- Name: shots cpf_bepmhd_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_bepmhd_truby_fkey FOREIGN KEY (cpf_bepmhd_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3239 (class 2606 OID 29169)
-- Name: shots cpf_betmhd_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_betmhd_ipmax_fkey FOREIGN KEY (cpf_betmhd_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3240 (class 2606 OID 29174)
-- Name: shots cpf_betmhd_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_betmhd_max_fkey FOREIGN KEY (cpf_betmhd_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3241 (class 2606 OID 29179)
-- Name: shots cpf_betmhd_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_betmhd_truby_fkey FOREIGN KEY (cpf_betmhd_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3242 (class 2606 OID 29184)
-- Name: shots cpf_bt_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_bt_ipmax_fkey FOREIGN KEY (cpf_bt_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3243 (class 2606 OID 29189)
-- Name: shots cpf_bt_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_bt_max_fkey FOREIGN KEY (cpf_bt_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3244 (class 2606 OID 29194)
-- Name: shots cpf_bt_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_bt_truby_fkey FOREIGN KEY (cpf_bt_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3245 (class 2606 OID 29199)
-- Name: shots cpf_c2ratio_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_c2ratio_fkey FOREIGN KEY (cpf_c2ratio_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3246 (class 2606 OID 29204)
-- Name: shots cpf_column_temp_in_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_column_temp_in_fkey FOREIGN KEY (cpf_column_temp_in_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3247 (class 2606 OID 29209)
-- Name: shots cpf_column_temp_out_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_column_temp_out_fkey FOREIGN KEY (cpf_column_temp_out_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3248 (class 2606 OID 29214)
-- Name: shots cpf_creation_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_creation_fkey FOREIGN KEY (cpf_creation_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3249 (class 2606 OID 29219)
-- Name: shots cpf_dwmhd_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_dwmhd_ipmax_fkey FOREIGN KEY (cpf_dwmhd_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3250 (class 2606 OID 29224)
-- Name: shots cpf_dwmhd_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_dwmhd_max_fkey FOREIGN KEY (cpf_dwmhd_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3251 (class 2606 OID 29229)
-- Name: shots cpf_dwmhd_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_dwmhd_truby_fkey FOREIGN KEY (cpf_dwmhd_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3252 (class 2606 OID 29234)
-- Name: shots cpf_enbi_max_ss_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_enbi_max_ss_fkey FOREIGN KEY (cpf_enbi_max_ss_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3253 (class 2606 OID 29239)
-- Name: shots cpf_enbi_max_sw_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_enbi_max_sw_fkey FOREIGN KEY (cpf_enbi_max_sw_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3254 (class 2606 OID 29244)
-- Name: shots cpf_exp_date_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_exp_date_fkey FOREIGN KEY (cpf_exp_date_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3255 (class 2606 OID 29249)
-- Name: shots cpf_exp_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_exp_number_fkey FOREIGN KEY (cpf_exp_number_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3256 (class 2606 OID 29254)
-- Name: shots cpf_exp_time_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_exp_time_fkey FOREIGN KEY (cpf_exp_time_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3257 (class 2606 OID 29259)
-- Name: shots cpf_gdc_duration_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_gdc_duration_fkey FOREIGN KEY (cpf_gdc_duration_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3258 (class 2606 OID 29264)
-- Name: shots cpf_gdc_time_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_gdc_time_fkey FOREIGN KEY (cpf_gdc_time_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3259 (class 2606 OID 29269)
-- Name: shots cpf_ibgas_pressure_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ibgas_pressure_fkey FOREIGN KEY (cpf_ibgas_pressure_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3260 (class 2606 OID 29274)
-- Name: shots cpf_ip_av_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ip_av_fkey FOREIGN KEY (cpf_ip_av_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3261 (class 2606 OID 29279)
-- Name: shots cpf_ip_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ip_max_fkey FOREIGN KEY (cpf_ip_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3262 (class 2606 OID 29284)
-- Name: shots cpf_jnbi_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_ipmax_fkey FOREIGN KEY (cpf_jnbi_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3263 (class 2606 OID 29289)
-- Name: shots cpf_jnbi_ipmax_ss_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_ipmax_ss_fkey FOREIGN KEY (cpf_jnbi_ipmax_ss_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3264 (class 2606 OID 29294)
-- Name: shots cpf_jnbi_ipmax_sw_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_ipmax_sw_fkey FOREIGN KEY (cpf_jnbi_ipmax_sw_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3265 (class 2606 OID 29299)
-- Name: shots cpf_jnbi_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_max_fkey FOREIGN KEY (cpf_jnbi_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3266 (class 2606 OID 29304)
-- Name: shots cpf_jnbi_max_ss_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_max_ss_fkey FOREIGN KEY (cpf_jnbi_max_ss_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3267 (class 2606 OID 29309)
-- Name: shots cpf_jnbi_max_sw_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_max_sw_fkey FOREIGN KEY (cpf_jnbi_max_sw_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3268 (class 2606 OID 29314)
-- Name: shots cpf_jnbi_total_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_total_fkey FOREIGN KEY (cpf_jnbi_total_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3269 (class 2606 OID 29319)
-- Name: shots cpf_jnbi_total_ss_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_total_ss_fkey FOREIGN KEY (cpf_jnbi_total_ss_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3270 (class 2606 OID 29324)
-- Name: shots cpf_jnbi_total_sw_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_total_sw_fkey FOREIGN KEY (cpf_jnbi_total_sw_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3271 (class 2606 OID 29329)
-- Name: shots cpf_jnbi_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_truby_fkey FOREIGN KEY (cpf_jnbi_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3272 (class 2606 OID 29334)
-- Name: shots cpf_jnbi_truby_ss_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_truby_ss_fkey FOREIGN KEY (cpf_jnbi_truby_ss_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3273 (class 2606 OID 29339)
-- Name: shots cpf_jnbi_truby_sw_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_jnbi_truby_sw_fkey FOREIGN KEY (cpf_jnbi_truby_sw_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3274 (class 2606 OID 29344)
-- Name: shots cpf_johm_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_johm_ipmax_fkey FOREIGN KEY (cpf_johm_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3275 (class 2606 OID 29349)
-- Name: shots cpf_johm_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_johm_max_fkey FOREIGN KEY (cpf_johm_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3276 (class 2606 OID 29354)
-- Name: shots cpf_johm_total_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_johm_total_fkey FOREIGN KEY (cpf_johm_total_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3277 (class 2606 OID 29359)
-- Name: shots cpf_johm_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_johm_truby_fkey FOREIGN KEY (cpf_johm_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3278 (class 2606 OID 29364)
-- Name: shots cpf_kappa_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_kappa_ipmax_fkey FOREIGN KEY (cpf_kappa_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3279 (class 2606 OID 29369)
-- Name: shots cpf_kappa_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_kappa_max_fkey FOREIGN KEY (cpf_kappa_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3280 (class 2606 OID 29374)
-- Name: shots cpf_kappa_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_kappa_truby_fkey FOREIGN KEY (cpf_kappa_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3281 (class 2606 OID 29379)
-- Name: shots cpf_li_2_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_li_2_ipmax_fkey FOREIGN KEY (cpf_li_2_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3282 (class 2606 OID 29384)
-- Name: shots cpf_li_2_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_li_2_max_fkey FOREIGN KEY (cpf_li_2_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3283 (class 2606 OID 29389)
-- Name: shots cpf_li_2_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_li_2_truby_fkey FOREIGN KEY (cpf_li_2_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3284 (class 2606 OID 29394)
-- Name: shots cpf_li_3_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_li_3_ipmax_fkey FOREIGN KEY (cpf_li_3_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3285 (class 2606 OID 29399)
-- Name: shots cpf_li_3_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_li_3_max_fkey FOREIGN KEY (cpf_li_3_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3286 (class 2606 OID 29404)
-- Name: shots cpf_li_3_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_li_3_truby_fkey FOREIGN KEY (cpf_li_3_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3287 (class 2606 OID 29409)
-- Name: shots cpf_log_base_pressure_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_log_base_pressure_fkey FOREIGN KEY (cpf_log_base_pressure_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3288 (class 2606 OID 29414)
-- Name: shots cpf_ndl_co2_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ndl_co2_ipmax_fkey FOREIGN KEY (cpf_ndl_co2_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3289 (class 2606 OID 29419)
-- Name: shots cpf_ndl_co2_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ndl_co2_max_fkey FOREIGN KEY (cpf_ndl_co2_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3290 (class 2606 OID 29424)
-- Name: shots cpf_ndl_co2_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ndl_co2_truby_fkey FOREIGN KEY (cpf_ndl_co2_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3291 (class 2606 OID 29429)
-- Name: shots cpf_ne0_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ne0_ipmax_fkey FOREIGN KEY (cpf_ne0_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3292 (class 2606 OID 29434)
-- Name: shots cpf_ne0_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ne0_max_fkey FOREIGN KEY (cpf_ne0_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3293 (class 2606 OID 29439)
-- Name: shots cpf_ne0_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ne0_truby_fkey FOREIGN KEY (cpf_ne0_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3294 (class 2606 OID 29444)
-- Name: shots cpf_ne0ratio_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ne0ratio_ipmax_fkey FOREIGN KEY (cpf_ne0ratio_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3295 (class 2606 OID 29449)
-- Name: shots cpf_ne0ruby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ne0ruby_fkey FOREIGN KEY (cpf_ne0ruby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3296 (class 2606 OID 29454)
-- Name: shots cpf_ne_bar_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ne_bar_ipmax_fkey FOREIGN KEY (cpf_ne_bar_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3297 (class 2606 OID 29459)
-- Name: shots cpf_ne_yag_bar_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ne_yag_bar_ipmax_fkey FOREIGN KEY (cpf_ne_yag_bar_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3298 (class 2606 OID 29464)
-- Name: shots cpf_ngreenwald_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ngreenwald_ipmax_fkey FOREIGN KEY (cpf_ngreenwald_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3299 (class 2606 OID 29469)
-- Name: shots cpf_ngreenwaldratio_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ngreenwaldratio_ipmax_fkey FOREIGN KEY (cpf_ngreenwaldratio_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3300 (class 2606 OID 29474)
-- Name: shots cpf_o2ratio_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_o2ratio_fkey FOREIGN KEY (cpf_o2ratio_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3301 (class 2606 OID 29479)
-- Name: shots cpf_objective_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_objective_fkey FOREIGN KEY (cpf_objective_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3302 (class 2606 OID 28669)
-- Name: shots cpf_p03249_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p03249_fkey FOREIGN KEY (cpf_p03249_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3303 (class 2606 OID 28674)
-- Name: shots cpf_p04673_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p04673_fkey FOREIGN KEY (cpf_p04673_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3304 (class 2606 OID 28679)
-- Name: shots cpf_p04674_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p04674_fkey FOREIGN KEY (cpf_p04674_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3305 (class 2606 OID 28684)
-- Name: shots cpf_p04675_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p04675_fkey FOREIGN KEY (cpf_p04675_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3306 (class 2606 OID 28689)
-- Name: shots cpf_p04676_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p04676_fkey FOREIGN KEY (cpf_p04676_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3307 (class 2606 OID 28694)
-- Name: shots cpf_p04677_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p04677_fkey FOREIGN KEY (cpf_p04677_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3308 (class 2606 OID 28699)
-- Name: shots cpf_p04678_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p04678_fkey FOREIGN KEY (cpf_p04678_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3309 (class 2606 OID 28704)
-- Name: shots cpf_p04679_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p04679_fkey FOREIGN KEY (cpf_p04679_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3310 (class 2606 OID 28709)
-- Name: shots cpf_p04680_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p04680_fkey FOREIGN KEY (cpf_p04680_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3311 (class 2606 OID 28714)
-- Name: shots cpf_p04681_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p04681_fkey FOREIGN KEY (cpf_p04681_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3312 (class 2606 OID 28719)
-- Name: shots cpf_p04833_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p04833_fkey FOREIGN KEY (cpf_p04833_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3313 (class 2606 OID 28724)
-- Name: shots cpf_p04993_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p04993_fkey FOREIGN KEY (cpf_p04993_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3314 (class 2606 OID 28729)
-- Name: shots cpf_p05007_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05007_fkey FOREIGN KEY (cpf_p05007_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3315 (class 2606 OID 28734)
-- Name: shots cpf_p05008_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05008_fkey FOREIGN KEY (cpf_p05008_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3316 (class 2606 OID 28739)
-- Name: shots cpf_p05009_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05009_fkey FOREIGN KEY (cpf_p05009_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3317 (class 2606 OID 28744)
-- Name: shots cpf_p05010_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05010_fkey FOREIGN KEY (cpf_p05010_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3318 (class 2606 OID 28749)
-- Name: shots cpf_p05011_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05011_fkey FOREIGN KEY (cpf_p05011_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3319 (class 2606 OID 28754)
-- Name: shots cpf_p05015_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05015_fkey FOREIGN KEY (cpf_p05015_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3320 (class 2606 OID 28759)
-- Name: shots cpf_p05016_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05016_fkey FOREIGN KEY (cpf_p05016_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3321 (class 2606 OID 28764)
-- Name: shots cpf_p05017_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05017_fkey FOREIGN KEY (cpf_p05017_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3322 (class 2606 OID 28769)
-- Name: shots cpf_p05025_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05025_fkey FOREIGN KEY (cpf_p05025_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3323 (class 2606 OID 28774)
-- Name: shots cpf_p05027_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05027_fkey FOREIGN KEY (cpf_p05027_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3324 (class 2606 OID 28779)
-- Name: shots cpf_p05028_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05028_fkey FOREIGN KEY (cpf_p05028_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3325 (class 2606 OID 28784)
-- Name: shots cpf_p05029_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05029_fkey FOREIGN KEY (cpf_p05029_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3326 (class 2606 OID 28789)
-- Name: shots cpf_p05030_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05030_fkey FOREIGN KEY (cpf_p05030_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3327 (class 2606 OID 28794)
-- Name: shots cpf_p05032_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05032_fkey FOREIGN KEY (cpf_p05032_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3328 (class 2606 OID 28799)
-- Name: shots cpf_p05033_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05033_fkey FOREIGN KEY (cpf_p05033_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3329 (class 2606 OID 28804)
-- Name: shots cpf_p05153_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p05153_fkey FOREIGN KEY (cpf_p05153_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3330 (class 2606 OID 28809)
-- Name: shots cpf_p06000_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p06000_fkey FOREIGN KEY (cpf_p06000_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3331 (class 2606 OID 28814)
-- Name: shots cpf_p06001_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p06001_fkey FOREIGN KEY (cpf_p06001_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3332 (class 2606 OID 28819)
-- Name: shots cpf_p06002_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p06002_fkey FOREIGN KEY (cpf_p06002_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3333 (class 2606 OID 28824)
-- Name: shots cpf_p06003_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p06003_fkey FOREIGN KEY (cpf_p06003_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3334 (class 2606 OID 28829)
-- Name: shots cpf_p06004_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p06004_fkey FOREIGN KEY (cpf_p06004_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3335 (class 2606 OID 28834)
-- Name: shots cpf_p10963_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p10963_fkey FOREIGN KEY (cpf_p10963_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3336 (class 2606 OID 28839)
-- Name: shots cpf_p10964_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p10964_fkey FOREIGN KEY (cpf_p10964_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3337 (class 2606 OID 28844)
-- Name: shots cpf_p12441_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p12441_fkey FOREIGN KEY (cpf_p12441_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3338 (class 2606 OID 28849)
-- Name: shots cpf_p12450_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p12450_fkey FOREIGN KEY (cpf_p12450_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3339 (class 2606 OID 28854)
-- Name: shots cpf_p12451_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p12451_fkey FOREIGN KEY (cpf_p12451_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3340 (class 2606 OID 28859)
-- Name: shots cpf_p12452_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p12452_fkey FOREIGN KEY (cpf_p12452_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3341 (class 2606 OID 28864)
-- Name: shots cpf_p15202_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p15202_fkey FOREIGN KEY (cpf_p15202_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3342 (class 2606 OID 28869)
-- Name: shots cpf_p15203_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p15203_fkey FOREIGN KEY (cpf_p15203_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3343 (class 2606 OID 28874)
-- Name: shots cpf_p15209_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p15209_fkey FOREIGN KEY (cpf_p15209_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3344 (class 2606 OID 28879)
-- Name: shots cpf_p15659_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p15659_fkey FOREIGN KEY (cpf_p15659_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3345 (class 2606 OID 28884)
-- Name: shots cpf_p15660_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p15660_fkey FOREIGN KEY (cpf_p15660_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3346 (class 2606 OID 28889)
-- Name: shots cpf_p15661_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p15661_fkey FOREIGN KEY (cpf_p15661_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3347 (class 2606 OID 28894)
-- Name: shots cpf_p20000_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p20000_fkey FOREIGN KEY (cpf_p20000_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3348 (class 2606 OID 28899)
-- Name: shots cpf_p20204_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p20204_fkey FOREIGN KEY (cpf_p20204_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3349 (class 2606 OID 28904)
-- Name: shots cpf_p20205_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p20205_fkey FOREIGN KEY (cpf_p20205_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3350 (class 2606 OID 28909)
-- Name: shots cpf_p20206_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p20206_fkey FOREIGN KEY (cpf_p20206_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3351 (class 2606 OID 28914)
-- Name: shots cpf_p20207_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p20207_fkey FOREIGN KEY (cpf_p20207_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3352 (class 2606 OID 28919)
-- Name: shots cpf_p20208_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p20208_fkey FOREIGN KEY (cpf_p20208_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3353 (class 2606 OID 28924)
-- Name: shots cpf_p21010_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21010_fkey FOREIGN KEY (cpf_p21010_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3354 (class 2606 OID 28929)
-- Name: shots cpf_p21011_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21011_fkey FOREIGN KEY (cpf_p21011_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3355 (class 2606 OID 28934)
-- Name: shots cpf_p21012_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21012_fkey FOREIGN KEY (cpf_p21012_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3356 (class 2606 OID 28939)
-- Name: shots cpf_p21021_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21021_fkey FOREIGN KEY (cpf_p21021_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3357 (class 2606 OID 28944)
-- Name: shots cpf_p21022_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21022_fkey FOREIGN KEY (cpf_p21022_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3358 (class 2606 OID 28949)
-- Name: shots cpf_p21029_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21029_fkey FOREIGN KEY (cpf_p21029_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3359 (class 2606 OID 28954)
-- Name: shots cpf_p21035_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21035_fkey FOREIGN KEY (cpf_p21035_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3360 (class 2606 OID 28959)
-- Name: shots cpf_p21037_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21037_fkey FOREIGN KEY (cpf_p21037_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3361 (class 2606 OID 28964)
-- Name: shots cpf_p21041_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21041_fkey FOREIGN KEY (cpf_p21041_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3362 (class 2606 OID 28969)
-- Name: shots cpf_p21042_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21042_fkey FOREIGN KEY (cpf_p21042_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3363 (class 2606 OID 28974)
-- Name: shots cpf_p21043_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21043_fkey FOREIGN KEY (cpf_p21043_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3364 (class 2606 OID 28979)
-- Name: shots cpf_p21044_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21044_fkey FOREIGN KEY (cpf_p21044_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3365 (class 2606 OID 28984)
-- Name: shots cpf_p21045_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21045_fkey FOREIGN KEY (cpf_p21045_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3366 (class 2606 OID 28989)
-- Name: shots cpf_p21046_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21046_fkey FOREIGN KEY (cpf_p21046_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3367 (class 2606 OID 28994)
-- Name: shots cpf_p21047_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21047_fkey FOREIGN KEY (cpf_p21047_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3368 (class 2606 OID 28999)
-- Name: shots cpf_p21048_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21048_fkey FOREIGN KEY (cpf_p21048_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3369 (class 2606 OID 29004)
-- Name: shots cpf_p21051_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21051_fkey FOREIGN KEY (cpf_p21051_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3370 (class 2606 OID 29009)
-- Name: shots cpf_p21052_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21052_fkey FOREIGN KEY (cpf_p21052_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3371 (class 2606 OID 29014)
-- Name: shots cpf_p21053_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21053_fkey FOREIGN KEY (cpf_p21053_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3372 (class 2606 OID 29019)
-- Name: shots cpf_p21054_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21054_fkey FOREIGN KEY (cpf_p21054_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3373 (class 2606 OID 29024)
-- Name: shots cpf_p21055_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21055_fkey FOREIGN KEY (cpf_p21055_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3374 (class 2606 OID 29029)
-- Name: shots cpf_p21056_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21056_fkey FOREIGN KEY (cpf_p21056_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3375 (class 2606 OID 29034)
-- Name: shots cpf_p21075_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21075_fkey FOREIGN KEY (cpf_p21075_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3376 (class 2606 OID 29039)
-- Name: shots cpf_p21076_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21076_fkey FOREIGN KEY (cpf_p21076_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3377 (class 2606 OID 29044)
-- Name: shots cpf_p21077_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21077_fkey FOREIGN KEY (cpf_p21077_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3378 (class 2606 OID 29049)
-- Name: shots cpf_p21078_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21078_fkey FOREIGN KEY (cpf_p21078_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3379 (class 2606 OID 29054)
-- Name: shots cpf_p21079_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21079_fkey FOREIGN KEY (cpf_p21079_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3380 (class 2606 OID 29059)
-- Name: shots cpf_p21080_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21080_fkey FOREIGN KEY (cpf_p21080_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3381 (class 2606 OID 29064)
-- Name: shots cpf_p21081_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21081_fkey FOREIGN KEY (cpf_p21081_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3382 (class 2606 OID 29069)
-- Name: shots cpf_p21082_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21082_fkey FOREIGN KEY (cpf_p21082_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3383 (class 2606 OID 29074)
-- Name: shots cpf_p21083_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21083_fkey FOREIGN KEY (cpf_p21083_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3384 (class 2606 OID 29079)
-- Name: shots cpf_p21084_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21084_fkey FOREIGN KEY (cpf_p21084_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3385 (class 2606 OID 29084)
-- Name: shots cpf_p21085_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21085_fkey FOREIGN KEY (cpf_p21085_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3386 (class 2606 OID 29089)
-- Name: shots cpf_p21086_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21086_fkey FOREIGN KEY (cpf_p21086_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3387 (class 2606 OID 29094)
-- Name: shots cpf_p21087_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21087_fkey FOREIGN KEY (cpf_p21087_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3388 (class 2606 OID 29099)
-- Name: shots cpf_p21088_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21088_fkey FOREIGN KEY (cpf_p21088_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3389 (class 2606 OID 29104)
-- Name: shots cpf_p21089_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21089_fkey FOREIGN KEY (cpf_p21089_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3390 (class 2606 OID 29109)
-- Name: shots cpf_p21092_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21092_fkey FOREIGN KEY (cpf_p21092_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3391 (class 2606 OID 29114)
-- Name: shots cpf_p21093_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_p21093_fkey FOREIGN KEY (cpf_p21093_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3392 (class 2606 OID 29484)
-- Name: shots cpf_pe0_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pe0_ipmax_fkey FOREIGN KEY (cpf_pe0_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3393 (class 2606 OID 29489)
-- Name: shots cpf_pe0_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pe0_max_fkey FOREIGN KEY (cpf_pe0_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3394 (class 2606 OID 29494)
-- Name: shots cpf_pe0_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pe0_truby_fkey FOREIGN KEY (cpf_pe0_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3395 (class 2606 OID 29499)
-- Name: shots cpf_pe0ruby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pe0ruby_fkey FOREIGN KEY (cpf_pe0ruby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3396 (class 2606 OID 29504)
-- Name: shots cpf_pic_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pic_fkey FOREIGN KEY (cpf_pic_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3397 (class 2606 OID 29509)
-- Name: shots cpf_pnbi_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pnbi_ipmax_fkey FOREIGN KEY (cpf_pnbi_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3398 (class 2606 OID 29514)
-- Name: shots cpf_pnbi_ipmax_ss_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pnbi_ipmax_ss_fkey FOREIGN KEY (cpf_pnbi_ipmax_ss_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3399 (class 2606 OID 29519)
-- Name: shots cpf_pnbi_ipmax_sw_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pnbi_ipmax_sw_fkey FOREIGN KEY (cpf_pnbi_ipmax_sw_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3400 (class 2606 OID 29524)
-- Name: shots cpf_pnbi_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pnbi_max_fkey FOREIGN KEY (cpf_pnbi_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3401 (class 2606 OID 29529)
-- Name: shots cpf_pnbi_max_ss_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pnbi_max_ss_fkey FOREIGN KEY (cpf_pnbi_max_ss_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3402 (class 2606 OID 29534)
-- Name: shots cpf_pnbi_max_sw_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pnbi_max_sw_fkey FOREIGN KEY (cpf_pnbi_max_sw_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3403 (class 2606 OID 29539)
-- Name: shots cpf_pnbi_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pnbi_truby_fkey FOREIGN KEY (cpf_pnbi_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3404 (class 2606 OID 29544)
-- Name: shots cpf_pnbi_truby_ss_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pnbi_truby_ss_fkey FOREIGN KEY (cpf_pnbi_truby_ss_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3405 (class 2606 OID 29549)
-- Name: shots cpf_pnbi_truby_sw_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pnbi_truby_sw_fkey FOREIGN KEY (cpf_pnbi_truby_sw_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3406 (class 2606 OID 29554)
-- Name: shots cpf_pohm_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pohm_ipmax_fkey FOREIGN KEY (cpf_pohm_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3407 (class 2606 OID 29559)
-- Name: shots cpf_pohm_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pohm_max_fkey FOREIGN KEY (cpf_pohm_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3408 (class 2606 OID 29564)
-- Name: shots cpf_pohm_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pohm_truby_fkey FOREIGN KEY (cpf_pohm_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3409 (class 2606 OID 29569)
-- Name: shots cpf_postshot_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_postshot_fkey FOREIGN KEY (cpf_postshot_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3410 (class 2606 OID 29574)
-- Name: shots cpf_prad_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_prad_ipmax_fkey FOREIGN KEY (cpf_prad_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3411 (class 2606 OID 29579)
-- Name: shots cpf_prad_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_prad_max_fkey FOREIGN KEY (cpf_prad_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3412 (class 2606 OID 29584)
-- Name: shots cpf_prad_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_prad_truby_fkey FOREIGN KEY (cpf_prad_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3413 (class 2606 OID 29589)
-- Name: shots cpf_pradne2_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pradne2_fkey FOREIGN KEY (cpf_pradne2_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3414 (class 2606 OID 29594)
-- Name: shots cpf_preshot_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_preshot_fkey FOREIGN KEY (cpf_preshot_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3415 (class 2606 OID 29599)
-- Name: shots cpf_program_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_program_fkey FOREIGN KEY (cpf_program_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3416 (class 2606 OID 29604)
-- Name: shots cpf_pulno_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_pulno_fkey FOREIGN KEY (cpf_pulno_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3417 (class 2606 OID 29609)
-- Name: shots cpf_q95_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_q95_ipmax_fkey FOREIGN KEY (cpf_q95_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3418 (class 2606 OID 29614)
-- Name: shots cpf_q95_min_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_q95_min_fkey FOREIGN KEY (cpf_q95_min_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3419 (class 2606 OID 29619)
-- Name: shots cpf_q95_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_q95_truby_fkey FOREIGN KEY (cpf_q95_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3420 (class 2606 OID 29624)
-- Name: shots cpf_reference_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_reference_fkey FOREIGN KEY (cpf_reference_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3421 (class 2606 OID 29629)
-- Name: shots cpf_rgeo_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_rgeo_ipmax_fkey FOREIGN KEY (cpf_rgeo_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3422 (class 2606 OID 29634)
-- Name: shots cpf_rgeo_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_rgeo_max_fkey FOREIGN KEY (cpf_rgeo_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3423 (class 2606 OID 29639)
-- Name: shots cpf_rgeo_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_rgeo_truby_fkey FOREIGN KEY (cpf_rgeo_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3424 (class 2606 OID 29644)
-- Name: shots cpf_rinner_da_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_rinner_da_fkey FOREIGN KEY (cpf_rinner_da_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3425 (class 2606 OID 29649)
-- Name: shots cpf_rinner_efit_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_rinner_efit_fkey FOREIGN KEY (cpf_rinner_efit_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3426 (class 2606 OID 29654)
-- Name: shots cpf_rmag_efit_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_rmag_efit_fkey FOREIGN KEY (cpf_rmag_efit_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3427 (class 2606 OID 29659)
-- Name: shots cpf_router_da_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_router_da_fkey FOREIGN KEY (cpf_router_da_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3428 (class 2606 OID 29664)
-- Name: shots cpf_router_efit_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_router_efit_fkey FOREIGN KEY (cpf_router_efit_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3429 (class 2606 OID 29669)
-- Name: shots cpf_sarea_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_sarea_ipmax_fkey FOREIGN KEY (cpf_sarea_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3430 (class 2606 OID 29674)
-- Name: shots cpf_sarea_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_sarea_max_fkey FOREIGN KEY (cpf_sarea_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3431 (class 2606 OID 29679)
-- Name: shots cpf_sarea_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_sarea_truby_fkey FOREIGN KEY (cpf_sarea_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3432 (class 2606 OID 29684)
-- Name: shots cpf_sl_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_sl_fkey FOREIGN KEY (cpf_sl_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3433 (class 2606 OID 29689)
-- Name: shots cpf_summary_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_summary_fkey FOREIGN KEY (cpf_summary_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3434 (class 2606 OID 29694)
-- Name: shots cpf_tamin_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tamin_max_fkey FOREIGN KEY (cpf_tamin_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3435 (class 2606 OID 29699)
-- Name: shots cpf_tarea_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tarea_max_fkey FOREIGN KEY (cpf_tarea_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3436 (class 2606 OID 29704)
-- Name: shots cpf_tautot_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tautot_ipmax_fkey FOREIGN KEY (cpf_tautot_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3437 (class 2606 OID 29709)
-- Name: shots cpf_tautot_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tautot_max_fkey FOREIGN KEY (cpf_tautot_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3438 (class 2606 OID 29714)
-- Name: shots cpf_tautot_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tautot_truby_fkey FOREIGN KEY (cpf_tautot_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3439 (class 2606 OID 29719)
-- Name: shots cpf_tbepmhd_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tbepmhd_max_fkey FOREIGN KEY (cpf_tbepmhd_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3440 (class 2606 OID 29724)
-- Name: shots cpf_tbetmhd_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tbetmhd_max_fkey FOREIGN KEY (cpf_tbetmhd_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3441 (class 2606 OID 29729)
-- Name: shots cpf_tbt_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tbt_max_fkey FOREIGN KEY (cpf_tbt_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3442 (class 2606 OID 29734)
-- Name: shots cpf_tdwmhd_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tdwmhd_max_fkey FOREIGN KEY (cpf_tdwmhd_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3443 (class 2606 OID 29739)
-- Name: shots cpf_te0_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_te0_ipmax_fkey FOREIGN KEY (cpf_te0_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3444 (class 2606 OID 29744)
-- Name: shots cpf_te0_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_te0_max_fkey FOREIGN KEY (cpf_te0_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3445 (class 2606 OID 29749)
-- Name: shots cpf_te0_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_te0_truby_fkey FOREIGN KEY (cpf_te0_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3446 (class 2606 OID 29754)
-- Name: shots cpf_te0ratio_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_te0ratio_ipmax_fkey FOREIGN KEY (cpf_te0ratio_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3447 (class 2606 OID 29759)
-- Name: shots cpf_te0ruby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_te0ruby_fkey FOREIGN KEY (cpf_te0ruby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3448 (class 2606 OID 29764)
-- Name: shots cpf_te_yag_bar_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_te_yag_bar_ipmax_fkey FOREIGN KEY (cpf_te_yag_bar_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3449 (class 2606 OID 29769)
-- Name: shots cpf_tend_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tend_fkey FOREIGN KEY (cpf_tend_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3450 (class 2606 OID 29774)
-- Name: shots cpf_tend_ibgas_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tend_ibgas_fkey FOREIGN KEY (cpf_tend_ibgas_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3451 (class 2606 OID 29779)
-- Name: shots cpf_tend_nbi_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tend_nbi_fkey FOREIGN KEY (cpf_tend_nbi_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3452 (class 2606 OID 29784)
-- Name: shots cpf_tend_nbi_ss_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tend_nbi_ss_fkey FOREIGN KEY (cpf_tend_nbi_ss_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3453 (class 2606 OID 29789)
-- Name: shots cpf_tend_nbi_sw_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tend_nbi_sw_fkey FOREIGN KEY (cpf_tend_nbi_sw_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3454 (class 2606 OID 29794)
-- Name: shots cpf_term_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_term_code_fkey FOREIGN KEY (cpf_term_code_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3455 (class 2606 OID 29799)
-- Name: shots cpf_tftend_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tftend_fkey FOREIGN KEY (cpf_tftend_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3456 (class 2606 OID 29804)
-- Name: shots cpf_tftstart_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tftstart_fkey FOREIGN KEY (cpf_tftstart_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3457 (class 2606 OID 29809)
-- Name: shots cpf_tipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tipmax_fkey FOREIGN KEY (cpf_tipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3458 (class 2606 OID 29814)
-- Name: shots cpf_tkappa_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tkappa_max_fkey FOREIGN KEY (cpf_tkappa_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3459 (class 2606 OID 29819)
-- Name: shots cpf_tli_2_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tli_2_max_fkey FOREIGN KEY (cpf_tli_2_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3460 (class 2606 OID 29824)
-- Name: shots cpf_tli_3_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tli_3_max_fkey FOREIGN KEY (cpf_tli_3_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3461 (class 2606 OID 29829)
-- Name: shots cpf_tndl_co2_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tndl_co2_max_fkey FOREIGN KEY (cpf_tndl_co2_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3462 (class 2606 OID 29834)
-- Name: shots cpf_tne0_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tne0_max_fkey FOREIGN KEY (cpf_tne0_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3463 (class 2606 OID 29839)
-- Name: shots cpf_tpe0_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tpe0_max_fkey FOREIGN KEY (cpf_tpe0_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3464 (class 2606 OID 29844)
-- Name: shots cpf_tpnbi_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tpnbi_max_fkey FOREIGN KEY (cpf_tpnbi_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3465 (class 2606 OID 29849)
-- Name: shots cpf_tpnbi_max_ss_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tpnbi_max_ss_fkey FOREIGN KEY (cpf_tpnbi_max_ss_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3466 (class 2606 OID 29854)
-- Name: shots cpf_tpnbi_max_sw_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tpnbi_max_sw_fkey FOREIGN KEY (cpf_tpnbi_max_sw_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3467 (class 2606 OID 29859)
-- Name: shots cpf_tpohm_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tpohm_max_fkey FOREIGN KEY (cpf_tpohm_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3468 (class 2606 OID 29864)
-- Name: shots cpf_tprad_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tprad_max_fkey FOREIGN KEY (cpf_tprad_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3469 (class 2606 OID 29869)
-- Name: shots cpf_tq95_min_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tq95_min_fkey FOREIGN KEY (cpf_tq95_min_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3470 (class 2606 OID 29874)
-- Name: shots cpf_trgeo_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_trgeo_max_fkey FOREIGN KEY (cpf_trgeo_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3471 (class 2606 OID 29879)
-- Name: shots cpf_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_truby_fkey FOREIGN KEY (cpf_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3472 (class 2606 OID 29884)
-- Name: shots cpf_tsarea_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tsarea_max_fkey FOREIGN KEY (cpf_tsarea_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3473 (class 2606 OID 29889)
-- Name: shots cpf_tstart_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tstart_fkey FOREIGN KEY (cpf_tstart_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3474 (class 2606 OID 29894)
-- Name: shots cpf_tstart_ibgas_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tstart_ibgas_fkey FOREIGN KEY (cpf_tstart_ibgas_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3475 (class 2606 OID 29899)
-- Name: shots cpf_tstart_nbi_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tstart_nbi_fkey FOREIGN KEY (cpf_tstart_nbi_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3476 (class 2606 OID 29904)
-- Name: shots cpf_tstart_nbi_ss_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tstart_nbi_ss_fkey FOREIGN KEY (cpf_tstart_nbi_ss_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3477 (class 2606 OID 29909)
-- Name: shots cpf_tstart_nbi_sw_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tstart_nbi_sw_fkey FOREIGN KEY (cpf_tstart_nbi_sw_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3478 (class 2606 OID 29914)
-- Name: shots cpf_ttautot_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_ttautot_max_fkey FOREIGN KEY (cpf_ttautot_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3479 (class 2606 OID 29919)
-- Name: shots cpf_tte0_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tte0_max_fkey FOREIGN KEY (cpf_tte0_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3480 (class 2606 OID 29924)
-- Name: shots cpf_tvol_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tvol_max_fkey FOREIGN KEY (cpf_tvol_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3481 (class 2606 OID 29929)
-- Name: shots cpf_twmhd_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_twmhd_max_fkey FOREIGN KEY (cpf_twmhd_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3482 (class 2606 OID 29934)
-- Name: shots cpf_tzeff_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_tzeff_max_fkey FOREIGN KEY (cpf_tzeff_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3483 (class 2606 OID 29939)
-- Name: shots cpf_useful_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_useful_fkey FOREIGN KEY (cpf_useful_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3484 (class 2606 OID 29944)
-- Name: shots cpf_vol_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_vol_ipmax_fkey FOREIGN KEY (cpf_vol_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3485 (class 2606 OID 29949)
-- Name: shots cpf_vol_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_vol_max_fkey FOREIGN KEY (cpf_vol_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3486 (class 2606 OID 29954)
-- Name: shots cpf_vol_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_vol_truby_fkey FOREIGN KEY (cpf_vol_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3487 (class 2606 OID 29959)
-- Name: shots cpf_wmhd_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_wmhd_ipmax_fkey FOREIGN KEY (cpf_wmhd_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3488 (class 2606 OID 29964)
-- Name: shots cpf_wmhd_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_wmhd_max_fkey FOREIGN KEY (cpf_wmhd_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3489 (class 2606 OID 29969)
-- Name: shots cpf_wmhd_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_wmhd_truby_fkey FOREIGN KEY (cpf_wmhd_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3490 (class 2606 OID 29974)
-- Name: shots cpf_zeff_ipmax_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_zeff_ipmax_fkey FOREIGN KEY (cpf_zeff_ipmax_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3491 (class 2606 OID 29979)
-- Name: shots cpf_zeff_max_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_zeff_max_fkey FOREIGN KEY (cpf_zeff_max_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3492 (class 2606 OID 29984)
-- Name: shots cpf_zeff_truby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_zeff_truby_fkey FOREIGN KEY (cpf_zeff_truby_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3493 (class 2606 OID 29989)
-- Name: shots cpf_zmag_efit_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT cpf_zmag_efit_fkey FOREIGN KEY (cpf_zmag_efit_summary) REFERENCES public.cpf_summary(id) NOT VALID;


--
-- TOC entry 3494 (class 2606 OID 28654)
-- Name: shots scenario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shots
    ADD CONSTRAINT scenario_fkey FOREIGN KEY (scenario) REFERENCES public.scenarios(id) NOT VALID;


--
-- TOC entry 3227 (class 2606 OID 28659)
-- Name: shot_signal_link shot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shot_signal_link
    ADD CONSTRAINT shot_id_fkey FOREIGN KEY (shot_id) REFERENCES public.shots(shot_id) NOT VALID;


--
-- TOC entry 3228 (class 2606 OID 28664)
-- Name: shot_signal_link signal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.shot_signal_link
    ADD CONSTRAINT signal_id_fkey FOREIGN KEY (signal_id) REFERENCES public.signals(signal_id) NOT VALID;


-- Completed on 2023-03-20 15:21:26 UTC

--
-- PostgreSQL database dump complete
--

