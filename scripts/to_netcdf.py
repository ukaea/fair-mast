import click
import h5py
import dask
import dask.array as da
import xarray as xr
import pandas as pd
import logging
from dask.distributed import Client, progress
from pathlib import Path


def _is_ragged(df):
    df['ragged'] = len(df['shape'].unique()) > 1
    return df

def _read_signal(path, name):
    file_handle = h5py.File(path)
    data = da.from_array(file_handle[name])
    data = da.squeeze(data)
    data = da.atleast_1d(data)
    return data

@click.command()
@click.argument('input_folder')
@click.argument('output_folder')
@click.option('--format', default='netcdf', type=click.Choice(['netcdf', 'zarr']))
def main(input_folder, output_folder, format):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger("NetCDF Writer")
    logger.setLevel(logging.INFO)

    input_folder = Path(input_folder)
    paths = list(Path(input_folder).glob('*.h5'))
    output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True, parents=True)

    _ = Client(n_workers=8, threads_per_worker=2, memory_limit='20GB')

    logger.info('Loading metadata')
    meta_df = pd.read_parquet(input_folder / 'metadata.parquet')
    meta_df['shape'] = meta_df['shape'].apply(tuple)
    meta_df['path'] = meta_df['shot_id'].apply(lambda p: f"./data/hdf/{p}.h5")

    data_signals = meta_df.loc[meta_df.signal_type == 'data']
    time_signals = meta_df.loc[meta_df.signal_type == 'time']
    error_signals = meta_df.loc[meta_df.signal_type == 'errors']

    merged = pd.merge(data_signals, time_signals, on=['shot_id', 'signal_name'], suffixes=('', '_time'))
    merged = pd.merge(merged, error_signals, on=['shot_id', 'signal_name'], suffixes=('', '_error'))
    merged = merged.groupby('signal_name').apply(_is_ragged)
    # merged = merged.loc[merged.n_dims == merged.n_dims_time]
    # merged = merged.loc[merged.n_dims == 1]
    merged = merged.loc[merged.signal_name.apply(lambda x: x[0] != 'x')]

    logger.info(f"{len(merged.groupby('signal_name'))}")
    logger.info("Creating datasets")
    
    paths= []
    datasets =[]
    for group_index, df in merged.groupby('signal_name'):
        name = group_index.replace('/', '_')

        datas, errors, times, shot_ids = [], [], [], []
        for _, row in list(df.iterrows()):
            data = _read_signal(row.path, row['name'])
            error = _read_signal(row.path, row['name_error'])
            time = _read_signal(row.path, row['name_time'])

            if time.shape[0] != data.shape[0]:
                time = da.repeat(time, data.shape[0], axis=0)

            shot_num = da.full_like(time, row.shot_id)
            shot_ids.append(shot_num)
            datas.append(data)
            errors.append(error)
            times.append(time)

        logger.info(f'\t {group_index} {row.ragged} {datas[0].shape}, {time[0].shape} ')

        datas = da.concatenate(datas)
        errors = da.concatenate(errors)
        times = da.concatenate(times)
        shot_ids = da.concatenate(shot_ids)

        dims = ['index']
        dims += [f'dim_{i}' for i in range(len(datas.shape) - 1)]

        time = xr.DataArray(times, dims=['index'])
        shot_ids = xr.DataArray(shot_ids, dims=['index'])
        data = xr.DataArray(datas, dims=dims)
        error = xr.DataArray(errors, dims=dims)
        dataset = xr.Dataset({name: data, name + '_error': error, 'shot_id': shot_ids, 'time': time})

        datasets.append(dataset)
        path = output_folder / f"{group_index.replace('/', '_')}.nc"
        paths.append(path)

    logger.info(f"Writing {len(paths)} datasets")
    if format == 'netcdf':
        job = xr.save_mfdataset(datasets, paths, mode='w', engine='netcdf4', compute=False)
        progress(job.persist())
    elif format == 'zarr':
        results = [dataset.to_zarr(path.with_suffix(''), compute=False) for path, dataset in zip(paths, datasets)]
        progress(dask.persist(*results))
        
    
if __name__ == "__main__":
    main()