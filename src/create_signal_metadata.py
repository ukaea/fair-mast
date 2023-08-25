import multiprocessing as mp
from tqdm import tqdm
import pandas as pd
from pathlib import Path
import click
import zarr
import numpy as np
from rich.progress import track
from netCDF4 import Dataset

def parse_signal_metadata(path):
    dataset = Dataset(path, mode='r')
    # signal_root = zarr.open(path, mode='r')
    shot_nums = list(dataset.groups.keys())
    group = dataset[shot_nums[0]]
    metadata = group.__dict__

    item = {}
    item['shot_nums'] = shot_nums
    item['name'] = path.stem
    item['uri'] = str(path)
    item['dimensions'] = list(group.dimensions.keys())
    item.update(metadata)
    print(path, len(shot_nums), item['shape'])
    return item


def parse_metadata(paths, metadata_dir):
    pool = mp.Pool(8)
    mapper = pool.map(parse_signal_metadata, paths)

    metadata = []
    for item in track(mapper, total=len(paths)):
        metadata.append(item)
    metadata = pd.DataFrame(metadata)
    metadata['shape'] = metadata['shape'].map(lambda x: np.atleast_1d(x).tolist())
    print(metadata['shape'])
    metadata.to_parquet(metadata_dir / 'signal_metadata.parquet')


@click.command()
@click.argument('data_dir')
@click.argument('metadata_dir')
def main(data_dir, metadata_dir):
    data_dir = Path(data_dir)
    metadata_dir = Path(metadata_dir)

    signal_files = list(sorted(data_dir.glob('*.nc')))
    print(len(signal_files))
    signal_files = signal_files
    parse_metadata(signal_files, metadata_dir)


if __name__ == "__main__":
    main()
