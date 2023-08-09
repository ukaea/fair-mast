from typing import Optional
import enum
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Time,
    SmallInteger,
    REAL,
    Enum,
)
from sqlalchemy.orm import relationship
import datetime

from .types import CurrentRange, DivertorConfig, PlasmaShape, Comissioner, Facility
from .database import Base
from sqlmodel import Field, SQLModel


class ShotModel(SQLModel, table=True):
    __tablename__ = "shots"

    shot_id: int = Field(primary_key=True, index=True, nullable=False)
    timestamp: datetime.datetime = Field()
    reference_shot: Optional[int] = Field(nullable=True)
    scenario: Optional[int] = Field(nullable=True)

    # current_range = Column(
    #     Enum(CurrentRange, values_callable=lambda obj: [e.value for e in obj])
    # )
    # heating = Column(String)
    # divertor_config = Column(
    #     Enum(DivertorConfig, values_callable=lambda obj: [e.value for e in obj])
    # )
    # pellets = Column(Boolean)
    # plasma_shape = Column(
    #     Enum(PlasmaShape, values_callable=lambda obj: [e.value for e in obj])
    # )
    # rmp_coil = Column(Boolean)
    # preshot_description = Column(String)
    # postshot_description = Column(String)
    # comissioner = Column(
    #     Enum(Comissioner, values_callable=lambda obj: [e.value for e in obj])
    # )
    # campaign = Column(String)
    # facility = Column(
    #     Enum(Facility, values_callable=lambda obj: [e.value for e in obj])
    # )


#     cpf_p03249 = Column(REAL)

#     cpf_p04673 = Column(REAL)

#     cpf_p04674 = Column(REAL)

#     cpf_p04675 = Column(REAL)

#     cpf_p04676 = Column(REAL)

#     cpf_p04677 = Column(REAL)

#     cpf_p04678 = Column(REAL)

#     cpf_p04679 = Column(REAL)

#     cpf_p04680 = Column(REAL)

#     cpf_p04681 = Column(REAL)

#     cpf_p04833 = Column(REAL)

#     cpf_p04993 = Column(REAL)

#     cpf_p05007 = Column(REAL)

#     cpf_p05008 = Column(REAL)

#     cpf_p05009 = Column(REAL)

#     cpf_p05010 = Column(REAL)

#     cpf_p05011 = Column(REAL)

#     cpf_p05015 = Column(REAL)

#     cpf_p05016 = Column(REAL)

#     cpf_p05017 = Column(REAL)

#     cpf_p05025 = Column(REAL)

#     cpf_p05027 = Column(REAL)

#     cpf_p05028 = Column(REAL)

#     cpf_p05029 = Column(REAL)

#     cpf_p05030 = Column(REAL)

#     cpf_p05032 = Column(REAL)

#     cpf_p05033 = Column(REAL)

#     cpf_p05153 = Column(REAL)

#     cpf_p06000 = Column(REAL)

#     cpf_p06001 = Column(REAL)

#     cpf_p06002 = Column(REAL)

#     cpf_p06003 = Column(REAL)

#     cpf_p06004 = Column(REAL)

#     cpf_p10963 = Column(REAL)

#     cpf_p10964 = Column(REAL)

#     cpf_p12441 = Column(REAL)

#     cpf_p12450 = Column(REAL)

#     cpf_p12451 = Column(REAL)

#     cpf_p12452 = Column(REAL)

#     cpf_p15202 = Column(REAL)

#     cpf_p15203 = Column(REAL)

#     cpf_p15209 = Column(REAL)

#     cpf_p15659 = Column(REAL)

#     cpf_p15660 = Column(REAL)

#     cpf_p15661 = Column(REAL)

#     cpf_p20000 = Column(REAL)

#     cpf_p20204 = Column(REAL)

#     cpf_p20205 = Column(REAL)

#     cpf_p20206 = Column(REAL)

#     cpf_p20207 = Column(REAL)

#     cpf_p20208 = Column(REAL)

#     cpf_p21010 = Column(REAL)

#     cpf_p21011 = Column(REAL)

#     cpf_p21012 = Column(REAL)

#     cpf_p21021 = Column(REAL)

#     cpf_p21022 = Column(REAL)

#     cpf_p21029 = Column(REAL)

#     cpf_p21035 = Column(REAL)

#     cpf_p21037 = Column(REAL)

#     cpf_p21041 = Column(REAL)

#     cpf_p21042 = Column(REAL)

#     cpf_p21043 = Column(REAL)

#     cpf_p21044 = Column(REAL)

#     cpf_p21045 = Column(REAL)

#     cpf_p21046 = Column(REAL)

#     cpf_p21047 = Column(REAL)

#     cpf_p21048 = Column(REAL)

#     cpf_p21051 = Column(REAL)

#     cpf_p21052 = Column(REAL)

#     cpf_p21053 = Column(REAL)

#     cpf_p21054 = Column(REAL)

#     cpf_p21055 = Column(REAL)

#     cpf_p21056 = Column(REAL)

#     cpf_p21075 = Column(REAL)

#     cpf_p21076 = Column(REAL)

#     cpf_p21077 = Column(REAL)

