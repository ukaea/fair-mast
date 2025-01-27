import logging
import sqlite3
import uuid
from enum import Enum
from pathlib import Path

import click
import dask
import numpy as np
import pandas as pd
from psycopg2.extras import Json
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy_utils.functions import (
    create_database,
    database_exists,
    drop_database,
)
from sqlmodel import SQLModel

# Do not remove. Sqlalchemy needs this import to create tables
from . import models  # noqa: F401
from .environment import DB_NAME, SQLALCHEMY_DATABASE_URL, SQLALCHEMY_DEBUG

logging.basicConfig(level=logging.INFO)

LAST_MAST_SHOT = 30473  # This is the last MAST shot before MAST-U


class Context(str, Enum):
    DCAT = "http://www.w3.org/ns/dcat#"
    DCT = "http://purl.org/dc/terms/"
    FOAF = "http://xmlns.com/foaf/0.1/"
    SCHEMA = "schema.org"
    DQV = "http://www.w3.org/ns/dqv#"
    SDMX = "http://purl.org/linked-data/sdmx/2009/measure#"


base_context = {
    "schema": Context.SCHEMA,
    "dqv": Context.DQV,
    "sdmx-measure": Context.SDMX,
    "dcat": Context.DCAT,
    "foaf": Context.FOAF,
    "dct": Context.DCT,
}


class URLType(Enum):
    """Enum type for different types of storage endpoint"""

    S3 = 1
    SSH = 2


def get_dataset_uuid(shot: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_OID, str(shot)))


def get_dataset_item_uuid(name: str, shot: int) -> str:
    oid_name = name + "/" + str(shot)
    return str(uuid.uuid5(uuid.NAMESPACE_OID, oid_name))


def connect(uri):
    engine = create_engine(uri, echo=SQLALCHEMY_DEBUG)
    metadata_obj = MetaData()
    metadata_obj.reflect(engine)
    return metadata_obj, engine


def lookup_status_code(status):
    """Status code mapping from the numeric representation to the meaning"""
    lookup = {-1: "Very Bad", 0: "Bad", 1: "Not Checked", 2: "Checked", 3: "Validated"}
    return lookup[status]


def normalize_signal_name(name):
    """Make the signal name sensible"""
    signal_name = (
        str(name)
        .strip("_")
        .strip()
        .replace("/", "_")
        .replace(" ", "_")
        .replace(",", "_")
        .replace("(", "_")
        .replace(")", "")
    )
    return signal_name


class MetadataReader:
    def __init__(self, uri):
        db_path = Path(uri).absolute()
        self.con = sqlite3.connect(db_path)

    def read(self, table_name: str, index_col: str = "uuid") -> pd.DataFrame:
        df = pd.read_sql(
            f"SELECT * FROM {table_name}", con=self.con, index_col=index_col
        )
        return df


