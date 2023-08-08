from dask_mpi import initialize
initialize()

import yaml
import zarr
import click
from pathlib import Path
from rich.progress import Progress

from dask.distributed import Client, as_completed

@click.command()
@click.argument('folder')
def main(folder):
    client = Client()  # Connect this local process to remote workers

    paths = Path(folder).glob('*.zarr')
    paths = list(sorted(paths))

    tasks = [client.submit(zarr.convenience.consolidate_metadata, path) for path in paths]

    with Progress() as progress:
        task = progress.add_task("Consolidating files", total=len(paths))
        for path, result in zip(paths, as_completed(tasks)):
            progress.console.print(path)
            progress.advance(task)

if __name__ == "__main__":
    main()