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
from collections import defaultdict
from dask.base import DaskMethodsMixin

class DatasetWrapper(object):
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        if name != '__array__':
            return getattr(self._obj, name)
        else:
            raise AttributeError('Not an attribute')

    def __repr__(self):
        return str(self._obj)


@pd.api.extensions.register_dataframe_accessor("xdt")
class XArrayDatasetTableAccessor:
    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        # verify there is a column latitude and a column longitude
        if "dataset" not in obj.columns:
            raise AttributeError("Must have 'dataset' column.")

    @property
    def ds(self):
        return self._obj.dataset

    def __getitem__(self, key):
        def _func(x):
            x = x.compute()
            return x.get(key)

        return (
            self._obj.xdt.ds
                .map(lambda x: dask.delayed(_func)(x))
        )

    def compute(self):
        values = list(map(DatasetWrapper, dask.compute(*self._obj.dataset.values)))
        self._obj['dataset'] = values
        return values

    def to_dict(self):
        self.compute()
        return self._obj.dataset.map(lambda x: x._obj).to_dict()

    def to_datatree(self):
        item = self.to_dict()
        return datatree.DataTree.from_dict(item)

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
        'time': ['time'],
        'dim_0': ['dim_0']
    }
    for variable in dims.keys():
        item = signal_data[variable]
        value = da.from_zarr(item)
        arr = xr.DataArray(value, name=variable, dims=dims[variable])
        arrs[variable] = arr

    dataset = xr.Dataset(arrs)
    # dataset.attrs = dict(signal_data.attrs)
    return dataset

def load_zarr_grouped_custom(file_name):
    store = zarr.open_consolidated(file_name, mode='r')
    groups = store.groups()
    groups = list(groups)
    keys = [key for key, group in groups]
    objs = [dask.delayed(load_group)(group) for key, group in groups]

    objs = list(dask.compute(*objs))
    ds = dict(zip(keys, objs))


    
    # def _get_shapes(group):
    #     attrs = dict(group.attrs)
    #     shape = attrs['shape']
    #     return shape

    # shapes = [_get_shapes(group) for key, group in groups]

    # items = {'index': ds.keys(), 'shape': shapes, 'dataset': ds.values()}
    # ds = pd.DataFrame(items)
    # ds = ds.set_index('index')
    ds = datatree.DataTree.from_dict(ds)
    return ds

def load_zarr_compact(file_name):
    store = zarr.open(file_name, mode='r')
    names = ['data', 'error', 'time', 'dim_0']

    dims = {
        'data': ['time', 'dim_0'],
        'error': ['time', 'dim_0'],
        'time': ['time'],
        'dim_0': ['dim_0']
    }

    shapes = {name: store[f'{name}_shape'][:] for name in names}
    def _func(store, offset, size, shape):
        return store[offset:offset+size].reshape(shape)

    datasets = {}
    offsets = defaultdict(lambda: 0)
    for shot_index, shot_name in enumerate(store['shot']):

        items = {}
        for name in names:
            shape = np.atleast_1d(shapes[name][shot_index])

            size = np.prod(shape)
            arr = da.from_delayed(dask.delayed(_func)(store[name], offsets[name], size, shape), shape=shape, dtype=float)
            items[name] = xr.DataArray(arr, name=name, dims=dims[name])
            offsets[name] += size

        datasets[shot_name] = xr.Dataset(items)

    ds = datatree.DataTree.from_dict(datasets)
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
    shape_df = pd.read_csv('data/shapes.csv', index_col=0)

    store = zarr.open_consolidated(file_name, mode='r')
    def _null(store, group, name):
        return store[group][name]

    names = ['data', 'error', 'time', 'dim_0']
    dims = {
        'data': ['time', 'dim_0'],
        'error': ['time', 'dim_0'],
        'time': ['time'],
        'dim_0': ['dim_0']
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
            items[name] = xr.DataArray(da.from_delayed(dask.delayed(_null)(store, group, name), shape=shapes[name], dtype=float), name=name, dims=dims[name]) 
            # items[name] = xr.DataArray(da.from_zarr(store[group][name]), name=name, dims=dims[name]) 

        dataset = xr.Dataset(items)
        datasets[f"{group}"] = dataset

    dt = datatree.DataTree.from_dict(datasets)
    return dt

def run_test(func, file_name):
    print("Testing:", func.__name__)
    with Timer('Open'):
        tree = func(file_name)
        # tree = tree.iloc[:100]
        # tree.xdt.compute()
        # tree = tree.xdt.to_datatree()
        # print(tree)
        # tree.dataset = tree.xdt['data']
    # with Timer('Open'):
    #     tree = tree.xdt.to_datatree()
    
    with Timer('Load'):
        names = [name for name, c in tree.children.items()]
        values = [c.ds for name, c in tree.children.items()]
        values = list(dask.compute(*values))
        items = dict(zip(names, values))
        tree = datatree.DataTree.from_dict(items)
        

def main():
    data_dir = Path('data')
    file_name = data_dir / 'AIT_TPROFILE_ISP.zarr'

    # run_test(load_zarr_grouped_parallel, file_name)
    run_test(load_zarr_grouped_custom, file_name)
    # run_test(load_shape, file_name)
    # run_test(load_zarr_grouped_datatree, file_name)

    # data_dir = Path('file_test')
    # file_name = data_dir / 'compact_AIT_TPROFILE_ISP.zarr'
    # run_test(load_zarr_compact, file_name)

    # data_dir = Path('file_test')
    # file_name = data_dir / 'parquet_AIT_TPROFILE_ISP'
    # run_test(load_parquet, file_name)

if __name__ == '__main__':
    main()