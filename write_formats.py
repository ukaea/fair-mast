import dask
import dask.array as da
import datatree
import xarray as xr
from functools import partial
from pathlib import Path
import zarr
import time

class Timer():

    def __init__(self, name=''):
        self.name = name

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args, **kwargs):
        self.end = time.time()
        print(self.name, self.end - self.start)

def load_group(signal_data):
    arrs = {}
    with Timer('Load Group'):
        for variable in signal_data.keys():
            item = signal_data[variable]
            def _get_value(item):
                return item[:]
            value = dask.delayed(_get_value)(item)
            array = da.from_delayed(value, item.shape, dtype=item.dtype)
            dims = item.attrs['_ARRAY_DIMENSIONS']
            attrs = {k: v for k, v in item.attrs.items() if not k.startswith('_')}
            arr = xr.DataArray(array, name=variable, dims=dims, attrs=attrs)
            arrs[variable] = arr

    dataset = xr.Dataset(data_vars=arrs)
    dataset.attrs = dict(signal_data.attrs)
    return dataset

def load_zarr(file_name):
    store = zarr.open_consolidated(file_name)
    groups = store.groups()
    ds = {key: load_group(group) for key, group in groups}
    ds = datatree.DataTree.from_dict(ds)
    return ds

def main():
    data_dir = Path('data/mast')
    file_name = data_dir / 'EFM_PLASMA_VOLUME.zarr'
    with Timer('Load'):
        dt = load_zarr(file_name)
        print(dt)

if __name__ == '__main__':
    main()