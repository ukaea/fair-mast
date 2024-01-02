from pathlib import Path
import pandas as pd
import dask
import dask.dataframe as dd
import click
import json
from tqdm import tqdm
from sqlalchemy_utils.functions import (
    drop_database,
    database_exists,
    create_database,
)
from sqlmodel import SQLModel
from sqlalchemy import dialects
from sqlalchemy import types
from sqlalchemy import create_engine, MetaData, select
from .environment import SQLALCHEMY_DATABASE_URL, SQLALCHEMY_DEBUG
from . import models


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
    def __init__(self, uri: str):
        self.uri = uri

    def create_database(self):
        if database_exists(self.uri):
            drop_database(self.uri)
        create_database(self.uri)

        self.metadata_obj, self.engine = connect(self.uri)

        engine = create_engine(self.uri, echo=True)
        SQLModel.metadata.create_all(engine)
        # recreate the engine/metadata object
        self.metadata_obj, self.engine = connect(self.uri)

    def create_cpf_summary(self, cpf_metadata: pd.DataFrame):
        """Create the CPF summary table"""
        cpf_metadata.to_sql("cpf_summary", self.uri, if_exists="replace")

    def create_scenarios(self, shot_metadata: pd.DataFrame):
        """Create the scenarios metadata table"""
        ids = shot_metadata["scenario_id"].unique()
        scenarios = shot_metadata["scenario"].unique()

        data = pd.DataFrame(dict(id=ids, name=scenarios)).set_index("id")
        data = data.dropna()
        data.to_sql("scenarios", self.uri, if_exists="append")

    def create_shots(self, shot_metadata: pd.DataFrame):
        """Create the shot metadata table"""
        shot_metadata["facility"] = "MAST"
        shot_metadata = shot_metadata.set_index("shot_id")
        shot_metadata["scenario"] = shot_metadata["scenario_id"]
        shot_metadata = shot_metadata.drop(["scenario_id", "reference_id"], axis=1)
        shot_metadata.to_sql("shots", self.uri, if_exists="append")

    def create_signal_datasets(self, signal_dataset_metadata: pd.DataFrame):
        """Create the signal metadata table"""
        # signal_dataset_metadata["context_"] =
        signal_dataset_metadata["name"] = signal_dataset_metadata["name"].map(
            normalize_signal_name
        )
        signal_dataset_metadata["description"] = signal_dataset_metadata["description"]
        signal_dataset_metadata["signal_type"] = signal_dataset_metadata["type"]
        signal_dataset_metadata["quality"] = signal_dataset_metadata[
            "signal_status"
        ].map(lookup_status_code)
        signal_dataset_metadata["dimensions"] = signal_dataset_metadata[
            "dimensions"
        ].map(list, meta=pd.Series(dtype="object"))
        signal_dataset_metadata["doi"] = ""
        signal_dataset_metadata["url"] = signal_dataset_metadata["name"].map(
            lambda name: f"s3://mast/{name}.zarr"
        )

        signal_metadata = signal_dataset_metadata[
            [
                # "context_",
                "name",
                "description",
                "signal_type",
                "quality",
                "dimensions",
                "rank",
                "units",
                "doi",
                "url",
            ]
        ]

        def dict2json(dictionary):
            return json.dumps(dictionary, ensure_ascii=False)

        # signal_metadata["context_"] = signal_metadata["context_"].map(dict2json)

        signal_metadata.to_sql(
            "signal_datasets", self.uri, if_exists="append", index=False
        )

    def create_signals(self, signals_metadata: pd.DataFrame, n_partitions=10):
        # signals_metadata = signals_metadata.repartition(npartitions=10)
        signals_metadata = signals_metadata.rename(columns=dict(shot_nums="shot_id"))

        signal_datasets_table = self.metadata_obj.tables["signal_datasets"]
        stmt = select(
            signal_datasets_table.c.signal_dataset_id, signal_datasets_table.c.name
        )
        signal_datasets = dd.read_sql(stmt, con=self.uri, index_col="signal_dataset_id")
        signal_datasets = signal_datasets.reset_index()
        signal_datasets = signal_datasets.repartition(n_partitions)

        for part in tqdm(signal_datasets.partitions, total=n_partitions):
            df = dd.merge(signals_metadata, part, left_on="name", right_on="name")
            df["quality"] = df["signal_status"].map(lookup_status_code)
            df["shape"] = df["shape"].map(
                lambda x: x.tolist(), meta=pd.Series(dtype="object")
            )

            df["url"] = (
                "s3://mast/"
                + df["name"].map(normalize_signal_name)
                + ".zarr/"
                + df["shot_id"]
            )

            df["signal_name"] = df["name"].map(normalize_signal_name)

            df["name"] = df["name"] + "_" + df["shot_id"]

            df["version"] = 0

            columns = [
                "signal_dataset_id",
                "signal_name",
                "shot_id",
                "quality",
                "shape",
                "name",
                "url",
                "version",
            ]
            df = df[columns]
            df = df.set_index("shot_id")
            df.to_sql("signals", self.uri, if_exists="append")

    def create_image_metadata(self, signal_dataset_metadata: pd.DataFrame):
        signal_datasets_table = self.metadata_obj.tables["signal_datasets"]
        stmt = select(
            signal_datasets_table.c.signal_dataset_id, signal_datasets_table.c.name
        )
        signal_datasets = dd.read_sql(stmt, con=self.uri, index_col="signal_dataset_id")
        signal_datasets = signal_datasets.reset_index()

        signals_metadata = dd.merge(
            signal_dataset_metadata, signal_datasets, left_on="name", right_on="name"
        )

        columns = ["signal_dataset_id", "IMAGE_SUBCLASS", "IMAGE_VERSION", "format"]
        signals_metadata = signals_metadata[columns]
        signals_metadata = signals_metadata.rename(
            columns={
                "IMAGE_SUBCLASS": "subclass",
                "IMAGE_VERSION": "version",
            },
        )
        signals_metadata = signals_metadata.set_index("signal_dataset_id")
        signals_metadata.to_sql("image_metadata", self.uri, if_exists="append")

    def create_sources(self, source_metadata: pd.DataFrame):
        source_metadata["name"] = source_metadata["source_alias"]
        source_metadata["source_type"] = source_metadata["type"]
        source_metadata = source_metadata[["description", "name", "source_type"]]
        source_metadata = source_metadata.drop_duplicates()
        source_metadata = source_metadata.sort_values("name")
        source_metadata.to_sql("sources", self.uri, if_exists="append", index=False)

    def create_shot_source_links(self, sources_metadata: pd.DataFrame):
        sources_metadata["source"] = sources_metadata["source_alias"]
        sources_metadata["quality"] = sources_metadata["status"].map(lookup_status_code)
        sources_metadata["shot_id"] = sources_metadata["shot"].astype(int)
        sources_metadata = sources_metadata[
            ["source", "shot_id", "quality", "pass", "format"]
        ]
        sources_metadata = sources_metadata.sort_values("source")
        sources_metadata.to_sql(
            "shot_source_link", self.uri, if_exists="append", index=False
        )


