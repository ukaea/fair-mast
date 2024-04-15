import datetime
import s3fs
import configparser
import xarray as xr
import time
import subprocess
import zarr
from zarr.meta import json_dumps, json_loads
import shutil
import click
import logging
import pandas as pd
from pathlib import Path
from dataclasses import asdict
from rich.progress import track
from dask_mpi import initialize
from dask.distributed import Client, as_completed
from dask.distributed import KilledWorker
from rich.console import Console

from src.archive.mast import MASTClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.ERROR)
logger.addHandler(c_handler)

def lookup_status_code(status):
    """Status code mapping from the numeric representation to the meaning"""
    lookup = {-1: "Very Bad", 0: "Bad", 1: "Not Checked", 2: "Checked", 3: "Validated"}
    return lookup[status]


def is_zarr_key(key):
    return key.endswith(".zarray") or key.endswith(".zgroup") or key.endswith(".zattrs")


def _get_signal(name: str, shot: int):
    client = MASTClient()
    try:
        return client.get_signal(shot, name)
    except Exception as e:
        return f"{name}/{shot}: {e}"


def _get_signal_infos(shot: int):
    client = MASTClient()
    try:
        return client.get_signal_infos(shot)
    except Exception as e:
        return f"{shot}: {e}"

def _get_image_infos(shot: int):
    client = MASTClient()
    try:
        return client.get_image_infos(shot)
    except Exception as e:
        return f"{shot}: {e}"

def read_shot_file(shot_file: str) -> list[int]:
    with open(shot_file) as f:
        shot_nums = f.readlines()[1:]
        shot_nums = map(lambda x: x.strip(), shot_nums)
        shot_nums = list(sorted(map(int, shot_nums)))
    return shot_nums


def archive_file(file_name: str):
    archive_name = f"{file_name}.zip"
    command = f"7zzs a {archive_name} {file_name}/. -sdel -mmt1"
    subprocess.check_output(command, shell=True)
    shutil.rmtree(file_name)


class DatasetReader:
    def get_signal(self, name: str, shot: int):
        client = MASTClient()
        try:
            return client.get_signal(shot, name)
        except Exception as e:
            return f"{name}/{shot}: {e}"

    def get_signal_infos(self, shot: int):
        client = MASTClient()
        try:
            return client.get_signal_infos(shot)
        except Exception as e:
            return f"{shot}: {e}"


class DatasetWriter:
    def __init__(self, path: str, fs=None) -> None:
        self.fs = fs
        self.path = str(path)

    def get_store(self, file_name: str):
        root = self.path + '/' + file_name
        store = zarr.storage.FSStore(root, fs=self.fs)
        return store

    def write(self, dataset: xr.Dataset, name: str):
        group_name = str(dataset.attrs["shot_id"])
        file_name = self.get_file_name(name)
        store = self.get_store(file_name)
        dataset.to_zarr(store, group=group_name, consolidated=False, mode="a")
        # metadata = {key: json_loads(store[key]) for key in store if is_zarr_key(key)}
        store.close()
        return {}

    def get_file_name(self, name: str) -> str:
        name = name.replace("/", "-")
        name = name.replace(" ", "-")
        name = name.replace("(", "")
        name = name.replace(")", "")
        file_name = f"{name}.zarr"
        return file_name


def _do_write_signal(
    metadata: dict, name: str, reader: DatasetReader, writer: DatasetWriter, force_write: bool = False
):
    shot = metadata['shot']
    file_name = writer.get_file_name(name)
    group_name = str(shot)
    key = writer.path + '/' + file_name + '/' + group_name
    if not force_write and writer.fs.exists(key):
        return metadata

    dataset = reader.get_signal(name, shot)

    if isinstance(dataset, str):
        return dataset

    now = datetime.datetime.now().isoformat()
    updated_metadata = metadata.copy()
    updated_metadata['created'] = now
    updated_metadata['identifier'] = updated_metadata.pop('dataset_item_uuid')
    updated_metadata['quality'] = lookup_status_code(metadata['status'])
    updated_metadata.pop('shot')
    updated_metadata.pop('status')
    dataset.attrs.update(updated_metadata)
    return writer.write(dataset, name)


def write_signals(client, name: str, records: pd.DataFrame, fs=None, output_path: str = "./", force_write: bool = False):
    reader = DatasetReader()
    writer = DatasetWriter(output_path, fs=fs)

    tasks = []
    for index, row in records.iterrows():
        row = row.to_dict()
        dataset = client.submit(_do_write_signal, row, name, reader, writer, force_write)
        tasks.append(dataset)

    num_tasks = len(tasks)
    for i, item in enumerate(as_completed(tasks)):
        try:
            result = item.result()
        except KilledWorker as e:
            logger.warning(e)
            print(e)
            continue

        if isinstance(result, str):
            # Special case: a fatal error, we should stop the transfer
            if "The User Specified Socket Connection does not exist" in result:
                raise RuntimeError(result)

            logger.warning(result)
            print(result)

        print(f'Finished task {i+1} of {num_tasks}: {(i+1)/num_tasks * 100:.2f}%')

