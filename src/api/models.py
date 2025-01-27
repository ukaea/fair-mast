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

    dimensions: Optional[List[str]] = Field(
        sa_column=Column(ARRAY(Text)),
        description="The dimension names of the dataset, in order. e.g. ['time', 'radius']",
    )

    imas: Optional[str] = Field(
        description="The IMAS reference string for this record."
    )

    shot: "ShotModel" = Relationship(back_populates="signals")


class Level2SignalModel(SQLModel, table=True):
    __tablename__ = "level2_signals"

    uuid: uuid_pkg.UUID = Field(
        primary_key=True,
        default=None,
        description="UUID for a specific signal data",
    )

    shot_id: int = Field(
        foreign_key="level2_shots.shot_id",
        nullable=False,
        description="ID of the shot this signal was produced by.",
    )

    name: str = Field(
        description="Human readable name of this specific signal. A combination of the signal type and the shot number e.g. AMC_PLASMA_CURRENT"
    )

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

    dimensions: Optional[List[str]] = Field(
        sa_column=Column(ARRAY(Text)),
        description="The dimension names of the dataset, in order. e.g. ['time', 'radius']",
    )

    imas: Optional[str] = Field(
        description="The IMAS reference string for this record."
    )

    shot: "Level2ShotModel" = Relationship()


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

    imas: Optional[str] = Field(
        description="The IMAS reference string for this record."
    )

    shot: "ShotModel" = Relationship(back_populates="sources")


