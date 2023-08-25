import click
from pathlib import Path
import xarray as xr
import zarr
import multiprocessing as mp
from rich.progress import track
from netCDF4 import Dataset
from functools import partial


def create_file(file_name, output_folder):
    print(file_name)
    file_name = Path(file_name)
    with Dataset(file_name) as handle:
        new_name = f"{output_folder}/{file_name.stem}.zarr"
        for key in handle.groups.keys():
            ds = xr.open_dataset(file_name, group=key)
            ds.to_zarr(new_name, group=key, mode="w")

    zarr.convenience.consolidate_metadata(new_name)


@click.command()
@click.argument("folder")
@click.argument("output_folder")
def main(folder, output_folder):
    pool = mp.Pool(8)

    folder = Path(folder)
    file_names = folder.glob("*.nc")
    for item in track(
        pool.map(partial(create_file, output_folder=output_folder), file_names)
    ):
        pass


if __name__ == "__main__":
    main()