#     cpf_p21078 = Column(REAL)

#     cpf_p21079 = Column(REAL)

#     cpf_p21080 = Column(REAL)

#     cpf_p21081 = Column(REAL)

#     cpf_p21082 = Column(REAL)

#     cpf_p21083 = Column(REAL)

#     cpf_p21084 = Column(REAL)

#     cpf_p21085 = Column(REAL)

#     cpf_p21086 = Column(REAL)

#     cpf_p21087 = Column(REAL)

#     cpf_p21088 = Column(REAL)

#     cpf_p21089 = Column(REAL)

#     cpf_p21092 = Column(REAL)

#     cpf_p21093 = Column(REAL)

#     cpf_abort = Column(REAL)

#     cpf_amin_ipmax = Column(REAL)

#     cpf_amin_max = Column(REAL)

#     cpf_amin_truby = Column(REAL)

#     cpf_area_ipmax = Column(REAL)

#     cpf_area_max = Column(REAL)

#     cpf_area_truby = Column(REAL)

#     cpf_bepmhd_ipmax = Column(REAL)

#     cpf_bepmhd_max = Column(REAL)

#     cpf_bepmhd_truby = Column(REAL)

#     cpf_betmhd_ipmax = Column(REAL)

#     cpf_betmhd_max = Column(REAL)

#     cpf_betmhd_truby = Column(REAL)

#     cpf_bt_ipmax = Column(REAL)

#     cpf_bt_max = Column(REAL)

#     cpf_bt_truby = Column(REAL)

#     cpf_c2ratio = Column(REAL)

#     cpf_column_temp_in = Column(REAL)

#     cpf_column_temp_out = Column(REAL)

#     cpf_creation = Column(DateTime)

#     cpf_dwmhd_ipmax = Column(REAL)

#     cpf_dwmhd_max = Column(REAL)

#     cpf_dwmhd_truby = Column(REAL)

#     cpf_enbi_max_ss = Column(REAL)

#     cpf_enbi_max_sw = Column(REAL)

#     cpf_exp_date = Column(DateTime)

#     cpf_exp_number = Column(Integer)

#     cpf_exp_time = Column(Time)

#     cpf_gdc_duration = Column(REAL)

#     cpf_gdc_time = Column(REAL)

#     cpf_ibgas_pressure = Column(REAL)

#     cpf_ip_av = Column(REAL)

#     cpf_ip_max = Column(REAL)

#     cpf_jnbi_ipmax = Column(REAL)

#     cpf_jnbi_ipmax_ss = Column(REAL)

#     cpf_jnbi_ipmax_sw = Column(REAL)

#     cpf_jnbi_max = Column(REAL)

#     cpf_jnbi_max_ss = Column(REAL)

#     cpf_jnbi_max_sw = Column(REAL)

#     cpf_jnbi_total = Column(REAL)

#     cpf_jnbi_total_ss = Column(REAL)

#     cpf_jnbi_total_sw = Column(REAL)

#     cpf_jnbi_truby = Column(REAL)

#     cpf_jnbi_truby_ss = Column(REAL)

#     cpf_jnbi_truby_sw = Column(REAL)

#     cpf_johm_ipmax = Column(REAL)

#     cpf_johm_max = Column(REAL)

#     cpf_johm_total = Column(REAL)

#     cpf_johm_truby = Column(REAL)

#     cpf_kappa_ipmax = Column(REAL)

#     cpf_kappa_max = Column(REAL)

#     cpf_kappa_truby = Column(REAL)

#     cpf_li_2_ipmax = Column(REAL)

#     cpf_li_2_max = Column(REAL)

#     cpf_li_2_truby = Column(REAL)

#     cpf_li_3_ipmax = Column(REAL)

#     cpf_li_3_max = Column(REAL)

#     cpf_li_3_truby = Column(REAL)

#     cpf_log_base_pressure = Column(REAL)

#     cpf_ndl_co2_ipmax = Column(REAL)

#     cpf_ndl_co2_max = Column(REAL)

#     cpf_ndl_co2_truby = Column(REAL)

#     cpf_ne0_ipmax = Column(REAL)

#     cpf_ne0_max = Column(REAL)

#     cpf_ne0_truby = Column(REAL)

#     cpf_ne0ratio_ipmax = Column(REAL)

#     cpf_ne0ruby = Column(REAL)

#     cpf_ne_bar_ipmax = Column(REAL)

#     cpf_ne_yag_bar_ipmax = Column(REAL)

#     cpf_ngreenwald_ipmax = Column(REAL)

#     cpf_ngreenwaldratio_ipmax = Column(REAL)

#     cpf_o2ratio = Column(REAL)

#     cpf_objective = Column(String)

#     cpf_pe0_ipmax = Column(REAL)

#     cpf_pe0_max = Column(REAL)

#     cpf_pe0_truby = Column(REAL)

#     cpf_pe0ruby = Column(REAL)

#     cpf_pic = Column(String)

#     cpf_pnbi_ipmax = Column(REAL)

#     cpf_pnbi_ipmax_ss = Column(REAL)

#     cpf_pnbi_ipmax_sw = Column(REAL)

