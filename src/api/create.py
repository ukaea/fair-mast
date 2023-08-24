from pathlib import Path
import pandas as pd
import click
import json
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


class DBCreationClient:
    def __init__(self, uri: str):
        self.uri = uri
        self.metadata_obj, self.engine = connect(self.uri)

    def create_database(self):
        if database_exists(self.uri):
            drop_database(self.uri)
        create_database(self.uri)

        engine = create_engine(self.uri, echo=True)
        SQLModel.metadata.create_all(engine)
        # recreate the engine/metadata object
        self.metadata_obj, self.engine = connect(self.uri)

    def create_cpf_summary(self, cpf_metadata: pd.DataFrame):
        """Create the CPF summary table"""
        cpf_metadata.to_sql("cpf_summary", self.engine, if_exists="replace")

    def create_scenarios(self, shot_metadata: pd.DataFrame):
        """Create the scenarios metadata table"""
        ids = shot_metadata["scenario_id"].unique()
        scenarios = shot_metadata["scenario"].unique()

        data = pd.DataFrame(dict(id=ids, name=scenarios)).set_index("id")
        data = data.dropna()
        data.to_sql("scenarios", self.engine, if_exists="append")

    def create_shots(self, shot_metadata: pd.DataFrame):
        """Create the shot metadata table"""
        shot_metadata["facility"] = "MAST"
        shot_metadata = shot_metadata.set_index("shot_id")
        shot_metadata["scenario"] = shot_metadata["scenario_id"]
        shot_metadata = shot_metadata.drop(["scenario_id", "reference_id"], axis=1)
        shot_metadata.to_sql("shots", self.engine, if_exists="append")

    def create_signal_datasets(self, signal_dataset_metadata: pd.DataFrame):
        """Create the signal metadata table"""
        signal_dataset_metadata["context_"] = [{'@vocab': ""}] * len(signal_dataset_metadata)
        signal_dataset_metadata["name"] = signal_dataset_metadata["signal_name"]
        signal_dataset_metadata["description"] = signal_dataset_metadata["description"]
        signal_dataset_metadata["signal_type"] = signal_dataset_metadata["type"]
        signal_dataset_metadata["quality"] = signal_dataset_metadata[
            "signal_status"
        ].map(lookup_status_code)
        signal_dataset_metadata["dimensions"] = signal_dataset_metadata[
            "dimensions"
        ].map(list)
        signal_dataset_metadata["doi"] = ""

        signal_metadata = signal_dataset_metadata.drop(
            [
                "shot_nums",
                "shape",
                "time_index",
                "label",
                "generic_name",
                "pass_",
                "source_alias",
                "signal_status",
                "mds_name",
                "type",
                "shot",
                "signal_name",
            ],
            axis=1,
        )

        def dict2json(dictionary):
            return json.dumps(dictionary, ensure_ascii=False)

        signal_metadata['context_'] = signal_metadata['context_'].map(dict2json)

        signal_metadata.to_sql(
            "signal_datasets", self.engine, if_exists="append", index=False
        )

    def create_signals(self, signals_metadata: pd.DataFrame):
        signal_datasets_table = self.metadata_obj.tables["signal_datasets"]
        stmt = select(
            signal_datasets_table.c.signal_dataset_id, signal_datasets_table.c.name
        )
        signal_datasets = pd.read_sql(stmt, con=self.engine.connect())
        signals_metadata = pd.merge(
            signals_metadata, signal_datasets, left_on="name", right_on="name"
        )
        signals_metadata["quality"] = signals_metadata["signal_status"].map(
            lookup_status_code
        )
        signals_metadata["shape"] = signals_metadata["shape"].map(lambda x: x.tolist())
        signals_metadata['name'] = signals_metadata['name'] + '/' + signals_metadata['shot_nums']
        signals_metadata['version'] = 0

        columns = ["signal_dataset_id", "shot_nums", "quality", "shape", "name", "version"]
        signals_metadata = signals_metadata[columns]
        signals_metadata = signals_metadata.rename(dict(shot_nums="shot_id"), axis=1)

        signals_metadata = signals_metadata.set_index("shot_id")
        signals_metadata.to_sql("signals", self.engine, if_exists="append")

    def create_sources(self, source_metadata: pd.DataFrame):
        source_metadata = source_metadata
        source_metadata["name"] = source_metadata["source_alias"]
        source_metadata["source_type"] = source_metadata["type"]
        source_metadata = source_metadata[["description", "name", "source_type"]]
        source_metadata = source_metadata.drop_duplicates()
        source_metadata = source_metadata.sort_values("name")
        source_metadata.to_sql("sources", self.engine, if_exists="append", index=False)

    def create_shot_source_links(self, sources_metadata: pd.DataFrame):
        sources_metadata = sources_metadata
        sources_metadata["source"] = sources_metadata["source_alias"]
        sources_metadata["quality"] = sources_metadata["status"].map(lookup_status_code)
        sources_metadata["shot_id"] = sources_metadata["shot"].astype(int)
        sources_metadata = sources_metadata[
            ["source", "shot_id", "quality", "pass", "format"]
        ]
        sources_metadata = sources_metadata.sort_values("source")
        sources_metadata.to_sql(
            "shot_source_link", self.engine, if_exists="append", index=False
        )


def read_cpf_summary_metadata(cpf_summary_file_name: Path) -> pd.DataFrame:
    cpf_summary_metadata = pd.read_parquet(cpf_summary_file_name)
    return cpf_summary_metadata


def read_cpf_metadata(cpf_file_name: Path) -> pd.DataFrame:
    cpf_metadata = pd.read_parquet(cpf_file_name)
    cpf_metadata["shot_id"] = cpf_metadata.shot_id.astype(int)
    columns = {
        name: f'cpf_{name.split("__")[0].lower()}'
        for name in cpf_metadata.columns
        if name != "shot_id"
    }
    cpf_metadata = cpf_metadata.rename(columns=columns)
    for column in cpf_metadata.columns:
        cpf_metadata[column] = pd.to_numeric(cpf_metadata[column], errors="coerce")
    return cpf_metadata


def read_shot_metadata(
    shot_file_name: Path, cpf_metadata: pd.DataFrame
) -> pd.DataFrame:
    shot_metadata = pd.read_parquet(shot_file_name)
    shot_metadata = pd.merge(
        shot_metadata, cpf_metadata, left_on="shot_id", right_on="shot_id", how="outer"
    )
    return shot_metadata


def read_signal_dataset_metadata(signal_file_name: Path) -> pd.DataFrame:
    signal_metadata = pd.read_parquet(signal_file_name)
    return signal_metadata


def read_sources_metadata(source_file_name: Path) -> pd.DataFrame:
    source_metadata = pd.read_parquet(source_file_name)
    return source_metadata


def read_signals_metadata(sample_file_name: Path) -> pd.DataFrame:
    sample_metadata = pd.read_parquet(sample_file_name)
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
    client.create_cpf_summary(cpf_summary_metadata)
    client.create_scenarios(shot_metadata)
    client.create_shots(shot_metadata)
    client.create_signal_datasets(signal_dataset_metadata)
    client.create_signals(signals_metadata)
    client.create_sources(source_metadata)
    client.create_shot_source_links(source_metadata)


if __name__ == "__main__":
    create_db_and_tables()