class DBCreationClient:
    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name

    def create_signals(self, table_name: str, reader: MetadataReader):
        df = reader.read("signals")

        # Convert to lists
        df["shape"] = df["shape"].map(
            lambda x: list(map(int, x.split(","))) if x != "" else None
        )
        df["dimensions"] = df["dimensions"].map(lambda x: list(x.split(",")))

        df.to_sql(table_name, self.uri, if_exists="append")

    def create_sources(self, table_name, reader: MetadataReader):
        df = reader.read("sources")
        df.to_sql(table_name, self.uri, if_exists="append")

    def create_database(self):
        if database_exists(self.uri):
            drop_database(self.uri)

        create_database(self.uri)

        self.metadata_obj, self.engine = connect(self.uri)

        engine = create_engine(self.uri, echo=True)
        SQLModel.metadata.create_all(engine)
        # recreate the engine/metadata object
        self.metadata_obj, self.engine = connect(self.uri)
        return engine

    def create_user(self):
        engine = create_engine(self.uri, echo=True)
        name = password = "public_user"
        drop_user = text(f"DROP USER IF EXISTS {name}")
        create_user_query = text(f"CREATE USER {name} WITH PASSWORD :password;")
        grant_privledges = text(f"GRANT CONNECT ON DATABASE {self.db_name} TO {name};")
        grant_public_schema = text(f"GRANT USAGE ON SCHEMA public TO {name};")
        grant_public_schema_tables = text(
            f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {name};"
        )
        with engine.connect() as conn:
            conn.execute(drop_user)
            conn.execute(create_user_query, {"password": password})
            conn.execute(grant_privledges)
            conn.execute(grant_public_schema)
            conn.execute(grant_public_schema_tables)

    def create_cpf_summary(self, data_path: Path):
        """Create the CPF summary table"""
        paths = data_path.glob("cpf/*_cpf_columns.parquet")
        for path in paths:
            df = pd.read_parquet(path)
            # replacing col name row values with cpf alias value in shotmodel
            df["name"] = df["name"].apply(
                lambda x: models.ShotModel.__fields__.get("cpf_" + x.lower()).alias
                if models.ShotModel.__fields__.get("cpf_" + x.lower())
                else x
            )
            df.to_sql("cpf_summary", self.uri, if_exists="replace")

    def create_scenarios(self, data_path: Path):
        """Create the scenarios metadata table"""
        shot_file_name = data_path / "shots.parquet"
        shot_metadata = pd.read_parquet(shot_file_name)
        ids = shot_metadata["scenario_id"].unique()
        scenarios = shot_metadata["scenario"].unique()

        data = pd.DataFrame(dict(id=ids, name=scenarios)).set_index("id")
        data = data.dropna()
        data.to_sql("scenarios", self.uri, if_exists="append")

    def create_shots(
        self, table_name: str, endpoint: str, data_path: Path, reader: MetadataReader
    ):
        """Create the shot metadata table"""
        try:
            df = reader.read("sources")
            shot_ids = df.shot_id.unique()
        except Exception:
            df = pd.read_parquet(data_path / "sources.parquet")
            shot_ids = df.shot_id.unique()

        shot_file_name = data_path / "shots.parquet"
        shot_metadata = pd.read_parquet(shot_file_name)
        shot_metadata = shot_metadata.loc[shot_metadata["shot_id"] <= LAST_MAST_SHOT]
        shot_metadata = shot_metadata.loc[shot_metadata.shot_id.isin(shot_ids)]
        shot_metadata = shot_metadata.set_index("shot_id", drop=True)
        shot_metadata = shot_metadata.sort_index()

        shot_metadata["scenario"] = shot_metadata["scenario_id"]
        shot_metadata["facility"] = "MAST"
        shot_metadata = shot_metadata.drop(["scenario_id", "reference_id"], axis=1)
        shot_metadata["uuid"] = shot_metadata.index.map(get_dataset_uuid)
        shot_metadata["url"] = (
            f"{endpoint}/" + shot_metadata.index.astype(str) + ".zarr"
        )

        paths = data_path.glob("cpf/*_cpf_data.parquet")
        cpfs = []
        for path in paths:
            cpf_metadata = read_cpf_metadata(path)
            cpf_metadata = cpf_metadata.set_index("shot_id", drop=True)
            cpf_metadata = cpf_metadata.sort_index()
            cpfs.append(cpf_metadata)

        cpfs = pd.concat(cpfs, axis=0)
        cpfs = cpfs = cpfs.reset_index()
        cpfs = cpfs.loc[cpfs.shot_id <= LAST_MAST_SHOT]
        cpfs = cpfs.drop_duplicates(subset="shot_id")
        cpfs = cpfs.set_index("shot_id")

        shot_metadata = pd.merge(
            shot_metadata,
            cpfs,
            left_on="shot_id",
            right_on="shot_id",
            how="left",
        )

        shot_metadata.to_sql(table_name, self.uri, if_exists="append")

    def create_serve_dataset(self):
        data = {
            "servesdataset": [
                [
                    "host/json/dataset/shots",
                    "host/json/dataset/shots/aggregate",
                    "host/json/dataset/shots/shot_id",
                    "host/json/dataset/shots/shot_id/signal",
                    "host/json/dataset/signals",
                    "host/json/dataset/signals/uuid",
                    "host/json/dataset/signals/uuid/shots",
                    "host/json/dataset/scenario",
                    "host/json/dataset/source",
                    "host/json/dataset/source/aggregate",
                    "host/json/dataset/source/name",
                    "host/json/dataset/cpfsummary",
                ]
            ],
            "theme": [
                [
                    "host/json/dataset/shots",
                    "host/json/dataset/signal",
                    "host/json/dataset/source",
                    "host/json/dataset/scenario",
                    "host/json/dataset/cpfsummary",
                ]
            ],
            "type": ["dcat:DataService"],
            "id": ["host/json/data-service"],
            "title": ["FAIR MAST Data Service"],
            "description": [
                "UKAEA Data Service providing access to the FAIR MAST dataset. \
                          This includes signal, source, shots and other datasets."
            ],
            "endpointurl": ["host"],
        }
        publisher = {
            "dct__publisher": {
                "type_": "foaf:Organization",
                "foaf:name": "UKAEA",
                "foaf:homepage": "http://ukaea.uk",
            }
        }
        df = pd.DataFrame(data, index=[0])
        df["publisher"] = Json(publisher)
        df["id"] = "host/json/data-service"
        df["context"] = Json(dict(list(base_context.items())[-3:]))
        df.to_sql("dataservice", self.uri, if_exists="append", index=False)


def read_cpf_metadata(cpf_file_name: Path) -> pd.DataFrame:
    cpf_metadata = pd.read_parquet(cpf_file_name)
    cpf_metadata["shot_id"] = cpf_metadata.shot_id.astype(int)
    columns = {
        name: f'cpf_{name.split("__")[0].lower()}'
        for name in cpf_metadata.columns
        if name != "shot_id"
    }
    cpf_metadata = cpf_metadata.rename(columns=columns)
    cpf_metadata = cpf_metadata.replace("nan", np.nan)
    return cpf_metadata


def create_db_and_tables(data_path: str, uri: str, name: str):
    data_path = Path(data_path)

    client = DBCreationClient(uri, name)
    client.create_database()
    # populate the database tables
    logging.info("Create CPF summary")
    client.create_cpf_summary(data_path)

    logging.info("Create Scenarios")
    client.create_scenarios(data_path)

    level1_reader = MetadataReader(data_path / "level1.csd3.db")

    logging.info("Create Shots")
    client.create_shots("shots", "s3://mast/level1/shots", data_path, level1_reader)

    logging.info("Create L1 Sources")
    client.create_sources("sources", level1_reader)

    logging.info("Create L1 Signals")
    client.create_signals("signals", level1_reader)

    level2_reader = MetadataReader(data_path / "level2.csd3.db")

    logging.info("Create L2 shots")
    client.create_shots(
        "level2_shots", "s3://mast/level2/shots", data_path, level2_reader
    )

    logging.info("Create L2 sources")
    client.create_sources("level2_sources", level2_reader)

    logging.info("Create L2 signals")
    client.create_signals("level2_signals", level2_reader)

    logging.info("Create Data Service Endpoints")
    client.create_serve_dataset()


@click.command()
@click.argument("data_path", default="~/mast-data/meta")
def main(data_path):
    create_db_and_tables(data_path, SQLALCHEMY_DATABASE_URL, DB_NAME)


if __name__ == "__main__":
    dask.config.set({"dataframe.convert-string": False})
    main()
