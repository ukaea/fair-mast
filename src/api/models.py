from typing import Optional, List, Dict
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    ARRAY,
    Text,
    String,
    DateTime,
    Time,
    SmallInteger,
    REAL,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import datetime
import uuid as uuid_pkg

from .types import (
    CurrentRange,
    DivertorConfig,
    PlasmaShape,
    Comissioner,
    Facility,
    SignalType,
    Quality,
    ImageFormat,
    ImageSubclass,
)
from sqlmodel import Field, SQLModel, Relationship, text, JSON


class SignalModel(SQLModel, table=True):
    __tablename__ = "signals"

    id: int = Field(primary_key=True, index=True)

    signal_dataset_id: int = Field(
        foreign_key="signal_datasets.signal_dataset_id",
        nullable=False,
        description="ID for the signal.",
    )

    shot_id: int = Field(
        foreign_key="shots.shot_id",
        nullable=False,
        description="ID of the shot this signal was produced by.",
    )

    name: str = Field(
        description="Human readable name of this specific signal. A combination of the signal type and the shot number e.g. AMC_PLASMA_CURRENT/30420"
    )

    signal_name: str = Field(
        description="Name of the signal dataset this signal belongs to."
    )

    version: int = Field(description="Version number of this dataset")

    uuid: Optional[uuid_pkg.UUID] = Field(
        sa_column=Column(UUID(as_uuid=True), server_default=text("gen_random_uuid()")),
        default=None,
        description="UUID for a specific version of the data",
    )

    url: str = Field(description="The URL for the location of this signal.")

    quality: Quality = Field(
        sa_column=Column(
            Enum(Quality, values_callable=lambda obj: [e.value for e in obj])
        ),
        description="Quality flag for this signal.",
    )

    shape: List[int] = Field(
        sa_column=Column(ARRAY(Integer)),
        description="Shape of each dimension of this signal. e.g. [10, 100, 3]",
    )

    provenance: Optional[Dict] = Field(
        default={},
        sa_column=Column(JSONB),
        description="Information about the provenance graph that generated this signal in the PROV standard.",
    )

    signal_dataset: "SignalDatasetModel" = Relationship(back_populates="signals")
    shot: "ShotModel" = Relationship(back_populates="signals")


class SourceModel(SQLModel, table=True):
    __tablename__ = "sources"

    name: str = Field(
        primary_key=True,
        nullable=False,
        description="Short name of the source.",
    )

    description: str = Field(
        sa_column=Column(Text), description="Description of this source"
    )

    doi: Optional[str] = Field(
        sa_column=Column(Text), description="DOI for this source."
    )

    source_type: SignalType = Field(
        sa_column=Column(
            Enum(SignalType, values_callable=lambda obj: [e.value for e in obj])
        ),
        description="The type of the source.",
    )


class SignalDatasetModel(SQLModel, table=True):
    __tablename__ = "signal_datasets"

    context_: Dict = Field(
        default={},
        sa_column=Column(JSONB),
        description="JSON-LD context field",
        alias="@context",
    )

    signal_dataset_id: int = Field(
        primary_key=True,
        nullable=False,
        index=True,
        description="The ID of this signal dataset.",
    )
    name: str = Field(sa_column=Column(Text), description="The name of this dataset.")
    units: str = Field(description="The units of data contained within this dataset.")
    rank: int = Field(
        description="The rank of the dataset. This is the number of dimensions a signal will have e.g. 2 if dimensions are ['time', 'radius']"
    )
    url: str = Field(description="The URL for the location of this signal.")

    description: str = Field(
        sa_column=Column(Text), description="The description of the dataset."
    )

    signal_type: SignalType = Field(
        sa_column=Column(
            Enum(SignalType, values_callable=lambda obj: [e.value for e in obj])
        ),
        description="The type of the signal dataset. e.g. 'Raw', 'Analysed'",
    )

    quality: Quality = Field(
        sa_column=Column(
            Enum(Quality, values_callable=lambda obj: [e.value for e in obj])
        ),
        description="The quality of the signal for the whole dataset. e.g. 'Validated'",
    )

    doi: str = Field(
        sa_column=Column(Text), description="A DOI for the dataset, if it exists."
    )

    dimensions: List[str] = Field(
        sa_column=Column(ARRAY(Text)),
        description="The dimension names of the dataset, in order. e.g. ['time', 'radius']",
    )

    shots: List["ShotModel"] = Relationship(
        back_populates="signal_datasets", link_model=SignalModel
    )

    signals: List["SignalModel"] = Relationship(back_populates="signal_dataset")

    image_metadata: Optional["ImageMetadataModel"] = Relationship(
        sa_relationship_kwargs={"uselist": False}, back_populates="signal_dataset"
    )


