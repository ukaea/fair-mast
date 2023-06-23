import time
import xarray as xr
import datatree
import zarr
from huggingface_hub import login
from datasets import load_dataset
import dask
import dask.array as da

def load_dt(url):
    store = zarr.storage.FSStore(url=url, mode='r')
    archive = zarr.open(store)
    keys = [key.split('/')[0] for key in store.keys() if not key.startswith('.')]
    keys = set(keys)
    datasets = {}
    for key in keys:
        signal_data = archive[key] 
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
        dataset.attrs = dict(archive[key].attrs)
        datasets[key] = dataset
    ds = datatree.DataTree.from_dict(datasets)
    return ds

def main():
    login(new_session=False)

    # def _sel(x):
    #     x['data'] = x['data'].sel({'Time (sec)': slice(0, .5)})
    #     return x

    dataset = load_dataset('sljack/mast', 
                           'EFM_PSI_R_Z',
                           use_auth_token=True, 
                           streaming=True, 
                           download_mode="force_redownload",
                           return_xarray=False)

    dataset = dataset['full']
    # dataset = dataset.map(_sel)
    for item in dataset:
        print(item.keys())
    
    # start = time.time()
    # url = "zip://::hf://datasets/sljack/mast/data/EFM_PSI_R_Z.zarr.zip"
    # ds = load_dt(url)
    # end = time.time()
    # print(end-start)
    # print(len(ds))
    # print(ds['28456']['data'].compute())
    # start = time.time()
    # ds = datatree.open_datatree(url, engine='zarr', chunks={})
    # end = time.time()
    # print(end-start)


    # dataset = datatree.open_datatree('AMC_PLASMA CURRENT.zarr', engine='zarr')
    # store = zarr.ZipStore('Test/data/example.zarr.zip', mode='w')
    # dataset.to_zarr(store)
    
if __name__ == "__main__":
    main()