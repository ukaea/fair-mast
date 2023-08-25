import multiprocessing as mp
from tqdm import tqdm
import pandas as pd
from pathlib import Path
import click
import zarr
import numpy as np
from rich.progress import track
from netCDF4 import Dataset


def read_netcdf(path):
    dataset = Dataset(path, mode="r")
    shot_nums = list(dataset.groups.keys())
    group = dataset[shot_nums[0]]
    metadata = group.__dict__
    dimensions = list(group.dimensions.keys())
    return shot_nums, metadata, dimensions


def read_zarr(path):
    dataset = zarr.open_consolidated(path)
    shot_nums = list(dataset.group_keys())
    group = next(dataset.groups())[1]
    dimensions = group["data"].attrs["_ARRAY_DIMENSIONS"]
    metadata = dict(group.attrs)
    return shot_nums, metadata, dimensions


def parse_signal_metadata(path):
    if path.suffix == ".nc":
        shot_nums, metadata, dimensions = read_netcdf(path)
    elif path.suffix == ".zarr":
        shot_nums, metadata, dimensions = read_zarr(path)

    metadata["signal_status"] = metadata.get("signal_status", metadata["status"])
    metadata["units"] = metadata.get("units", "dimensionless")

    item = {}
    item["shot_nums"] = shot_nums
    item["name"] = path.stem.upper()
    item["uri"] = str(path)
    item["dimensions"] = dimensions
    item["rank"] = len(dimensions)
    item.update(metadata)
    return item


def parse_metadata(paths, output_file):
    pool = mp.Pool(8)
    mapper = pool.map(parse_signal_metadata, paths)

    metadata = []
    for item in track(mapper, total=len(paths)):
        metadata.append(item)
    metadata = pd.DataFrame(metadata)
    metadata.to_parquet(output_file)


@click.command()
@click.argument("data_dir")
@click.argument("output_file")
def main(data_dir, output_file):
    data_dir = Path(data_dir)
    signal_files = list(sorted(data_dir.glob("*.zarr")))
    signal_files = signal_files
    parse_metadata(signal_files, output_file)


if __name__ == "__main__":
    main()