class ImageMetadataModel(SQLModel, table=True):
    __tablename__ = "image_metadata"

    signal_dataset_id: int = Field(
        primary_key=True,
        foreign_key="signal_datasets.signal_dataset_id",
        nullable=False,
        description="ID for the signal dataset.",
    )

    subclass: ImageSubclass = Field(
        sa_column=Column(
            Enum(ImageSubclass, values_callable=lambda obj: [e.value for e in obj]),
            nullable=True,
        ),
        description="The subclass for this image data.",
    )

    format: ImageFormat = Field(
        sa_column=Column(
            Enum(ImageFormat, values_callable=lambda obj: [e.value for e in obj]),
            nullable=True,
        ),
        description="The format the image was original recorded in. e.g. IPX",
    )

    version: str = Field(description="The version for this image.")

    signal_dataset: SignalDatasetModel = Relationship(back_populates="image_metadata")


class CPFSummaryModel(SQLModel, table=True):
    __tablename__ = "cpf_summary"

    index: int = Field(primary_key=True, nullable=False)
    name: str = Field(sa_column=Column(Text), description="Name of the CPF variable.")
    description: str = Field("Description of the CPF variable")


class ScenarioModel(SQLModel, table=True):
    __tablename__ = "scenarios"
    id: int = Field(primary_key=True, nullable=False)
    name: str = Field(sa_column=Column(Text), description="Name of the scenario.")


