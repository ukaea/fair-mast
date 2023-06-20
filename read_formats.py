import xarray as xr
import h5py
import netCDF4
from netCDF4 import Dataset
import time
import zarr
import dask.array as da

class Timer():

    def __init__(self, name=''):
        self.name = name

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args, **kwargs):
        self.end = time.time()
        print(self.name, self.end - self.start)

class GroupedNetCDFReader:

    def read(self, path):
        ncf = netCDF4.Dataset(path, mode='r')
        keys = list(ncf.groups.keys())
        data = {name: self.read_group(ncf, name) for name in keys}
        ncf.close()

    def read_group(self, ncf, name):
        store = xr.backends.NetCDF4DataStore(ncf.groups.get(name))
        dataset = xr.open_dataset(store, chunks=-1)
        return dataset

class GroupedZarrReader:

    def read(self, path):
        store = zarr.open_consolidated(path, mode='r')

        for name, group in store.groups():
            xr.open_dataset(xr.backends.ZarrStore(group, mode='r'), chunks={})
        # groups = store.groups()
        # _, group = next(groups)
        # dims = {}
        # for key in group.keys():
        #     dims[key] = group[key].attrs['_ARRAY_DIMENSIONS']

        # keys = [key for key, group in groups]
        # objs = [self.read_group(group, dims) for key, group in store.groups()]

        # ds = dict(zip(keys, objs))

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


def main():
    with Timer('Zarr'):
        reader = GroupedZarrReader()
        reader.read('file_test/AIT_TPROFILE_ISP.zarr')

    with Timer('Grouped NetCDF'):
        reader = GroupedNetCDFReader()
        reader.read('file_test/grouped_AIT_TPROFILE_ISP.nc')

    with Timer('Grouped HDF'):
        reader = GroupedNetCDFReader()
        reader.read('file_test/grouped_AIT_TPROFILE_ISP.hdf')


if __name__ == "__main__":
    main()