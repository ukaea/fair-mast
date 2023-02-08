from pathlib import Path
import numpy as np
import h5py
import pandas as pd
import click

def load_hdf(path):
    results = []

    def _visitor(name, node):
        if isinstance(node, h5py.Dataset):
            shape = node.shape
            shape = tuple(v for v in shape if v != 1)
            n_dims = len(shape) if len(node.shape) >= 1 else 1 
            units = node.attrs.get('units', '')
            label = node.parent.attrs.get('label', '')
            description = node.parent.attrs.get('description', '')
            result = dict(name=name, shape=shape, n_dims=n_dims, dtype=str(node.dtype), units=units, label=label, description=description)
            results.append(result)
            
    with h5py.File(path) as handle:
        handle.visititems(_visitor)
        meta_df = pd.DataFrame(results)
    meta_df['shot_id'] = int(path.stem)
    return meta_df

@click.command()
@click.argument('input_folder')
@click.argument('output_file')
def main(input_folder, output_file):
    hdf_files = list(Path(input_folder).glob('*.h5'))
    meta_df = pd.concat([load_hdf(data_file) for data_file in hdf_files])

    sep = '/'
    meta_df['n_elements'] = meta_df['shape'].apply(np.prod)
    meta_df['signal_name'] = meta_df.name.map(lambda x: sep.join(x.split(sep)[:-1]))
    meta_df['source_name'] = meta_df.name.map(lambda x: x.split(sep)[0])
    meta_df['signal_type'] = meta_df.name.map(lambda x: x.split(sep)[-1])
    meta_df.to_parquet(output_file)
    

if __name__ == "__main__":
    main()