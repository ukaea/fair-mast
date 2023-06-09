import dask
import dask.array as da
import datatree
import xarray as xr
from functools import partial
from pathlib import Path
import zarr
import time

def load_group(signal_data):
    arrs = {}
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

def main():
    data_dir = Path('data/mast')
    file_name = data_dir / 'EFM_PLASMA_VOLUME.zarr'
    store = zarr.open_consolidated(file_name)
    keys = list(store.keys())[1:]

    # store = zarr.open(file_name)
    def read_group(key, store):
        return load_group(store[key])

    start = time.time()
    func = partial(read_group, store=store)
    results = list(map(func, keys[:100]))
    end = time.time()
    print(end-start)

if __name__ == '__main__':
    main()