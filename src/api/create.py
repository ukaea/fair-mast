import logging
import math
import uuid
from enum import Enum
from pathlib import Path

import click
import dask
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from psycopg2.extras import Json
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy_utils.functions import create_database, database_exists, drop_database
from sqlmodel import SQLModel
from tqdm import tqdm

# Do not remove. Sqlalchemy needs this import to create tables
from . import models  # noqa: F401
from .environment import DB_NAME, SQLALCHEMY_DATABASE_URL, SQLALCHEMY_DEBUG

logging.basicConfig(level=logging.INFO)

LAST_MAST_SHOT = 30471  # This is the last MAST shot before MAST-U


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


class DBCreationClient:
    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name

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
        dfs = [pd.read_parquet(path) for path in paths]
        df = pd.concat(dfs).reset_index(drop=True)
        df["context"] = [Json(base_context)] * len(df)
        df = df.drop_duplicates(subset=["name"])
        df["name"] = df["name"].apply(
                lambda x: models.ShotModel.__fields__.get("cpf_" + x.lower()).alias
                if models.ShotModel.__fields__.get("cpf_" + x.lower())
                else x
            )
        df.to_sql("cpf_summary", self.uri, if_exists="append")

    def create_scenarios(self, data_path: Path):
        """Create the scenarios metadata table"""
        shot_file_name = data_path / "shots.parquet"
        shot_metadata = pd.read_parquet(shot_file_name)
        ids = shot_metadata["scenario_id"].unique()
        scenarios = shot_metadata["scenario"].unique()

        data = pd.DataFrame(dict(id=ids, name=scenarios)).set_index("id")
        data = data.dropna()
        data["context"] = [Json(base_context)] * len(data)
        data.to_sql("scenarios", self.uri, if_exists="append")

    def create_shots(self, data_path: Path):
        """Create the shot metadata table"""
        sources_file = data_path / "sources.parquet"
        sources_metadata = pd.read_parquet(sources_file)
        shot_ids = sources_metadata.shot_id.unique()

        shot_file_name = data_path / "shots.parquet"
        shot_metadata = pd.read_parquet(shot_file_name)
        shot_metadata = shot_metadata.loc[shot_metadata["shot_id"] <= LAST_MAST_SHOT]
        shot_metadata = shot_metadata.loc[shot_metadata.shot_id.isin(shot_ids)]
        shot_metadata = shot_metadata.set_index("shot_id", drop=True)
        shot_metadata = shot_metadata.sort_index()

        shot_metadata["scenario"] = shot_metadata["scenario_id"]
        shot_metadata["facility"] = "MAST"
        shot_metadata = shot_metadata.drop(["scenario_id", "reference_id"], axis=1)
        shot_metadata["context"] = [Json(base_context)] * len(shot_metadata)
        shot_metadata["uuid"] = shot_metadata.index.map(get_dataset_uuid)
        shot_metadata["url"] = (
            "s3://mast/level1/shots/" + shot_metadata.index.astype(str) + ".zarr"
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

        shot_metadata.to_sql("shots", self.uri, if_exists="append")

    def create_signals(self, data_path: Path):
        logging.info(f"Loading signals from {data_path}")
        file_name = data_path / "signals.parquet"

        parquet_file = pq.ParquetFile(file_name)
        batch_size = 10000
        n = math.ceil(parquet_file.scan_contents() / batch_size)
        for batch in tqdm(parquet_file.iter_batches(batch_size=batch_size), total=n):
            signals_metadata = batch.to_pandas()

            signals_metadata = signals_metadata.rename(
                columns=dict(shot_nums="shot_id")
            )

            df = signals_metadata
            df = df[df.shot_id <= LAST_MAST_SHOT]
            df = df.drop_duplicates(subset="uuid")
            df["context"] = [Json(base_context)] * len(df)
            df["shape"] = df["shape"].map(lambda x: x.tolist())
            df["dimensions"] = df["dimensions"].map(lambda x: x.tolist())
            df["url"] = (
                "s3://mast/level1/shots/"
                + df["shot_id"].map(str)
                + ".zarr/"
                + df["name"]
            )

            uda_attributes = ["uda_name", "mds_name", "file_name", "format"]
            df = df.drop(uda_attributes, axis=1)
            df["shot_id"] = df.shot_id.astype(int)
            df = df.set_index("shot_id", drop=True)
            df["description"] = df.description.map(lambda x: "" if x is None else x)
            df.to_sql("signals", self.uri, if_exists="append")

    def create_sources(self, data_path: Path):
        source_metadata = pd.read_parquet(data_path / "sources.parquet")
        source_metadata = source_metadata.drop_duplicates("uuid")
        source_metadata = source_metadata.loc[source_metadata.shot_id <= LAST_MAST_SHOT]
        source_metadata["context"] = [Json(base_context)] * len(source_metadata)
        source_metadata["url"] = (
            "s3://mast/level1/shots/"
            + source_metadata["shot_id"].map(str)
            + ".zarr/"
            + source_metadata["name"]
        )
        column_names = [
            "uuid",
            "shot_id",
            "name",
            "description",
            "quality",
            "url",
            "context",
        ]
        source_metadata = source_metadata[column_names]
        source_metadata.to_sql("sources", self.uri, if_exists="append", index=False)

    def create_serve_dataset(self):
        data = {
            "servesdataset": [
                [
                    "host/json/shots",
                    "host/json/shots/aggregate",
                    "host/json/shots/shot_id",
                    "host/json/shots/shot_id/signal",
                    "host/json/signals",
                    "host/json/signals/uuid",
                    "host/json/signals/uuid/shots",
                    "host/json/scenario",
                    "host/json/source",
                    "host/json/source/aggregate",
                    "host/json/source/name",
                    "host/json/cpfsummary",
                ]
            ],
            "theme": [
                [
                    "host/json/shots",
                    "host/json/signal",
                    "host/json/source",
                    "host/json/scenario",
                    "host/json/cpfsummary",
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


@click.command()
@click.argument("data_path", default="~/mast-data/meta")
def create_db_and_tables(data_path):
    data_path = Path(data_path)

    client = DBCreationClient(SQLALCHEMY_DATABASE_URL, DB_NAME)
    client.create_database()

    # populate the database tables
    logging.info("Create CPF summary")
    client.create_cpf_summary(data_path)

    logging.info("Create Scenarios")
    client.create_scenarios(data_path)

    logging.info("Create Shots")
    client.create_shots(data_path)

    logging.info("Create Sources")
    client.create_sources(data_path)

    logging.info("Create Signals")
    client.create_signals(data_path)

    logging.info("Create dataservice")
    client.create_serve_dataset()

    client.create_user()


if __name__ == "__main__":
    dask.config.set({"dataframe.convert-string": False})
    # print(models.ShotModel.__fields__)
    create_db_and_tables()
