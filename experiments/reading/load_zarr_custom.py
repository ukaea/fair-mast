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
    for variable in signal_data.keys():
        item = signal_data[variable]
        def _get_value(item):
            return item[:]
        value = dask.delayed(_get_value)(item)
        array = da.from_delayed(value, item.shape, dtype=item.dtype)
        dims = item.attrs['_ARRAY_DIMENSIONS']
        # attrs = {k: v for k, v in item.attrs.items() if not k.startswith('_')}
        arr = xr.DataArray(array, name=variable, dims=dims)
        arrs[variable] = arr

    dataset = xr.Dataset(data_vars=arrs)
    dataset.attrs = dict(signal_data.attrs)
    return dataset

def load_zarr(file_name):
    store = zarr.open(file_name)
    groups = store.groups()
    groups = list(groups)
    ds = {key: load_group(group) for key, group in groups}
    return ds

def main():
    data_dir = Path('data')
    file_name = data_dir / 'example.zarr'
    with Timer('Read'):
        dt = load_zarr(file_name)

    with Timer('Write Total'):
        datasets = dt.values()
        groups = list(dt.keys())
        offsets = [ds.dims['time'] for ds in datasets]

        # for ds, group, offset in zip(datasets, groups, offsets):
        #     with Timer('Write'):
        #         file_name = 'data/example3.zarr'
        #         mode = 'a' if Path(file_name).exists() else 'w'
        #         append_dim = 'time' if mode == 'a' else None
        #         ds['offsets'] = xr.DataArray([offset], dims='shot_index', coords=dict(shot_index=[group]))
        #         ds.to_zarr(file_name, mode=mode, append_dim=append_dim)

        ds = xr.concat(dt.values(), dim='time')
        ds = ds.chunk("auto")
        ds['offsets'] = xr.DataArray(offsets, dims='shot_index', coords=dict(shot_index=groups))
        ds.to_zarr('data/example2.zarr', mode='w')


if __name__ == '__main__':
    main()