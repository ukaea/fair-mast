from typing import Optional
from pydantic import BaseModel
import datetime
import strawberry

from .types import CurrentRange, DivertorConfig, PlasmaShape, Facility, Comissioner


class Shot(BaseModel):
    shot_id: int
    timestamp: datetime.datetime
    reference_shot: Optional[int]
    scenario: Optional[int]
    current_range: Optional[CurrentRange]
    heating: Optional[str]
    divertor_config: Optional[DivertorConfig]
    pellets: Optional[bool]
    plasma_shape: Optional[PlasmaShape]
    rmp_coil: Optional[bool]
    preshot_description: str
    postshot_description: str
    comissioner: Optional[Comissioner]
    campaign: str
    facility: Facility

    # CPF Variables from now on
    cpf_p03249: Optional[float]

    cpf_p04673: Optional[float]

    cpf_p04674: Optional[float]

    cpf_p04675: Optional[float]

    cpf_p04676: Optional[float]

    cpf_p04677: Optional[float]

    cpf_p04678: Optional[float]

    cpf_p04679: Optional[float]

    cpf_p04680: Optional[float]

    cpf_p04681: Optional[float]

    cpf_p04833: Optional[float]

    cpf_p04993: Optional[float]

    cpf_p05007: Optional[float]

    cpf_p05008: Optional[float]

    cpf_p05009: Optional[float]

    cpf_p05010: Optional[float]

    cpf_p05011: Optional[float]

    cpf_p05015: Optional[float]

    cpf_p05016: Optional[float]

    cpf_p05017: Optional[float]

    cpf_p05025: Optional[float]

    cpf_p05027: Optional[float]

    cpf_p05028: Optional[float]

    cpf_p05029: Optional[float]

    cpf_p05030: Optional[float]

    cpf_p05032: Optional[float]

    cpf_p05033: Optional[float]

    cpf_p05153: Optional[float]

    cpf_p06000: Optional[float]

    cpf_p06001: Optional[float]

    cpf_p06002: Optional[float]

    cpf_p06003: Optional[float]

    cpf_p06004: Optional[float]

    cpf_p10963: Optional[float]

    cpf_p10964: Optional[float]

    cpf_p12441: Optional[float]

    cpf_p12450: Optional[float]

    cpf_p12451: Optional[float]

    cpf_p12452: Optional[float]

    cpf_p15202: Optional[float]

    cpf_p15203: Optional[float]

    cpf_p15209: Optional[float]

    cpf_p15659: Optional[float]

    cpf_p15660: Optional[float]

    cpf_p15661: Optional[float]

    cpf_p20000: Optional[float]

    cpf_p20204: Optional[float]

    cpf_p20205: Optional[float]

    cpf_p20206: Optional[float]

    cpf_p20207: Optional[float]

    cpf_p20208: Optional[float]

    cpf_p21010: Optional[float]

    cpf_p21011: Optional[float]

    cpf_p21012: Optional[float]

    cpf_p21021: Optional[float]

    cpf_p21022: Optional[float]

    cpf_p21029: Optional[float]

    cpf_p21035: Optional[float]

    cpf_p21037: Optional[float]

    cpf_p21041: Optional[float]

    cpf_p21042: Optional[float]

    cpf_p21043: Optional[float]

    cpf_p21044: Optional[float]

    cpf_p21045: Optional[float]

    cpf_p21046: Optional[float]

    cpf_p21047: Optional[float]

    cpf_p21048: Optional[float]

    cpf_p21051: Optional[float]

    cpf_p21052: Optional[float]

    cpf_p21053: Optional[float]

    cpf_p21054: Optional[float]

    cpf_p21055: Optional[float]

    cpf_p21056: Optional[float]

    cpf_p21075: Optional[float]

    cpf_p21076: Optional[float]

    cpf_p21077: Optional[float]

    cpf_p21078: Optional[float]

    cpf_p21079: Optional[float]

    cpf_p21080: Optional[float]

    cpf_p21081: Optional[float]

    cpf_p21082: Optional[float]

    cpf_p21083: Optional[float]

    cpf_p21084: Optional[float]

    cpf_p21085: Optional[float]

    cpf_p21086: Optional[float]

    cpf_p21087: Optional[float]

    cpf_p21088: Optional[float]

    cpf_p21089: Optional[float]

    cpf_p21092: Optional[float]

    cpf_p21093: Optional[float]

    cpf_abort: Optional[float]

    cpf_amin_ipmax: Optional[float]

    cpf_amin_max: Optional[float]

    cpf_amin_truby: Optional[float]

    cpf_area_ipmax: Optional[float]

    cpf_area_max: Optional[float]

    cpf_area_truby: Optional[float]

    cpf_bepmhd_ipmax: Optional[float]

    cpf_bepmhd_max: Optional[float]

    cpf_bepmhd_truby: Optional[float]

    cpf_betmhd_ipmax: Optional[float]

    cpf_betmhd_max: Optional[float]

    cpf_betmhd_truby: Optional[float]

    cpf_bt_ipmax: Optional[float]

    cpf_bt_max: Optional[float]

    cpf_bt_truby: Optional[float]

    cpf_c2ratio: Optional[float]

    cpf_column_temp_in: Optional[float]

    cpf_column_temp_out: Optional[float]

    cpf_creation: Optional[datetime.datetime]

    cpf_dwmhd_ipmax: Optional[float]

    cpf_dwmhd_max: Optional[float]

    cpf_dwmhd_truby: Optional[float]

    cpf_enbi_max_ss: Optional[float]

    cpf_enbi_max_sw: Optional[float]

    cpf_exp_date: Optional[datetime.datetime]

    cpf_exp_number: Optional[int]

    cpf_exp_time: Optional[datetime.time]

    cpf_gdc_duration: Optional[float]

    cpf_gdc_time: Optional[float]

    cpf_ibgas_pressure: Optional[float]

    cpf_ip_av: Optional[float]

    cpf_ip_max: Optional[float]

    cpf_jnbi_ipmax: Optional[float]

    cpf_jnbi_ipmax_ss: Optional[float]

    cpf_jnbi_ipmax_sw: Optional[float]

    cpf_jnbi_max: Optional[float]

    cpf_jnbi_max_ss: Optional[float]

    cpf_jnbi_max_sw: Optional[float]

    cpf_jnbi_total: Optional[float]

    cpf_jnbi_total_ss: Optional[float]

    cpf_jnbi_total_sw: Optional[float]

    cpf_jnbi_truby: Optional[float]

    cpf_jnbi_truby_ss: Optional[float]

    cpf_jnbi_truby_sw: Optional[float]

    cpf_johm_ipmax: Optional[float]

    cpf_johm_max: Optional[float]

    cpf_johm_total: Optional[float]

    cpf_johm_truby: Optional[float]

    cpf_kappa_ipmax: Optional[float]

    cpf_kappa_max: Optional[float]

    cpf_kappa_truby: Optional[float]

    cpf_li_2_ipmax: Optional[float]

    cpf_li_2_max: Optional[float]

    cpf_li_2_truby: Optional[float]

    cpf_li_3_ipmax: Optional[float]

    cpf_li_3_max: Optional[float]

    cpf_li_3_truby: Optional[float]

    cpf_log_base_pressure: Optional[float]

    cpf_ndl_co2_ipmax: Optional[float]

    cpf_ndl_co2_max: Optional[float]

    cpf_ndl_co2_truby: Optional[float]

    cpf_ne0_ipmax: Optional[float]

    cpf_ne0_max: Optional[float]

    cpf_ne0_truby: Optional[float]

    cpf_ne0ratio_ipmax: Optional[float]

    cpf_ne0ruby: Optional[float]

    cpf_ne_bar_ipmax: Optional[float]

    cpf_ne_yag_bar_ipmax: Optional[float]

    cpf_ngreenwald_ipmax: Optional[float]

    cpf_ngreenwaldratio_ipmax: Optional[float]

    cpf_o2ratio: Optional[float]

    cpf_objective: Optional[str]

    cpf_pe0_ipmax: Optional[float]

    cpf_pe0_max: Optional[float]

    cpf_pe0_truby: Optional[float]

    cpf_pe0ruby: Optional[float]

    cpf_pic: Optional[str]

    cpf_pnbi_ipmax: Optional[float]

    cpf_pnbi_ipmax_ss: Optional[float]

    cpf_pnbi_ipmax_sw: Optional[float]

    cpf_pnbi_max: Optional[float]

    cpf_pnbi_max_ss: Optional[float]

    cpf_pnbi_max_sw: Optional[float]

    cpf_pnbi_truby: Optional[float]

    cpf_pnbi_truby_ss: Optional[float]

    cpf_pnbi_truby_sw: Optional[float]

    cpf_pohm_ipmax: Optional[float]

    cpf_pohm_max: Optional[float]

    cpf_pohm_truby: Optional[float]

    cpf_postshot: Optional[str]

    cpf_prad_ipmax: Optional[float]

    cpf_prad_max: Optional[float]

    cpf_prad_truby: Optional[float]

    cpf_pradne2: Optional[float]

    cpf_preshot: Optional[str]

    cpf_program: Optional[str]

    cpf_pulno: Optional[float]

    cpf_q95_ipmax: Optional[float]

    cpf_q95_min: Optional[float]

    cpf_q95_truby: Optional[float]

    cpf_reference: Optional[float]

    cpf_rgeo_ipmax: Optional[float]

    cpf_rgeo_max: Optional[float]

    cpf_rgeo_truby: Optional[float]

    cpf_rinner_da: Optional[float]

    cpf_rinner_efit: Optional[float]

    cpf_rmag_efit: Optional[float]

    cpf_router_da: Optional[float]

    cpf_router_efit: Optional[float]

    cpf_sarea_ipmax: Optional[float]

    cpf_sarea_max: Optional[float]

    cpf_sarea_truby: Optional[float]

    cpf_sl: Optional[str]

    cpf_summary: Optional[str]

    cpf_tamin_max: Optional[float]

    cpf_tarea_max: Optional[float]

    cpf_tautot_ipmax: Optional[float]

    cpf_tautot_max: Optional[float]

    cpf_tautot_truby: Optional[float]

    cpf_tbepmhd_max: Optional[float]

    cpf_tbetmhd_max: Optional[float]

    cpf_tbt_max: Optional[float]

    cpf_tdwmhd_max: Optional[float]

    cpf_te0_ipmax: Optional[float]

    cpf_te0_max: Optional[float]

    cpf_te0_truby: Optional[float]

    cpf_te0ratio_ipmax: Optional[float]

    cpf_te0ruby: Optional[float]

    cpf_te_yag_bar_ipmax: Optional[float]

    cpf_tend: Optional[float]

    cpf_tend_ibgas: Optional[float]

    cpf_tend_nbi: Optional[float]

    cpf_tend_nbi_ss: Optional[float]

    cpf_tend_nbi_sw: Optional[float]

    cpf_term_code: Optional[float]

    cpf_tftend: Optional[float]

    cpf_tftstart: Optional[float]

    cpf_tipmax: Optional[float]

    cpf_tkappa_max: Optional[float]

    cpf_tli_2_max: Optional[float]

    cpf_tli_3_max: Optional[float]

    cpf_tndl_co2_max: Optional[float]

    cpf_tne0_max: Optional[float]

    cpf_tpe0_max: Optional[float]

    cpf_tpnbi_max: Optional[float]

    cpf_tpnbi_max_ss: Optional[float]

    cpf_tpnbi_max_sw: Optional[float]

    cpf_tpohm_max: Optional[float]

    cpf_tprad_max: Optional[float]

    cpf_tq95_min: Optional[float]

    cpf_trgeo_max: Optional[float]

    cpf_truby: Optional[float]

    cpf_tsarea_max: Optional[float]

    cpf_tstart: Optional[float]

    cpf_tstart_ibgas: Optional[float]

    cpf_tstart_nbi: Optional[float]

    cpf_tstart_nbi_ss: Optional[float]

    cpf_tstart_nbi_sw: Optional[float]

    cpf_ttautot_max: Optional[float]

    cpf_tte0_max: Optional[float]

    cpf_tvol_max: Optional[float]

    cpf_twmhd_max: Optional[float]

    cpf_tzeff_max: Optional[float]

    cpf_useful: Optional[float]

    cpf_vol_ipmax: Optional[float]

    cpf_vol_max: Optional[float]

    cpf_vol_truby: Optional[float]

    cpf_wmhd_ipmax: Optional[float]

    cpf_wmhd_max: Optional[float]

    cpf_wmhd_truby: Optional[float]

    cpf_zeff_ipmax: Optional[float]

    cpf_zeff_max: Optional[float]

    cpf_zeff_truby: Optional[float]

    cpf_zmag_efit: Optional[float]

    class Config:
        orm_mode = True


class ShotSignalLink(BaseModel):
    shot_id: int
    signal_id: int

    class Config:
        orm_mode = True


@strawberry.experimental.pydantic.type(ShotModel, all_fields=True)
class Shot:
    pass


Query = create_query_root([Shot])

schema = strawberry.Schema(query=Query)
