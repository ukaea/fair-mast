import dask
import dask.array as da
import datatree
import pandas as pd
import xarray as xr
import awkward as ak
import pyarrow.dataset as pads
from functools import partial
from pathlib import Path
import zarr
import time
import numpy as np
from collections import defaultdict

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
    dims = {
        'data': ['time', 'dim_0'],
        'error': ['time', 'dim_0'],
        'time': ['coord_time'],
        'dim_0': ['coord_dim_0']
    }
    for variable in signal_data.keys():
        item = signal_data[variable]
        value = da.from_zarr(item)
        # dims = item.attrs['_ARRAY_DIMENSIONS']
        # attrs = {k: v for k, v in item.attrs.items() if not k.startswith('_')}
        arr = xr.DataArray(value, name=variable, dims=dims[variable])
        arrs[variable] = arr

    dataset = xr.Dataset(arrs)
    dataset.attrs = dict(signal_data.attrs)
    return dataset

def load_zarr_compact(file_name):
    store = zarr.open(file_name, mode='r')
    names = ['data', 'error', 'time', 'dim_0']

    dims = {
        'data': ['time', 'dim_0'],
        'error': ['time', 'dim_0'],
        'time': ['coord_time'],
        'dim_0': ['coord_dim_0']
    }

    shapes = {name: store[f'{name}_shape'][:] for name in names}
    def _func(store, offset, size):
        return store[offset:offset+size]

    datasets = {}
    offsets = defaultdict(lambda: 0)
    for shot_index, shot_name in enumerate(store['shot']):

        items = {}
        for name in names:
            shape = shapes[name][shot_index]

            size = np.prod(shape)
            arr = da.from_delayed(dask.delayed(_func)(store[name], offsets[name], size), shape=(size,), dtype=float)
            arr = arr.reshape(shape)
            items[name] = xr.DataArray(arr, name=name, dims=dims[name])
            offsets[name] += size

        datasets[shot_name] = xr.Dataset(items)

    ds = datatree.DataTree.from_dict(datasets)
    return ds


def load_zarr_grouped_custom(file_name):
    store = zarr.open_consolidated(file_name, mode='r')
    groups = store.groups()
    groups = list(groups)
    ds = {key: load_group(group) for key, group in groups}
    ds = datatree.DataTree.from_dict(ds)
    return ds

def load_zarr_grouped_datatree(file_name):
    tree = datatree.open_datatree(file_name, engine='zarr', consolidated=True, chunks={})
    return tree

def load_parquet(file_name):
    dataset = pads.dataset(file_name)
    ds = dataset.to_table()
    ds = ak.from_arrow(ds)
    print(ds)

    # datasets = {}
    # for item in ds:
    #     dataset = xr.Dataset(dict(
    #         data=xr.DataArray(ak.to_numpy(item['data']).squeeze(), name='data', dims=['time', 'dim_0']),
    #         error=xr.DataArray(ak.to_numpy(item['error']).squeeze(), name='error', dims=['time', 'dim_0']),
    #         time=xr.DataArray(ak.to_numpy(item['time']).squeeze(), name='time', dims=['t']),
    #         dim_0=xr.DataArray(ak.to_numpy(item['dim_0']).squeeze(), name='dim_0', dims=['d'])
    #     ))

    #     datasets[f"{item['shot']}"] = dataset

    # dt = datatree.DataTree.from_dict(datasets)
    return ds

def load_shape(file_name):
    shape_df = pd.read_csv('shapes.csv', index_col=0)

    store = zarr.open_consolidated(file_name, mode='r')
    def _null(group, name):
        return store[group][name]

    names = ['data', 'error', 'time', 'dim_0']
    dims = {
        'data': ['time', 'dim_0'],
        'error': ['time', 'dim_0'],
        'time': ['coord_time'],
        'dim_0': ['coord_dim_0']
    }

    datasets = {}
    for group, item in shape_df.iterrows():
        shape = item.values.squeeze()

        shapes = dict(
            data=shape,
            error=shape,
            time=shape[:1],
            dim_0=shape[1:]
        )

        items = {}
        for name in names:
            items[name] = xr.DataArray(da.from_delayed(dask.delayed(_null)(group, name), shape=shapes[name], dtype=float), name=name, dims=dims[name]) 
            # items[name] = xr.DataArray(da.from_zarr(store[group][name]), name=name, dims=dims[name]) 

        dataset = xr.Dataset(items)
        datasets[f"{group}"] = dataset

    dt = datatree.DataTree.from_dict(datasets)
    return dt

def run_test(func, file_name):
    print("Testing:", func.__name__)
    with Timer('Open'):
        tree = func(file_name)
    
    with Timer('Load'):
        result = [c.ds.compute() for c in tree.subtree]
    # print(tree)
        

def main():
    data_dir = Path('.')
    file_name = data_dir / 'AIT_TPROFILE_ISP.zarr'

    # run_test(load_zarr_grouped_datatree, file_name)
    # run_test(load_zarr_grouped_custom, file_name)
    run_test(load_shape, file_name)

    # data_dir = Path('file_test')
    # file_name = data_dir / 'compact_AIT_TPROFILE_ISP.zarr'
    # run_test(load_zarr_compact, file_name)

    # data_dir = Path('file_test')
    # file_name = data_dir / 'parquet_AIT_TPROFILE_ISP'
    # run_test(load_parquet, file_name)

if __name__ == '__main__':
    main()