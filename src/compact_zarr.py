import zarr
import intake
import dask
import dask.array as da
import xarray as xr
import numpy as np
from functools import partial
from pathlib import Path
from rich.progress import Progress, track
from dask.distributed import Client, as_completed

@xr.register_dataset_accessor("shots")
class ShotAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj
        self._center = None

    def to_datatree(self):
        result = self.to_dict()
        return datatree.DataTree.from_dict(result)
        
    def to_dict(self):
        offsets = self._obj.offsets.compute()
        ntime = self._obj.dims['time']

        shot_groups = {}
        lower = 0
        for shot_index, (shot, offset) in enumerate(zip(self._obj.shot_index.values, offsets.values)):
            upper = lower+offset
            shot_slice = self._obj.isel(dict(time=np.arange(lower, upper), shot_index=shot_index))
            shot_groups[shot] = shot_slice
            lower = upper

        return shot_groups

    def groupby(self):
        ntime = self._obj.dims['time']
        shot_groups = {}
        lower = 0
        offsets = self._obj.offsets.compute()
        shots = self._obj.shot_index.compute()
        index = np.empty(ntime, dtype='<U6')
        for shot_index, (shot, offset) in enumerate(zip(shots.values, offsets.values)):
            upper = lower+offset
            index[lower:upper] = shot
            lower = upper

        index = xr.DataArray(index, dims=['time'])
        return self._obj.groupby(index)



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
    store = zarr.open(file_name, mode='r')
    groups = store.groups()
    groups = list(groups)
    ds = {key: load_group(group) for key, group in groups}
    return ds

def convert_file(path, output_dir):
    name = Path(path).name
    store = zarr.open(path, mode='r')

    groups = store.groups()
    groups = list(groups)
    groups = [k for k, v in groups]
    offsets = []

    file_name = output_dir / name
    for group in groups:
        ds = load_group(store[group])
        mode = 'a' if Path(file_name).exists() else 'w'
        append_dim = 'time' if mode == 'a' else None
        # ds['offsets'] = xr.DataArray([offset], dims='shot_index', coords=dict(shot_index=[group]))
        offsets.append(ds.dims['time'])
        ds.to_zarr(file_name, mode=mode, append_dim=append_dim)

    store = zarr.open(file_name)
    store.array('offsets', offsets)
    store['offsets'].attrs.update(dict(_ARRAY_DIMENSIONS='shot_index'))

    store.array('shot_index', groups)
    store['shot_index'].attrs.update(dict(_ARRAY_DIMENSIONS='shot_index'))

    zarr.convenience.consolidate_metadata(file_name)

def main():
    client = Client(scheduler_file='scheduler.json')

    catalog = intake.open_catalog('data/mast/catalog.yml')
    keys = catalog.keys()
    keys = list(keys)

    output_dir = Path('data/compact')
    output_dir.mkdir(exist_ok=True)

    func = partial(convert_file, output_dir=output_dir)

    tasks = []
    for key in keys:
        path = catalog[key].urlpath
        print("Submitted", path)
        task = client.submit(func, path)
        tasks.append(task)

    for item in track(as_completed(tasks), description='Writing files...', total=len(tasks)):
        pass

if __name__ == "__main__":
    main()