def read_cpf_summary_metadata(cpf_summary_file_name: Path) -> pd.DataFrame:
    cpf_summary_metadata = dd.read_parquet(cpf_summary_file_name)
    return cpf_summary_metadata


def read_cpf_metadata(cpf_file_name: Path) -> pd.DataFrame:
    cpf_metadata = dd.read_parquet(cpf_file_name)
    cpf_metadata["shot_id"] = cpf_metadata.shot_id.astype(int)
    columns = {
        name: f'cpf_{name.split("__")[0].lower()}'
        for name in cpf_metadata.columns
        if name != "shot_id"
    }
    cpf_metadata = cpf_metadata.rename(columns=columns)
    for column in cpf_metadata.columns:
        cpf_metadata[column] = dd.to_numeric(cpf_metadata[column], errors="coerce")
    return cpf_metadata


def read_shot_metadata(
    shot_file_name: Path, cpf_metadata: pd.DataFrame
) -> pd.DataFrame:
    shot_metadata = dd.read_parquet(shot_file_name)
    shot_metadata = dd.merge(
        shot_metadata, cpf_metadata, left_on="shot_id", right_on="shot_id", how="outer"
    )
    return shot_metadata


def read_signal_dataset_metadata(signal_file_name: Path) -> pd.DataFrame:
    signal_metadata = dd.read_parquet(signal_file_name)
    return signal_metadata


def read_sources_metadata(source_file_name: Path) -> pd.DataFrame:
    source_metadata = dd.read_parquet(source_file_name)
    return source_metadata


def read_signals_metadata(sample_file_name: Path) -> pd.DataFrame:
    sample_metadata = dd.read_parquet(sample_file_name)
    return sample_metadata


@click.command()
@click.argument("data_path", default="~/mast-data/meta")
def create_db_and_tables(data_path):
    data_path = Path(data_path)

    client = DBCreationClient(SQLALCHEMY_DATABASE_URL)
    client.create_database()

    # read meta data from preprocessed files
    cpf_summary_file_name = data_path / "cpf_summary.parquet"
    cpf_file_name = data_path / "cpf_data.parquet"
    shot_file_name = data_path / "shot_metadata.parquet"
    signal_dataset_file_name = data_path / "signal_metadata.parquet"
    source_file_name = data_path / "sources_metadata.parquet"
    sample_file_name = data_path / "sample_summary_metadata.parquet"

    cpf_summary_metadata = read_cpf_summary_metadata(cpf_summary_file_name)
    cpf_metadata = read_cpf_metadata(cpf_file_name)
    shot_metadata = read_shot_metadata(shot_file_name, cpf_metadata)
    signal_dataset_metadata = read_signal_dataset_metadata(signal_dataset_file_name)
    source_metadata = read_sources_metadata(source_file_name)
    signals_metadata = read_signals_metadata(sample_file_name)

    # populate the database tables
    print("Create CPF summary")
    client.create_cpf_summary(cpf_summary_metadata)
    print("Create Scenarios")
    client.create_scenarios(shot_metadata)
    print("Create Shots")
    client.create_shots(shot_metadata)
    print("Create Datasets")
    client.create_signal_datasets(signal_dataset_metadata)
    print("Create Signals")
    client.create_signals(signals_metadata)
    print("Create Sources")
    client.create_sources(source_metadata)
    print("Create Shot Source Links")
    client.create_shot_source_links(source_metadata)

    # add the image data
    image_signal_dataset_file_name = data_path / "image_signal_metadata.parquet"
    image_signal_file_name = data_path / "image_sample_metadata.parquet"

    image_signal_dataset = read_signal_dataset_metadata(image_signal_dataset_file_name)
    image_signals = read_signals_metadata(image_signal_file_name)

    # client.create_signal_datasets(image_signal_dataset)
    # client.create_image_metadata(image_signal_dataset)
    # client.create_signals(image_signals)


if __name__ == "__main__":
    dask.config.set({"dataframe.convert-string": False})
    create_db_and_tables()
