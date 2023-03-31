import click
import h5py
import dask
import dask.array as da
import xarray as xr
import numpy as np
import pandas as pd
import logging
from datatree import DataTree
from dask.distributed import Client, progress
from pathlib import Path


def _is_ragged(df):
    df['ragged'] = len(df['shape'].unique()) > 1
    return df

def _read_attrs(path, name):
    with h5py.File(path) as handle:
        source_name = name.split('/')[0]
        attrs = dict(handle[source_name].attrs)
        parent = handle[name].parent
        attrs.update(dict(parent.attrs))
        return attrs
        
def _read_signal(path, name):
    file_handle = h5py.File(path)
    data = da.from_array(file_handle[name])
    #data = da.squeeze(data)
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

    logger.info('Loading metadata')
    meta_df = pd.read_parquet(input_folder / 'metadata.parquet')
    meta_df['shape'] = meta_df['shape'].apply(tuple)
    meta_df['path'] = meta_df['shot_id'].apply(lambda p: input_folder / f"{p}.h5")

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

    
    for group_index, df in merged.groupby('signal_name'):
        logger.info(f'\t {group_index}')

        datasets = {}
        for _, row in list(df.iterrows()):
            data = _read_signal(row.path, row['name'])
            error = _read_signal(row.path, row['name_error'])
            time = _read_signal(row.path, row['name_time'])
            attrs = _read_attrs(row.path, row['name'])

            dims = ['time']
            dims += [f'dim_{i}' for i in range(len(data.shape[1:]))]
            
            dataset = xr.Dataset(
                data_vars={
                'data': (dims, data),
                'error': (dims, error),
            }, coords={
                'time': time
            }, attrs=attrs)

            shot_id = str(attrs['shot'])
            datasets[shot_id] = dataset

        file_name = group_index.replace('/', '_').replace(' ', '_')
        file_name = output_folder / f"{file_name}.zarr"
        tree = DataTree.from_dict(datasets)
        tree.to_zarr(file_name, mode='a')


if __name__ == "__main__":
    main()
