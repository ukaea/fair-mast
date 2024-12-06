import datetime
import uuid as uuid_pkg
from typing import Dict, List, Optional

from sqlalchemy import (
    ARRAY,
    Column,
    Enum,
    Integer,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from .types import (
    Comissioner,
    CurrentRange,
    DivertorConfig,
    Facility,
    PlasmaShape,
    Quality,
    SignalType,
)


class SignalModel(SQLModel, table=True):
    __tablename__ = "signals"

    uuid: uuid_pkg.UUID = Field(
        primary_key=True,
        default=None,
        description="UUID for a specific signal data",
    )

    shot_id: int = Field(
        foreign_key="shots.shot_id",
        nullable=False,
        description="ID of the shot this signal was produced by.",
    )

    name: str = Field(
        description="Human readable name of this specific signal. A combination of the signal type and the shot number e.g. AMC_PLASMA_CURRENT"
    )

    version: int = Field(description="Version number of this dataset")

    rank: int = Field(description="Rank of the shape of this signal.")

    url: str = Field(description="The URL for the location of this signal.")

    source: str = Field(description="Name of the source this signal belongs to.")

    quality: Quality = Field(
        sa_column=Column(
            Enum(Quality, values_callable=lambda obj: [e.value for e in obj])
        ),
        description="Quality flag for this signal.",
    )

    shape: Optional[List[int]] = Field(
        sa_column=Column(ARRAY(Integer)),
        description="Shape of each dimension of this signal. e.g. [10, 100, 3]",
    )

    provenance: Optional[Dict] = Field(
        default={},
        sa_column=Column(JSONB),
        description="Information about the provenance graph that generated this signal in the PROV standard.",
    )

    units: Optional[str] = Field(
        description="The units of data contained within this dataset."
    )

    description: str = Field(
        sa_column=Column(Text), description="The description of the dataset."
    )

    signal_type: SignalType = Field(
        sa_column=Column(
            Enum(SignalType, values_callable=lambda obj: [e.value for e in obj])
        ),
        description="The type of the signal dataset. e.g. 'Raw', 'Analysed'",
    )

    dimensions: Optional[List[str]] = Field(
        sa_column=Column(ARRAY(Text)),
        description="The dimension names of the dataset, in order. e.g. ['time', 'radius']",
    )

    shot: "ShotModel" = Relationship(back_populates="signals")


class SourceModel(SQLModel, table=True):
    __tablename__ = "sources"

    uuid: uuid_pkg.UUID = Field(
        primary_key=True,
        default=None,
        description="UUID for a specific source data",
    )

    shot_id: int = Field(
        foreign_key="shots.shot_id",
        nullable=False,
        description="ID of the shot this signal was produced by.",
    )

    name: str = Field(
        nullable=False,
        description="Short name of the source.",
    )

    url: str = Field(description="The URL for the location of this source.")

    description: str = Field(
        sa_column=Column(Text), description="Description of this source"
    )

    quality: Quality = Field(
        sa_column=Column(
            Enum(Quality, values_callable=lambda obj: [e.value for e in obj])
        ),
        description="Quality flag for this source.",
    )

    shot: "ShotModel" = Relationship(back_populates="sources")


class CPFSummaryModel(SQLModel, table=True):
    __tablename__ = "cpf_summary"

    index: int = Field(primary_key=True, nullable=False)
    name: str = Field(sa_column=Column(Text), description="Name of the CPF variable.")
    description: str = Field("Description of the CPF variable")


class ScenarioModel(SQLModel, table=True):
    __tablename__ = "scenarios"
    id: int = Field(primary_key=True, nullable=False)
    name: str = Field(description="Name of the scenario.")


class ShotModel(SQLModel, table=True):
    __tablename__ = "shots"

    shot_id: int = Field(
        primary_key=True,
        index=True,
        nullable=False,
        description='ID of the shot. Also known as the shot index. e.g. "30420"',
    )

    uuid: uuid_pkg.UUID = Field(
        unique=True,
        index=True,
        default=None,
        description="UUID for this dataset",
    )

    url: str = Field(
        sa_column=Column(Text),
        description="The URL to this dataset",
    )

    timestamp: datetime.datetime = Field(
        description='Time the shot was fired in ISO 8601 format. e.g. "2023‐08‐10T09:51:19+00:00"'
    )

    preshot_description: str = Field(
        sa_column=Column(Text),
        description="A description by the investigator of the experiment before the shot was fired.",
    )

    postshot_description: str = Field(
        sa_column=Column(Text),
        description="A description by the investigator of the experiment after the shot was fired.",
    )

    campaign: str = Field(
        sa_column=Column(Text),
        description='The campagin that this show was part of. e.g. "M9"',
    )

    reference_shot: Optional[int] = Field(
        description='Reference shot ID used as the basis for setting up this shot, if used. e.g. "30420"',
    )

    scenario: Optional[int] = Field(
         description="The scenario used for this shot."
    )

    heating: Optional[str] = Field(
         description="The type of heating used for this shot."
    )

    pellets: Optional[bool] = Field(
         description="Whether pellets were used as part of this shot."
    )

    rmp_coil: Optional[bool] = Field(
         description="Whether an RMP coil was used as port of this shot."
    )

    current_range: Optional[CurrentRange] = Field(
        sa_column=Column(
            Enum(CurrentRange, values_callable=lambda obj: [e.value for e in obj]),
            
        ),
        description="The current range used for this shot. e.g. '7500 kA'",
    )

    divertor_config: Optional[DivertorConfig] = Field(
        sa_column=Column(
            Enum(DivertorConfig, values_callable=lambda obj: [e.value for e in obj])
        ),
        description="The divertor configuration used for this shot. e.g. 'Super-X'",
    )

    plasma_shape: Optional[PlasmaShape] = Field(
        sa_column=Column(
            Enum(PlasmaShape, values_callable=lambda obj: [e.value for e in obj])
        ),
        description="The plasma shape used for this shot. e.g. 'Connected Double Null'",
    )

    comissioner: Optional[Comissioner] = Field(
        sa_column=Column(
            Enum(Comissioner, values_callable=lambda obj: [e.value for e in obj])
        ),
        description="The comissioner of this shot. e.g. 'UKAEA'",
    )

    facility: Facility = Field(
        sa_column=Column(
            Enum(Facility, values_callable=lambda obj: [e.value for e in obj])
        ),
        description="The facility (tokamak) that produced this shot. e.g. 'MAST'",
    )

    signals: List["SignalModel"] = Relationship(back_populates="shot")
    sources: List["SourceModel"] = Relationship(back_populates="shot")

    cpf_p03249: Optional[float] = Field(alias="cpf_gdc_ps_mcs",
                                        description="(MCS Setup) GDC completed prior to shot for MAST only")

    cpf_p04673: Optional[float] = Field(alias="cpf_s_pv1_mcs",
                                        description="(MCS Setup) select gas group 1 for MAST only")

    cpf_p04674: Optional[float] = Field(alias="cpf_s_pv2_mcs",
                                        description="(MCS Setup) select gas group 2 for MAST only")

    cpf_p04675: Optional[float] = Field(alias="cpf_s_pv3_mcs", 
                                        description="(MCS Setup) select gas group 3 for MAST only")

    cpf_p04676: Optional[float] = Field(alias="cpf_s_pv4_mcs", 
                                        description="(MCS Setup) select gas group 4 for MAST only")

    cpf_p04677: Optional[float] = Field(alias="cpf_s_pv5_mcs",
                                        description="(MCS Setup) select gas group 5 for MAST only")

    cpf_p04678: Optional[float] = Field(alias="cpf_s_pv6_mcs",
                                        description="(MCS Setup) select gas group 6 for MAST only")

    cpf_p04679: Optional[float] = Field(alias="cpf_s_pv7_mcs",
                                        description="(MCS Setup) select gas group 7 for MAST only")

    cpf_p04680: Optional[float] = Field(alias="cpf_s_pv8_mcs",
                                        description="(MCS Setup) select gas group 8 for MAST only")

    cpf_p04681: Optional[float] = Field(alias="cpf_s_pv9_mcs",
                                        description="(MCS Setup) select gas group 9 for MAST only")

    cpf_p04833: Optional[float] = Field(alias="cpf_s_lvps_mcs",
                                        description="(MCS Setup) select TF power supply for MAST only")

    cpf_p04993: Optional[float] = Field(alias="cpf_s_cp3s_mcs", 
                                        description="(MCS Setup) select P3 start bank for MAST only")

    cpf_p05007: Optional[float] = Field(alias="cpf_s_fa1_mcs")

    cpf_p05008: Optional[float] = Field(alias="cpf_s_fa2_mcs")

    cpf_p05009: Optional[float] = Field(alias="cpf_s_mfps_mcs")

    cpf_p05010: Optional[float] = Field(alias="cpf_s_efps_mcs")

    cpf_p05011: Optional[float] = Field(alias="cpf_s_sfps_mcs")

    cpf_p05015: Optional[float] = Field(alias="cpf_s_scs4_mcs")

    cpf_p05016: Optional[float] = Field(alias="cpf_s_fa3_mcs")

    cpf_p05017: Optional[float] = Field(alias="cpf_s_fa4_mcs")

    cpf_p05025: Optional[float] = Field(alias="cpf_s_p1ps_mcs")

    cpf_p05027: Optional[float] = Field(alias="cpf_s_cp3c_mcs",
                                        description="(MCS Setup) select P3 counterpulse bank for MAST only")

    cpf_p05028: Optional[float] = Field(alias="cpf_s_cp4_mcs",
                                        description="(MCS Setup) select P4 start bank for MAST only")

    cpf_p05029: Optional[float] = Field(alias="cpf_s_cp5_mcs",
                                        description="(MCS Setup) select P3 start bank for MAST only")

    cpf_p05030: Optional[float] = Field(alias="cpf_s_p3_ps_mcs",
                                        description="(MCS Setup) select Siemens & GEC switches for P3 plasma Initiation for MAST only")

    cpf_p05032: Optional[float] = Field(alias="cpf_s_p4_thy_mcs",
                                        description="(MCS Setup) select P4 Ignitron and Thyristor circuit for MAST only")

    cpf_p05033: Optional[float] = Field(alias="cpf_s_p5_thy_mcs",
                                        description="(MCS Setup) select P5 Ignitron and Thyristor circuit for MAST only")

    cpf_p05153: Optional[float] = Field(alias="cpf_s_ecrh_mcs")

    cpf_p06000: Optional[float] = Field(alias="cpf_s_xmm_os9_mcs")

    cpf_p06001: Optional[float] = Field(alias="cpf_s_xpc_os9_mcs")

    cpf_p06002: Optional[float] = Field(alias="cpf_s_xcm_os9_mcs")

    cpf_p06003: Optional[float] = Field(alias="cpf_s_xmw_os9_mcs")

    cpf_p06004: Optional[float] = Field(alias="cpf_s_xma_os9_mcs")

    cpf_p10963: Optional[float] = Field(alias="cpf_ss_nbi_gas_mcs",
                                        description="(MCS Setup) MCS_SS_NBI_gas_species for MAST only")

    cpf_p10964: Optional[float] = Field(alias="cpf_sw_nbi_gas_mcs",
                                        description="(MCS Setup) MCS_SW_NBI_gas_species for MAST only")

    cpf_p12441: Optional[float] = Field(alias="cpf_cp3s_volts_mcs",
                                        description="(MCS Setup) CP3 set volts for MAST only")

    cpf_p12450: Optional[float] = Field(alias="cpf_cp3c_volts_mcs")

    cpf_p12451: Optional[float] = Field(alias="cpf_cp4s_volts_mcs",
                                        description="(MCS Setup) CP4 set volts for MAST only")

    cpf_p12452: Optional[float] = Field(alias="cpf_cp5s_volts_mcs",
                                        description="(MCS Setup) CP5 set volts for MAST only")

    cpf_p15202: Optional[float] = Field(alias="cpf_tg1_p_mcs",
                                        description="(MCS Setup) TG1 Base Pressure for MAST only")

    cpf_p15203: Optional[float] = Field(alias="cpf_agp_mcs",
                                        description="(MCS Setup) Additive gas pressure of main fueling plenum for MAST only")

    cpf_p15209: Optional[float] = Field(alias="cpf_wgp_mcs",
                                        description="(MCS Setup) Latest gas pressure of main fueling plenum for MAST only")

    cpf_p15659: Optional[float] = Field(alias="cpf_p3_dir_mcs",
                                        description="(MCS Setup) P3 Direction Monitored state of \
                                            Polarity-reversing/isolation switches for MAST only")

    cpf_p15660: Optional[float] = Field(alias="cpf_p4_dir_mcs",
                                        description="(MCS Setup) P4 direction: \
                                          1= Normal Direction (Positive Ip), 3= Open Circuit for MAST only")

    cpf_p15661: Optional[float] = Field(alias="cpf_p5_dir_mcs",
                                        description="(MCS Setup) P5 direction: \
                                          2= Reverse Direction (Positive Ip) for MAST only")

    cpf_p20000: Optional[float] = Field(alias="cpf_ss_mcs",
                                        description="(MCS Setup) Shot sequence number for MAST only")

    cpf_p20204: Optional[float] = Field(alias="cpf_ps_gdct",
                                        description="(MCS Setup) Pre-Shot GDC duration for MAST only")

    cpf_p20205: Optional[float] = Field(alias="cpf_gdc_st_mcs",
                                        description="(MCS Setup) Last GDC start time for MAST only")

    cpf_p20206: Optional[float] = Field(alias="cpf_igp_p_mcs",
                                        description="(MCS Setup) Inboard Gas Puff Pressure for MAST only")

    cpf_p20207: Optional[float] = Field(alias="cpf_igp_st_mcs",
                                        description="(MCS Setup) Inboard Gas Puff Start Time Relative to 10s for MAST only")

    cpf_p20208: Optional[float] = Field(alias="cpf_igp_d_mcs",
                                        description="(MCS Setup) Inboard Gas Puff Duration for MAST only")

    cpf_p21010: Optional[float] = Field(alias="cpf_p2xo_mcs",
                                        description="(MCS Setup) Param mim430 - P2XO Mode \
                                                    (P2 Reversing Switch Mode: 0= +ve only, 1= -ve only, \
                                                    2= +ve => -ve, 3= -ve => +ve) for MAST only")

    cpf_p21011: Optional[float] = Field(alias="cpf_p2xo_sf_mcs",
                                        description="(MCS Setup) Param mim430 - P2XO Start Forward \
                                                            (Offset by 5s: enable +ve polarity at time-5s) for MAST only")

    cpf_p21012: Optional[float] = Field(alias="cpf_p2xo_sr_mcs",
                                        description="(MCS Setup) Param mim430 - P2XO Start Reverse \
                                                            (Enable -ve polarity at 5s + time) for MAST only")

    cpf_p21021: Optional[float] = Field(alias="cpf_tfft_v_mcs",
                                        description="(MCS Setup) Param mim421 - TF Flat Top set value \
                                                        (Tesla @ R=0.7m) for MAST only")

    cpf_p21022: Optional[float] = Field(alias="cpf_tfft_t_mcs",
                                        description="(MCS Setup) Param mim421 - TF Flat Top set time (End of Flat Top) for MAST only")

    cpf_p21029: Optional[float] = Field(alias="cpf_tfrt_vmcs",
                                        )

    cpf_p21035: Optional[float] = Field(alias="cpf_p_dir_mcs",
                                        description="(MCS  Setup) Plasma Direction \
                                                    (1.0 => Positive: Dervived from P3/P4/P5 switch settings (P15659-P15661)) for MAST only")

    cpf_p21037: Optional[float] = Field(alias="cpf_p2_config_mcs",
                                        description="(MCS Setup) Required P2 Linkboard config \
                                            number (must match setting in PLC) for MAST only")

    cpf_p21041: Optional[float] = Field(alias="cpf_cp3s_st_mcs",
                                        description="(MCS Setup) CP3s start time (Offset by 5s) for MAST only")

    cpf_p21042: Optional[float] = Field(alias="cpf_cp3c_st_mcs",
                                        description="(MCS Setup) CP3c start time (Offset by 5s) for MAST only")

    cpf_p21043: Optional[float] = Field(alias="cpf_cp4_st_mcs",
                                        description="(MCS Setup) CP4 start time (Offset by 5s) for MAST only")

    cpf_p21044: Optional[float] = Field(alias="cpf_p4_igst_mcs",
                                        description="(MCS Setup) Close P4 circuit \
                                                            ignitron start time (Offset by 5s) for MAST only")

    cpf_p21045: Optional[float] = Field(alias="cpf_p4_thyst_mcs",
                                        description="(MCS Setup) P4 Circuit \
                                                            thyristor start time (Offset by 5s) for MAST only")

    cpf_p21046: Optional[float] = Field(alias="cpf_cp5_st_mcs",
                                        description="(MCS Setup) CP5 Start time (Offset by 5s) for MAST only")

    cpf_p21047: Optional[float] = Field(alias="cpf_p5_igst_mcs",
                                        description="(MCS Setup) P5 ignitron start time (Offset by 5s) for MAST only")

    cpf_p21048: Optional[float] = Field(alias="cpf_p5_thyst_mcs",
                                        description="(MCS Setup) P5 thyristor start time (Offset by 5s) for MAST only")

    cpf_p21051: Optional[float] = Field(alias="cpf_mfps_il_mcs",
                                        description="(MCS Setup) MFPS Power supply current limit for MAST only")


    cpf_p21052: Optional[float] = Field(alias="cpf_mfps_st_mcs",
                                        description="(MCS Setup) MFPS set enable start time (Offset by 5s) for MAST only")

    cpf_p21053: Optional[float] = Field(alias="cpf_efps_il_mcs",
                                        description="(MCS Setup) EFPS Power supply current limit for MAST only")

    cpf_p21054: Optional[float] = Field(alias="cpf_efps_st_mcs",
                                        description="(MCS Setup) EFPS set enable start time (Offset by 5s) for MAST only")

    cpf_p21055: Optional[float] = Field(alias="cpf_sfps_il_mcs",
                                        description="(MCS Setup) SFPS power supply current limit for MAST only")

    cpf_p21056: Optional[float] = Field(alias="cpf_sfps_st_mcs",
                                        description="(MCS Setup) SFPS set enable start time (Offset by 5s) for MAST only")

    cpf_p21075: Optional[float] = Field(alias="cpf_mfps_d_mcs", 
                                        description="(MCS Setup) MFPS enable duration for MAST only")

    cpf_p21076: Optional[float] = Field(alias="cpf_efps_d_mcs",
                                        description="(MCS Setup) EFPS enable duration for MAST only")

    cpf_p21077: Optional[float] = Field(alias="cpf_sfps_d_mcs",
                                        description="(MCS Setup) SFPS enable duration for MAST only")

    cpf_p21078: Optional[float] = Field(alias="cpf_p1ps_pil_mcs",
                                        description="(MCS Setup) P1PS maximum positive current for MAST only")

    cpf_p21079: Optional[float] = Field(alias="cpf_p1ps_nil_mcs",
                                        description="(MCS Setup) P1PS maximum negative current for MAST only")

    cpf_p21080: Optional[float] = Field(alias="cpf_p1ps_st_mcs",
                                        description="(MCS Setup) P1PS enable start time (offset by 5s) for MAST only")

    cpf_p21081: Optional[float] = Field(alias="cpf_p1ps_d_mcs",
                                        description="(MCS Setup) P1PS enable duration for MAST only")

    cpf_p21082: Optional[float] = Field(alias="cpf_fa1_st_mcs",
                                        description="(MCS Setup) FA1 enable start time (offset by 5s) for MAST only")

    cpf_p21083: Optional[float] = Field(alias="cpf_fa1_d_mcs",
                                        description="(MCS Setup) FA1 enable duration for MAST only")

    cpf_p21084: Optional[float] = Field(alias="cpf_fa2_st_mcs",
                                        description="(MCS Setup) FA2 enable start time (offset by 5s) for MAST only")

    cpf_p21085: Optional[float] = Field(alias="cpf_fa2_d_mcs",
                                        description="(MCS Setup) FA2 enable duration for MAST only")

    cpf_p21086: Optional[float] = Field(alias="cpf_fa3_st_mcs",
                                        description="(MCS Setup) FA3 enable start time (offset by 5s) for MAST only")

    cpf_p21087: Optional[float] = Field(alias="cpf_fa3_d_mcs",
                                        description="(MCS Setup) FA3 enable duration for MAST only")

    cpf_p21088: Optional[float] = Field(alias="cpf_fa4_st_mcs",
                                        description="(MCS Setup) FA4 enable start time (offset by 5s) for MAST only")

    cpf_p21089: Optional[float] = Field(alias="cpf_fa4_d_mcs",
                                        description="(MCS Setup) FA4 enable duration for MAST only")

    cpf_p21092: Optional[float] = Field(alias="cpf_scs4_st_mcs",
                                        description="(MCS Setup) SCS4 enabled start time used by MBD for MAST only")

    cpf_p21093: Optional[float] = Field(alias="cpf_scs4_d_mcs",
                                        description="(MCS Setup) SCS4 enabled duration for MAST only")

    cpf_abort: Optional[float] = Field(alias="cpf_abort_shot",
                                       description="Shot aborted for MAST and MAST-U")

    cpf_amin_ipmax: Optional[float] = Field(alias="cpf_amin_ipmax_gen",
                                            description="(Generic) Minor radius at time of peak plasma current for MAST and MAST-U")

    cpf_amin_max: Optional[float] = Field(alias="cpf_amin_max_gen",
                                          description="(Generic) Maximum value of minor radius for MAST and MAST-U")

    cpf_amin_truby: Optional[float] = Field(alias="cpf_amin_truby_gen",
                                            description="(Generic) Minor radius at time of Ruby TS for MAST only")

    cpf_area_ipmax: Optional[float] = Field(alias="cpf_area_ipmax_gen",
                                            description="(Generic) poloidal cross-sectional area at time of \
                                                peak plasma current for MAST and MAST-U")

    cpf_area_max: Optional[float] = Field(alias="cpf_area_max_gen",
                                          description="(Generic) Maximum Poloidal Cross-Sectional Area for MAST and MAST-U")

    cpf_area_truby: Optional[float] = Field(alias="cpf_area_truby_gen",
                                            description="(Generic) Poloidal Cross-Sectional Area at time of Ruby TS for MAST only")

    cpf_bepmhd_ipmax: Optional[float] = Field(alias="cpf_bepmhd_ipmax_gen",
                                              description="(Generic) Beta poloidal at time of Peak Plasma Current for MAST and MAST-U")

    cpf_bepmhd_max: Optional[float] = Field(alias="cpf_bepmhd_max_gen",
                                            description="(Generic) Maximum Beta poloidal for MAST and MAST-U")

    cpf_bepmhd_truby: Optional[float] = Field(alias="cpf_bepmhd_truby_gen",
                                              description="(Generic) Beta poloidal at time of Ruby TS for MAST only")

    cpf_betmhd_ipmax: Optional[float] = Field(alias="cpf_betmhd_ipmax_gen",
                                              description="(Generic) Beta at time of peak plasma current for MAST and MAST-U")

    cpf_betmhd_max: Optional[float] = Field(alias="cpf_betmhd_max_gen",
                                            description="(Generic) Maximum beta at time of peak plasma current for MAST and MAST-U")

    cpf_betmhd_truby: Optional[float] = Field(alias="cpf_betmhd_truby_gen",
                                              description="(Generic) Beta at time of ruby TS for MAST only")

    cpf_bt_ipmax: Optional[float] = Field(alias="cpf_bt_ipmax_gen",
                                          description="(Generic) Toroidal field strength at time of peak \
                                                    plasma current for MAST and MAST-U")

    cpf_bt_max: Optional[float] = Field(alias="cpf_bt_max_gen",
                                        description="(Generic) Maximum Toroidal field strength at time of peak \
                                                    plasma current for MAST and MAST-U")

    cpf_bt_truby: Optional[float] = Field(alias="cpf_bt_truby_gen",
                                          description="(Generic) Toroidal field strength at time of ruby TS for MAST only")

    cpf_c2ratio: Optional[float] = Field(alias="cpf_c2ratio_rad",
                                         description="(Radii) CII Line ratio averaged over Ip flat top from 150ms for MAST and MAST-U")

    cpf_column_temp_in: Optional[float] = Field(alias="cpf_col_temp_in_gas",
                                               description="(Gas) centre column outlet temperature for MAST only")

    cpf_column_temp_out: Optional[float] = Field(alias="cpf_col_temp_out_gas",
                                                 description="(Gas) centre column inlet temperature for MAST only")

    cpf_creation: Optional[datetime.datetime] = Field(alias="cpf_creation_d_shot",
                                                      description="(Shot metdata) data dictionary entry creation \
                                                                date for MAST and MAST-U")

    cpf_dwmhd_ipmax: Optional[float] = Field(alias="cpf_dwmhd_ipmax_gen",
                                             description="(Generic) rate of change of total stored energy at \
                                                            time of peak plasma current for MAST and MAST-U")

    cpf_dwmhd_max: Optional[float] = Field(alias="cpf_dwmhd_max_gen",
                                           description="(Generic) maximum rate of change of MHD stored energy at \
                                            time of peak plasma current for MAST and MAST-U")

    cpf_dwmhd_truby: Optional[float] = Field(alias="cpf_dwmhd_truby_gen",
                                            description="(Generic) rate of change of MHD stored energy at \
                                            time of ruby TS for MAST only")

    cpf_enbi_max_ss: Optional[float] = Field(alias="cpf_enbi_max_ss",
                                            description="(NBI) injection energy from SS beam at time of peak power \
                                            for MAST and MAST-U")

    cpf_enbi_max_sw: Optional[float] = Field(alias="cpf_enbi_max_sw",
                                            description="(NBI) injection energy from SW beam at time of peak power \
                                            for MAST and MAST-U")

    cpf_exp_date: Optional[datetime.datetime] = Field(alias="cpf_exp_date_shot",
                                                      description="MAST shot experiment pulse date for MAST and MAST-U")

    cpf_exp_number: Optional[int] = Field(alias="cpf_exp_number_shot",
                                          description="MAST shot experiment pulse number for MAST and MAST-U")

    cpf_exp_time: Optional[datetime.time] = Field(alias="cpf_exp_time_shot",
                                                  description="MAST shot experiment pulse time for MAST and MAST-U")

    cpf_gdc_duration: Optional[float] = Field(alias="cpf_gdc_d_shot",
                                              description="Shot glow discharge duration for both")

    cpf_gdc_time: Optional[float] = Field(alias="cpf_gdc_time_shot",
                                          description="Shot glow discharge time for both")

    cpf_ibgas_pressure: Optional[float] = Field(alias="cpf_ibgas_pressure",
                                                description="Inboard gas pressure prior to pulse for MAST only")

    cpf_ip_av: Optional[float] = Field(alias="cpf_ip_av_plasma",
                                       description="(Plasma) Time averaged plasma current during flat-top for MAST and MAST-U")

    cpf_ip_max: Optional[float] = Field(alias="cpf_ip_max_plasma",
                                        description="(Plasma) Maximum value of plasma current for MAST and MAST-U")

    cpf_jnbi_ipmax: Optional[float] = Field(alias="cpf_jnbi_ipmax",
                                            description="(NBI) injected energy from \
                                                        SS+SW beams at time of peak current for MAST and MAST-U")

    cpf_jnbi_ipmax_ss: Optional[float] = Field(alias="cpf_jnbi_ipmax_ss",
                                               description="(NBI) injected energy from \
                                                            SS beams at time of peak current for MAST and MAST-U")

    cpf_jnbi_ipmax_sw: Optional[float] = Field(alias="cpf_jnbi_ipmax_sw",
                                               description="(NBI) injected energy from \
                                                            SW beams at time of peak current for MAST and MAST-U")

    cpf_jnbi_max: Optional[float] = Field(alias="cpf_jnbi_max",
                                          description="(NBI) injected energy from SS+SW \
                                                        beams at time of peak power for MAST and MAST-U")

    cpf_jnbi_max_ss: Optional[float] = Field(alias="cpf_jnbi_max_ss",
                                             description="(NBI) injection energy from SS \
                                           beam at time of peak power for MAST and MAST-U")

    cpf_jnbi_max_sw: Optional[float] = Field(alias="cpf_jnbi_max_sw",
                                             description="(NBI) injection energy from SW \
                                                        beam at time of peak power for MAST and MAST-U")

    cpf_jnbi_total: Optional[float] = Field(alias="cpf_jnbi_total",
                                            description="Total NBI injected energy from \
                                                                SS+SW beams for MAST and MAST-U")

    cpf_jnbi_total_ss: Optional[float] = Field(alias="cpf_jnbi_total_ss",
                                               description="Total NBI Injected Energy from SS Beam \
                                                                        for MAST and MAST-U")

    cpf_jnbi_total_sw: Optional[float] = Field(alias="cpf_jnbi_total_sw",
                                               description="Total NBI Injected Energy from SW Beam \
                                                                    for MAST and MAST-U")

    cpf_jnbi_truby: Optional[float] = Field(alias="cpf_jnbi_truby",
                                            description="(NBI) Injected Energy from SS+SW Beams at \
                                                                time of Ruby TS for MAST only")

    cpf_jnbi_truby_ss: Optional[float] = Field(alias="cpf_jnbi_truby_ss",
                                               description="NBI Injected Energy from SW Beam at time \
                                                                    of Ruby TS for MAST only")

    cpf_jnbi_truby_sw: Optional[float] = Field(alias="cpf_jnbi_truby_sw",
                                               description="(NBI) Injected Energy from SW Beam at time \
                                                                    of Ruby TS for MAST only")

    cpf_johm_ipmax: Optional[float] = Field(alias="cpf_johm_ipmax",
                                            description="Ohmic Heating Energy Input at time of \
                                                                Peak Current for MAST and MAST-U")

    cpf_johm_max: Optional[float] = Field(alias="cpf_johm_max",
                                          description="Ohmic Heating Energy Input at time of \
                                                                Maximum Ohmic Heating for MAST and MAST-U")

    cpf_johm_total: Optional[float] = Field(alias="cpf_johm_total",
                                            description="Total Ohmic Heating Energy Input \
                                                                    for MAST and MAST-U")

    cpf_johm_truby: Optional[float] = Field(alias="cpf_johm_truby",
                                            description="Ohmic Heat Energy Input at time \
                                                                    of Ruby TS for MAST only")

    cpf_kappa_ipmax: Optional[float] = Field(alias="cpf_kappa_ipmax_gen",
                                             description="(Generic) Plasma Elongation at time of Peak \
                                                            Plasma Current for MAST and MAST-U")

    cpf_kappa_max: Optional[float] = Field(alias="cpf_kappa_max_gen", 
                                           description="(Generic) Maximum value of Plasma Elongation \
                                                                for MAST and MAST-U")

    cpf_kappa_truby: Optional[float] = Field(alias="cpf_kappa_truby_gen",
                                             description="(Generic) Plasma Elongation at time of Ruby TS for MAST only")

    cpf_li_2_ipmax: Optional[float] = Field(alias="cpf_li_2_ipmax_equi",
                                            description="(Equilibrium) li(2) at time of Peak Current for MAST and MAST-U")

    cpf_li_2_max: Optional[float] = Field(alias="cpf_li_2_max_equi",
                                          description="(Equilibrium) li(2) Maximum value for MAST and MAST-U")

    cpf_li_2_truby: Optional[float] = Field(alias="cpf_li_2_truby_equi",
                                            description="(Equilibrium) li(2) Maximum value for MAST and MAST-U")

    cpf_li_3_ipmax: Optional[float] = Field(alias="cpf_li_3_ipmax_equi",
                                            description="(Equilibrium) li(3) at time of Peak Current for MAST and MAST-U")

    cpf_li_3_max: Optional[float] = Field(alias="cpf_li_3_max_equi",
                                          description="(Equilibrium) li(3) Maximum value for MAST and MAST-U")

    cpf_li_3_truby: Optional[float] = Field(alias="cpf_li_3_truby_equi",
                                            description="(Equilibrium) li(3) at time of Ruby TS for MAST only")

    cpf_log_base_pressure: Optional[float] = Field(alias="cpf_log_base_p_gas",
                                                   description="(Gas) TG1 Base Pressure prior to Shot for MAST only")

    cpf_ndl_co2_ipmax: Optional[float] = Field(alias="cpf_ndl_ipmax_thom",
                                               description="(Thomson) Electron Density Line Integral at time \
                                                            of Peak Plasma Current for MAST and MAST-U")

    cpf_ndl_co2_max: Optional[float] = Field(alias="cpf_ndl_max_thom",
                                              description="(Thomson) Maximum Electron Density Line Integral \
                                                            observed by CO2 Interferometer for MAST and MAST-U")

    cpf_ndl_co2_truby: Optional[float] = Field(alias="cpf_ndl_truby_thom",
                                               description="(Thomson) Electron Density Line Integral at time \
                                                                    of Ruby TS for MAST only")

    cpf_ne0_ipmax: Optional[float] = Field(alias="cpf_ne0_ipmax_thom",
                                           description="(Thomson) Core Electron Density (Nd.YAG) at time of \
                                                                    Peak Current for MAST and MAST-U")

    cpf_ne0_max: Optional[float] = Field(alias="cpf_ne0_max_thom",
                                         description="(Thomson) Peak Core Electron Density (Nd.YAG) for MAST and MAST-U")

    cpf_ne0_truby: Optional[float] = Field(alias="cpf_ne0_truby_thom",
                                           description="(Thomson) Core Electron Density (Nd.YAG) at time of Ruby TS for MAST only")

    cpf_ne0ratio_ipmax: Optional[float] = Field(alias="cpf_ne0ratio_ipmax_thom",
                                                description="(Thomson) Ratio of ne0 to line average ne for MAST and MAST-U")

    cpf_ne0ruby: Optional[float] = Field(alias="cpf_ne0ruby_thom",
                                         description="(Thomson) Core Electron Density (Nd.YAG) at time of Ruby TS for MAST only")

    cpf_ne_bar_ipmax: Optional[float] = Field(alias="cpf_ne_bar_ipmax_thom",
                                              description="(Thomson) Mid-plane line average electron density \
                                                            from CO2 interferometer for MAST and MAST-U")

    cpf_ne_yag_bar_ipmax: Optional[float] = Field(alias="cpf_ne_yag_bar_ipmax_thom",
                                                  description="(Thomson) Mid-plane line average electron density from CO2 \
                                                                    interferometer for MAST and MAST-U")

    cpf_ngreenwald_ipmax: Optional[float] = Field(alias="cpf_ngreenwald_ipmax_thom",
                                                  description="(Thomson) Greenwald Density Limit for MAST and MAST-U")

    cpf_ngreenwaldratio_ipmax: Optional[float] = Field(alias="cpf_ngreenwaldrat_ipmax_thom",
                                                       description="(Thomson) Ratio of Greenwald density limit to mid-plane \
                                                                        line averaged electron density for MAST and MAST-U")

    cpf_o2ratio: Optional[float] = Field(alias="cpf_o2ratio_rad",
                                         description="(Radii) OII Line Ratio averaged over Ip flat top from 150ms \
                                                                for MAST and MAST-U")

    cpf_objective: Optional[str] = Field(alias="cpf_objective_shot",
                                         description="Shot Scientific Objective for MAST and MAST-U")

    cpf_pe0_ipmax: Optional[float] = Field(alias="cpf_pe0_ipmax_thom",
                                           description="(Thomsom) Core Electron Pressure (Nd.YAG) at time of Peak \
                                                                Plasma Current for MAST and MAST-U")

    cpf_pe0_max: Optional[float] = Field(alias="cpf_pe0_max_thom",
                                         description="(Thomsom) Maximum value of Core Electron Pressure (Nd.YAG) \
                                                                    for MAST and MAST-U")

    cpf_pe0_truby: Optional[float] = Field(alias="cpf_pe0_truby_thom",
                                           description="(Thomsom) Core Electron Pressure (Nd.YAG) at time of Ruby TS \
                                                                for MAST only")

    cpf_pe0ruby: Optional[float] = Field(alias="cpf_pe0ruby_thom",
                                         description="(Thomsom) Ruby TS Core Electron Pressure for MAST only")

    cpf_pic: Optional[str] = Field(alias="cpf_pic_shot",
                                   description="(Shot) physicist in charge for MAST and MAST-U")

    cpf_pnbi_ipmax: Optional[float] = Field(alias="cpf_pnbi_ipmax",
                                            description="(NBI) Power from SS+SW Beams at time of Peak Current \
                                                                for MAST and MAST-U")

    cpf_pnbi_ipmax_ss: Optional[float] = Field(alias="cpf_pnbi_ipmax_ss",
                                               description="(NBI) Power from SS Beam at time of Peak Current \
                                                            for MAST and MAST-U")

    cpf_pnbi_ipmax_sw: Optional[float] = Field(alias="cpf_pnbi_ipmax_sw",
                                               description="(NBI) Power from SW Beam at time of Peak Current \
                                                            for MAST and MAST-U")

    cpf_pnbi_max: Optional[float] = Field(alias="cpf_pnbi_max",
                                          description="(NBI) Power from SS+SW Beams at time of Peak power \
                                                        for MAST and MAST-U")

    cpf_pnbi_max_ss: Optional[float] = Field(alias="cpf_pnbi_max_ss",
                                             description="Peak NBI Power from SS Beam for MAST and MAST-U")

    cpf_pnbi_max_sw: Optional[float] = Field(alias="cpf_pnbi_max_sw",
                                             description="Peak NBI Power from SW Beam for MAST and MAST-U")

    cpf_pnbi_truby: Optional[float] = Field(alias="cpf_pnbi_truby",
                                            description="(NBI) Power from SS+SW Beams at time of Ruby TS for MAST and MAST-U")

    cpf_pnbi_truby_ss: Optional[float] = Field(
                                               description="(NBI) Power from SS Beam at time of Ruby TS for MAST and MAST-U")

    cpf_pnbi_truby_sw: Optional[float] = Field(
                                               description="(NBI) Power from SW Beam at time of Ruby TS for MAST and MAST-U")

    cpf_pohm_ipmax: Optional[float] = Field(
                                            description="Ohmic Heating Rate at time of Peak Current for MAST and MAST-U")

    cpf_pohm_max: Optional[float] = Field(
                                          description="Maximum Ohmic Heating Rate for MAST and MAST-U")

    cpf_pohm_truby: Optional[float] = Field( 
                                            description="Ohmic Heating Rate at time of Ruby TS for MAST only")

    cpf_postshot: Optional[str] = Field(
                                        description="Session Leaders Post-Shot Comment for MAST and MAST-U")

    cpf_prad_ipmax: Optional[float] = Field(alias="cpf_prad_ipmax_gen",
                                            description="(Generic) Total Radiated Power Loss at time of \
                                                                Peak Plasma Current for MAST and MAST-U")

    cpf_prad_max: Optional[float] = Field(alias="cpf_prad_max_gen",
                                          description="(Generic) Maximum Total Radiated Power Loss for MAST and MAST-U")

    cpf_prad_truby: Optional[float] = Field(alias="cpf_prad_truby_gen",
                                            description="(Generic) Total Radiated Power Loss at time of Ruby TS for MAST only")

    cpf_pradne2: Optional[float] = Field(alias="cpf_pradne2_rad",
                                         description="(Radii) Flat Top Ratio of Power Radiated to Line Density squared \
                                                        averaged over Ip flat top from 150ms for MAST and MAST-U")

    cpf_preshot: Optional[str] = Field( 
                                       description="Session Leaders Pre-Shot Comment for MAST and MAST-U")

    cpf_program: Optional[str] = Field(alias="cpf_shot_program",
                                       description="(Shot) Scientific Program for MAST and MAST-U")

    cpf_pulno: Optional[float] = Field(alias="cpf_pulno_shot",
                                       description="(Ghot) MAST Experiment Pulse Number for MAST and MAST-U")

    cpf_q95_ipmax: Optional[float] = Field(alias="cpf_q95_ipmax_gen",
                                           description="(Generic) q-95 at time of Peak Plasma Current for MAST and MAST-U")

    cpf_q95_min: Optional[float] = Field(alias="cpf_q95_min_gen",
                                         description="(Generic) Minimum value of q-95 for MAST and MAST-U")

    cpf_q95_truby: Optional[float] = Field(alias="cpf_q95_truby_gen",
                                           description="(Generic) q-95 at time of Ruby TS")

    cpf_reference: Optional[float] = Field(alias="cpf_shot_reference",
                                           description="(Shot) Reference shot for MAST and MAST-U")

    cpf_rgeo_ipmax: Optional[float] = Field(alias="cpf_rgeo_ipmax_gen",
                                            description="(Generic) q-95 at time of Peak Plasma Current for MAST and MAST-U")

    cpf_rgeo_max: Optional[float] = Field(alias="cpf_rgeo_max_gen",
                                          description="(Generic) Maximum value of Geometrical Center \
                                                                    Major Radius for MAST and MAST-U")

    cpf_rgeo_truby: Optional[float] = Field(alias="cpf_rgeo_truby_gen",
                                            description="(Generic) geometrical Center Major Radius at time \
                                                            of Ruby TS for MAST and MAST-U")

    cpf_rinner_da: Optional[float] = Field(alias="cpf_rinner_da_rad",
                                           description="(Radii) rinner major Radius from Visible D_Alpha Light \
                                                            for MAST and MAST-U")

    cpf_rinner_efit: Optional[float] = Field(alias="cpf_rinner_efit_rad",
                                             description="(Radii) rinner major Radius from EFIT Equilibrium \
                                                            for MAST and MAST-U")

    cpf_rmag_efit: Optional[float] = Field(alias="cpf_mag_efit_rad",
                                           description="(Radii) magnetic Axis major Radius from EFIT Equilibrium \
                                                            for MAST and MAST-U")

    cpf_router_da: Optional[float] = Field(alias="cpf_router_da_rad",
                                           description="(Radii) router major Radius from Visible D_Alpha Light \
                                                            for MAST and MAST-U")

    cpf_router_efit: Optional[float] = Field(alias="cpf_router_efit_rad",
                                             description="(Radii) router major Radius from EFIT Equilibrium \
                                                            for MAST and MAST-U")

    cpf_sarea_ipmax: Optional[float] = Field(alias="cpf_sarea_ipmax_rad",
                                             description="(Generic) Total Surface Area at time of Peak Plasma \
                                                            Current for MAST and MAST-U")

    cpf_sarea_max: Optional[float] = Field(alias="cpf_sarea_max_gen",
                                           description="(Generic) maximum Total Surface Area for MAST and MAST-U")

    cpf_sarea_truby: Optional[float] = Field(alias="cpf_sarea_truby_gen",
                                             description="(Generic) total Surface Area at time of Ruby TS for MAST only")

    cpf_sl: Optional[str] = Field(alias="cpf_shot_sl",
                                  description="(Shot) session leader for MAST and MAST-U")

    cpf_sc: Optional[str] = Field(nullable=True)

    cpf_summary: Optional[str] = Field(alias="cpf_shot_summary",
                                        description="(Shot) session summary for MAST and MAST-U")

    cpf_tamin_max: Optional[float] = Field(alias="cpf_tamin_max_gen",
                                           description="(Generic) Time of Maximum Plasma Minor Radius for MAST and MAST-U")

    cpf_tarea_max: Optional[float] = Field(alias="cpf_tarea_max_gen",
                                           description="(Generic) Time of Maximum Poloidal Cross-Sectional Area \
                                                                    for MAST and MAST-U")

    cpf_tautot_ipmax: Optional[float] = Field(alias="cpf_tautot_ipmax_gen",
                                               description="(Generic) Energy Confinement Time at time of Peak Plasma Current \
                                                                    for MAST and MAST-U")


    cpf_tautot_max: Optional[float] = Field(alias="cpf_tautot_max_gen",
                                            description="(Generic) Maximum value of Energy Confinement Time for MAST and MAST-U")

    cpf_tautot_truby: Optional[float] = Field(alias="cpf_tautot_truby_gen",
                                              description="(Generic) Energy Confinement Time at time of Ruby TS for MAST and MAST-U")

    cpf_tbepmhd_max: Optional[float] = Field(alias="cpf_tbepmhd_max_gen",
                                             description="(Generic) Time of Maximum Beta Poloidal MHD for MAST and MAST-U")

    cpf_tbetmhd_max: Optional[float] = Field(alias="cpf_tbetmhd_max_gen",
                                             description="(Generic) Time of Maximum Beta MHD for MAST and MAST-U")

    cpf_tbt_max: Optional[float] = Field(alias="cpf_tbt_max_gen",
                                         description="(Generic) Time of Maximum Toroidal Magnetic Field Strength \
                                                                    for MAST and MAST-U")

    cpf_tdwmhd_max: Optional[float] = Field(alias="cpf_tdwmhd_max_gen",
                                            description="(Generic) Time of Maximum Rate of Change of MHD Stored Energy \
                                                                    for MAST and MAST-U")

    cpf_te0_ipmax: Optional[float] = Field(alias="cpf_te0_ipmax_thom",
                                           description="(Thomoson) Core Electron Temperature (Nd.YAG) at time of \
                                                                        Peak Current for MAST and MAST-U")

    cpf_te0_max: Optional[float] = Field(alias="cpf_te0_max_thom",
                                         description="(Thomson) Peak Core Electron Temperature (Nd.YAG) \
                                                                        for MAST and MAST-U")

    cpf_te0_truby: Optional[float] = Field(alias="cpf_te0_truby_thom",
                                           description="(Thomson) Core Electron Temperature (Nd.YAG) at \
                                                                            time of Ruby TS for MAST only")

    cpf_te0ratio_ipmax: Optional[float] = Field(alias="cpf_te0ratio_ipmax_thom",
                                                description="(Thomson) ratio of Te0 to line average Te \
                                                                                for MAST and MAST-U")

    cpf_te0ruby: Optional[float] = Field(alias="cpf_te0ruby_thom",
                                         description="(Thomson) Ruby TS Core Electron Temperature for MAST only")

    cpf_te_yag_bar_ipmax: Optional[float] = Field(alias="cpf_te_yag_bar_ipmax_thom",
                                                  description="Mid-plane line average electron temperature from \
                                                                            YAG Thomson scattering for MAST and MAST-U")

    cpf_tend: Optional[float] = Field(alias="cpf_tend_plasma",
                                      description="(Plasma) current end time for MAST and MAST-U")

    cpf_tend_ibgas: Optional[float] = Field( 
                                            description="Inboard Gas Puff End Time for MAST only")

    cpf_tend_nbi: Optional[float] = Field( description="(NBI) end time for MAST and MAST-U")

    cpf_tend_nbi_ss: Optional[float] = Field( description="SS NBI end time for MAST and MAST-U")

    cpf_tend_nbi_sw: Optional[float] = Field( description="SW NBI end time for MAST and MAST-U")

    cpf_term_code: Optional[float] = Field(alias="cpf_shot_term_code",
                                           description="(Plasma) shot termination reason code for MAST and MASt-U")

    cpf_tftend: Optional[float] = Field(alias="cpf_tftend_plasma",
                                        description="(Plasma) Current Flat-Top End Time for MAST and MAST-U")

    cpf_tftstart: Optional[float] = Field(alias="cpf_tftstart_plasma",
                                          description="(Plasma) Current Flat-Top Start Time for MAST and MAST-U")

    cpf_tipmax: Optional[float] = Field(alias="cpf_tipmax_plasma",
                                        description="(Plasma) Time of Maximum Plasma Current for MAST and MAST-U")

    cpf_tkappa_max: Optional[float] = Field(alias="cpf_tkappa_max_gen",
                                             description="(Generic) Time of Maximum Plasma Elongation for MAST and MAST-U")

    cpf_tli_2_max: Optional[float] = Field(alias="cpf_tli_2_max_equi",
                                           description="(Equilibrium) time of Maximum li(2) for MAST and MAST-U")

    cpf_tli_3_max: Optional[float] = Field(alias="cpf_tli_3_max_equi",
                                           description="(Equilibrium) time of Maximum li(3) for MAST and MAST-U")

    cpf_tndl_co2_max: Optional[float] = Field(alias="cpf_tndl_max_thom",
                                              description="(Thomson) Time of Maximum Electron Density Line Integral \
                                                                for MAST and MAST-U")

    cpf_tne0_max: Optional[float] = Field(alias="cpf_tne0_max_thom",
                                          description="(thomson) Time of Maximum Core Electron Density (from Nd.YAG TS) \
                                                                for MAST and MAST-U")

    cpf_tpe0_max: Optional[float] = Field(alias="cpf_tpe0_max_thom",
                                          description="(Thomson) Time of Maximum Core Electron Pressure (from Nd.YAG TS) \
                                                                    for MAST and MAST-U")

    cpf_tpnbi_max: Optional[float] = Field( 
                                           description="(NBI) Time of Maximum NB Power for MAST and MAST-U")

    cpf_tpnbi_max_ss: Optional[float] = Field( description="(NBI) Time of Maximum SS NBI Power for MAST and MAST-U")

    cpf_tpnbi_max_sw: Optional[float] = Field( description="(NBI) Time of Maximum SW NBI Power for MAST and MAST-U")

    cpf_tpohm_max: Optional[float] = Field( description="(NBI) Time of Maximum Ohmic Heating for MAST and MAST-U")

    cpf_tprad_max: Optional[float] = Field(alias="cpf_tprad_max_gen",
                                           description="(Generic) Time of Maximum Plasma Radiated Power Loss for MAST and MAST-U")

    cpf_tq95_min: Optional[float] = Field(alias="cpf_tq95_min_gen",
                                          description="(Generic) Time of Minimum q 95 for MAST and MAST-U")

    cpf_trgeo_max: Optional[float] = Field(alias="cpf_trgeo_max_gen",
                                           description="(Generic) Time of Maximum Geometrical Mid-plane Center Major Radius \
                                           for MAST and MAST-U")

    cpf_truby: Optional[float] = Field(alias="cpf_truby_thom",
                                       description="(Thomson) Ruby Thomson Scattering Time for MAST only")

    cpf_tsarea_max: Optional[float] = Field(alias="cpf_tsarea_max_gen",
                                            description="(Generic) Time of Maximum Plasma Surface Area for MAST and MAST-U")

    cpf_tstart: Optional[float] = Field(alias="cpf_tstart_plasma",
                                         description="(Plasma) Current Flat-Top Start Time for MAST and MAST-U")

    cpf_tstart_ibgas: Optional[float] = Field( description="Inboard Gas Puff Start Time for MAST only")

    cpf_tstart_nbi: Optional[float] = Field( description="(NBI) Start Time for MAST and MAST-U")

    cpf_tstart_nbi_ss: Optional[float] = Field( description="SS NBI Start Time for MAST and MAST-U")

    cpf_tstart_nbi_sw: Optional[float] = Field( description="SW NBI Start Time for MAST and MAST-U")

    cpf_ttautot_max: Optional[float] = Field(alias="cpf_ttautot_max_gen",
                                             description="(Generic) Time of Maximum Total Energy Confinement Time for MAST and MAST-U")

    cpf_tte0_max: Optional[float] = Field(alias="cpf_tte0_max_thom",
                                          description="(Thomson) Time of Maximum Core Electron Temperature (from Nd.YAG TS) \
                                                                    for MAST and MAST-U")

    cpf_tvol_max: Optional[float] = Field(alias="cpf_tvol_max_gen",
                                          description="(Generic) Time of Maximum Plasma Volume for MAST and MAST-U")

    cpf_twmhd_max: Optional[float] = Field(alias="cpf_twmhd_max_gen",
                                           description="(Generic) Time of Maximum MHD Stored Energy for MAST and MAST-U")

    cpf_tzeff_max: Optional[float] = Field(alias="cpf_tzeff_max_gen",
                                           description="(Generic) Time of Maximum Plasma Z-Effective for MAST and MAST-U")

    cpf_useful: Optional[float] = Field(alias="cpf_useful_shot",
                                        description="Useful Shot for MAST and MAST-U")

    cpf_vol_ipmax: Optional[float] = Field(alias="cpf_vol_ipmax_gen",
                                           description="(Generic) Plasma Volume at time of Peak Plasma Current for MAST and MAST-U")

    cpf_vol_max: Optional[float] = Field(alias="cpf_vol_max_gen",
                                         description="(Generic) Maximum Plasma Volume for MAST and MAST-U")

    cpf_vol_truby: Optional[float] = Field(alias="cpf_vol_truby_gen",
                                           description="(Generic) Plasma Volume at time of Ruby TS for MAST only")

    cpf_wmhd_ipmax: Optional[float] = Field(alias="cpf_wmhd_ipmax_gen",
                                            description="(Generic) Stored Energy at time of Peak Plasma Current \
                                                                        for MAST and MAST-U")

    cpf_wmhd_max: Optional[float] = Field(alias="cpf_wmhd_max_gen",
                                          description="(Generic) Maximum Stored Energy for MAST and MAST-U")

    cpf_wmhd_truby: Optional[float] = Field(alias="cpf_wmhd_truby_gen",
                                            description="(Generic) Stored Energy at time of Ruby TS for MAST only")

    cpf_zeff_ipmax: Optional[float] = Field(alias="cpf_zeff_ipmax_gen",
                                            description="(Generic) Plasma Z-Effective at time of Peak Plasma Current \
                                                                            for MAST and MAST-U")

    cpf_zeff_max: Optional[float] = Field(alias="cpf_zeff_max_gen",
                                          description="(Generic) Maximum Plasma Z-Effective for MAST and MASt-U")

    cpf_zeff_truby: Optional[float] = Field(alias="cpf_zeff_truby_gen",
                                            description="(Generic) Plasma Z-Effective at time of Ruby TS for MAST only")

    cpf_zmag_efit: Optional[float] = Field(alias="cpf_zmag_efit_radii",
                                           description="(Radii) Magnetic Axis height above Mid-Plane from EFIT Equilibrium \
                                                                            for MAST and MAST-U")