def write_dataset_archive(client, records, name, fs, force_write: bool = False, consolidate: bool = False):
    item = records.iloc[0].to_dict()
    source = item['source']
    output_path = f's3://mast/{source}'
    writer = DatasetWriter(output_path, fs)

    store = writer.get_store(writer.get_file_name(name))

    with zarr.open(store) as handle:
        now = datetime.datetime.now().isoformat()
        handle.attrs['created'] = now
        handle.attrs['identifier'] = item['dataset_uuid'] 
        handle.attrs['type'] = item['type']
        handle.attrs['quality'] = lookup_status_code(item['status'])
        handle.attrs['description'] = item['description']
        handle.attrs['source'] = item['source']


    write_signals(client, name, records, fs, output_path, force_write)

    if consolidate:
        print('Consolidating metadata')
        zarr.consolidate_metadata(store)
        print('Done!')


def write_dataset_summary(shots: list[int], summary_file: str):
    client = Client()
    tasks = []
    for shot in shots:
        task = client.submit(_get_signal_infos, shot)
        tasks.append(task)
        task = client.submit(_get_image_infos, shot)
        tasks.append(task)

    num_tasks = len(shots) * 2
    all_datasets = []
    for i, datasets in enumerate(as_completed(tasks)):
        datasets = datasets.result()

        if isinstance(datasets, str):
            print(datasets)
            logger.warning(datasets)
            continue

        all_datasets.extend(datasets)
        print(f'Finished task {i+1} of {num_tasks}: {(i+1)/num_tasks*100:.2f}%')

    df = pd.DataFrame([asdict(d) for d in all_datasets])
    df.to_parquet(summary_file)


def read_config(fs_config: str):
    config = configparser.ConfigParser()
    with open(Path(fs_config).expanduser()) as stream:
        config.read_string("[DEFAULT]\n" + stream.read())
        config = config["DEFAULT"]
    return config

def get_file_system(config):
    key = config["access_key"]
    secret = config["secret_key"]
    host_base = config['host_base']
    url = f"https://{host_base}"
    fs = s3fs.S3FileSystem(anon=False, key=key, secret=secret, endpoint_url=url)
    return fs


@click.group()
def cli():
    initialize()


@cli.command()
@click.argument("shot-file")
@click.argument("summary-file")
def summary(shot_file, summary_file):
    shots = read_shot_file(shot_file)
    write_dataset_summary(shots, summary_file)


@cli.command()
@click.argument("summary-file")
@click.argument("name")
@click.option("--fs-config", "-c", default='~/.s3cfg', type=str)
@click.option("--force", "-f", is_flag=True, default=False, type=bool)
@click.option("--consolidate", is_flag=True, default=False, type=bool)
def write_dataset(summary_file, name, fs_config, force, consolidate):
    client = Client()

    fs_config = Path(fs_config).expanduser()
    config = read_config(fs_config)
    fs = get_file_system(config)

    dataset_summary = pd.read_parquet(summary_file)
    dataset_summary = dataset_summary.loc[dataset_summary["name"] == name]

    if len(dataset_summary) == 0:
        raise RuntimeError(f'No records found for dataset {name}')

    write_dataset_archive(client, dataset_summary, name, fs, force, consolidate)


@cli.command()
@click.argument("summary-file")
@click.option("--fs-config", "-c", default='~/.s3cfg', type=str)
@click.option("--force", "-f", is_flag=True, default=False, type=bool)
@click.option("--consolidate", is_flag=True, default=False, type=bool)
@click.option(
    "--signal-type",
    "-t",
    default="Analysed",
    type=click.Choice(["Analysed", "Raw", "Image"]),
)
def write_datasets(summary_file, fs_config, signal_type, force, consolidate):
    client = Client()
    f_handler = logging.FileHandler(f"{Path(summary_file).stem}_transfer.log")
    f_handler.setLevel(logging.WARNING)
    logger.addHandler(f_handler)

    fs_config = Path(fs_config).expanduser()
    config = read_config(fs_config)
    fs = get_file_system(config)

    dataset_summary = pd.read_parquet(summary_file)
    dataset_summary = dataset_summary.loc[dataset_summary["type"] == signal_type]
    n = len(dataset_summary.groupby('name').groups)

    for i, (_, metadata) in enumerate(dataset_summary.groupby('name')):
        name = metadata.iloc[0]["name"]

        print(f"Writing archive for {name} ({i+1}/{n} = {(i+1)/n*100:.2f}%) ")
        start = time.time()
        write_dataset_archive(client, metadata, name, fs, force, consolidate) 
        end = time.time()
        print(f"Wrote {name} archive in {end-start:.2f}s")


if __name__ == "__main__":
    cli()
