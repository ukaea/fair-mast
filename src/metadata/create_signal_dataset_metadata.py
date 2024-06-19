import uuid
import multiprocessing as mp
import pandas as pd
from pathlib import Path
import click
import zarr
from netCDF4 import Dataset
import logging

logging.basicConfig(level=logging.INFO)


def read_netcdf(path):
    dataset = Dataset(path, mode="r")
    shot_id = next(iter(dataset.groups.keys()))
    group = dataset[shot_id]
    metadata = group.__dict__
    dimensions = list(group.dimensions.keys())
    return metadata, dimensions


def read_zarr(path):
    with zarr.ZipStore(path) as store:
        dataset = zarr.open_consolidated(store, mode="r")

        try:
            group = next(iter(dataset.groups()))[1]
        except StopIteration:
            raise RuntimeError(f"No data in path {path}")

        dimensions = group["data"].attrs["_ARRAY_DIMENSIONS"]
        metadata = dict(dataset.attrs)

    return metadata, dimensions


def parse_signal_metadata(path):
    try:
        if path.suffix == ".nc":
            metadata, dimensions = read_netcdf(path)
        elif path.suffix == ".zip":
            metadata, dimensions = read_zarr(path)
    except Exception as e:
        return {"error": e}

    metadata["units"] = metadata.get("units", "dimensionless")

    item = {}
    item["name"] = Path(path.stem).stem.upper()
    oid_name = path.parent.stem + "/" + item["name"]
    item["uuid"] = str(uuid.uuid5(uuid.NAMESPACE_OID, oid_name))
    item["uri"] = str(path)
    item["dimensions"] = dimensions
    item["rank"] = len(dimensions)
    item.update(metadata)

    return item


def parse_metadata(paths, output_file, num_workers):
    metadata = []

    pool = mp.Pool(num_workers)
    items = pool.imap(parse_signal_metadata, paths)

    for item in items:
        if "error" in item:
            logging.warning(f"Path {item['error']} has no data")
            continue
        logging.info(f"Adding {item['name']}")
        metadata.append(item)

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
@click.option("--num-workers", "-n", default=16, type=int, help="Number of workers")
def main(data_dir, output_file, format, num_workers):
    data_dir = Path(data_dir)
    ext = "*.zarr.zip" if format == "zarr" else "*.nc"
    signal_files = list(sorted(data_dir.glob("**/" + ext)))
    parse_metadata(signal_files, output_file, num_workers)


if __name__ == "__main__":
    main()
