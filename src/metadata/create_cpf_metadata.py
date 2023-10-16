import numpy as np
from importlib import import_module
import pandas as pd
import multiprocessing as mp
import click
from functools import partial
from tqdm import tqdm
from pycpf import pycpf


def read_cpf_for_shot(shot, columns):
    pycpf = import_module('pycpf')
    cpf_data = {}
    for name in columns:
        entry = pycpf.pycpf.query(name, f"shot = {shot}") 
        value = entry[name][0] if name in entry else np.nan
        cpf_data[name] = value 

    cpf_data['shot_id'] = shot
    return cpf_data

@click.command()
@click.argument("shot_file")
def main(shot_file):
    shot_ids = pd.read_csv(shot_file)
    shot_ids = shot_ids['shot_id'].values

    columns = pycpf.columns()
    columns = pd.DataFrame(columns, columns=['name', 'description'])
    columns.to_parquet('data/cpf_columns.parquet')

    pool = mp.Pool(8)
    column_names = columns['name'].values
    func = partial(read_cpf_for_shot, columns=column_names)
    mapper = pool.imap_unordered(func, shot_ids)
    rows = [item for item in tqdm(mapper, total=len(shot_ids))]
    cpf_data = pd.DataFrame(rows)

    # Convert objects to strings
    for column in cpf_data.columns:
        dtype = cpf_data[column].dtype
        if isinstance(dtype, object):
            cpf_data[column] = cpf_data[column].astype(str)

    cpf_data.to_parquet('data/cpf_data.parquet')
    print(cpf_data)
   

if __name__ == "__main__":
    main()
