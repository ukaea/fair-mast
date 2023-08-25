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

def load_zarr(file_name):
    store = zarr.open(file_name, mode='r')
    ds = {}

    def _get_value(item, index):
        return item[index]

    def _dask_slice(item, i):
        shape = item.attrs['shapes'][i]
        value = dask.delayed(_get_value)(item, i)
        array = da.from_delayed(value, shape, dtype='int64')
        return array
    
    data = store.data
    error = store.error
    time = store.time

    for i in range(len(store.data)):
        variables = {}
        variables['data'] = xr.DataArray(_dask_slice(data, i))
        variables['error'] = xr.DataArray(_dask_slice(error, i))
        variables['time'] = xr.DataArray(_dask_slice(time, i))
        dataset = xr.Dataset(variables)
        ds[str(i)] = dataset

    return datatree.DataTree.from_dict(ds)

def main():
    data_dir = Path('data/')
    file_name = data_dir / 'example.zarr'
    with Timer('Load'):
        dt = load_zarr(file_name)
    # print(dt)
    print(dt['0'].compute())

if __name__ == '__main__':
    main()