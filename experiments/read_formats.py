import xarray as xr
import h5py
import netCDF4
from netCDF4 import Dataset
import time
import zarr
import dask
import dask.array as da
import datatree
import pandas as pd

class Timer():

    def __init__(self, name=''):
        self.name = name

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args, **kwargs):
        self.end = time.time()
        print(self.name, self.end - self.start)

    def get_results(self):
        return dict(name=self.name, start=self.start, end=self.end, duration=self.end-self.start)
        

class GroupedNetCDFReader:

    def read(self, path):
        ncf = netCDF4.Dataset(path, mode='r')
        keys = list(ncf.groups.keys())
        data = {name: self.read_group(ncf, name) for name in keys}
        return datatree.DataTree.from_dict(data)

    def read_group(self, ncf, name):
        store = xr.backends.NetCDF4DataStore(ncf.groups.get(name))
        dataset = xr.open_dataset(store, chunks=-1)
        return dataset

class GroupedZarrReader:

    def read(self, path):
        store = zarr.open_consolidated(path, mode='r')
        data = {name: self.read_group(group) for name, group in store.groups()}
        return datatree.DataTree.from_dict(data)

    def read_group(self, group):
        return xr.open_dataset(xr.backends.ZarrStore(group, mode='r'), chunks={})

class GroupedZarrFastReader:

    def read(self, path):
        store = zarr.open_consolidated(path, mode='r')

        groups = store.groups()
        _, group = next(groups)
        dims = {}
        for key in group.keys():
            dims[key] = group[key].attrs['_ARRAY_DIMENSIONS']

        keys = [key for key, group in groups]
        objs = [dask.delayed(self.read_group)(group, dims) for key, group in store.groups()]

        objs = dask.compute(objs)[0]
        ds = dict(zip(keys, objs))
        return datatree.DataTree.from_dict(ds)

    def read_group(self, signal_data, dims):
        arrs = {}

        for variable in dims.keys():
            item = signal_data[variable]
            value = da.from_zarr(item)
            arr = xr.DataArray(value, name=variable, dims=dims[variable])
            arrs[variable] = arr

        dataset = xr.Dataset(arrs)
        # dataset.attrs = dict(signal_data.attrs)
        return dataset

def load_datatree(tree):
    names = [name for name, c in tree.children.items()]
    values = [c.ds for name, c in tree.children.items()]
    values = list(dask.compute(*values))
    items = dict(zip(names, values))
    tree = datatree.DataTree.from_dict(items)
    return tree

def run_test(name, file_name, reader):
    timer = Timer(name + '/Open')
    with timer:
        dt = reader.read(file_name)
    open_results = timer.get_results()

    timer = Timer(name + '/Load')
    with timer:
        load_datatree(dt)
    load_results = timer.get_results()

    return open_results, load_results

def main():
    results = pd.DataFrame()

    names = ['NetCDF', 'HDF', 'Zarr', 'FastZarr']
    file_names = [
        'file_test/grouped_AIT_TPROFILE_ISP.nc',
        'file_test/grouped_AIT_TPROFILE_ISP.hdf',
        'file_test/AIT_TPROFILE_ISP.zarr',
        'file_test/AIT_TPROFILE_ISP.zarr'
    ]

    readers = [
        GroupedNetCDFReader(),
        GroupedNetCDFReader(),
        GroupedZarrReader(),
        GroupedZarrFastReader(),
    ]

    results = []
    for name, file_name, reader in zip(names, file_names, readers):
        open_result, load_result = run_test(name, file_name, reader)
        results.append(open_result)
        results.append(load_result)

    df = pd.DataFrame(results)
    df.to_csv('experiments/results.csv')



if __name__ == "__main__":
    main()