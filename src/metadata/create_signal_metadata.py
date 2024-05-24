import click
import uuid
import zarr
import pandas as pd
import numpy as np
import multiprocessing as mp
from pathlib import Path
from rich.progress import track
from netCDF4 import Dataset
import logging

logging.basicConfig(level=logging.INFO)


def parse_signal_metadata_zarr(path):
    with zarr.ZipStore(path) as store:
        dataset = zarr.open_consolidated(store, mode="r")

        items = []
        for shot_num, group in dataset.groups():
            metadata = dict(group.attrs)
            metadata["units"] = metadata.get("units", "dimensionless")

            item = {}
            name = Path(path.stem).stem.upper()
            logging.info(name)
            oid_name = path.parent.stem + "/" + name
            item["dataset_uuid"] = str(uuid.uuid5(uuid.NAMESPACE_OID, oid_name))
            shot_oid_name = path.parent.stem + "/" + name + "/" + str(shot_num)
            logging.info(shot_oid_name)
            item["uuid"] = str(uuid.uuid5(uuid.NAMESPACE_OID, shot_oid_name))
            item["shot_id"] = shot_num
            item["name"] = name
            item["uri"] = str(path) + "/" + str(shot_num)
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
        item["uuid"] = str(uuid.uuid4())
        item["shot_id"] = shot_num
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


def parse_metadata(paths, output_file, format, num_workers):
    parser_funcs = {
        "netcdf": parse_signal_metadata_netcdf,
        "zarr": parse_signal_metadata_zarr,
    }

    pool = mp.Pool(num_workers)
    mapper = pool.imap(parser_funcs[format], paths)

    metadata = []
    for items in track(mapper, total=len(paths)):
        if len(items) == 0:
            logging.info("Skipping dataset due to no shots.")
            continue
        name = items[0]["name"]
        logging.info(f"Add shots from {name}")
        metadata.extend(items)

    logging.info(f"Writing metadata to {output_file}")
    metadata = pd.DataFrame(metadata)
    metadata.to_parquet(output_file)
    logging.info("Done!")


@click.command()
@click.argument("data_dir")
@click.argument("output_file")
@click.option(
    "--format",
    default="zarr",
    type=click.Choice(["netcdf", "zarr"]),
    help="File format to parse",
)
@click.option("-num-workers", "-n", default=16, type=int, help="Number of workers")
def main(data_dir, output_file, format, num_workers):
    data_dir = Path(data_dir)

    ext = "*.zarr.zip" if format == "zarr" else "*.nc"
    signal_files = list(sorted(data_dir.glob("**/" + ext)))
    parse_metadata(signal_files, output_file, format, num_workers)


if __name__ == "__main__":
    main()