class ShotModel(SQLModel, table=True):
    __tablename__ = "shots"

    shot_id: int = Field(
        primary_key=True,
        index=True,
        nullable=False,
        description='ID of the shot. Also known as the shot index. e.g. "30420"',
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
        nullable=True,
        description='Reference shot ID used as the basis for setting up this shot, if used. e.g. "30420"',
    )

    scenario: Optional[int] = Field(
        nullable=True, description="The scenario used for this shot."
    )
    heating: Optional[str] = Field(
        nullable=True, description="The type of heating used for this shot."
    )
    pellets: Optional[bool] = Field(
        nullable=True, description="Whether pellets were used as part of this shot."
    )
    rmp_coil: Optional[bool] = Field(
        nullable=True, description="Whether an RMP coil was used as port of this shot."
    )

    current_range: Optional[CurrentRange] = Field(
        sa_column=Column(
            Enum(CurrentRange, values_callable=lambda obj: [e.value for e in obj]),
            nullable=True,
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

    signal_datasets: List["SignalDatasetModel"] = Relationship(
        back_populates="shots", link_model=SignalModel
    )

    signals: List["SignalModel"] = Relationship(back_populates="shot")

    cpf_p03249: Optional[float] = Field(nullable=True)

    cpf_p04673: Optional[float] = Field(nullable=True)

    cpf_p04674: Optional[float] = Field(nullable=True)

    cpf_p04675: Optional[float] = Field(nullable=True)

    cpf_p04676: Optional[float] = Field(nullable=True)

    cpf_p04677: Optional[float] = Field(nullable=True)

    cpf_p04678: Optional[float] = Field(nullable=True)

    cpf_p04679: Optional[float] = Field(nullable=True)

    cpf_p04680: Optional[float] = Field(nullable=True)

    cpf_p04681: Optional[float] = Field(nullable=True)

    cpf_p04833: Optional[float] = Field(nullable=True)

    cpf_p04993: Optional[float] = Field(nullable=True)

    cpf_p05007: Optional[float] = Field(nullable=True)

    cpf_p05008: Optional[float] = Field(nullable=True)

    cpf_p05009: Optional[float] = Field(nullable=True)

    cpf_p05010: Optional[float] = Field(nullable=True)

    cpf_p05011: Optional[float] = Field(nullable=True)

    cpf_p05015: Optional[float] = Field(nullable=True)

    cpf_p05016: Optional[float] = Field(nullable=True)

    cpf_p05017: Optional[float] = Field(nullable=True)

    cpf_p05025: Optional[float] = Field(nullable=True)

    cpf_p05027: Optional[float] = Field(nullable=True)

    cpf_p05028: Optional[float] = Field(nullable=True)

    cpf_p05029: Optional[float] = Field(nullable=True)

    cpf_p05030: Optional[float] = Field(nullable=True)

    cpf_p05032: Optional[float] = Field(nullable=True)

    cpf_p05033: Optional[float] = Field(nullable=True)

    cpf_p05153: Optional[float] = Field(nullable=True)

    cpf_p06000: Optional[float] = Field(nullable=True)

    cpf_p06001: Optional[float] = Field(nullable=True)

    cpf_p06002: Optional[float] = Field(nullable=True)

    cpf_p06003: Optional[float] = Field(nullable=True)

    cpf_p06004: Optional[float] = Field(nullable=True)

    cpf_p10963: Optional[float] = Field(nullable=True)

    cpf_p10964: Optional[float] = Field(nullable=True)

    cpf_p12441: Optional[float] = Field(nullable=True)

    cpf_p12450: Optional[float] = Field(nullable=True)

    cpf_p12451: Optional[float] = Field(nullable=True)

    cpf_p12452: Optional[float] = Field(nullable=True)

    cpf_p15202: Optional[float] = Field(nullable=True)

    cpf_p15203: Optional[float] = Field(nullable=True)

    cpf_p15209: Optional[float] = Field(nullable=True)

    cpf_p15659: Optional[float] = Field(nullable=True)

    cpf_p15660: Optional[float] = Field(nullable=True)

    cpf_p15661: Optional[float] = Field(nullable=True)

    cpf_p20000: Optional[float] = Field(nullable=True)

    cpf_p20204: Optional[float] = Field(nullable=True)

    cpf_p20205: Optional[float] = Field(nullable=True)

    cpf_p20206: Optional[float] = Field(nullable=True)

    cpf_p20207: Optional[float] = Field(nullable=True)

    cpf_p20208: Optional[float] = Field(nullable=True)

    cpf_p21010: Optional[float] = Field(nullable=True)

    cpf_p21011: Optional[float] = Field(nullable=True)

    cpf_p21012: Optional[float] = Field(nullable=True)

    cpf_p21021: Optional[float] = Field(nullable=True)

    cpf_p21022: Optional[float] = Field(nullable=True)

    cpf_p21029: Optional[float] = Field(nullable=True)

    cpf_p21035: Optional[float] = Field(nullable=True)

    cpf_p21037: Optional[float] = Field(nullable=True)

    cpf_p21041: Optional[float] = Field(nullable=True)

    cpf_p21042: Optional[float] = Field(nullable=True)

    cpf_p21043: Optional[float] = Field(nullable=True)

    cpf_p21044: Optional[float] = Field(nullable=True)

    cpf_p21045: Optional[float] = Field(nullable=True)

    cpf_p21046: Optional[float] = Field(nullable=True)

    cpf_p21047: Optional[float] = Field(nullable=True)

    cpf_p21048: Optional[float] = Field(nullable=True)

    cpf_p21051: Optional[float] = Field(nullable=True)

    cpf_p21052: Optional[float] = Field(nullable=True)

    cpf_p21053: Optional[float] = Field(nullable=True)

    cpf_p21054: Optional[float] = Field(nullable=True)

    cpf_p21055: Optional[float] = Field(nullable=True)

    cpf_p21056: Optional[float] = Field(nullable=True)

    cpf_p21075: Optional[float] = Field(nullable=True)

    cpf_p21076: Optional[float] = Field(nullable=True)

    cpf_p21077: Optional[float] = Field(nullable=True)

    cpf_p21078: Optional[float] = Field(nullable=True)

    cpf_p21079: Optional[float] = Field(nullable=True)

    cpf_p21080: Optional[float] = Field(nullable=True)

    cpf_p21081: Optional[float] = Field(nullable=True)

    cpf_p21082: Optional[float] = Field(nullable=True)

    cpf_p21083: Optional[float] = Field(nullable=True)

    cpf_p21084: Optional[float] = Field(nullable=True)

    cpf_p21085: Optional[float] = Field(nullable=True)

    cpf_p21086: Optional[float] = Field(nullable=True)

    cpf_p21087: Optional[float] = Field(nullable=True)

    cpf_p21088: Optional[float] = Field(nullable=True)

    cpf_p21089: Optional[float] = Field(nullable=True)

    cpf_p21092: Optional[float] = Field(nullable=True)

    cpf_p21093: Optional[float] = Field(nullable=True)

    cpf_abort: Optional[float] = Field(nullable=True)

    cpf_amin_ipmax: Optional[float] = Field(nullable=True)

    cpf_amin_max: Optional[float] = Field(nullable=True)

    cpf_amin_truby: Optional[float] = Field(nullable=True)

    cpf_area_ipmax: Optional[float] = Field(nullable=True)

    cpf_area_max: Optional[float] = Field(nullable=True)

    cpf_area_truby: Optional[float] = Field(nullable=True)

    cpf_bepmhd_ipmax: Optional[float] = Field(nullable=True)

    cpf_bepmhd_max: Optional[float] = Field(nullable=True)

    cpf_bepmhd_truby: Optional[float] = Field(nullable=True)

    cpf_betmhd_ipmax: Optional[float] = Field(nullable=True)

    cpf_betmhd_max: Optional[float] = Field(nullable=True)

    cpf_betmhd_truby: Optional[float] = Field(nullable=True)

    cpf_bt_ipmax: Optional[float] = Field(nullable=True)

    cpf_bt_max: Optional[float] = Field(nullable=True)

    cpf_bt_truby: Optional[float] = Field(nullable=True)

    cpf_c2ratio: Optional[float] = Field(nullable=True)

    cpf_column_temp_in: Optional[float] = Field(nullable=True)

    cpf_column_temp_out: Optional[float] = Field(nullable=True)

    cpf_creation: Optional[datetime.datetime] = Field(nullable=True)

    cpf_dwmhd_ipmax: Optional[float] = Field(nullable=True)

    cpf_dwmhd_max: Optional[float] = Field(nullable=True)

    cpf_dwmhd_truby: Optional[float] = Field(nullable=True)

    cpf_enbi_max_ss: Optional[float] = Field(nullable=True)

    cpf_enbi_max_sw: Optional[float] = Field(nullable=True)

    cpf_exp_date: Optional[datetime.datetime] = Field(nullable=True)

    cpf_exp_number: Optional[int] = Field(nullable=True)

    cpf_exp_time: Optional[datetime.time] = Field(nullable=True)

    cpf_gdc_duration: Optional[float] = Field(nullable=True)

    cpf_gdc_time: Optional[float] = Field(nullable=True)

    cpf_ibgas_pressure: Optional[float] = Field(nullable=True)

    cpf_ip_av: Optional[float] = Field(nullable=True)

    cpf_ip_max: Optional[float] = Field(nullable=True)

    cpf_jnbi_ipmax: Optional[float] = Field(nullable=True)

    cpf_jnbi_ipmax_ss: Optional[float] = Field(nullable=True)

    cpf_jnbi_ipmax_sw: Optional[float] = Field(nullable=True)

    cpf_jnbi_max: Optional[float] = Field(nullable=True)

    cpf_jnbi_max_ss: Optional[float] = Field(nullable=True)

    cpf_jnbi_max_sw: Optional[float] = Field(nullable=True)

    cpf_jnbi_total: Optional[float] = Field(nullable=True)

    cpf_jnbi_total_ss: Optional[float] = Field(nullable=True)

    cpf_jnbi_total_sw: Optional[float] = Field(nullable=True)

    cpf_jnbi_truby: Optional[float] = Field(nullable=True)

    cpf_jnbi_truby_ss: Optional[float] = Field(nullable=True)

    cpf_jnbi_truby_sw: Optional[float] = Field(nullable=True)

    cpf_johm_ipmax: Optional[float] = Field(nullable=True)

    cpf_johm_max: Optional[float] = Field(nullable=True)

    cpf_johm_total: Optional[float] = Field(nullable=True)

    cpf_johm_truby: Optional[float] = Field(nullable=True)

    cpf_kappa_ipmax: Optional[float] = Field(nullable=True)

    cpf_kappa_max: Optional[float] = Field(nullable=True)

    cpf_kappa_truby: Optional[float] = Field(nullable=True)

    cpf_li_2_ipmax: Optional[float] = Field(nullable=True)

    cpf_li_2_max: Optional[float] = Field(nullable=True)

    cpf_li_2_truby: Optional[float] = Field(nullable=True)

    cpf_li_3_ipmax: Optional[float] = Field(nullable=True)

    cpf_li_3_max: Optional[float] = Field(nullable=True)

    cpf_li_3_truby: Optional[float] = Field(nullable=True)

    cpf_log_base_pressure: Optional[float] = Field(nullable=True)

    cpf_ndl_co2_ipmax: Optional[float] = Field(nullable=True)

    cpf_ndl_co2_max: Optional[float] = Field(nullable=True)

    cpf_ndl_co2_truby: Optional[float] = Field(nullable=True)

    cpf_ne0_ipmax: Optional[float] = Field(nullable=True)

    cpf_ne0_max: Optional[float] = Field(nullable=True)

    cpf_ne0_truby: Optional[float] = Field(nullable=True)

    cpf_ne0ratio_ipmax: Optional[float] = Field(nullable=True)

    cpf_ne0ruby: Optional[float] = Field(nullable=True)

    cpf_ne_bar_ipmax: Optional[float] = Field(nullable=True)

    cpf_ne_yag_bar_ipmax: Optional[float] = Field(nullable=True)

    cpf_ngreenwald_ipmax: Optional[float] = Field(nullable=True)

    cpf_ngreenwaldratio_ipmax: Optional[float] = Field(nullable=True)

    cpf_o2ratio: Optional[float] = Field(nullable=True)

    cpf_objective: Optional[str] = Field(sa_column=Column(Text), nullable=True)

    cpf_pe0_ipmax: Optional[float] = Field(nullable=True)

    cpf_pe0_max: Optional[float] = Field(nullable=True)

    cpf_pe0_truby: Optional[float] = Field(nullable=True)

    cpf_pe0ruby: Optional[float] = Field(nullable=True)

    cpf_pic: Optional[str] = Field(sa_column=Column(Text), nullable=True)

    cpf_pnbi_ipmax: Optional[float] = Field(nullable=True)

    cpf_pnbi_ipmax_ss: Optional[float] = Field(nullable=True)

    cpf_pnbi_ipmax_sw: Optional[float] = Field(nullable=True)

    cpf_pnbi_max: Optional[float] = Field(nullable=True)

    cpf_pnbi_max_ss: Optional[float] = Field(nullable=True)

    cpf_pnbi_max_sw: Optional[float] = Field(nullable=True)

    cpf_pnbi_truby: Optional[float] = Field(nullable=True)

    cpf_pnbi_truby_ss: Optional[float] = Field(nullable=True)

    cpf_pnbi_truby_sw: Optional[float] = Field(nullable=True)

    cpf_pohm_ipmax: Optional[float] = Field(nullable=True)

    cpf_pohm_max: Optional[float] = Field(nullable=True)

    cpf_pohm_truby: Optional[float] = Field(nullable=True)

    cpf_postshot: Optional[str] = Field(sa_column=Column(Text), nullable=True)

    cpf_prad_ipmax: Optional[float] = Field(nullable=True)

    cpf_prad_max: Optional[float] = Field(nullable=True)

    cpf_prad_truby: Optional[float] = Field(nullable=True)

    cpf_pradne2: Optional[float] = Field(nullable=True)

    cpf_preshot: Optional[str] = Field(sa_column=Column(Text), nullable=True)

    cpf_program: Optional[str] = Field(sa_column=Column(Text), nullable=True)

    cpf_pulno: Optional[float] = Field(nullable=True)

    cpf_q95_ipmax: Optional[float] = Field(nullable=True)

    cpf_q95_min: Optional[float] = Field(nullable=True)

    cpf_q95_truby: Optional[float] = Field(nullable=True)

    cpf_reference: Optional[float] = Field(nullable=True)

    cpf_rgeo_ipmax: Optional[float] = Field(nullable=True)

    cpf_rgeo_max: Optional[float] = Field(nullable=True)

    cpf_rgeo_truby: Optional[float] = Field(nullable=True)

    cpf_rinner_da: Optional[float] = Field(nullable=True)

    cpf_rinner_efit: Optional[float] = Field(nullable=True)

    cpf_rmag_efit: Optional[float] = Field(nullable=True)

    cpf_router_da: Optional[float] = Field(nullable=True)

    cpf_router_efit: Optional[float] = Field(nullable=True)

    cpf_sarea_ipmax: Optional[float] = Field(nullable=True)

    cpf_sarea_max: Optional[float] = Field(nullable=True)

    cpf_sarea_truby: Optional[float] = Field(nullable=True)

    cpf_sl: Optional[str] = Field(sa_column=Column(Text), nullable=True)

    cpf_summary: Optional[str] = Field(sa_column=Column(Text), nullable=True)

    cpf_tamin_max: Optional[float] = Field(nullable=True)

    cpf_tarea_max: Optional[float] = Field(nullable=True)

    cpf_tautot_ipmax: Optional[float] = Field(nullable=True)

    cpf_tautot_max: Optional[float] = Field(nullable=True)

    cpf_tautot_truby: Optional[float] = Field(nullable=True)

    cpf_tbepmhd_max: Optional[float] = Field(nullable=True)

    cpf_tbetmhd_max: Optional[float] = Field(nullable=True)

    cpf_tbt_max: Optional[float] = Field(nullable=True)

    cpf_tdwmhd_max: Optional[float] = Field(nullable=True)

    cpf_te0_ipmax: Optional[float] = Field(nullable=True)

    cpf_te0_max: Optional[float] = Field(nullable=True)

    cpf_te0_truby: Optional[float] = Field(nullable=True)

    cpf_te0ratio_ipmax: Optional[float] = Field(nullable=True)

    cpf_te0ruby: Optional[float] = Field(nullable=True)

    cpf_te_yag_bar_ipmax: Optional[float] = Field(nullable=True)

    cpf_tend: Optional[float] = Field(nullable=True)

    cpf_tend_ibgas: Optional[float] = Field(nullable=True)

    cpf_tend_nbi: Optional[float] = Field(nullable=True)

    cpf_tend_nbi_ss: Optional[float] = Field(nullable=True)

    cpf_tend_nbi_sw: Optional[float] = Field(nullable=True)

    cpf_term_code: Optional[float] = Field(nullable=True)

    cpf_tftend: Optional[float] = Field(nullable=True)

    cpf_tftstart: Optional[float] = Field(nullable=True)

    cpf_tipmax: Optional[float] = Field(nullable=True)

    cpf_tkappa_max: Optional[float] = Field(nullable=True)

    cpf_tli_2_max: Optional[float] = Field(nullable=True)

    cpf_tli_3_max: Optional[float] = Field(nullable=True)

    cpf_tndl_co2_max: Optional[float] = Field(nullable=True)

    cpf_tne0_max: Optional[float] = Field(nullable=True)

    cpf_tpe0_max: Optional[float] = Field(nullable=True)

    cpf_tpnbi_max: Optional[float] = Field(nullable=True)

    cpf_tpnbi_max_ss: Optional[float] = Field(nullable=True)

    cpf_tpnbi_max_sw: Optional[float] = Field(nullable=True)

    cpf_tpohm_max: Optional[float] = Field(nullable=True)

    cpf_tprad_max: Optional[float] = Field(nullable=True)

    cpf_tq95_min: Optional[float] = Field(nullable=True)

    cpf_trgeo_max: Optional[float] = Field(nullable=True)

    cpf_truby: Optional[float] = Field(nullable=True)

    cpf_tsarea_max: Optional[float] = Field(nullable=True)

    cpf_tstart: Optional[float] = Field(nullable=True)

    cpf_tstart_ibgas: Optional[float] = Field(nullable=True)

    cpf_tstart_nbi: Optional[float] = Field(nullable=True)

    cpf_tstart_nbi_ss: Optional[float] = Field(nullable=True)

    cpf_tstart_nbi_sw: Optional[float] = Field(nullable=True)

    cpf_ttautot_max: Optional[float] = Field(nullable=True)

    cpf_tte0_max: Optional[float] = Field(nullable=True)

    cpf_tvol_max: Optional[float] = Field(nullable=True)

    cpf_twmhd_max: Optional[float] = Field(nullable=True)

    cpf_tzeff_max: Optional[float] = Field(nullable=True)

    cpf_useful: Optional[float] = Field(nullable=True)

    cpf_vol_ipmax: Optional[float] = Field(nullable=True)

    cpf_vol_max: Optional[float] = Field(nullable=True)

    cpf_vol_truby: Optional[float] = Field(nullable=True)

    cpf_wmhd_ipmax: Optional[float] = Field(nullable=True)

    cpf_wmhd_max: Optional[float] = Field(nullable=True)

    cpf_wmhd_truby: Optional[float] = Field(nullable=True)

    cpf_zeff_ipmax: Optional[float] = Field(nullable=True)

    cpf_zeff_max: Optional[float] = Field(nullable=True)

    cpf_zeff_truby: Optional[float] = Field(nullable=True)

    cpf_zmag_efit: Optional[float] = Field(nullable=True)
