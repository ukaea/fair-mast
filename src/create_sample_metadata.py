import click
import pandas as pd
import numpy as np
import multiprocessing as mp
from pathlib import Path
from rich.progress import Progress
from netCDF4 import Dataset

def parse_signal_metadata(path):
    print(path)
    dataset = Dataset(path, mode='r')
    # signal_root = zarr.open(path, mode='r')
    shot_nums = list(dataset.groups.keys())

    items = []
    for shot_num, group in dataset.groups.items():
        metadata = group.__dict__

        item = {}
        item['shot_nums'] = shot_num
        item['name'] = path.stem
        item['uri'] = str(path)
        item['shape'] = metadata['shape']
        item['shape'] = np.atleast_1d(item['shape']).tolist()
        item['rank'] = metadata['rank']
        item['signal_status'] = metadata['signal_status']
        item['source_alias'] = metadata['source_alias']
        item['units'] = metadata['units']
        item['description'] = metadata['description']
        item['label'] = metadata['label']
        item['dimensions'] = list(group.dimensions.keys())

        items.append(item)
    return items


def parse_metadata(paths, metadata_dir):
    pool = mp.Pool(8)
    mapper = pool.map(parse_signal_metadata, paths)
    
    metadata = []
    for item in mapper:
        metadata.extend(item)

    metadata = pd.DataFrame(metadata)
    metadata.to_parquet(metadata_dir / 'sample_summary_metadata.parquet')


@click.command()
@click.argument('data_dir')
@click.argument('metadata_dir')
def main(data_dir, metadata_dir):
    data_dir = Path(data_dir)
    metadata_dir = Path(metadata_dir)

    signal_files = list(sorted(data_dir.glob('*.nc')))
    signal_files = signal_files
    parse_metadata(signal_files, metadata_dir)


if __name__ == "__main__":
    main()