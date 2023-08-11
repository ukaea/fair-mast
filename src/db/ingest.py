import h5py
import click
import zarr
import yaml
import numpy as np
import pandas as pd
import dateutil.parser as parser
from pathlib import Path
from src.db.client import Client


def read_config(path):
    with Path(path).open("r") as handle:
        config = yaml.load(handle, yaml.SafeLoader)
    return config


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
@click.argument("data_path", default="~/mast-data")
def main(data_path):
    data_path = Path(data_path)

    config = read_config("config.yml")
    uri = config["db_uri"]

    client = Client(uri, config)
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

    # delete all instances in the database
    client.delete_all("signals")
    client.delete_all("shots")
    client.delete_all("signal_datasets")
    client.delete_all("scenarios")
    client.delete_all("cpf_summary")

    # reset the ID counters
    client.reset_counter("signal_datasets", "signal_dataset_id")
    client.reset_counter("signals", "id")

    # populate the database tables
    client.create_cpf_summary(cpf_summary_metadata)
    client.create_scenarios(shot_metadata)
    client.create_shots(shot_metadata)
    client.create_signal_datasets(signal_dataset_metadata)
    client.create_signals(signals_metadata)
    client.create_sources(source_metadata)
    client.create_shot_source_links(source_metadata)


if __name__ == "__main__":
    main()
