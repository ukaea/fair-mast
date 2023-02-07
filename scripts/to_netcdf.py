import h5py
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path

def load_meta_hdf(path):
    with h5py.File(path) as handle:
        results = traverse(handle)
        meta_df = pd.DataFrame(results)
    return meta_df

def traverse(handle):
    return [item for k in handle.keys() for item in _traverse(handle[k], k)]
        
def _traverse(item, key):
    if hasattr(item, 'keys'):
        results = []
        for k in item.keys():
            out = _traverse(item[k], key + '/' + k)
            results.extend(out)
        return results
    else:
        shape = item.shape
        shape = tuple(v for v in shape if v != 1)
        n_dims = len(shape) if len(item.shape) >= 1 else 1 
        return [dict(name=key, shape=shape, n_dims=n_dims, dtype=item.dtype)]

def convert_to_netcdf(path, output_dir):
    meta_df = load_meta_hdf(path)

    sep = '/'
    meta_df['n_elements'] = meta_df['shape'].apply(np.prod)
    meta_df['signal_name'] = meta_df.name.map(lambda x: sep.join(x.split(sep)[:-1]))
    meta_df['source_name'] = meta_df.name.map(lambda x: x.split(sep)[0])
    meta_df['signal_type'] = meta_df.name.map(lambda x: x.split(sep)[-1])

    data_signals = meta_df.loc[meta_df.signal_type == 'data']
    time_signals = meta_df.loc[meta_df.signal_type == 'time']
    error_signals = meta_df.loc[meta_df.signal_type == 'errors']

    merged = pd.merge(data_signals, time_signals, on='signal_name', suffixes=('', '_time'))
    merged = pd.merge(merged, error_signals, on='signal_name', suffixes=('', '_error'))
    merged = merged.loc[merged.n_dims == merged.n_dims_time]

    def _get_array(name):
        parts = name.split(sep)
        with h5py.File(path) as handle:
            for part in parts:
                keys = handle.keys()
                handle = handle[part]
            return np.atleast_1d(handle[:].squeeze())

    for index, item in merged.iterrows():
        data = _get_array(item['name'])
        error = _get_array(item['name_error'])
        time = _get_array(item['name_time'])

        name = item['name'].replace('/', '-')
        name_error = item['name_error'].replace('/', '-')
        name_time = item['name_time'].replace('/', '-')

        dataset = xr.Dataset(
            data_vars={
                name: (name_time, data),
                name_error: (name_time, error)
            },
            coords={name_time: time}
        )
        print(dataset)
        # dataset.to_netcdf(output_dir / f'{path.stem}.nc', mode='a')
        dataset.to_zarr(output_dir / f'{path.stem}.zarr', mode='a')


def main():
    from src.source import HDFSource
    from dask.distributed import Client, progress
    import logging

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger("NetCDF Writer")
    logger.setLevel(logging.INFO)

    paths = list(Path('./data').glob('*.h5'))
    output_dir = Path('./data/netcdf/test')
    output_dir.mkdir(exist_ok=True, parents=True)

    client = Client(n_workers=8, threads_per_worker=2, memory_limit='20GB')

    logger.info('Loading metadata')
    meta_df = load_meta_hdf(paths[0])

    sep = '/'
    meta_df['n_elements'] = meta_df['shape'].apply(np.prod)
    meta_df['signal_name'] = meta_df.name.map(lambda x: sep.join(x.split(sep)[:-1]))
    meta_df['source_name'] = meta_df.name.map(lambda x: x.split(sep)[0])
    meta_df['signal_type'] = meta_df.name.map(lambda x: x.split(sep)[-1])

    data_signals = meta_df.loc[meta_df.signal_type == 'data']
    time_signals = meta_df.loc[meta_df.signal_type == 'time']
    error_signals = meta_df.loc[meta_df.signal_type == 'errors']

    merged = pd.merge(data_signals, time_signals, on='signal_name', suffixes=('', '_time'))
    merged = pd.merge(merged, error_signals, on='signal_name', suffixes=('', '_error'))
    merged = merged.loc[merged.n_dims == merged.n_dims_time]
    merged = merged.loc[merged.n_dims == 1]
    merged = merged.loc[merged.signal_name.apply(lambda x: x[0] != 'x')]

    logger.info("Loading signals")
    source = HDFSource('./data')
    signals = source.read_shot_all_signals(shot='30449')
    
    logger.info(f"Loaded {len(signals)} signals")
    logger.info("Creating dataset")
    
    datasets = []
    paths = []
    for group_index, df in merged.groupby('signal_name'):
        dataset = xr.Dataset()
        # Group data, error, and time together
        data_vars = {}
        for _, row in list(df.iterrows()):
            data = signals[row['name']]
            error = signals[row.name_error]
            time = signals[row.name_time]

            name = row['name'].replace('/', '-')
            name_time = row['name_time'].replace('/', '-')
            name_error = row['name_error'].replace('/', '-')
            
            logger.info(f'\t {group_index} {str(data.shape)}')
            coord = xr.DataArray(data=time, dims=name_time)
            data_vars[name] = xr.DataArray(data=data, coords={name_time: coord})
            data_vars[name_error] = xr.DataArray(data=error, coords={name_time: coord})
    
        dataset = xr.Dataset(data_vars)
        datasets.append(dataset)
        path = output_dir / f"30449_{group_index.replace('/', '_')}.nc"
        paths.append(path)

    logger.info(dataset)
    logger.info("Writing dataset")
    job = xr.save_mfdataset(datasets, paths, mode='w', engine='netcdf4', compute=False)
    progress(job.persist())

        
    
if __name__ == "__main__":
    main()