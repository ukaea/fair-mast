import h5py
import zarr
import yaml
import numpy as np
import pandas as pd
import dateutil.parser as parser
from pathlib import Path

from sqlalchemy import insert, select, update
from sqlalchemy.sql.expression import cast
from sqlalchemy.types import TIMESTAMP, DATE, TIME, INTEGER, FLOAT
from sqlalchemy_utils.functions import drop_database, database_exists, create_database
from src.db_utils import connect, delete_all, reset_counter, execute_script

def read_config(path):
    with Path(path).open('r') as handle:
        config = yaml.load(handle, yaml.SafeLoader)
    return config

def create_scenarios(metadata_obj, engine, shot_metadata):
    ids = shot_metadata['scenario_id'].unique()
    scenarios = shot_metadata['scenario'].unique()

    data = pd.DataFrame(dict(id=ids, name=scenarios)).set_index('id')
    data = data.dropna()
    data.to_sql('scenarios', engine, if_exists='append')

def create_shot_cpf(metadata_obj, engine, config):
    shots_table = metadata_obj.tables['shots']
    dtypes = {c.name: c.type for c in shots_table.columns}

    # Read CPF values from HDF
    for file_name in Path(config['hdf_store']).glob('*.h5'):
        data = {}
        shot_id = int(file_name.name.split('.')[0])
        with h5py.File(file_name) as handle:
            cpf_values = dict(handle.attrs)
            for key, value in cpf_values.items():
                if str(value) != 'NO VALUE':
                    column_name = f'cpf_{key}'

                    # Parse timestamps/dates/times to proper datetime objects
                    if isinstance(dtypes[column_name], TIMESTAMP): 
                        value = parser.parse(value)
                    if isinstance(dtypes[column_name], DATE): 
                        value = parser.parse(value).date()
                    if isinstance(dtypes[column_name], TIME): 
                        value = parser.parse(value).time()
                    if isinstance(dtypes[column_name], INTEGER):
                        data[column_name] = int(value)
                    if isinstance(dtypes[column_name], FLOAT):
                        data[column_name] = float(value)
                    else:
                        data[column_name] = str(value)

        stmt = (
            update(shots_table)
            .where(shots_table.c.shot_id == shot_id)
            .values(**data)
        )

        with engine.begin() as conn:
            conn.execute(stmt)

def lookup_status_code(status):
    lookup = {
        -1: 'Very Bad',
        0: 'Bad',
        1: 'Not Checked',
        2: 'Checked',
        3: 'Validated'
    }
    return lookup[status]
    
def create_signal(file_name, metadata_obj, engine):
    dataset = zarr.open_group(file_name)
    shot_id = next(dataset.group_keys())
    dataset = dataset[shot_id]
    attrs = dataset.attrs

    data = {}
    data['name'] = file_name.stem
    data['units'] = attrs['units']
    data['uri'] = str(file_name.resolve())
    data['rank'] = attrs['rank']
    data['description'] = attrs['label']
    data['signal_type'] = attrs['signal_type']
    data['quality'] = lookup_status_code(attrs['status'])
    data['doi'] = ''

    signal_table = metadata_obj.tables['signals']
    stmt = (
        insert(signal_table).
        values(**data).returning(signal_table.c.signal_id)
    )

    with engine.begin() as conn:
        result = conn.execute(stmt)
        signal_id = result.all()[0][0]

    return signal_id

def create_signal_link(file_name, signal_id, metadata_obj, engine):
    dataset = zarr.open_group(file_name)
    shot_ids = list(dataset.group_keys())
    df =  pd.DataFrame()
    df['shot_id'] = shot_ids
    print(f'Ingesting signal {file_name}, {len(df)}')
    df['shot_id'] = df['shot_id'].astype(int)
    df['signal_id'] = signal_id
    df = df.set_index('shot_id')
    df.to_sql('shot_signal_link', engine, if_exists='append')

