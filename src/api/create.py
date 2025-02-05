import logging
import math
import sqlite3
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

    def create_signals(
        self,
        data_path: Path,
        table_name: str,
        url: str,
        endpoint_url: str,
        signals_file: str,
    ):
        df = pd.read_parquet(data_path / "shots.parquet")
        shot_ids = df.shot_id.unique()

        parquet_file = pq.ParquetFile(data_path / signals_file)
        batch_size = 100000
        n = math.ceil(parquet_file.scan_contents() / batch_size)
        for batch in tqdm(parquet_file.iter_batches(batch_size=batch_size), total=n):
            df = batch.to_pandas()
            df = df.reset_index(drop=True)
            df = df.drop_duplicates(["uuid"])
            df = df.loc[df.shot_id.isin(shot_ids)]
            df["context"] = [Json(base_context)] * len(df)

            # Convert to lists
            df["shape"] = df["shape"].map(
                lambda x: list(map(int, x.split(","))) if x != "" else None
            )
            df["dimensions"] = df["dimensions"].map(lambda x: list(x.split(",")))

            df["url"] = f"{url}/" + df.shot_id.astype(str) + ".zarr"
            df["endpoint_url"] = endpoint_url

            df.to_sql(table_name, self.uri, if_exists="append", index=False)

    def create_sources(
        self, data_path, table_name, url, endpoint_url: str, sources_file: str
    ):
        df = pd.read_parquet(data_path / "shots.parquet")
        shot_ids = df.shot_id.unique()

        df = pd.read_parquet(data_path / sources_file)
        df = df.reset_index(drop=True)
        df = df.loc[df.shot_id.isin(shot_ids)]
        df["endpoint_url"] = endpoint_url
        df["context"] = [Json(base_context)] * len(df)

        df = df.drop_duplicates(["uuid"])
        df["url"] = f"{url}/" + df.shot_id.astype(str) + ".zarr"
        df.to_sql(table_name, self.uri, if_exists="append", index=False)

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
        paths = data_path.glob("*_cpf_columns.parquet")
        for path in paths:
            df = pd.read_parquet(path)
            # replacing col name row values with cpf alias value in shotmodel
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

    def create_shots(
        self,
        table_name: str,
        url: str,
        endpoint_url: str,
        data_path: Path,
        sources_file: str,
        cpf_file: str,
    ):
        """Create the shot metadata table"""
        df = pd.read_parquet(data_path / sources_file)
        shot_ids = df.shot_id.unique()

        shot_file_name = data_path / "shots.parquet"
        shot_metadata = pd.read_parquet(shot_file_name)
        shot_metadata = shot_metadata.loc[shot_metadata.shot_id.isin(shot_ids)]
        shot_metadata = shot_metadata.set_index("shot_id", drop=True)
        shot_metadata = shot_metadata.sort_index()

        shot_metadata["scenario"] = shot_metadata["scenario_id"]
        shot_metadata["facility"] = shot_metadata.index.map(
            lambda x: "MAST" if x <= LAST_MAST_SHOT else "MAST-U"
        )
        shot_metadata = shot_metadata.drop(["scenario_id", "reference_id"], axis=1)
        shot_metadata["context"] = [Json(base_context)] * len(shot_metadata)
        shot_metadata["uuid"] = shot_metadata.index.map(get_dataset_uuid)
        shot_metadata["url"] = f"{url}/" + shot_metadata.index.astype(str) + ".zarr"
        shot_metadata["endpoint_url"] = endpoint_url

        cpf_metadata = read_cpf_metadata(data_path / cpf_file)
        cpf_metadata = cpf_metadata.set_index("shot_id", drop=True)
        cpf_metadata = cpf_metadata.sort_index()
        cpf_metadata["cpf_exp_number"] = cpf_metadata["cpf_exp_number"].map(
            lambda x: float(x)
        )
        cpf_metadata = cpf_metadata.drop("cpf_sl", axis=1)

        cpf_metadata = cpf_metadata = cpf_metadata.reset_index()
        cpf_metadata = cpf_metadata.drop_duplicates(subset="shot_id")
        cpf_metadata = cpf_metadata.set_index("shot_id")

        shot_metadata = pd.merge(
            shot_metadata,
            cpf_metadata,
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

    url = "s3://mast/level1/shots"
    sources_file = "mast-level1-sources.parquet"
    signals_file = "mast-level1-signals.parquet"
    endpoint_url = "https://s3.echo.stfc.ac.uk"

    logging.info("Create MAST L1 shots")
    client.create_shots(
        "shots",
        url,
        endpoint_url,
        data_path,
        sources_file,
        cpf_file="mast_cpf_data.parquet",
    )

    logging.info("Create MAST L1 sources")
    client.create_sources(data_path, "sources", url, endpoint_url, sources_file)

    logging.info("Create MAST L1 signals")
    client.create_signals(data_path, "signals", url, endpoint_url, signals_file)

    url = "s3://mast/level2/shots"
    sources_file = "mast-level2-sources.parquet"
    signals_file = "mast-level2-signals.parquet"
    endpoint_url = "https://s3.echo.stfc.ac.uk"

    logging.info("Create MAST L2 shots")
    client.create_shots(
        "level2_shots",
        url,
        endpoint_url,
        data_path,
        sources_file,
        cpf_file="mast_cpf_data.parquet",
    )

    logging.info("Create MAST L2 sources")
    client.create_sources(data_path, "level2_sources", url, endpoint_url, sources_file)

    logging.info("Create MAST L2 signals")
    client.create_signals(data_path, "level2_signals", url, endpoint_url, signals_file)

    url = "s3://fairmast/mastu/level2/shots"
    sources_file = "mastu-level2-sources.parquet"
    signals_file = "mastu-level2-signals.parquet"
    endpoint_url = "http://mon3.cepheus.hpc.l:8000"

    logging.info("Create MAST-U L2 shots")
    client.create_shots(
        "level2_shots",
        url,
        endpoint_url,
        data_path,
        sources_file,
        cpf_file="mastu_cpf_data.parquet",
    )

    logging.info("Create MAST-U L2 sources")
    client.create_sources(data_path, "level2_sources", url, endpoint_url, sources_file)

    logging.info("Create MAST-U L2 signals")
    client.create_signals(data_path, "level2_signals", url, endpoint_url, signals_file)

    logging.info("Create Data Service Endpoints")
    client.create_serve_dataset()


@click.command()
@click.argument("data_path", default="~/mast-data/meta")
def main(data_path):
    create_db_and_tables(data_path, SQLALCHEMY_DATABASE_URL, DB_NAME)


if __name__ == "__main__":
    dask.config.set({"dataframe.convert-string": False})
    main()
