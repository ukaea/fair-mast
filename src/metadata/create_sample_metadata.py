import click
import zarr
import pandas as pd
import numpy as np
import multiprocessing as mp
from pathlib import Path
from rich.progress import track
from netCDF4 import Dataset


def parse_signal_metadata_zarr(path):
    dataset = zarr.open_consolidated(path)

    items = []
    for shot_num, group in dataset.groups():
        metadata = dict(group.attrs)

        metadata["signal_status"] = metadata.get("signal_status", metadata["status"])
        metadata["units"] = metadata.get("units", "dimensionless")

        item = {}
        item["shot_nums"] = shot_num
        item["name"] = path.stem.upper()
        item["uri"] = str(path)
        item["shape"] = group["data"].shape
        item["shape"] = np.atleast_1d(item["shape"]).tolist()
        item["dimensions"] = group["data"].attrs["_ARRAY_DIMENSIONS"]
        item["rank"] = len(item["shape"])

        item.update(metadata)
        items.append(item)
    return items


def parse_signal_metadata_netcdf(path):
    dataset = Dataset(path, mode="r")

    items = []
    for shot_num, group in dataset.groups.items():
        metadata = group.__dict__

        item = {}
        item["shot_nums"] = shot_num
        item["name"] = path.stem.upper()
        item["uri"] = str(path)
        item["shape"] = metadata["shape"]
        item["shape"] = np.atleast_1d(item["shape"]).tolist()
        item["rank"] = metadata["rank"]
        item["signal_status"] = metadata["signal_status"]
        item["source_alias"] = metadata["source_alias"]
        item["units"] = metadata["units"]
        item["description"] = metadata["description"]
        item["label"] = metadata["label"]
        item["dimensions"] = list(group.dimensions.keys())

        items.append(item)
    return items


def parse_metadata(paths, output_file):
    pool = mp.Pool(8)
    mapper = pool.map(parse_signal_metadata_zarr, paths)

    metadata = []
    for item in track(mapper, total=len(paths)):
        metadata.extend(item)

    metadata = pd.DataFrame(metadata)
    metadata.to_parquet(output_file)


@click.command()
@click.argument("data_dir")
@click.argument("output_file")
def main(data_dir, output_file):
    data_dir = Path(data_dir)
    signal_files = list(sorted(data_dir.glob("*.zarr")))
    parse_metadata(signal_files, output_file)


if __name__ == "__main__":
    main()
