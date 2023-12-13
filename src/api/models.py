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

