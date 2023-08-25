import yaml
import zarr
import click
import h5py
from netCDF4 import Dataset
import numpy as np
from pathlib import Path
from rich.progress import Progress

def read_zarr(path):
    store = zarr.open_consolidated(path, mode='r')
    if len(list(store.groups())) > 0:
        _, item = next(store.groups())
    else:
        item = store
    metadata = dict(item.attrs)
    return metadata

def read_hdf(path):
    with h5py.File(path, mode='r') as store:
        key = next(iter(store.keys()))
        attrs = dict(store[key].attrs)

    # Convert numpy types to Python
    metadata = {}
    for key, item in attrs.items():
        if isinstance(item, np.generic):
            metadata[key] = item.item()
        elif isinstance(item, np.ndarray):
            metadata[key] = item.tolist()
        else:
            metadata[key] = item

    return metadata

def read_netcdf(path):
    store = Dataset(path, mode='r')
    key = next(iter(store.groups.keys()))
    attrs = store[key].__dict__
    store.close()

    # Convert numpy types to Python
    metadata = {}
    for key, item in attrs.items():
        if isinstance(item, np.generic):
            metadata[key] = item.item()
        elif isinstance(item, np.ndarray):
            metadata[key] = item.tolist()
        else:
            metadata[key] = item

    return metadata

@click.command()
@click.argument('folder')
def main(folder):
    catalog_data = {
        'description': 'The MAST Data Archive Catalog',
        'metadata': dict(version=1),
        'sources': {}
    }

    paths = Path(folder).glob('*.hdf')
    paths = list(sorted(paths))

    with Progress() as progress:
        task = progress.add_task("Compiling Catalog", total=len(paths))
        for path in paths:
            progress.console.print(path)
            name = path.stem
            if name.startswith('_'):
                continue

            metadata = read_hdf(path)

            source = {
                'description': metadata['description'],
                'driver': {
                    'xarray-datatree': {
                        'class': 'intake_xarray_datatree.intake_xarray_datatree.DataTreeSource',
                        'args': {'fastzarr': True}
                    },
                },
                'metadata': metadata,
                'args': {
                    'urlpath': '{{ CATALOG_DIR }}' + name + '.nc',
                }
            }
            catalog_data['sources'][name] = source
            progress.advance(task)

    catalog_file = Path(folder) / 'catalog.yml'
    with catalog_file.open('w') as handle:
        yaml.safe_dump(catalog_data, handle)


if __name__ == "__main__":
    main()