def load_hdf_metadata(path):
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

    sep = '/'
    meta_df['shot_id'] = int(path.stem)
    meta_df['n_elements'] = meta_df['shape'].apply(np.prod)
    meta_df['signal_name'] = meta_df.name.map(lambda x: sep.join(x.split(sep)[:-1]))
    meta_df['signal_name'] = meta_df['signal_name'].str.replace('/', '_')
    meta_df['source_name'] = meta_df.name.map(lambda x: x.split(sep)[0])
    meta_df['signal_type'] = meta_df.name.map(lambda x: x.split(sep)[-1])
    meta_df = meta_df.loc[meta_df.signal_name.apply(lambda x: x[0] != 'x')]
    return meta_df

def create_shot_signal_links(metadata_obj, engine, config):
    df = pd.read_parquet('./data/signal_metadata.parquet')

    signals_table = metadata_obj.tables['signals']
    stmt = select(signals_table.c.signal_id, signals_table.c.name)
    signals = pd.read_sql(stmt, con=engine.connect())
    df = pd.merge(df[['shot_nums', 'name']], signals, on='name')

    shot_signal_link = []
    for index, row in df.iterrows():
        tmp = pd.DataFrame(row.shot_nums, columns=['shot_id'])
        tmp['signal_id'] = int(row.signal_id)
        tmp['shot_id'] = tmp.shot_id.astype(int)
        shot_signal_link.append(tmp)

    shot_signal_link = pd.concat(shot_signal_link)
    shot_signal_link = shot_signal_link.set_index('shot_id')
    shot_signal_link.to_sql('shot_signal_link', engine, if_exists='append')

def create_signals(metadata_obj, engine, config):
    df = pd.read_parquet('./data/signal_metadata.parquet')
    df['description'] = df['label']
    df['signal_type'] = 'Analysed'
    df['quality'] = 'Not Checked'#lookup_status_code(attrs['status'])
    df['doi'] = ''
    df = df.drop(['shot_nums', 'shape', 'time_index', 'label'], axis=1)
    df.to_sql('signals', engine, if_exists='append', index=False)

def create_shots(metadata_obj, engine, config, shot_metadata):
    shot_metadata['facility'] = 'MAST'
    shot_metadata = shot_metadata.set_index('shot_id')
    shot_metadata['scenario'] = shot_metadata['scenario_id']
    shot_metadata = shot_metadata.drop(['scenario_id', 'reference_id'], axis=1)
    shot_metadata.to_sql('shots', engine, if_exists='append')
    # create_shot_cpf(metadata_obj, engine, config)
    

def create_cpf_summary(metadata_obj, engine, config):
    shot_files = list(Path(config['hdf_store']).glob('*.h5'))
    with h5py.File(shot_files[0], 'r') as handle:
        cpf_definitions = dict(handle['definitions'].attrs)
        cpf_definitions = {f'cpf_{key}': value for key, value in cpf_definitions.items()}

    df = pd.DataFrame([cpf_definitions]).T
    df.columns = ['description']
    df.name = 'name'

    df.to_sql('cpf_summary', engine, if_exists='replace')

def main():
    config = read_config('config.yml')
    uri = config['db_uri']

    # create database
    if database_exists(uri):
        drop_database(uri)
    create_database(uri)

    # create database tables
    metadata_obj, engine = connect(uri)
    execute_script('./sql/create_tables.sql', engine)

    # refresh engine to get table metadata
    metadata_obj, engine = connect(uri)

    shot_metadata = pd.read_parquet(config['shot_metadata'])

    # delete all instances in the database
    delete_all('shot_signal_link', metadata_obj, engine)
    delete_all('shots', metadata_obj, engine)
    delete_all('signals', metadata_obj, engine)
    delete_all('scenarios', metadata_obj, engine)
    delete_all('cpf_summary', metadata_obj, engine)

    # reset the ID counters
    reset_counter('signals', 'signal_id', engine)
    reset_counter('shot_signal_link', 'id', engine)

    # populate the database tables
    # create_cpf_summary(metadata_obj, engine, config)
    create_scenarios(metadata_obj, engine, shot_metadata)
    create_shots(metadata_obj, engine, config, shot_metadata)
    create_signals(metadata_obj, engine, config)
    create_shot_signal_links(metadata_obj, engine, config)


if __name__ == "__main__":
    main()