class Level2SourceModel(SQLModel, table=True):
    __tablename__ = "level2_sources"

    uuid: uuid_pkg.UUID = Field(
        primary_key=True,
        default=None,
        description="UUID for a specific source data",
    )

    shot_id: int = Field(
        foreign_key="level2_shots.shot_id",
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

    imas: Optional[str] = Field(
        description="The IMAS reference string for this record."
    )

    shot: "Level2ShotModel" = Relationship()


class DataService(SQLModel, table=True):
    __tablename__ = "dataservice"

    context: Optional[Dict] = Field(
        sa_column=Column(JSONB),
        default={},
        description="Context mapping vocabulary to IRIs",
        alias="context_",
    )

    type: Optional[str] = Field(description="a structured set of data", alias="type_")

    id: Optional[str] = Field(
        primary_key=True,
        description="unique IRI indentification for the data",
        alias="id_",
    )
    title: Optional[str] = Field(
        description="the title of the dataset", alias="dct__title"
    )

    description: Optional[str] = Field(
        description="representation of the data", alias="dct__description"
    )

    publisher: Optional[str] = Field(
        sa_column=Column(JSONB),
        default={},
        description="organisation responsible for the dataset.",
        alias="dct__publisher",
    )

    endpointurl: Optional[str] = Field(alias="dcat__endpointURL")

    servesdataset: Optional[List[str]] = Field(
        sa_column=Column(ARRAY(Text)), alias="dcat__servesDataset"
    )

    theme: Optional[List[str]] = Field(
        sa_column=Column(ARRAY(Text)), alias="dct__theme"
    )


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

    scenario: Optional[int] = Field(description="The scenario used for this shot.")

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

    cpf_p03249: Optional[float] = Field(
        alias="mcs_gdc_pre_shot",
        description="(MCS Setup) GDC completed prior to shot for MAST only",
    )

    cpf_p04673: Optional[float] = Field(
        alias="mcs_select_gas_group_pv1",
        description="(MCS Setup) select gas group 1 for MAST only",
    )

    cpf_p04674: Optional[float] = Field(
        alias="mcs_select_gas_group_pv2",
        description="(MCS Setup) select gas group 2 for MAST only",
    )

    cpf_p04675: Optional[float] = Field(
        alias="mcs_select_gas_group_pv3",
        description="(MCS Setup) select gas group 3 for MAST only",
    )

    cpf_p04676: Optional[float] = Field(
        alias="mcs_select_gas_group_pv4",
        description="(MCS Setup) select gas group 4 for MAST only",
    )

    cpf_p04677: Optional[float] = Field(
        alias="mcs_select_gas_group_pv5",
        description="(MCS Setup) select gas group 5 for MAST only",
    )

    cpf_p04678: Optional[float] = Field(
        alias="mcs_select_gas_group_pv6",
        description="(MCS Setup) select gas group 6 for MAST only",
    )

    cpf_p04679: Optional[float] = Field(
        alias="mcs_select_gas_group_pv7",
        description="(MCS Setup) select gas group 7 for MAST only",
    )

    cpf_p04680: Optional[float] = Field(
        alias="mcs_select_gas_group_pv8",
        description="(MCS Setup) select gas group 8 for MAST only",
    )

    cpf_p04681: Optional[float] = Field(
        alias="mcs_select_gas_group_pv9",
        description="(MCS Setup) select gas group 9 for MAST only",
    )

    cpf_p04833: Optional[float] = Field(
        alias="mcs_select_lvps_tf_power_supply",
        description="(MCS Setup) select TF power supply for MAST only",
    )

    cpf_p04993: Optional[float] = Field(
        alias="mcs_select_cp3s_start_bank",
        description="(MCS Setup) select P3 start bank for MAST only",
    )

    cpf_p05007: Optional[float] = Field(
        alias="mcs_select_fa1", description="Select FA1 for MAST only"
    )

    cpf_p05008: Optional[float] = Field(
        alias="mcs_select_fa2", description="Select FA2 for MAST only"
    )

    cpf_p05009: Optional[float] = Field(
        alias="mcs_select_mfps", description="Select MFPS for MAST only"
    )

    cpf_p05010: Optional[float] = Field(
        alias="mcs_select_efps", description="Select EFPS for MAST only"
    )

    cpf_p05011: Optional[float] = Field(
        alias="mcs_select_sfps", description="Select SFPS for MAST only"
    )

    cpf_p05015: Optional[float] = Field(
        alias="mcs_select_scs4", description="Select SCS4 for MAST only"
    )

    cpf_p05016: Optional[float] = Field(
        alias="mcs_select_fa3", description="Select FA3 for MAST only"
    )

    cpf_p05017: Optional[float] = Field(
        alias="mcs_select_fa4", description="Select FA4 for MAST only"
    )

    cpf_p05025: Optional[float] = Field(
        alias="mcs_select_p1ps", description="Select P1Ps for MAST only"
    )

    cpf_p05027: Optional[float] = Field(
        alias="mcs_select_cp3c_counterpulse_bank",
        description="(MCS Setup) select P3 counterpulse bank for MAST only",
    )

    cpf_p05028: Optional[float] = Field(
        alias="mcs_select_cp4_start_bank",
        description="(MCS Setup) select P4 start bank for MAST only",
    )

    cpf_p05029: Optional[float] = Field(
        alias="mcs_select_cp5_start_bank",
        description="(MCS Setup) select P3 start bank for MAST only",
    )

    cpf_p05030: Optional[float] = Field(
        alias="mcs_select_p3p",
        description="(MCS Setup) select Siemens & GEC switches for P3 plasma Initiation for MAST only",
    )

    cpf_p05032: Optional[float] = Field(
        alias="mcs_select_p4",
        description="(MCS Setup) select P4 Ignitron and Thyristor circuit for MAST only",
    )

    cpf_p05033: Optional[float] = Field(
        alias="mcs_select_p5",
        description="(MCS Setup) select P5 Ignitron and Thyristor circuit for MAST only",
    )

    cpf_p05153: Optional[float] = Field(
        alias="mcs_select_ecrh", description="(MCS Setup) Select ECRH for MAST only"
    )

    cpf_p06000: Optional[float] = Field(
        alias="mcs_select_xmm_os9",
        description="(MCS Setup) Select XMM OS9 (Flags a Critical DATACQ System, \
                                            causes shot to Abort if not ready) for MAST only",
    )

    cpf_p06001: Optional[float] = Field(
        alias="mcs_select_xpc_os9",
        description="(MCS Setup) Select XPC OS9 for MAST only",
    )

    cpf_p06002: Optional[float] = Field(
        alias="mcs_select_xcm_os9",
        description="(MCS Setup) Select XCM OS9 for MAST only",
    )

    cpf_p06003: Optional[float] = Field(
        alias="mcs_select_xmw_os9",
        description="(MCS Setup) Select XMW OS9 for MAST only",
    )

    cpf_p06004: Optional[float] = Field(
        alias="mcs_select_xma_os9",
        description="(MCS Setup) Select XMA OS9 for MAST only",
    )

    cpf_p10963: Optional[float] = Field(
        alias="mcs_ss_nbi_gas",
        description="(MCS Setup) MCS_SS_NBI_gas_species for MAST only",
    )

    cpf_p10964: Optional[float] = Field(
        alias="mcs_sw_nbi_gas_mcs",
        description="(MCS Setup) MCS_SW_NBI_gas_species for MAST only",
    )

    cpf_p12441: Optional[float] = Field(
        alias="mcs_cp3s_volt", description="(MCS Setup) CP3 set volts for MAST only"
    )

    cpf_p12450: Optional[float] = Field(
        alias="mcs_cp3c_volt", description="(MCS Setup) CP3c Set Volts for MAST only"
    )

    cpf_p12451: Optional[float] = Field(
        alias="mcs_cp4s_volt", description="(MCS Setup) CP4 set volts for MAST only"
    )

    cpf_p12452: Optional[float] = Field(
        alias="mcs_cp5s_volt", description="(MCS Setup) CP5 set volts for MAST only"
    )

    cpf_p15202: Optional[float] = Field(
        alias="mcs_additive_gas_pressure",
        description="(MCS Setup) Additive gas pressure of main fueling plenum for MAST only",
    )

    cpf_p15203: Optional[float] = Field(
        alias="mcs_plenum_gas_pressure",
        description="(MCS Setup) Latest gas pressure of main fueling plenum for MAST only",
    )

    cpf_p15209: Optional[float] = Field(
        alias="mcs_tg1_base_pressure",
        description="(MCS Setup) TG1 Base Pressure for MAST only",
    )

    cpf_p15659: Optional[float] = Field(
        alias="mcs_p3_direction",
        description="(MCS Setup) P3 Direction Monitored state of \
                        Polarity-reversing/isolation switches for MAST only",
    )

    cpf_p15660: Optional[float] = Field(
        alias="mcs_p4_direction",
        description="(MCS Setup) P4 direction: \
                        1= Normal Direction (Positive Ip), 3= Open Circuit for MAST only",
    )

    cpf_p15661: Optional[float] = Field(
        alias="mcs_p5_direction",
        description="(MCS Setup) P5 direction: \
                        2= Reverse Direction (Positive Ip) for MAST only",
    )

    cpf_p20000: Optional[float] = Field(
        alias="mcs_ss_number",
        description="(MCS Setup) Shot sequence number for MAST only",
    )

    cpf_p20204: Optional[float] = Field(
        alias="mcs_pshot_gdc_time",
        description="(MCS Setup) Pre-Shot GDC duration for MAST only",
    )

    cpf_p20205: Optional[float] = Field(
        alias="mcs_gdc_start_time",
        description="(MCS Setup) Last GDC start time for MAST only",
    )

    cpf_p20206: Optional[float] = Field(
        alias="mcs_gas_puff_pressure",
        description="(MCS Setup) Inboard Gas Puff Pressure for MAST only",
    )

    cpf_p20207: Optional[float] = Field(
        alias="mcs_gas_puff_start_time",
        description="(MCS Setup) Inboard Gas Puff Start Time Relative to 10s for MAST only",
    )

    cpf_p20208: Optional[float] = Field(
        alias="mcs_gas_puff_duration",
        description="(MCS Setup) Inboard Gas Puff Duration for MAST only",
    )

    cpf_p21010: Optional[float] = Field(
        alias="mcs_p2xo",
        description="(MCS Setup) Param mim430 - P2XO Mode \
                                                    (P2 Reversing Switch Mode: 0= +ve only, 1= -ve only, \
                                                    2= +ve => -ve, 3= -ve => +ve) for MAST only",
    )

    cpf_p21011: Optional[float] = Field(
        alias="mcs_p2xo_start_forward",
        description="(MCS Setup) Param mim430 - P2XO Start Forward \
                                                            (Offset by 5s: enable +ve polarity at time-5s) for MAST only",
    )

    cpf_p21012: Optional[float] = Field(
        alias="mcs_p2xo_start_reverse",
        description="(MCS Setup) Param mim430 - P2XO Start Reverse \
                                                            (Enable -ve polarity at 5s + time) for MAST only",
    )

    cpf_p21021: Optional[float] = Field(
        alias="mcs_tf_flat_top_value",
        description="(MCS Setup) Param mim421 - TF Flat Top set value \
                                                        (Tesla @ R=0.7m) for MAST only",
    )

    cpf_p21022: Optional[float] = Field(
        alias="mcs_tf_flat_top_time",
        description="(MCS Setup) Param mim421 - TF Flat Top set time for MAST only",
    )

    cpf_p21029: Optional[float] = Field(
        alias="mcs_tf_rise_time_value",
        description="(MCS Setup) Param mim421 - TF Rise Time set value \
                                            for MAST only",
    )

    cpf_p21035: Optional[float] = Field(
        alias="mcs_plasma_direction",
        description="(MCS  Setup) Plasma Direction \
                        (1.0 => Positive: Dervived from P3/P4/P5 switch settings (P15659-P15661)) for MAST only",
    )

    cpf_p21037: Optional[float] = Field(
        alias="mcs_p2_config",
        description="(MCS Setup) Required P2 Linkboard config \
                                            number (must match setting in PLC) for MAST only",
    )

    cpf_p21041: Optional[float] = Field(
        alias="mcs_cp3s_start_time",
        description="(MCS Setup) CP3s start time (Offset by 5s) for MAST only",
    )

    cpf_p21042: Optional[float] = Field(
        alias="mcs_cp3c_start_time",
        description="(MCS Setup) CP3c start time (Offset by 5s) for MAST only",
    )

    cpf_p21043: Optional[float] = Field(
        alias="mcs_cp4_start_time",
        description="(MCS Setup) CP4 start time (Offset by 5s) for MAST only",
    )

    cpf_p21044: Optional[float] = Field(
        alias="mcs_p4_ignitron_start_time",
        description="(MCS Setup) Close P4 circuit \
                        ignitron start time (Offset by 5s) for MAST only",
    )

    cpf_p21045: Optional[float] = Field(
        alias="mcs_p4_thyristor_start_time",
        description="(MCS Setup) P4 Circuit \
                        thyristor start time (Offset by 5s) for MAST only",
    )

    cpf_p21046: Optional[float] = Field(
        alias="mcs_cp5_start_time",
        description="(MCS Setup) CP5 Start time (Offset by 5s) for MAST only",
    )

    cpf_p21047: Optional[float] = Field(
        alias="mcs_p5_ignitron_start_time",
        description="(MCS Setup) P5 ignitron start time (Offset by 5s) for MAST only",
    )

    cpf_p21048: Optional[float] = Field(
        alias="mcs_p5_thyristor_start_time",
        description="(MCS Setup) P5 thyristor start time (Offset by 5s) for MAST only",
    )

    cpf_p21051: Optional[float] = Field(
        alias="mcs_mfps_current_limit",
        description="(MCS Setup) MFPS Power supply current limit for MAST only",
    )

    cpf_p21052: Optional[float] = Field(
        alias="mcs_mfps_start_time",
        description="(MCS Setup) MFPS set enable start time (Offset by 5s) for MAST only",
    )

    cpf_p21053: Optional[float] = Field(
        alias="mcs_efps_current_limit",
        description="(MCS Setup) EFPS Power supply current limit for MAST only",
    )

    cpf_p21054: Optional[float] = Field(
        alias="mcs_efps_start_time",
        description="(MCS Setup) EFPS set enable start time (Offset by 5s) for MAST only",
    )

    cpf_p21055: Optional[float] = Field(
        alias="mcs_sfps_current_limit",
        description="(MCS Setup) SFPS power supply current limit for MAST only",
    )

    cpf_p21056: Optional[float] = Field(
        alias="mcs_sfps_start_time",
        description="(MCS Setup) SFPS set enable start time (Offset by 5s) for MAST only",
    )

    cpf_p21075: Optional[float] = Field(
        alias="mcs_mfps_duration",
        description="(MCS Setup) MFPS enable duration for MAST only",
    )

    cpf_p21076: Optional[float] = Field(
        alias="mcs_efps_duration",
        description="(MCS Setup) EFPS enable duration for MAST only",
    )

    cpf_p21077: Optional[float] = Field(
        alias="mcs_sfps_duration",
        description="(MCS Setup) SFPS enable duration for MAST only",
    )

    cpf_p21078: Optional[float] = Field(
        alias="mcs_p1ps_pos_current_limit",
        description="(MCS Setup) P1PS maximum positive current limit for MAST only",
    )

    cpf_p21079: Optional[float] = Field(
        alias="mcs_p1ps_negative_current_limit",
        description="(MCS Setup) P1PS maximum negative current limit for MAST only",
    )

    cpf_p21080: Optional[float] = Field(
        alias="mcs_p1ps_start_time",
        description="(MCS Setup) P1PS enable start time (offset by 5s) for MAST only",
    )

    cpf_p21081: Optional[float] = Field(
        alias="mcs_p1ps_duration",
        description="(MCS Setup) P1PS enable duration for MAST only",
    )

    cpf_p21082: Optional[float] = Field(
        alias="mcs_fa1_start_time",
        description="(MCS Setup) FA1 enable start time (offset by 5s) for MAST only",
    )

    cpf_p21083: Optional[float] = Field(
        alias="mcs_fa1_duration",
        description="(MCS Setup) FA1 enable duration for MAST only",
    )

    cpf_p21084: Optional[float] = Field(
        alias="mcs_fa2_start_time",
        description="(MCS Setup) FA2 enable start time (offset by 5s) for MAST only",
    )

    cpf_p21085: Optional[float] = Field(
        alias="mcs_fa2_duration",
        description="(MCS Setup) FA2 enable duration for MAST only",
    )

    cpf_p21086: Optional[float] = Field(
        alias="mcs_fa3_start_time",
        description="(MCS Setup) FA3 enable start time (offset by 5s) for MAST only",
    )

    cpf_p21087: Optional[float] = Field(
        alias="mcs_fa3_duration",
        description="(MCS Setup) FA3 enable duration for MAST only",
    )

    cpf_p21088: Optional[float] = Field(
        alias="mcs_fa4_start_time",
        description="(MCS Setup) FA4 enable start time (offset by 5s) for MAST only",
    )

    cpf_p21089: Optional[float] = Field(
        alias="mcs_fa4_duration",
        description="(MCS Setup) FA4 enable duration for MAST only",
    )

    cpf_p21092: Optional[float] = Field(
        alias="mcs_scs4_start_time",
        description="(MCS Setup) SCS4 enabled start time used by MBD for MAST only",
    )

    cpf_p21093: Optional[float] = Field(
        alias="mcs_scs4_duration",
        description="(MCS Setup) SCS4 enabled duration for MAST only",
    )

    cpf_abort: Optional[float] = Field(
        alias="shot_abort", description="Shot aborted for MAST and MAST-U"
    )

    cpf_amin_ipmax: Optional[float] = Field(
        alias="generic_minor_radius_max_current",
        description="(Generic) Minor radius at time of peak plasma current for MAST and MAST-U",
    )

    cpf_amin_max: Optional[float] = Field(
        alias="generic_minor_radius",
        description="(Generic) Maximum value of minor radius for MAST and MAST-U",
    )

    cpf_amin_truby: Optional[float] = Field(
        alias="generic_minor_radius_ruby_time",
        description="(Generic) Minor radius at time of Ruby TS for MAST only",
    )

    cpf_area_ipmax: Optional[float] = Field(
        alias="generic_poloidal_area_max_current",
        description="(Generic) poloidal cross-sectional area at time of \
                                                peak plasma current for MAST and MAST-U",
    )

    cpf_area_max: Optional[float] = Field(
        alias="generic_max_poloidal_area",
        description="(Generic) Maximum Poloidal Cross-Sectional Area for MAST and MAST-U",
    )

    cpf_area_truby: Optional[float] = Field(
        alias="generic_poloidal_area_ruby_time",
        description="(Generic) Poloidal Cross-Sectional Area at time of Ruby TS for MAST only",
    )

    cpf_bepmhd_ipmax: Optional[float] = Field(
        alias="generic_beta_poloidal_max_current",
        description="(Generic) Beta poloidal at time of Peak Plasma Current for MAST and MAST-U",
    )

    cpf_bepmhd_max: Optional[float] = Field(
        alias="generic_max_beta_poloidal",
        description="(Generic) Maximum Beta poloidal for MAST and MAST-U",
    )

    cpf_bepmhd_truby: Optional[float] = Field(
        alias="generic_beta_poloidal_ruby_time",
        description="(Generic) Beta poloidal at time of Ruby TS for MAST only",
    )

    cpf_betmhd_ipmax: Optional[float] = Field(
        alias="generic_beta_time_max_current",
        description="(Generic) Beta at time of peak plasma current for MAST and MAST-U",
    )

    cpf_betmhd_max: Optional[float] = Field(
        alias="generic_max_beta_max_current",
        description="(Generic) Maximum beta at time of peak plasma current for MAST and MAST-U",
    )

    cpf_betmhd_truby: Optional[float] = Field(
        alias="generic_beta_ruby_time",
        description="(Generic) Beta at time of ruby TS for MAST only",
    )

    cpf_bt_ipmax: Optional[float] = Field(
        alias="generic_toroidal_max_current",
        description="(Generic) Toroidal field strength at time of peak \
                                                    plasma current for MAST and MAST-U",
    )

    cpf_bt_max: Optional[float] = Field(
        alias="generic_max_toroidal",
        description="(Generic) Maximum Toroidal field strength for MAST and MAST-U",
    )

    cpf_bt_truby: Optional[float] = Field(
        alias="generic_toroidal_ruby_time",
        description="(Generic) Toroidal field strength at time of ruby TS for MAST only",
    )

    cpf_c2ratio: Optional[float] = Field(
        alias="radii_c2ratio",
        description="(Radii) CII Line ratio averaged over Ip flat top from 150ms for MAST and MAST-U",
    )

    cpf_column_temp_in: Optional[float] = Field(
        alias="gas_col_temp_in",
        description="(Gas) centre column inlet temperature for MAST only",
    )

    cpf_column_temp_out: Optional[float] = Field(
        alias="gas_col_temp_out",
        description="(Gas) centre column outlet temperature for MAST only",
    )

    cpf_creation: Optional[datetime.datetime] = Field(
        alias="shot_creation_date",
        description="(Shot metdata) data dictionary entry creation \
                                                                date for MAST and MAST-U",
    )

    cpf_dwmhd_ipmax: Optional[float] = Field(
        alias="generic_dt_energy_max_current",
        description="(Generic) rate of change of total stored energy at \
                                                            time of peak plasma current for MAST and MAST-U",
    )

    cpf_dwmhd_max: Optional[float] = Field(
        alias="generic_dt_total_energy",
        description="(Generic) maximum rate of change of total stored energy \
                                                        for MAST and MAST-U",
    )

    cpf_dwmhd_truby: Optional[float] = Field(
        alias="generic_dt_energy_ruby_time",
        description="(Generic) rate of change of MHD stored energy at \
                                            time of ruby TS for MAST only",
    )

    cpf_enbi_max_ss: Optional[float] = Field(
        alias="nbi_energy_ss_max_power",
        description="(NBI) injection energy from SS beam at time of peak power \
                                            for MAST and MAST-U",
    )

    cpf_enbi_max_sw: Optional[float] = Field(
        alias="nbi_energy_sw_max_power",
        description="(NBI) injection energy from SW beam at time of peak power \
                                            for MAST and MAST-U",
    )

    cpf_exp_date: Optional[datetime.datetime] = Field(
        alias="shot_experiment_date",
        description="MAST shot experiment pulse date for MAST and MAST-U",
    )

    cpf_exp_number: Optional[int] = Field(
        alias="shot_experiment_number",
        description="MAST shot experiment pulse number for MAST and MAST-U",
    )

    cpf_exp_time: Optional[datetime.time] = Field(
        alias="shot_experiment_time",
        description="MAST shot experiment pulse time for MAST and MAST-U",
    )

    cpf_gdc_duration: Optional[float] = Field(
        alias="shot_glow_discharge_duration",
        description="Shot glow discharge duration for both",
    )

    cpf_gdc_time: Optional[float] = Field(
        alias="shot_glow_discharge_time",
        description="Shot glow discharge time for both",
    )

    cpf_ibgas_pressure: Optional[float] = Field(
        alias="gas_inboard_pressure_pre_pulse",
        description="Inboard gas pressure prior to pulse for MAST only",
    )

    cpf_ip_av: Optional[float] = Field(
        alias="plasma_time_avg_current",
        description="(Plasma) Time averaged plasma current during flat-top for MAST and MAST-U",
    )

    cpf_ip_max: Optional[float] = Field(
        alias="plasma_max_current",
        description="(Plasma) Maximum value of plasma current for MAST and MAST-U",
    )

    cpf_jnbi_ipmax: Optional[float] = Field(
        alias="nbi_injected_energy_max_current",
        description="(NBI) injected energy from \
                        SS+SW beams at time of peak current for MAST and MAST-U",
    )

    cpf_jnbi_ipmax_ss: Optional[float] = Field(
        alias="nbi_injected_energy_ss_max_current",
        description="(NBI) injected energy from \
                        SS beams at time of peak current for MAST and MAST-U",
    )

    cpf_jnbi_ipmax_sw: Optional[float] = Field(
        alias="nbi_injected_energy_ss_max_current",
        description="(NBI) injected energy from \
                        SW beams at time of peak current for MAST and MAST-U",
    )

    cpf_jnbi_max: Optional[float] = Field(
        alias="nbi_injected_energy_max",
        description="(NBI) injected energy from SS+SW \
                        beams at time of peak power for MAST and MAST-U",
    )

    cpf_jnbi_max_ss: Optional[float] = Field(
        alias="nbi_energy_ss_max_current",
        description="(NBI) injection energy from SS \
                        beam at time of peak power for MAST and MAST-U",
    )

    cpf_jnbi_max_sw: Optional[float] = Field(
        alias="nbi_energy_sw_max_current",
        description="(NBI) injection energy from SW \
                        beam at time of peak power for MAST and MAST-U",
    )

    cpf_jnbi_total: Optional[float] = Field(
        alias="nbi_total_injected_energy",
        description="Total NBI injected energy from SS+SW beams for MAST and MAST-U",
    )

    cpf_jnbi_total_ss: Optional[float] = Field(
        alias="nbi_total_injected_energy_ss",
        description="Total NBI Injected Energy from SS Beam for MAST and MAST-U",
    )

    cpf_jnbi_total_sw: Optional[float] = Field(
        alias="nbi_total_injected_energy_sw",
        description="Total NBI Injected Energy from SW Beam for MAST and MAST-U",
    )

    cpf_jnbi_truby: Optional[float] = Field(
        alias="nbi_injected_energy_ruby_time",
        description="(NBI) Injected Energy from SS+SW Beams at time of Ruby TS for MAST only",
    )

    cpf_jnbi_truby_ss: Optional[float] = Field(
        alias="nbi_injected_energy_ss_ruby_time",
        description="NBI Injected Energy from SW Beam at time of Ruby TS for MAST only",
    )

    cpf_jnbi_truby_sw: Optional[float] = Field(
        alias="nbi_injected_energy_sw_ruby_time",
        description="(NBI) Injected Energy from SW Beam at time of Ruby TS for MAST only",
    )

    cpf_johm_ipmax: Optional[float] = Field(
        alias="ohmnic_energy_max_current",
        description="Ohmic Heating Energy Input at time of Peak Current for MAST and MAST-U",
    )

    cpf_johm_max: Optional[float] = Field(
        alias="ohmnic_energy_max_heating",
        description="Ohmic Heating Energy Input at time of Maximum Ohmic Heating for MAST and MAST-U",
    )

    cpf_johm_total: Optional[float] = Field(
        alias="ohmnic_energy_total",
        description="Total Ohmic Heating Energy Input for MAST and MAST-U",
    )

    cpf_johm_truby: Optional[float] = Field(
        alias="ohmnic_energy_ruby_time",
        description="Ohmic Heat Energy Input at time of Ruby TS for MAST only",
    )

    cpf_kappa_ipmax: Optional[float] = Field(
        alias="generic_plasma_elongation_max_current",
        description="(Generic) Plasma Elongation at time of Peak \
                        Plasma Current for MAST and MAST-U",
    )

    cpf_kappa_max: Optional[float] = Field(
        alias="generic_plasma_elongation_max",
        description="(Generic) Maximum value of Plasma Elongation \
                        for MAST and MAST-U",
    )

    cpf_kappa_truby: Optional[float] = Field(
        alias="generic_plasma_elongation_ruby_time",
        description="(Generic) Plasma Elongation at time of Ruby TS for MAST only",
    )

    cpf_li_2_ipmax: Optional[float] = Field(
        alias="equi_li2_max_current",
        description="(Equilibrium) li(2) at time of Peak Current for MAST and MAST-U",
    )

    cpf_li_2_max: Optional[float] = Field(
        alias="equi_max_li2",
        description="(Equilibrium) li(2) Maximum value for MAST and MAST-U",
    )

    cpf_li_2_truby: Optional[float] = Field(
        alias="equi_li2_ruby_time",
        description="(Equilibrium) li(2) Maximum value for MAST and MAST-U",
    )

    cpf_li_3_ipmax: Optional[float] = Field(
        alias="equi_li3_max_current",
        description="(Equilibrium) li(3) at time of Peak Current for MAST and MAST-U",
    )

    cpf_li_3_max: Optional[float] = Field(
        alias="equi_max_li3",
        description="(Equilibrium) li(3) Maximum value for MAST and MAST-U",
    )

    cpf_li_3_truby: Optional[float] = Field(
        alias="equi_li3_ruby_time",
        description="(Equilibrium) li(3) at time of Ruby TS for MAST only",
    )

    cpf_log_base_pressure: Optional[float] = Field(
        alias="gas_tg1_pressure_ps",
        description="(Gas) TG1 Base Pressure prior to Shot for MAST only",
    )

    cpf_ndl_co2_ipmax: Optional[float] = Field(
        alias="thomson_density_line_max_current",
        description="(Thomson) Electron Density Line Integral at time \
                        of Peak Plasma Current for MAST and MAST-U",
    )

    cpf_ndl_co2_max: Optional[float] = Field(
        alias="thomson_max_density_line",
        description="(Thomson) Maximum Electron Density Line Integral \
                        observed by CO2 Interferometer for MAST and MAST-U",
    )

    cpf_ndl_co2_truby: Optional[float] = Field(
        alias="thomson_density_line_ruby_time",
        description="(Thomson) Electron Density Line Integral at time \
                        of Ruby TS for MAST only",
    )

    cpf_ne0_ipmax: Optional[float] = Field(
        alias="thomson_density_max_current",
        description="(Thomson) Core Electron Density (Nd.YAG) at time of \
                        Peak Current for MAST and MAST-U",
    )

    cpf_ne0_max: Optional[float] = Field(
        alias="thomson_density_max",
        description="(Thomson) Peak Core Electron Density (Nd.YAG) for MAST and MAST-U",
    )

    cpf_ne0_truby: Optional[float] = Field(
        alias="thomson_density_ruby_time",
        description="(Thomson) Core Electron Density (Nd.YAG) at time of Ruby TS for MAST only",
    )

    cpf_ne0ratio_ipmax: Optional[float] = Field(
        alias="thomson_ne0_rat_line_avg_ne",
        description="(Thomson) Ratio of ne0 to line average ne for MAST and MAST-U",
    )

    cpf_ne0ruby: Optional[float] = Field(
        alias="thomson_density_ruby_time",
        description="(Thomson) Core Electron Density (Nd.YAG) at time of Ruby TS for MAST only",
    )

    cpf_ne_bar_ipmax: Optional[float] = Field(
        alias="thomson_line_avg_density_co2",
        description="(Thomson) Mid-plane line average electron density \
                                                            from CO2 interferometer for MAST and MAST-U",
    )

    cpf_ne_yag_bar_ipmax: Optional[float] = Field(
        alias="thomson_line_avg_density_co2",
        description="(Thomson) Mid-plane line average electron density from CO2 \
                                                                    interferometer for MAST and MAST-U",
    )

    cpf_ngreenwald_ipmax: Optional[float] = Field(
        alias="thomson_greenwald_density_limit",
        description="(Thomson) Greenwald Density Limit for MAST and MAST-U",
    )

    cpf_ngreenwaldratio_ipmax: Optional[float] = Field(
        alias="thomson_greenwald_rat_line_avg_density",
        description="(Thomson) Ratio of Greenwald density limit to mid-plane \
                                                                        line averaged electron density for MAST and MAST-U",
    )

    cpf_o2ratio: Optional[float] = Field(
        alias="rad_o2ratio",
        description="(Radii) OII Line Ratio averaged over Ip flat top from 150ms \
                                                                for MAST and MAST-U",
    )

    cpf_objective: Optional[str] = Field(
        alias="shot_objective",
        description="Shot Scientific Objective for MAST and MAST-U",
    )

    cpf_pe0_ipmax: Optional[float] = Field(
        alias="thomson_pressure_max_current",
        description="(Thomsom) Core Electron Pressure (Nd.YAG) at time of Peak \
                                                                Plasma Current for MAST and MAST-U",
    )

    cpf_pe0_max: Optional[float] = Field(
        alias="thomson_pressure_max",
        description="(Thomsom) Maximum value of Core Electron Pressure (Nd.YAG) \
                                                                    for MAST and MAST-U",
    )

    cpf_pe0_truby: Optional[float] = Field(
        alias="thomson_pressure_ruby_time",
        description="(Thomsom) Core Electron Pressure (Nd.YAG) at time of Ruby TS \
                                                                for MAST only",
    )

    cpf_pe0ruby: Optional[float] = Field(
        alias="thomson_pressure_ruby",
        description="(Thomsom) Ruby TS Core Electron Pressure for MAST only",
    )

    cpf_pic: Optional[str] = Field(
        alias="shot_physicist",
        description="(Shot) physicist in charge for MAST and MAST-U",
    )

    cpf_pnbi_ipmax: Optional[float] = Field(
        alias="nbi_power_max_current",
        description="(NBI) Power from SS+SW Beams at time of Peak Current \
                                                                for MAST and MAST-U",
    )

    cpf_pnbi_ipmax_ss: Optional[float] = Field(
        alias="nbi_power_ss_max_current",
        description="(NBI) Power from SS Beam at time of Peak Current \
                                                            for MAST and MAST-U",
    )

    cpf_pnbi_ipmax_sw: Optional[float] = Field(
        alias="nbi_power_max_current",
        description="(NBI) Power from SW Beam at time of Peak Current \
                                                            for MAST and MAST-U",
    )

    cpf_pnbi_max: Optional[float] = Field(
        alias="nbi_power_max_power",
        description="(NBI) Power from SS+SW Beams at time of Peak power \
                                                        for MAST and MAST-U",
    )

    cpf_pnbi_max_ss: Optional[float] = Field(
        alias="nbi_power_max_ss",
        description="Peak NBI Power from SS Beam for MAST and MAST-U",
    )

    cpf_pnbi_max_sw: Optional[float] = Field(
        alias="nbi_power_max_sw",
        description="Peak NBI Power from SW Beam for MAST and MAST-U",
    )

    cpf_pnbi_truby: Optional[float] = Field(
        alias="nbi_power_ruby_time",
        description="(NBI) Power from SS+SW Beams at time of Ruby TS for MAST and MAST-U",
    )

    cpf_pnbi_truby_ss: Optional[float] = Field(
        alias="nbi_power_truby_ss",
        description="(NBI) Power from SS Beam at time of Ruby TS for MAST and MAST-U",
    )

    cpf_pnbi_truby_sw: Optional[float] = Field(
        alias="nbi_power_truby_sw",
        description="(NBI) Power from SW Beam at time of Ruby TS for MAST and MAST-U",
    )

    cpf_pohm_ipmax: Optional[float] = Field(
        alias="ohmnic_heating_max_current",
        description="Ohmic Heating Rate at time of Peak Current for MAST and MAST-U",
    )

    cpf_pohm_max: Optional[float] = Field(
        alias="ohmnic_max_heating",
        description="Maximum Ohmic Heating Rate for MAST and MAST-U",
    )

    cpf_pohm_truby: Optional[float] = Field(
        alias="ohmnic_heating_ruby_time",
        description="Ohmic Heating Rate at time of Ruby TS for MAST only",
    )

    cpf_postshot: Optional[str] = Field(
        alias="shot_postshot_comment",
        description="Session Leaders Post-Shot Comment for MAST and MAST-U",
    )

    cpf_prad_ipmax: Optional[float] = Field(
        alias="generic_rad_power_loss_max_current",
        description="(Generic) Total Radiated Power Loss at time of \
                                                                Peak Plasma Current for MAST and MAST-U",
    )

    cpf_prad_max: Optional[float] = Field(
        alias="generic_max_power_loss",
        description="(Generic) Maximum Total Radiated Power Loss for MAST and MAST-U",
    )

    cpf_prad_truby: Optional[float] = Field(
        alias="generic_power_loss_ruby_time",
        description="(Generic) Total Radiated Power Loss at time of Ruby TS for MAST only",
    )

    cpf_pradne2: Optional[float] = Field(
        alias="rad_flat_top_power_rat_avg_line_density",
        description="(Radii) Flat Top Ratio of Power Radiated to Line Density squared \
                                                        averaged over Ip flat top from 150ms for MAST and MAST-U",
    )

    cpf_preshot: Optional[str] = Field(
        alias="shot_preshot_comment",
        description="Session Leaders Pre-Shot Comment for MAST and MAST-U",
    )

    cpf_program: Optional[str] = Field(
        alias="shot_program",
        description="(Shot) Scientific Program for MAST and MAST-U",
    )

    cpf_pulno: Optional[float] = Field(
        alias="shot_pulse_number",
        description="(Ghot) MAST Experiment Pulse Number for MAST and MAST-U",
    )

    cpf_q95_ipmax: Optional[float] = Field(
        alias="generic_q95_max_current",
        description="(Generic) q-95 at time of Peak Plasma Current for MAST and MAST-U",
    )

    cpf_q95_min: Optional[float] = Field(
        alias="generic_min_q95",
        description="(Generic) Minimum value of q-95 for MAST and MAST-U",
    )

    cpf_q95_truby: Optional[float] = Field(
        alias="generic_q95_ruby_time", description="(Generic) q-95 at time of Ruby TS"
    )

    cpf_reference: Optional[float] = Field(
        alias="shot_reference", description="(Shot) Reference shot for MAST and MAST-U"
    )

    cpf_rgeo_ipmax: Optional[float] = Field(
        alias="generic_geo_radius_max_current",
        description="(Generic) geometrical center major radius at time of \
                                                peak plasma current for MAST and MAST-U",
    )

    cpf_rgeo_max: Optional[float] = Field(
        alias="generic_max_geo_radius",
        description="(Generic) Maximum value of Geometrical Center \
                                                                    Major Radius for MAST and MAST-U",
    )

    cpf_rgeo_truby: Optional[float] = Field(
        alias="generic_geo_radius_ruby_time",
        description="(Generic) geometrical Center Major Radius at time \
                                                            of Ruby TS for MAST and MAST-U",
    )

    cpf_rinner_da: Optional[float] = Field(
        alias="radii_rinner_radius_d_alpha",
        description="(Radii) rinner major Radius from Visible D_Alpha Light \
                                                            for MAST and MAST-U",
    )

    cpf_rinner_efit: Optional[float] = Field(
        alias="radii_rinner_radius_efit",
        description="(Radii) rinner major Radius from EFIT Equilibrium \
                                                            for MAST and MAST-U",
    )

    cpf_rmag_efit: Optional[float] = Field(
        alias="radii_magnetic__radius_efit",
        description="(Radii) magnetic Axis major Radius from EFIT Equilibrium \
                                                            for MAST and MAST-U",
    )

    cpf_router_da: Optional[float] = Field(
        alias="radii_router_radius_d_alpha",
        description="(Radii) router major Radius from Visible D_Alpha Light \
                                                            for MAST and MAST-U",
    )

    cpf_router_efit: Optional[float] = Field(
        alias="radii_router_radius_efit",
        description="(Radii) router major Radius from EFIT Equilibrium \
                                                            for MAST and MAST-U",
    )

    cpf_sarea_ipmax: Optional[float] = Field(
        alias="radii_s_area_max_current",
        description="(Generic) Total Surface Area at time of Peak Plasma \
                                                            Current for MAST and MAST-U",
    )

    cpf_sarea_max: Optional[float] = Field(
        alias="generic_s_area_max",
        description="(Generic) maximum Total Surface Area for MAST and MAST-U",
    )

    cpf_sarea_truby: Optional[float] = Field(
        alias="generic_s_area_ruby_time",
        description="(Generic) total Surface Area at time of Ruby TS for MAST only",
    )

    cpf_sl: Optional[str] = Field(
        alias="shot_session_leader",
        description="(Shot) session leader for MAST and MAST-U",
    )

    cpf_sc: Optional[str] = Field(nullable=True)

    cpf_summary: Optional[str] = Field(
        alias="shot_summary", description="(Shot) session summary for MAST and MAST-U"
    )

    cpf_tamin_max: Optional[float] = Field(
        alias="generic_min_radius_max_plasma",
        description="(Generic) Time of Maximum Plasma Minor Radius for MAST and MAST-U",
    )

    cpf_tarea_max: Optional[float] = Field(
        alias="generic_max_poloidal_area",
        description="(Generic) Time of Maximum Poloidal Cross-Sectional Area \
                                                                    for MAST and MAST-U",
    )

    cpf_tautot_ipmax: Optional[float] = Field(
        alias="generic_energy_time_max_current",
        description="(Generic) Energy Confinement Time at time of Peak Plasma Current \
                                                                    for MAST and MAST-U",
    )

    cpf_tautot_max: Optional[float] = Field(
        alias="generic_max_energy_time",
        description="(Generic) Maximum value of Energy Confinement Time for MAST and MAST-U",
    )

    cpf_tautot_truby: Optional[float] = Field(
        alias="generic_energy_time_ruby_time",
        description="(Generic) Energy Confinement Time at time of Ruby TS for MAST and MAST-U",
    )

    cpf_tbepmhd_max: Optional[float] = Field(
        alias="generic_max_beta_poloidal_mhd",
        description="(Generic) Time of Maximum Beta Poloidal MHD for MAST and MAST-U",
    )

    cpf_tbetmhd_max: Optional[float] = Field(
        alias="generic_max_beta_mhd",
        description="(Generic) Time of Maximum Beta MHD for MAST and MAST-U",
    )

    cpf_tbt_max: Optional[float] = Field(
        alias="generic_max_toroidal_time",
        description="(Generic) Time of Maximum Toroidal Magnetic Field Strength \
                                                                    for MAST and MAST-U",
    )

    cpf_tdwmhd_max: Optional[float] = Field(
        alias="generic_max_dt_mhd_energy_time",
        description="(Generic) Time of Maximum Rate of Change of MHD Stored Energy \
                                                                    for MAST and MAST-U",
    )

    cpf_te0_ipmax: Optional[float] = Field(
        alias="thomson_temp_max_current",
        description="(Thomoson) Core Electron Temperature (Nd.YAG) at time of \
                                                                        Peak Current for MAST and MAST-U",
    )

    cpf_te0_max: Optional[float] = Field(
        alias="thomson_temp_max",
        description="(Thomson) Peak Core Electron Temperature (Nd.YAG) \
                                                                        for MAST and MAST-U",
    )

    cpf_te0_truby: Optional[float] = Field(
        alias="thomson_temp_ruby_time",
        description="(Thomson) Core Electron Temperature (Nd.YAG) at \
                                                                            time of Ruby TS for MAST only",
    )

    cpf_te0ratio_ipmax: Optional[float] = Field(
        alias="thomson_temp_rat_line_avg_temp",
        description="(Thomson) ratio of Core Electron Temperature to line \
                                                            average Te for MAST and MAST-U",
    )

    cpf_te0ruby: Optional[float] = Field(
        alias="thomson_temp_ruby",
        description="(Thomson) Ruby TS Core Electron Temperature for MAST only",
    )

    cpf_te_yag_bar_ipmax: Optional[float] = Field(
        alias="thomson_yag_line_avg_temp",
        description="Mid-plane line average electron temperature from \
                                                                            YAG Thomson scattering for MAST and MAST-U",
    )

    cpf_tend: Optional[float] = Field(
        alias="plasma_end_time",
        description="(Plasma) current end time for MAST and MAST-U",
    )

    cpf_tend_ibgas: Optional[float] = Field(
        alias="gas_puff_end_time", description="Inboard Gas Puff End Time for MAST only"
    )

    cpf_tend_nbi: Optional[float] = Field(
        alias="nbi_end_time", description="(NBI) end time for MAST and MAST-U"
    )

    cpf_tend_nbi_ss: Optional[float] = Field(
        alias="nbi_end_time_ss", description="SS NBI end time for MAST and MAST-U"
    )

    cpf_tend_nbi_sw: Optional[float] = Field(
        alias="nbi_end_time_ss", description="SW NBI end time for MAST and MAST-U"
    )

    cpf_term_code: Optional[float] = Field(
        alias="shot_end_code",
        description="(Plasma) shot termination reason code for MAST and MASt-U",
    )

    cpf_tftend: Optional[float] = Field(
        alias="plasma_flat_top_end_time",
        description="(Plasma) Current Flat-Top End Time for MAST and MAST-U",
    )

    cpf_tftstart: Optional[float] = Field(
        alias="plasma_flat_top_start_time",
        description="(Plasma) Current Flat-Top Start Time for MAST and MAST-U",
    )

    cpf_tipmax: Optional[float] = Field(
        alias="plasma_max_plasma_current_time",
        description="(Plasma) Time of Maximum Plasma Current for MAST and MAST-U",
    )

    cpf_tkappa_max: Optional[float] = Field(
        alias="generic_max_plasma_elongation_time",
        description="(Generic) Time of Maximum Plasma Elongation for MAST and MAST-U",
    )

    cpf_tli_2_max: Optional[float] = Field(
        alias="equi_max_li2_time",
        description="(Equilibrium) time of Maximum li(2) for MAST and MAST-U",
    )

    cpf_tli_3_max: Optional[float] = Field(
        alias="equi_max_li3_time",
        description="(Equilibrium) time of Maximum li(3) for MAST and MAST-U",
    )

    cpf_tndl_co2_max: Optional[float] = Field(
        alias="thomson_max_density_line_time",
        description="(Thomson) Time of Maximum Electron Density Line Integral \
                                                                for MAST and MAST-U",
    )

    cpf_tne0_max: Optional[float] = Field(
        alias="thomson_max_density_time",
        description="(thomson) Time of Maximum Core Electron Density (from Nd.YAG TS) \
                                                                for MAST and MAST-U",
    )

    cpf_tpe0_max: Optional[float] = Field(
        alias="thomson_max_pressure_time",
        description="(Thomson) Time of Maximum Core Electron Pressure (from Nd.YAG TS) \
                                                                    for MAST and MAST-U",
    )

    cpf_tpnbi_max: Optional[float] = Field(
        alias="nbi_max_power_time",
        description="(NBI) Time of Maximum NB Power for MAST and MAST-U",
    )

    cpf_tpnbi_max_ss: Optional[float] = Field(
        alias="nbi_max_ss_power_time",
        description="(NBI) Time of Maximum SS NBI Power for MAST and MAST-U",
    )

    cpf_tpnbi_max_sw: Optional[float] = Field(
        alias="nbi_max_sw_power_time",
        description="(NBI) Time of Maximum SW NBI Power for MAST and MAST-U",
    )

    cpf_tpohm_max: Optional[float] = Field(
        alias="ohmnic_max_heating_time",
        description="(NBI) Time of Maximum Ohmic Heating for MAST and MAST-U",
    )

    cpf_tprad_max: Optional[float] = Field(
        alias="generic_max_plasma_power_loss_time",
        description="(Generic) Time of Maximum Plasma Radiated Power Loss for MAST and MAST-U",
    )

    cpf_tq95_min: Optional[float] = Field(
        alias="generic_min_q95_time",
        description="(Generic) Time of Minimum q 95 for MAST and MAST-U",
    )

    cpf_trgeo_max: Optional[float] = Field(
        alias="generic_max_geo_major_radius_time",
        description="(Generic) Time of Maximum Geometrical Mid-plane Center Major Radius \
                                           for MAST and MAST-U",
    )

    cpf_truby: Optional[float] = Field(
        alias="thomson_ruby_time",
        description="(Thomson) Ruby Thomson Scattering Time for MAST only",
    )

    cpf_tsarea_max: Optional[float] = Field(
        alias="generic_max_plasma_s_area_time",
        description="(Generic) Time of Maximum Plasma Surface Area for MAST and MAST-U",
    )

    cpf_tstart: Optional[float] = Field(
        alias="plasma_flat_top_start_time",
        description="(Plasma) Current Flat-Top Start Time for MAST and MAST-U",
    )

    cpf_tstart_ibgas: Optional[float] = Field(
        alias="gas_puff_start_time",
        description="Inboard Gas Puff Start Time for MAST only",
    )

    cpf_tstart_nbi: Optional[float] = Field(
        alias="nbi_start_time", description="(NBI) Start Time for MAST and MAST-U"
    )

    cpf_tstart_nbi_ss: Optional[float] = Field(
        alias="nbi_ss_start_time", description="SS NBI Start Time for MAST and MAST-U"
    )

    cpf_tstart_nbi_sw: Optional[float] = Field(
        alias="nbi_sw_start_time", description="SW NBI Start Time for MAST and MAST-U"
    )

    cpf_ttautot_max: Optional[float] = Field(
        alias="generic_max_total_energy_time",
        description="(Generic) Time of Maximum Total Energy Confinement Time for MAST and MAST-U",
    )

    cpf_tte0_max: Optional[float] = Field(
        alias="thomson_max_temp_time",
        description="(Thomson) Time of Maximum Core Electron Temperature (from Nd.YAG TS) \
                                                                    for MAST and MAST-U",
    )

    cpf_tvol_max: Optional[float] = Field(
        alias="generic_max_plasma_vol_time",
        description="(Generic) Time of Maximum Plasma Volume for MAST and MAST-U",
    )

    cpf_twmhd_max: Optional[float] = Field(
        alias="generic_max_mhd_energy_time",
        description="(Generic) Time of Maximum MHD Stored Energy for MAST and MAST-U",
    )

    cpf_tzeff_max: Optional[float] = Field(
        alias="generic_max_plasma_zeff_time",
        description="(Generic) Time of Maximum Plasma Z-Effective for MAST and MAST-U",
    )

    cpf_useful: Optional[float] = Field(
        alias="shot_useful", description="Useful Shot for MAST and MAST-U"
    )

    cpf_vol_ipmax: Optional[float] = Field(
        alias="generic_plasma_vol_max_current",
        description="(Generic) Plasma Volume at time of Peak Plasma Current for MAST and MAST-U",
    )

    cpf_vol_max: Optional[float] = Field(
        alias="generic_max_plasma_vol",
        description="(Generic) Maximum Plasma Volume for MAST and MAST-U",
    )

    cpf_vol_truby: Optional[float] = Field(
        alias="generic_plasma_vol_ruby_time",
        description="(Generic) Plasma Volume at time of Ruby TS for MAST only",
    )

    cpf_wmhd_ipmax: Optional[float] = Field(
        alias="generic_energy_current_max",
        description="(Generic) Stored Energy at time of Peak Plasma Current \
                                                                        for MAST and MAST-U",
    )

    cpf_wmhd_max: Optional[float] = Field(
        alias="generic_energy_max",
        description="(Generic) Maximum Stored Energy for MAST and MAST-U",
    )

    cpf_wmhd_truby: Optional[float] = Field(
        alias="generic_energy_ruby_time",
        description="(Generic) Stored Energy at time of Ruby TS for MAST only",
    )

    cpf_zeff_ipmax: Optional[float] = Field(
        alias="generic_plasma_zeff_max_current",
        description="(Generic) Plasma Z-Effective at time of Peak Plasma Current \
                                                                            for MAST and MAST-U",
    )

    cpf_zeff_max: Optional[float] = Field(
        alias="generic_plasma_zeff_max",
        description="(Generic) Maximum Plasma Z-Effective for MAST and MASt-U",
    )

    cpf_zeff_truby: Optional[float] = Field(
        alias="generic_plasma_zeff_ruby_time",
        description="(Generic) Plasma Z-Effective at time of Ruby TS for MAST only",
    )

    cpf_zmag_efit: Optional[float] = Field(
        alias="rad_magnetic_height_efit",
        description="(Radii) Magnetic Axis height above Mid-Plane from EFIT Equilibrium \
                                                                            for MAST and MAST-U",
    )


class Level2ShotModel(SQLModel, table=True):
    __tablename__ = "level2_shots"

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

    scenario: Optional[int] = Field(description="The scenario used for this shot.")

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

    signals: List["Level2SignalModel"] = Relationship(back_populates="shot")
    sources: List["Level2SourceModel"] = Relationship(back_populates="shot")

    cpf_p03249: Optional[float] = Field(
        alias="mcs_gdc_pre_shot",
        description="(MCS Setup) GDC completed prior to shot for MAST only",
    )

    cpf_p04673: Optional[float] = Field(
        alias="mcs_select_gas_group_pv1",
        description="(MCS Setup) select gas group 1 for MAST only",
    )

    cpf_p04674: Optional[float] = Field(
        alias="mcs_select_gas_group_pv2",
        description="(MCS Setup) select gas group 2 for MAST only",
    )

    cpf_p04675: Optional[float] = Field(
        alias="mcs_select_gas_group_pv3",
        description="(MCS Setup) select gas group 3 for MAST only",
    )

    cpf_p04676: Optional[float] = Field(
        alias="mcs_select_gas_group_pv4",
        description="(MCS Setup) select gas group 4 for MAST only",
    )

    cpf_p04677: Optional[float] = Field(
        alias="mcs_select_gas_group_pv5",
        description="(MCS Setup) select gas group 5 for MAST only",
    )

    cpf_p04678: Optional[float] = Field(
        alias="mcs_select_gas_group_pv6",
        description="(MCS Setup) select gas group 6 for MAST only",
    )

    cpf_p04679: Optional[float] = Field(
        alias="mcs_select_gas_group_pv7",
        description="(MCS Setup) select gas group 7 for MAST only",
    )

    cpf_p04680: Optional[float] = Field(
        alias="mcs_select_gas_group_pv8",
        description="(MCS Setup) select gas group 8 for MAST only",
    )

    cpf_p04681: Optional[float] = Field(
        alias="mcs_select_gas_group_pv9",
        description="(MCS Setup) select gas group 9 for MAST only",
    )

    cpf_p04833: Optional[float] = Field(
        alias="mcs_select_lvps_tf_power_supply",
        description="(MCS Setup) select TF power supply for MAST only",
    )

    cpf_p04993: Optional[float] = Field(
        alias="mcs_select_cp3s_start_bank",
        description="(MCS Setup) select P3 start bank for MAST only",
    )

    cpf_p05007: Optional[float] = Field(
        alias="mcs_select_fa1", description="Select FA1 for MAST only"
    )

    cpf_p05008: Optional[float] = Field(
        alias="mcs_select_fa2", description="Select FA2 for MAST only"
    )

    cpf_p05009: Optional[float] = Field(
        alias="mcs_select_mfps", description="Select MFPS for MAST only"
    )

    cpf_p05010: Optional[float] = Field(
        alias="mcs_select_efps", description="Select EFPS for MAST only"
    )

    cpf_p05011: Optional[float] = Field(
        alias="mcs_select_sfps", description="Select SFPS for MAST only"
    )

    cpf_p05015: Optional[float] = Field(
        alias="mcs_select_scs4", description="Select SCS4 for MAST only"
    )

    cpf_p05016: Optional[float] = Field(
        alias="mcs_select_fa3", description="Select FA3 for MAST only"
    )

    cpf_p05017: Optional[float] = Field(
        alias="mcs_select_fa4", description="Select FA4 for MAST only"
    )

    cpf_p05025: Optional[float] = Field(
        alias="mcs_select_p1ps", description="Select P1Ps for MAST only"
    )

    cpf_p05027: Optional[float] = Field(
        alias="mcs_select_cp3c_counterpulse_bank",
        description="(MCS Setup) select P3 counterpulse bank for MAST only",
    )

    cpf_p05028: Optional[float] = Field(
        alias="mcs_select_cp4_start_bank",
        description="(MCS Setup) select P4 start bank for MAST only",
    )

    cpf_p05029: Optional[float] = Field(
        alias="mcs_select_cp5_start_bank",
        description="(MCS Setup) select P3 start bank for MAST only",
    )

    cpf_p05030: Optional[float] = Field(
        alias="mcs_select_p3p",
        description="(MCS Setup) select Siemens & GEC switches for P3 plasma Initiation for MAST only",
    )

    cpf_p05032: Optional[float] = Field(
        alias="mcs_select_p4",
        description="(MCS Setup) select P4 Ignitron and Thyristor circuit for MAST only",
    )

    cpf_p05033: Optional[float] = Field(
        alias="mcs_select_p5",
        description="(MCS Setup) select P5 Ignitron and Thyristor circuit for MAST only",
    )

    cpf_p05153: Optional[float] = Field(
        alias="mcs_select_ecrh", description="(MCS Setup) Select ECRH for MAST only"
    )

    cpf_p06000: Optional[float] = Field(
        alias="mcs_select_xmm_os9",
        description="(MCS Setup) Select XMM OS9 (Flags a Critical DATACQ System, \
                                            causes shot to Abort if not ready) for MAST only",
    )

    cpf_p06001: Optional[float] = Field(
        alias="mcs_select_xpc_os9",
        description="(MCS Setup) Select XPC OS9 for MAST only",
    )

    cpf_p06002: Optional[float] = Field(
        alias="mcs_select_xcm_os9",
        description="(MCS Setup) Select XCM OS9 for MAST only",
    )

    cpf_p06003: Optional[float] = Field(
        alias="mcs_select_xmw_os9",
        description="(MCS Setup) Select XMW OS9 for MAST only",
    )

    cpf_p06004: Optional[float] = Field(
        alias="mcs_select_xma_os9",
        description="(MCS Setup) Select XMA OS9 for MAST only",
    )

    cpf_p10963: Optional[float] = Field(
        alias="mcs_ss_nbi_gas",
        description="(MCS Setup) MCS_SS_NBI_gas_species for MAST only",
    )

    cpf_p10964: Optional[float] = Field(
        alias="mcs_sw_nbi_gas_mcs",
        description="(MCS Setup) MCS_SW_NBI_gas_species for MAST only",
    )

    cpf_p12441: Optional[float] = Field(
        alias="mcs_cp3s_volt", description="(MCS Setup) CP3 set volts for MAST only"
    )

    cpf_p12450: Optional[float] = Field(
        alias="mcs_cp3c_volt", description="(MCS Setup) CP3c Set Volts for MAST only"
    )

    cpf_p12451: Optional[float] = Field(
        alias="mcs_cp4s_volt", description="(MCS Setup) CP4 set volts for MAST only"
    )

    cpf_p12452: Optional[float] = Field(
        alias="mcs_cp5s_volt", description="(MCS Setup) CP5 set volts for MAST only"
    )

    cpf_p15202: Optional[float] = Field(
        alias="mcs_additive_gas_pressure",
        description="(MCS Setup) Additive gas pressure of main fueling plenum for MAST only",
    )

    cpf_p15203: Optional[float] = Field(
        alias="mcs_plenum_gas_pressure",
        description="(MCS Setup) Latest gas pressure of main fueling plenum for MAST only",
    )

    cpf_p15209: Optional[float] = Field(
        alias="mcs_tg1_base_pressure",
        description="(MCS Setup) TG1 Base Pressure for MAST only",
    )

    cpf_p15659: Optional[float] = Field(
        alias="mcs_p3_direction",
        description="(MCS Setup) P3 Direction Monitored state of \
                        Polarity-reversing/isolation switches for MAST only",
    )

    cpf_p15660: Optional[float] = Field(
        alias="mcs_p4_direction",
        description="(MCS Setup) P4 direction: \
                        1= Normal Direction (Positive Ip), 3= Open Circuit for MAST only",
    )

    cpf_p15661: Optional[float] = Field(
        alias="mcs_p5_direction",
        description="(MCS Setup) P5 direction: \
                        2= Reverse Direction (Positive Ip) for MAST only",
    )

    cpf_p20000: Optional[float] = Field(
        alias="mcs_ss_number",
        description="(MCS Setup) Shot sequence number for MAST only",
    )

    cpf_p20204: Optional[float] = Field(
        alias="mcs_pshot_gdc_time",
        description="(MCS Setup) Pre-Shot GDC duration for MAST only",
    )

    cpf_p20205: Optional[float] = Field(
        alias="mcs_gdc_start_time",
        description="(MCS Setup) Last GDC start time for MAST only",
    )

    cpf_p20206: Optional[float] = Field(
        alias="mcs_gas_puff_pressure",
        description="(MCS Setup) Inboard Gas Puff Pressure for MAST only",
    )

    cpf_p20207: Optional[float] = Field(
        alias="mcs_gas_puff_start_time",
        description="(MCS Setup) Inboard Gas Puff Start Time Relative to 10s for MAST only",
    )

    cpf_p20208: Optional[float] = Field(
        alias="mcs_gas_puff_duration",
        description="(MCS Setup) Inboard Gas Puff Duration for MAST only",
    )

    cpf_p21010: Optional[float] = Field(
        alias="mcs_p2xo",
        description="(MCS Setup) Param mim430 - P2XO Mode \
                                                    (P2 Reversing Switch Mode: 0= +ve only, 1= -ve only, \
                                                    2= +ve => -ve, 3= -ve => +ve) for MAST only",
    )

    cpf_p21011: Optional[float] = Field(
        alias="mcs_p2xo_start_forward",
        description="(MCS Setup) Param mim430 - P2XO Start Forward \
                                                            (Offset by 5s: enable +ve polarity at time-5s) for MAST only",
    )

    cpf_p21012: Optional[float] = Field(
        alias="mcs_p2xo_start_reverse",
        description="(MCS Setup) Param mim430 - P2XO Start Reverse \
                                                            (Enable -ve polarity at 5s + time) for MAST only",
    )

    cpf_p21021: Optional[float] = Field(
        alias="mcs_tf_flat_top_value",
        description="(MCS Setup) Param mim421 - TF Flat Top set value \
                                                        (Tesla @ R=0.7m) for MAST only",
    )

    cpf_p21022: Optional[float] = Field(
        alias="mcs_tf_flat_top_time",
        description="(MCS Setup) Param mim421 - TF Flat Top set time for MAST only",
    )

    cpf_p21029: Optional[float] = Field(
        alias="mcs_tf_rise_time_value",
        description="(MCS Setup) Param mim421 - TF Rise Time set value \
                                            for MAST only",
    )

    cpf_p21035: Optional[float] = Field(
        alias="mcs_plasma_direction",
        description="(MCS  Setup) Plasma Direction \
                        (1.0 => Positive: Dervived from P3/P4/P5 switch settings (P15659-P15661)) for MAST only",
    )

    cpf_p21037: Optional[float] = Field(
        alias="mcs_p2_config",
        description="(MCS Setup) Required P2 Linkboard config \
                                            number (must match setting in PLC) for MAST only",
    )

    cpf_p21041: Optional[float] = Field(
        alias="mcs_cp3s_start_time",
        description="(MCS Setup) CP3s start time (Offset by 5s) for MAST only",
    )

    cpf_p21042: Optional[float] = Field(
        alias="mcs_cp3c_start_time",
        description="(MCS Setup) CP3c start time (Offset by 5s) for MAST only",
    )

    cpf_p21043: Optional[float] = Field(
        alias="mcs_cp4_start_time",
        description="(MCS Setup) CP4 start time (Offset by 5s) for MAST only",
    )

    cpf_p21044: Optional[float] = Field(
        alias="mcs_p4_ignitron_start_time",
        description="(MCS Setup) Close P4 circuit \
                        ignitron start time (Offset by 5s) for MAST only",
    )

    cpf_p21045: Optional[float] = Field(
        alias="mcs_p4_thyristor_start_time",
        description="(MCS Setup) P4 Circuit \
                        thyristor start time (Offset by 5s) for MAST only",
    )

    cpf_p21046: Optional[float] = Field(
        alias="mcs_cp5_start_time",
        description="(MCS Setup) CP5 Start time (Offset by 5s) for MAST only",
    )

    cpf_p21047: Optional[float] = Field(
        alias="mcs_p5_ignitron_start_time",
        description="(MCS Setup) P5 ignitron start time (Offset by 5s) for MAST only",
    )

    cpf_p21048: Optional[float] = Field(
        alias="mcs_p5_thyristor_start_time",
        description="(MCS Setup) P5 thyristor start time (Offset by 5s) for MAST only",
    )

    cpf_p21051: Optional[float] = Field(
        alias="mcs_mfps_current_limit",
        description="(MCS Setup) MFPS Power supply current limit for MAST only",
    )

    cpf_p21052: Optional[float] = Field(
        alias="mcs_mfps_start_time",
        description="(MCS Setup) MFPS set enable start time (Offset by 5s) for MAST only",
    )

    cpf_p21053: Optional[float] = Field(
        alias="mcs_efps_current_limit",
        description="(MCS Setup) EFPS Power supply current limit for MAST only",
    )

    cpf_p21054: Optional[float] = Field(
        alias="mcs_efps_start_time",
        description="(MCS Setup) EFPS set enable start time (Offset by 5s) for MAST only",
    )

    cpf_p21055: Optional[float] = Field(
        alias="mcs_sfps_current_limit",
        description="(MCS Setup) SFPS power supply current limit for MAST only",
    )

    cpf_p21056: Optional[float] = Field(
        alias="mcs_sfps_start_time",
        description="(MCS Setup) SFPS set enable start time (Offset by 5s) for MAST only",
    )

    cpf_p21075: Optional[float] = Field(
        alias="mcs_mfps_duration",
        description="(MCS Setup) MFPS enable duration for MAST only",
    )

    cpf_p21076: Optional[float] = Field(
        alias="mcs_efps_duration",
        description="(MCS Setup) EFPS enable duration for MAST only",
    )

    cpf_p21077: Optional[float] = Field(
        alias="mcs_sfps_duration",
        description="(MCS Setup) SFPS enable duration for MAST only",
    )

    cpf_p21078: Optional[float] = Field(
        alias="mcs_p1ps_pos_current_limit",
        description="(MCS Setup) P1PS maximum positive current limit for MAST only",
    )

    cpf_p21079: Optional[float] = Field(
        alias="mcs_p1ps_negative_current_limit",
        description="(MCS Setup) P1PS maximum negative current limit for MAST only",
    )

    cpf_p21080: Optional[float] = Field(
        alias="mcs_p1ps_start_time",
        description="(MCS Setup) P1PS enable start time (offset by 5s) for MAST only",
    )

    cpf_p21081: Optional[float] = Field(
        alias="mcs_p1ps_duration",
        description="(MCS Setup) P1PS enable duration for MAST only",
    )

    cpf_p21082: Optional[float] = Field(
        alias="mcs_fa1_start_time",
        description="(MCS Setup) FA1 enable start time (offset by 5s) for MAST only",
    )

    cpf_p21083: Optional[float] = Field(
        alias="mcs_fa1_duration",
        description="(MCS Setup) FA1 enable duration for MAST only",
    )

    cpf_p21084: Optional[float] = Field(
        alias="mcs_fa2_start_time",
        description="(MCS Setup) FA2 enable start time (offset by 5s) for MAST only",
    )

    cpf_p21085: Optional[float] = Field(
        alias="mcs_fa2_duration",
        description="(MCS Setup) FA2 enable duration for MAST only",
    )

    cpf_p21086: Optional[float] = Field(
        alias="mcs_fa3_start_time",
        description="(MCS Setup) FA3 enable start time (offset by 5s) for MAST only",
    )

    cpf_p21087: Optional[float] = Field(
        alias="mcs_fa3_duration",
        description="(MCS Setup) FA3 enable duration for MAST only",
    )

    cpf_p21088: Optional[float] = Field(
        alias="mcs_fa4_start_time",
        description="(MCS Setup) FA4 enable start time (offset by 5s) for MAST only",
    )

    cpf_p21089: Optional[float] = Field(
        alias="mcs_fa4_duration",
        description="(MCS Setup) FA4 enable duration for MAST only",
    )

    cpf_p21092: Optional[float] = Field(
        alias="mcs_scs4_start_time",
        description="(MCS Setup) SCS4 enabled start time used by MBD for MAST only",
    )

    cpf_p21093: Optional[float] = Field(
        alias="mcs_scs4_duration",
        description="(MCS Setup) SCS4 enabled duration for MAST only",
    )

    cpf_abort: Optional[float] = Field(
        alias="shot_abort", description="Shot aborted for MAST and MAST-U"
    )

    cpf_amin_ipmax: Optional[float] = Field(
        alias="generic_minor_radius_max_current",
        description="(Generic) Minor radius at time of peak plasma current for MAST and MAST-U",
    )

    cpf_amin_max: Optional[float] = Field(
        alias="generic_minor_radius",
        description="(Generic) Maximum value of minor radius for MAST and MAST-U",
    )

    cpf_amin_truby: Optional[float] = Field(
        alias="generic_minor_radius_ruby_time",
        description="(Generic) Minor radius at time of Ruby TS for MAST only",
    )

    cpf_area_ipmax: Optional[float] = Field(
        alias="generic_poloidal_area_max_current",
        description="(Generic) poloidal cross-sectional area at time of \
                                                peak plasma current for MAST and MAST-U",
    )

    cpf_area_max: Optional[float] = Field(
        alias="generic_max_poloidal_area",
        description="(Generic) Maximum Poloidal Cross-Sectional Area for MAST and MAST-U",
    )

    cpf_area_truby: Optional[float] = Field(
        alias="generic_poloidal_area_ruby_time",
        description="(Generic) Poloidal Cross-Sectional Area at time of Ruby TS for MAST only",
    )

    cpf_bepmhd_ipmax: Optional[float] = Field(
        alias="generic_beta_poloidal_max_current",
        description="(Generic) Beta poloidal at time of Peak Plasma Current for MAST and MAST-U",
    )

    cpf_bepmhd_max: Optional[float] = Field(
        alias="generic_max_beta_poloidal",
        description="(Generic) Maximum Beta poloidal for MAST and MAST-U",
    )

    cpf_bepmhd_truby: Optional[float] = Field(
        alias="generic_beta_poloidal_ruby_time",
        description="(Generic) Beta poloidal at time of Ruby TS for MAST only",
    )

    cpf_betmhd_ipmax: Optional[float] = Field(
        alias="generic_beta_time_max_current",
        description="(Generic) Beta at time of peak plasma current for MAST and MAST-U",
    )

    cpf_betmhd_max: Optional[float] = Field(
        alias="generic_max_beta_max_current",
        description="(Generic) Maximum beta at time of peak plasma current for MAST and MAST-U",
    )

    cpf_betmhd_truby: Optional[float] = Field(
        alias="generic_beta_ruby_time",
        description="(Generic) Beta at time of ruby TS for MAST only",
    )

    cpf_bt_ipmax: Optional[float] = Field(
        alias="generic_toroidal_max_current",
        description="(Generic) Toroidal field strength at time of peak \
                                                    plasma current for MAST and MAST-U",
    )

    cpf_bt_max: Optional[float] = Field(
        alias="generic_max_toroidal",
        description="(Generic) Maximum Toroidal field strength for MAST and MAST-U",
    )

    cpf_bt_truby: Optional[float] = Field(
        alias="generic_toroidal_ruby_time",
        description="(Generic) Toroidal field strength at time of ruby TS for MAST only",
    )

    cpf_c2ratio: Optional[float] = Field(
        alias="radii_c2ratio",
        description="(Radii) CII Line ratio averaged over Ip flat top from 150ms for MAST and MAST-U",
    )

    cpf_column_temp_in: Optional[float] = Field(
        alias="gas_col_temp_in",
        description="(Gas) centre column inlet temperature for MAST only",
    )

    cpf_column_temp_out: Optional[float] = Field(
        alias="gas_col_temp_out",
        description="(Gas) centre column outlet temperature for MAST only",
    )

    cpf_creation: Optional[datetime.datetime] = Field(
        alias="shot_creation_date",
        description="(Shot metdata) data dictionary entry creation \
                                                                date for MAST and MAST-U",
    )

    cpf_dwmhd_ipmax: Optional[float] = Field(
        alias="generic_dt_energy_max_current",
        description="(Generic) rate of change of total stored energy at \
                                                            time of peak plasma current for MAST and MAST-U",
    )

    cpf_dwmhd_max: Optional[float] = Field(
        alias="generic_dt_total_energy",
        description="(Generic) maximum rate of change of total stored energy \
                                                        for MAST and MAST-U",
    )

    cpf_dwmhd_truby: Optional[float] = Field(
        alias="generic_dt_energy_ruby_time",
        description="(Generic) rate of change of MHD stored energy at \
                                            time of ruby TS for MAST only",
    )

    cpf_enbi_max_ss: Optional[float] = Field(
        alias="nbi_energy_ss_max_power",
        description="(NBI) injection energy from SS beam at time of peak power \
                                            for MAST and MAST-U",
    )

    cpf_enbi_max_sw: Optional[float] = Field(
        alias="nbi_energy_sw_max_power",
        description="(NBI) injection energy from SW beam at time of peak power \
                                            for MAST and MAST-U",
    )

    cpf_exp_date: Optional[datetime.datetime] = Field(
        alias="shot_experiment_date",
        description="MAST shot experiment pulse date for MAST and MAST-U",
    )

    cpf_exp_number: Optional[int] = Field(
        alias="shot_experiment_number",
        description="MAST shot experiment pulse number for MAST and MAST-U",
    )

    cpf_exp_time: Optional[datetime.time] = Field(
        alias="shot_experiment_time",
        description="MAST shot experiment pulse time for MAST and MAST-U",
    )

    cpf_gdc_duration: Optional[float] = Field(
        alias="shot_glow_discharge_duration",
        description="Shot glow discharge duration for both",
    )

    cpf_gdc_time: Optional[float] = Field(
        alias="shot_glow_discharge_time",
        description="Shot glow discharge time for both",
    )

    cpf_ibgas_pressure: Optional[float] = Field(
        alias="gas_inboard_pressure_pre_pulse",
        description="Inboard gas pressure prior to pulse for MAST only",
    )

    cpf_ip_av: Optional[float] = Field(
        alias="plasma_time_avg_current",
        description="(Plasma) Time averaged plasma current during flat-top for MAST and MAST-U",
    )

    cpf_ip_max: Optional[float] = Field(
        alias="plasma_max_current",
        description="(Plasma) Maximum value of plasma current for MAST and MAST-U",
    )

    cpf_jnbi_ipmax: Optional[float] = Field(
        alias="nbi_injected_energy_max_current",
        description="(NBI) injected energy from \
                        SS+SW beams at time of peak current for MAST and MAST-U",
    )

    cpf_jnbi_ipmax_ss: Optional[float] = Field(
        alias="nbi_injected_energy_ss_max_current",
        description="(NBI) injected energy from \
                        SS beams at time of peak current for MAST and MAST-U",
    )

    cpf_jnbi_ipmax_sw: Optional[float] = Field(
        alias="nbi_injected_energy_ss_max_current",
        description="(NBI) injected energy from \
                        SW beams at time of peak current for MAST and MAST-U",
    )

    cpf_jnbi_max: Optional[float] = Field(
        alias="nbi_injected_energy_max",
        description="(NBI) injected energy from SS+SW \
                        beams at time of peak power for MAST and MAST-U",
    )

    cpf_jnbi_max_ss: Optional[float] = Field(
        alias="nbi_energy_ss_max_current",
        description="(NBI) injection energy from SS \
                        beam at time of peak power for MAST and MAST-U",
    )

    cpf_jnbi_max_sw: Optional[float] = Field(
        alias="nbi_energy_sw_max_current",
        description="(NBI) injection energy from SW \
                        beam at time of peak power for MAST and MAST-U",
    )

    cpf_jnbi_total: Optional[float] = Field(
        alias="nbi_total_injected_energy",
        description="Total NBI injected energy from SS+SW beams for MAST and MAST-U",
    )

    cpf_jnbi_total_ss: Optional[float] = Field(
        alias="nbi_total_injected_energy_ss",
        description="Total NBI Injected Energy from SS Beam for MAST and MAST-U",
    )

    cpf_jnbi_total_sw: Optional[float] = Field(
        alias="nbi_total_injected_energy_sw",
        description="Total NBI Injected Energy from SW Beam for MAST and MAST-U",
    )

    cpf_jnbi_truby: Optional[float] = Field(
        alias="nbi_injected_energy_ruby_time",
        description="(NBI) Injected Energy from SS+SW Beams at time of Ruby TS for MAST only",
    )

    cpf_jnbi_truby_ss: Optional[float] = Field(
        alias="nbi_injected_energy_ss_ruby_time",
        description="NBI Injected Energy from SW Beam at time of Ruby TS for MAST only",
    )

    cpf_jnbi_truby_sw: Optional[float] = Field(
        alias="nbi_injected_energy_sw_ruby_time",
        description="(NBI) Injected Energy from SW Beam at time of Ruby TS for MAST only",
    )

    cpf_johm_ipmax: Optional[float] = Field(
        alias="ohmnic_energy_max_current",
        description="Ohmic Heating Energy Input at time of Peak Current for MAST and MAST-U",
    )

    cpf_johm_max: Optional[float] = Field(
        alias="ohmnic_energy_max_heating",
        description="Ohmic Heating Energy Input at time of Maximum Ohmic Heating for MAST and MAST-U",
    )

    cpf_johm_total: Optional[float] = Field(
        alias="ohmnic_energy_total",
        description="Total Ohmic Heating Energy Input for MAST and MAST-U",
    )

    cpf_johm_truby: Optional[float] = Field(
        alias="ohmnic_energy_ruby_time",
        description="Ohmic Heat Energy Input at time of Ruby TS for MAST only",
    )

    cpf_kappa_ipmax: Optional[float] = Field(
        alias="generic_plasma_elongation_max_current",
        description="(Generic) Plasma Elongation at time of Peak \
                        Plasma Current for MAST and MAST-U",
    )

    cpf_kappa_max: Optional[float] = Field(
        alias="generic_plasma_elongation_max",
        description="(Generic) Maximum value of Plasma Elongation \
                        for MAST and MAST-U",
    )

    cpf_kappa_truby: Optional[float] = Field(
        alias="generic_plasma_elongation_ruby_time",
        description="(Generic) Plasma Elongation at time of Ruby TS for MAST only",
    )

    cpf_li_2_ipmax: Optional[float] = Field(
        alias="equi_li2_max_current",
        description="(Equilibrium) li(2) at time of Peak Current for MAST and MAST-U",
    )

    cpf_li_2_max: Optional[float] = Field(
        alias="equi_max_li2",
        description="(Equilibrium) li(2) Maximum value for MAST and MAST-U",
    )

    cpf_li_2_truby: Optional[float] = Field(
        alias="equi_li2_ruby_time",
        description="(Equilibrium) li(2) Maximum value for MAST and MAST-U",
    )

    cpf_li_3_ipmax: Optional[float] = Field(
        alias="equi_li3_max_current",
        description="(Equilibrium) li(3) at time of Peak Current for MAST and MAST-U",
    )

    cpf_li_3_max: Optional[float] = Field(
        alias="equi_max_li3",
        description="(Equilibrium) li(3) Maximum value for MAST and MAST-U",
    )

    cpf_li_3_truby: Optional[float] = Field(
        alias="equi_li3_ruby_time",
        description="(Equilibrium) li(3) at time of Ruby TS for MAST only",
    )

    cpf_log_base_pressure: Optional[float] = Field(
        alias="gas_tg1_pressure_ps",
        description="(Gas) TG1 Base Pressure prior to Shot for MAST only",
    )

    cpf_ndl_co2_ipmax: Optional[float] = Field(
        alias="thomson_density_line_max_current",
        description="(Thomson) Electron Density Line Integral at time \
                        of Peak Plasma Current for MAST and MAST-U",
    )

    cpf_ndl_co2_max: Optional[float] = Field(
        alias="thomson_max_density_line",
        description="(Thomson) Maximum Electron Density Line Integral \
                        observed by CO2 Interferometer for MAST and MAST-U",
    )

    cpf_ndl_co2_truby: Optional[float] = Field(
        alias="thomson_density_line_ruby_time",
        description="(Thomson) Electron Density Line Integral at time \
                        of Ruby TS for MAST only",
    )

    cpf_ne0_ipmax: Optional[float] = Field(
        alias="thomson_density_max_current",
        description="(Thomson) Core Electron Density (Nd.YAG) at time of \
                        Peak Current for MAST and MAST-U",
    )

    cpf_ne0_max: Optional[float] = Field(
        alias="thomson_density_max",
        description="(Thomson) Peak Core Electron Density (Nd.YAG) for MAST and MAST-U",
    )

    cpf_ne0_truby: Optional[float] = Field(
        alias="thomson_density_ruby_time",
        description="(Thomson) Core Electron Density (Nd.YAG) at time of Ruby TS for MAST only",
    )

    cpf_ne0ratio_ipmax: Optional[float] = Field(
        alias="thomson_ne0_rat_line_avg_ne",
        description="(Thomson) Ratio of ne0 to line average ne for MAST and MAST-U",
    )

    cpf_ne0ruby: Optional[float] = Field(
        alias="thomson_density_ruby_time",
        description="(Thomson) Core Electron Density (Nd.YAG) at time of Ruby TS for MAST only",
    )

    cpf_ne_bar_ipmax: Optional[float] = Field(
        alias="thomson_line_avg_density_co2",
        description="(Thomson) Mid-plane line average electron density \
                                                            from CO2 interferometer for MAST and MAST-U",
    )

    cpf_ne_yag_bar_ipmax: Optional[float] = Field(
        alias="thomson_line_avg_density_co2",
        description="(Thomson) Mid-plane line average electron density from CO2 \
                                                                    interferometer for MAST and MAST-U",
    )

    cpf_ngreenwald_ipmax: Optional[float] = Field(
        alias="thomson_greenwald_density_limit",
        description="(Thomson) Greenwald Density Limit for MAST and MAST-U",
    )

    cpf_ngreenwaldratio_ipmax: Optional[float] = Field(
        alias="thomson_greenwald_rat_line_avg_density",
        description="(Thomson) Ratio of Greenwald density limit to mid-plane \
                                                                        line averaged electron density for MAST and MAST-U",
    )

    cpf_o2ratio: Optional[float] = Field(
        alias="rad_o2ratio",
        description="(Radii) OII Line Ratio averaged over Ip flat top from 150ms \
                                                                for MAST and MAST-U",
    )

    cpf_objective: Optional[str] = Field(
        alias="shot_objective",
        description="Shot Scientific Objective for MAST and MAST-U",
    )

    cpf_pe0_ipmax: Optional[float] = Field(
        alias="thomson_pressure_max_current",
        description="(Thomsom) Core Electron Pressure (Nd.YAG) at time of Peak \
                                                                Plasma Current for MAST and MAST-U",
    )

    cpf_pe0_max: Optional[float] = Field(
        alias="thomson_pressure_max",
        description="(Thomsom) Maximum value of Core Electron Pressure (Nd.YAG) \
                                                                    for MAST and MAST-U",
    )

    cpf_pe0_truby: Optional[float] = Field(
        alias="thomson_pressure_ruby_time",
        description="(Thomsom) Core Electron Pressure (Nd.YAG) at time of Ruby TS \
                                                                for MAST only",
    )

    cpf_pe0ruby: Optional[float] = Field(
        alias="thomson_pressure_ruby",
        description="(Thomsom) Ruby TS Core Electron Pressure for MAST only",
    )

    cpf_pic: Optional[str] = Field(
        alias="shot_physicist",
        description="(Shot) physicist in charge for MAST and MAST-U",
    )

    cpf_pnbi_ipmax: Optional[float] = Field(
        alias="nbi_power_max_current",
        description="(NBI) Power from SS+SW Beams at time of Peak Current \
                                                                for MAST and MAST-U",
    )

    cpf_pnbi_ipmax_ss: Optional[float] = Field(
        alias="nbi_power_ss_max_current",
        description="(NBI) Power from SS Beam at time of Peak Current \
                                                            for MAST and MAST-U",
    )

    cpf_pnbi_ipmax_sw: Optional[float] = Field(
        alias="nbi_power_max_current",
        description="(NBI) Power from SW Beam at time of Peak Current \
                                                            for MAST and MAST-U",
    )

    cpf_pnbi_max: Optional[float] = Field(
        alias="nbi_power_max_power",
        description="(NBI) Power from SS+SW Beams at time of Peak power \
                                                        for MAST and MAST-U",
    )

    cpf_pnbi_max_ss: Optional[float] = Field(
        alias="nbi_power_max_ss",
        description="Peak NBI Power from SS Beam for MAST and MAST-U",
    )

    cpf_pnbi_max_sw: Optional[float] = Field(
        alias="nbi_power_max_sw",
        description="Peak NBI Power from SW Beam for MAST and MAST-U",
    )

    cpf_pnbi_truby: Optional[float] = Field(
        alias="nbi_power_ruby_time",
        description="(NBI) Power from SS+SW Beams at time of Ruby TS for MAST and MAST-U",
    )

    cpf_pnbi_truby_ss: Optional[float] = Field(
        alias="nbi_power_truby_ss",
        description="(NBI) Power from SS Beam at time of Ruby TS for MAST and MAST-U",
    )

    cpf_pnbi_truby_sw: Optional[float] = Field(
        alias="nbi_power_truby_sw",
        description="(NBI) Power from SW Beam at time of Ruby TS for MAST and MAST-U",
    )

    cpf_pohm_ipmax: Optional[float] = Field(
        alias="ohmnic_heating_max_current",
        description="Ohmic Heating Rate at time of Peak Current for MAST and MAST-U",
    )

    cpf_pohm_max: Optional[float] = Field(
        alias="ohmnic_max_heating",
        description="Maximum Ohmic Heating Rate for MAST and MAST-U",
    )

    cpf_pohm_truby: Optional[float] = Field(
        alias="ohmnic_heating_ruby_time",
        description="Ohmic Heating Rate at time of Ruby TS for MAST only",
    )

    cpf_postshot: Optional[str] = Field(
        alias="shot_postshot_comment",
        description="Session Leaders Post-Shot Comment for MAST and MAST-U",
    )

    cpf_prad_ipmax: Optional[float] = Field(
        alias="generic_rad_power_loss_max_current",
        description="(Generic) Total Radiated Power Loss at time of \
                                                                Peak Plasma Current for MAST and MAST-U",
    )

    cpf_prad_max: Optional[float] = Field(
        alias="generic_max_power_loss",
        description="(Generic) Maximum Total Radiated Power Loss for MAST and MAST-U",
    )

    cpf_prad_truby: Optional[float] = Field(
        alias="generic_power_loss_ruby_time",
        description="(Generic) Total Radiated Power Loss at time of Ruby TS for MAST only",
    )

    cpf_pradne2: Optional[float] = Field(
        alias="rad_flat_top_power_rat_avg_line_density",
        description="(Radii) Flat Top Ratio of Power Radiated to Line Density squared \
                                                        averaged over Ip flat top from 150ms for MAST and MAST-U",
    )

    cpf_preshot: Optional[str] = Field(
        alias="shot_preshot_comment",
        description="Session Leaders Pre-Shot Comment for MAST and MAST-U",
    )

    cpf_program: Optional[str] = Field(
        alias="shot_program",
        description="(Shot) Scientific Program for MAST and MAST-U",
    )

    cpf_pulno: Optional[float] = Field(
        alias="shot_pulse_number",
        description="(Ghot) MAST Experiment Pulse Number for MAST and MAST-U",
    )

    cpf_q95_ipmax: Optional[float] = Field(
        alias="generic_q95_max_current",
        description="(Generic) q-95 at time of Peak Plasma Current for MAST and MAST-U",
    )

    cpf_q95_min: Optional[float] = Field(
        alias="generic_min_q95",
        description="(Generic) Minimum value of q-95 for MAST and MAST-U",
    )

    cpf_q95_truby: Optional[float] = Field(
        alias="generic_q95_ruby_time", description="(Generic) q-95 at time of Ruby TS"
    )

    cpf_reference: Optional[float] = Field(
        alias="shot_reference", description="(Shot) Reference shot for MAST and MAST-U"
    )

    cpf_rgeo_ipmax: Optional[float] = Field(
        alias="generic_geo_radius_max_current",
        description="(Generic) geometrical center major radius at time of \
                                                peak plasma current for MAST and MAST-U",
    )

    cpf_rgeo_max: Optional[float] = Field(
        alias="generic_max_geo_radius",
        description="(Generic) Maximum value of Geometrical Center \
                                                                    Major Radius for MAST and MAST-U",
    )

    cpf_rgeo_truby: Optional[float] = Field(
        alias="generic_geo_radius_ruby_time",
        description="(Generic) geometrical Center Major Radius at time \
                                                            of Ruby TS for MAST and MAST-U",
    )

    cpf_rinner_da: Optional[float] = Field(
        alias="radii_rinner_radius_d_alpha",
        description="(Radii) rinner major Radius from Visible D_Alpha Light \
                                                            for MAST and MAST-U",
    )

    cpf_rinner_efit: Optional[float] = Field(
        alias="radii_rinner_radius_efit",
        description="(Radii) rinner major Radius from EFIT Equilibrium \
                                                            for MAST and MAST-U",
    )

    cpf_rmag_efit: Optional[float] = Field(
        alias="radii_magnetic__radius_efit",
        description="(Radii) magnetic Axis major Radius from EFIT Equilibrium \
                                                            for MAST and MAST-U",
    )

    cpf_router_da: Optional[float] = Field(
        alias="radii_router_radius_d_alpha",
        description="(Radii) router major Radius from Visible D_Alpha Light \
                                                            for MAST and MAST-U",
    )

    cpf_router_efit: Optional[float] = Field(
        alias="radii_router_radius_efit",
        description="(Radii) router major Radius from EFIT Equilibrium \
                                                            for MAST and MAST-U",
    )

    cpf_sarea_ipmax: Optional[float] = Field(
        alias="radii_s_area_max_current",
        description="(Generic) Total Surface Area at time of Peak Plasma \
                                                            Current for MAST and MAST-U",
    )

    cpf_sarea_max: Optional[float] = Field(
        alias="generic_s_area_max",
        description="(Generic) maximum Total Surface Area for MAST and MAST-U",
    )

    cpf_sarea_truby: Optional[float] = Field(
        alias="generic_s_area_ruby_time",
        description="(Generic) total Surface Area at time of Ruby TS for MAST only",
    )

    cpf_sl: Optional[str] = Field(
        alias="shot_session_leader",
        description="(Shot) session leader for MAST and MAST-U",
    )

    cpf_sc: Optional[str] = Field(nullable=True)

    cpf_summary: Optional[str] = Field(
        alias="shot_summary", description="(Shot) session summary for MAST and MAST-U"
    )

    cpf_tamin_max: Optional[float] = Field(
        alias="generic_min_radius_max_plasma",
        description="(Generic) Time of Maximum Plasma Minor Radius for MAST and MAST-U",
    )

    cpf_tarea_max: Optional[float] = Field(
        alias="generic_max_poloidal_area",
        description="(Generic) Time of Maximum Poloidal Cross-Sectional Area \
                                                                    for MAST and MAST-U",
    )

    cpf_tautot_ipmax: Optional[float] = Field(
        alias="generic_energy_time_max_current",
        description="(Generic) Energy Confinement Time at time of Peak Plasma Current \
                                                                    for MAST and MAST-U",
    )

    cpf_tautot_max: Optional[float] = Field(
        alias="generic_max_energy_time",
        description="(Generic) Maximum value of Energy Confinement Time for MAST and MAST-U",
    )

    cpf_tautot_truby: Optional[float] = Field(
        alias="generic_energy_time_ruby_time",
        description="(Generic) Energy Confinement Time at time of Ruby TS for MAST and MAST-U",
    )

    cpf_tbepmhd_max: Optional[float] = Field(
        alias="generic_max_beta_poloidal_mhd",
        description="(Generic) Time of Maximum Beta Poloidal MHD for MAST and MAST-U",
    )

    cpf_tbetmhd_max: Optional[float] = Field(
        alias="generic_max_beta_mhd",
        description="(Generic) Time of Maximum Beta MHD for MAST and MAST-U",
    )

    cpf_tbt_max: Optional[float] = Field(
        alias="generic_max_toroidal_time",
        description="(Generic) Time of Maximum Toroidal Magnetic Field Strength \
                                                                    for MAST and MAST-U",
    )

    cpf_tdwmhd_max: Optional[float] = Field(
        alias="generic_max_dt_mhd_energy_time",
        description="(Generic) Time of Maximum Rate of Change of MHD Stored Energy \
                                                                    for MAST and MAST-U",
    )

    cpf_te0_ipmax: Optional[float] = Field(
        alias="thomson_temp_max_current",
        description="(Thomoson) Core Electron Temperature (Nd.YAG) at time of \
                                                                        Peak Current for MAST and MAST-U",
    )

    cpf_te0_max: Optional[float] = Field(
        alias="thomson_temp_max",
        description="(Thomson) Peak Core Electron Temperature (Nd.YAG) \
                                                                        for MAST and MAST-U",
    )

    cpf_te0_truby: Optional[float] = Field(
        alias="thomson_temp_ruby_time",
        description="(Thomson) Core Electron Temperature (Nd.YAG) at \
                                                                            time of Ruby TS for MAST only",
    )

    cpf_te0ratio_ipmax: Optional[float] = Field(
        alias="thomson_temp_rat_line_avg_temp",
        description="(Thomson) ratio of Core Electron Temperature to line \
                                                            average Te for MAST and MAST-U",
    )

    cpf_te0ruby: Optional[float] = Field(
        alias="thomson_temp_ruby",
        description="(Thomson) Ruby TS Core Electron Temperature for MAST only",
    )

    cpf_te_yag_bar_ipmax: Optional[float] = Field(
        alias="thomson_yag_line_avg_temp",
        description="Mid-plane line average electron temperature from \
                                                                            YAG Thomson scattering for MAST and MAST-U",
    )

    cpf_tend: Optional[float] = Field(
        alias="plasma_end_time",
        description="(Plasma) current end time for MAST and MAST-U",
    )

    cpf_tend_ibgas: Optional[float] = Field(
        alias="gas_puff_end_time", description="Inboard Gas Puff End Time for MAST only"
    )

    cpf_tend_nbi: Optional[float] = Field(
        alias="nbi_end_time", description="(NBI) end time for MAST and MAST-U"
    )

    cpf_tend_nbi_ss: Optional[float] = Field(
        alias="nbi_end_time_ss", description="SS NBI end time for MAST and MAST-U"
    )

    cpf_tend_nbi_sw: Optional[float] = Field(
        alias="nbi_end_time_ss", description="SW NBI end time for MAST and MAST-U"
    )

    cpf_term_code: Optional[float] = Field(
        alias="shot_end_code",
        description="(Plasma) shot termination reason code for MAST and MASt-U",
    )

    cpf_tftend: Optional[float] = Field(
        alias="plasma_flat_top_end_time",
        description="(Plasma) Current Flat-Top End Time for MAST and MAST-U",
    )

    cpf_tftstart: Optional[float] = Field(
        alias="plasma_flat_top_start_time",
        description="(Plasma) Current Flat-Top Start Time for MAST and MAST-U",
    )

    cpf_tipmax: Optional[float] = Field(
        alias="plasma_max_plasma_current_time",
        description="(Plasma) Time of Maximum Plasma Current for MAST and MAST-U",
    )

    cpf_tkappa_max: Optional[float] = Field(
        alias="generic_max_plasma_elongation_time",
        description="(Generic) Time of Maximum Plasma Elongation for MAST and MAST-U",
    )

    cpf_tli_2_max: Optional[float] = Field(
        alias="equi_max_li2_time",
        description="(Equilibrium) time of Maximum li(2) for MAST and MAST-U",
    )

    cpf_tli_3_max: Optional[float] = Field(
        alias="equi_max_li3_time",
        description="(Equilibrium) time of Maximum li(3) for MAST and MAST-U",
    )

    cpf_tndl_co2_max: Optional[float] = Field(
        alias="thomson_max_density_line_time",
        description="(Thomson) Time of Maximum Electron Density Line Integral \
                                                                for MAST and MAST-U",
    )

    cpf_tne0_max: Optional[float] = Field(
        alias="thomson_max_density_time",
        description="(thomson) Time of Maximum Core Electron Density (from Nd.YAG TS) \
                                                                for MAST and MAST-U",
    )

    cpf_tpe0_max: Optional[float] = Field(
        alias="thomson_max_pressure_time",
        description="(Thomson) Time of Maximum Core Electron Pressure (from Nd.YAG TS) \
                                                                    for MAST and MAST-U",
    )

    cpf_tpnbi_max: Optional[float] = Field(
        alias="nbi_max_power_time",
        description="(NBI) Time of Maximum NB Power for MAST and MAST-U",
    )

    cpf_tpnbi_max_ss: Optional[float] = Field(
        alias="nbi_max_ss_power_time",
        description="(NBI) Time of Maximum SS NBI Power for MAST and MAST-U",
    )

    cpf_tpnbi_max_sw: Optional[float] = Field(
        alias="nbi_max_sw_power_time",
        description="(NBI) Time of Maximum SW NBI Power for MAST and MAST-U",
    )

    cpf_tpohm_max: Optional[float] = Field(
        alias="ohmnic_max_heating_time",
        description="(NBI) Time of Maximum Ohmic Heating for MAST and MAST-U",
    )

    cpf_tprad_max: Optional[float] = Field(
        alias="generic_max_plasma_power_loss_time",
        description="(Generic) Time of Maximum Plasma Radiated Power Loss for MAST and MAST-U",
    )

    cpf_tq95_min: Optional[float] = Field(
        alias="generic_min_q95_time",
        description="(Generic) Time of Minimum q 95 for MAST and MAST-U",
    )

    cpf_trgeo_max: Optional[float] = Field(
        alias="generic_max_geo_major_radius_time",
        description="(Generic) Time of Maximum Geometrical Mid-plane Center Major Radius \
                                           for MAST and MAST-U",
    )

    cpf_truby: Optional[float] = Field(
        alias="thomson_ruby_time",
        description="(Thomson) Ruby Thomson Scattering Time for MAST only",
    )

    cpf_tsarea_max: Optional[float] = Field(
        alias="generic_max_plasma_s_area_time",
        description="(Generic) Time of Maximum Plasma Surface Area for MAST and MAST-U",
    )

    cpf_tstart: Optional[float] = Field(
        alias="plasma_flat_top_start_time",
        description="(Plasma) Current Flat-Top Start Time for MAST and MAST-U",
    )

    cpf_tstart_ibgas: Optional[float] = Field(
        alias="gas_puff_start_time",
        description="Inboard Gas Puff Start Time for MAST only",
    )

    cpf_tstart_nbi: Optional[float] = Field(
        alias="nbi_start_time", description="(NBI) Start Time for MAST and MAST-U"
    )

    cpf_tstart_nbi_ss: Optional[float] = Field(
        alias="nbi_ss_start_time", description="SS NBI Start Time for MAST and MAST-U"
    )

    cpf_tstart_nbi_sw: Optional[float] = Field(
        alias="nbi_sw_start_time", description="SW NBI Start Time for MAST and MAST-U"
    )

    cpf_ttautot_max: Optional[float] = Field(
        alias="generic_max_total_energy_time",
        description="(Generic) Time of Maximum Total Energy Confinement Time for MAST and MAST-U",
    )

    cpf_tte0_max: Optional[float] = Field(
        alias="thomson_max_temp_time",
        description="(Thomson) Time of Maximum Core Electron Temperature (from Nd.YAG TS) \
                                                                    for MAST and MAST-U",
    )

    cpf_tvol_max: Optional[float] = Field(
        alias="generic_max_plasma_vol_time",
        description="(Generic) Time of Maximum Plasma Volume for MAST and MAST-U",
    )

    cpf_twmhd_max: Optional[float] = Field(
        alias="generic_max_mhd_energy_time",
        description="(Generic) Time of Maximum MHD Stored Energy for MAST and MAST-U",
    )

    cpf_tzeff_max: Optional[float] = Field(
        alias="generic_max_plasma_zeff_time",
        description="(Generic) Time of Maximum Plasma Z-Effective for MAST and MAST-U",
    )

    cpf_useful: Optional[float] = Field(
        alias="shot_useful", description="Useful Shot for MAST and MAST-U"
    )

    cpf_vol_ipmax: Optional[float] = Field(
        alias="generic_plasma_vol_max_current",
        description="(Generic) Plasma Volume at time of Peak Plasma Current for MAST and MAST-U",
    )

    cpf_vol_max: Optional[float] = Field(
        alias="generic_max_plasma_vol",
        description="(Generic) Maximum Plasma Volume for MAST and MAST-U",
    )

    cpf_vol_truby: Optional[float] = Field(
        alias="generic_plasma_vol_ruby_time",
        description="(Generic) Plasma Volume at time of Ruby TS for MAST only",
    )

    cpf_wmhd_ipmax: Optional[float] = Field(
        alias="generic_energy_current_max",
        description="(Generic) Stored Energy at time of Peak Plasma Current \
                                                                        for MAST and MAST-U",
    )

    cpf_wmhd_max: Optional[float] = Field(
        alias="generic_energy_max",
        description="(Generic) Maximum Stored Energy for MAST and MAST-U",
    )

    cpf_wmhd_truby: Optional[float] = Field(
        alias="generic_energy_ruby_time",
        description="(Generic) Stored Energy at time of Ruby TS for MAST only",
    )

    cpf_zeff_ipmax: Optional[float] = Field(
        alias="generic_plasma_zeff_max_current",
        description="(Generic) Plasma Z-Effective at time of Peak Plasma Current \
                                                                            for MAST and MAST-U",
    )

    cpf_zeff_max: Optional[float] = Field(
        alias="generic_plasma_zeff_max",
        description="(Generic) Maximum Plasma Z-Effective for MAST and MASt-U",
    )

    cpf_zeff_truby: Optional[float] = Field(
        alias="generic_plasma_zeff_ruby_time",
        description="(Generic) Plasma Z-Effective at time of Ruby TS for MAST only",
    )

    cpf_zmag_efit: Optional[float] = Field(
        alias="rad_magnetic_height_efit",
        description="(Radii) Magnetic Axis height above Mid-Plane from EFIT Equilibrium \
                                                                            for MAST and MAST-U",
    )