#     cpf_pnbi_max = Column(REAL)

#     cpf_pnbi_max_ss = Column(REAL)

#     cpf_pnbi_max_sw = Column(REAL)

#     cpf_pnbi_truby = Column(REAL)

#     cpf_pnbi_truby_ss = Column(REAL)

#     cpf_pnbi_truby_sw = Column(REAL)

#     cpf_pohm_ipmax = Column(REAL)

#     cpf_pohm_max = Column(REAL)

#     cpf_pohm_truby = Column(REAL)

#     cpf_postshot = Column(String)

#     cpf_prad_ipmax = Column(REAL)

#     cpf_prad_max = Column(REAL)

#     cpf_prad_truby = Column(REAL)

#     cpf_pradne2 = Column(REAL)

#     cpf_preshot = Column(String)

#     cpf_program = Column(String)

#     cpf_pulno = Column(REAL)

#     cpf_q95_ipmax = Column(REAL)

#     cpf_q95_min = Column(REAL)

#     cpf_q95_truby = Column(REAL)

#     cpf_reference = Column(REAL)

#     cpf_rgeo_ipmax = Column(REAL)

#     cpf_rgeo_max = Column(REAL)

#     cpf_rgeo_truby = Column(REAL)

#     cpf_rinner_da = Column(REAL)

#     cpf_rinner_efit = Column(REAL)

#     cpf_rmag_efit = Column(REAL)

#     cpf_router_da = Column(REAL)

#     cpf_router_efit = Column(REAL)

#     cpf_sarea_ipmax = Column(REAL)

#     cpf_sarea_max = Column(REAL)

#     cpf_sarea_truby = Column(REAL)

#     cpf_sl = Column(String)

#     cpf_summary = Column(String)

#     cpf_tamin_max = Column(REAL)

#     cpf_tarea_max = Column(REAL)

#     cpf_tautot_ipmax = Column(REAL)

#     cpf_tautot_max = Column(REAL)

#     cpf_tautot_truby = Column(REAL)

#     cpf_tbepmhd_max = Column(REAL)

#     cpf_tbetmhd_max = Column(REAL)

#     cpf_tbt_max = Column(REAL)

#     cpf_tdwmhd_max = Column(REAL)

#     cpf_te0_ipmax = Column(REAL)

#     cpf_te0_max = Column(REAL)

#     cpf_te0_truby = Column(REAL)

#     cpf_te0ratio_ipmax = Column(REAL)

#     cpf_te0ruby = Column(REAL)

#     cpf_te_yag_bar_ipmax = Column(REAL)

#     cpf_tend = Column(REAL)

#     cpf_tend_ibgas = Column(REAL)

#     cpf_tend_nbi = Column(REAL)

#     cpf_tend_nbi_ss = Column(REAL)

#     cpf_tend_nbi_sw = Column(REAL)

#     cpf_term_code = Column(REAL)

#     cpf_tftend = Column(REAL)

#     cpf_tftstart = Column(REAL)

#     cpf_tipmax = Column(REAL)

#     cpf_tkappa_max = Column(REAL)

#     cpf_tli_2_max = Column(REAL)

#     cpf_tli_3_max = Column(REAL)

#     cpf_tndl_co2_max = Column(REAL)

#     cpf_tne0_max = Column(REAL)

#     cpf_tpe0_max = Column(REAL)

#     cpf_tpnbi_max = Column(REAL)

#     cpf_tpnbi_max_ss = Column(REAL)

#     cpf_tpnbi_max_sw = Column(REAL)

#     cpf_tpohm_max = Column(REAL)

#     cpf_tprad_max = Column(REAL)

#     cpf_tq95_min = Column(REAL)

#     cpf_trgeo_max = Column(REAL)

#     cpf_truby = Column(REAL)

#     cpf_tsarea_max = Column(REAL)

#     cpf_tstart = Column(REAL)

#     cpf_tstart_ibgas = Column(REAL)

#     cpf_tstart_nbi = Column(REAL)

#     cpf_tstart_nbi_ss = Column(REAL)

#     cpf_tstart_nbi_sw = Column(REAL)

#     cpf_ttautot_max = Column(REAL)

#     cpf_tte0_max = Column(REAL)

#     cpf_tvol_max = Column(REAL)

#     cpf_twmhd_max = Column(REAL)

#     cpf_tzeff_max = Column(REAL)

#     cpf_useful = Column(REAL)

#     cpf_vol_ipmax = Column(REAL)

#     cpf_vol_max = Column(REAL)

#     cpf_vol_truby = Column(REAL)

#     cpf_wmhd_ipmax = Column(REAL)

#     cpf_wmhd_max = Column(REAL)

#     cpf_wmhd_truby = Column(REAL)

#     cpf_zeff_ipmax = Column(REAL)

#     cpf_zeff_max = Column(REAL)

#     cpf_zeff_truby = Column(REAL)

#     cpf_zmag_efit = Column(REAL)


# class ShotSignalLink(Base):
#     __tablename__ = "shot_signal_link"

#     id = Column(Integer, primary_key=True)
#     shot_id = Column(Integer)
#     signal_id = Column(Integer)
