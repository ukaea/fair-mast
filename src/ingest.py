import h5py
import zarr
import yaml
import numpy as np
import pandas as pd
import dateutil.parser as parser
from datetime import datetime
from pathlib import Path

from sqlalchemy import insert, select
from sqlalchemy.types import TIMESTAMP, DATE, TIME
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

def create_shot(path, metadata_obj, engine, shot_metadata):
    shots_table = metadata_obj.tables['shots']
    dtypes = {c.name: c.type for c in shots_table.columns}

    file_name = Path(path)
    with h5py.File(file_name) as handle:
        data = {}
        data['shot_id'] = int(str(file_name.name).split('.')[0])
        
        shot_data = shot_metadata.loc[shot_metadata.shot_id == data['shot_id']]
        shot_data = shot_data.iloc[0]

        data['reference_shot'] = shot_data['reference_shot_id']
        data['current_range'] = shot_data['physics_ip_range']
        data['divertor_config'] = shot_data['physics_div_config']
        data['plasma_shape'] = shot_data['physics_shape']
        data['preshot_description'] = shot_data['preshot']
        data['postshot_description'] = shot_data['postshot']
        data['comissioner'] = shot_data['comissioner']
        data['campaign'] = shot_data['campaign']
        data['scenario'] = shot_data['scenario_id']
        data['pellets'] = shot_data['phys_pellets']
        data['rpm_coil'] = shot_data['phys_rmp_coils']
        data['heating'] = shot_data['physics_heating']

        data['facility'] = 'MAST'

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
                data[column_name] = value 

        data['timestamp'] = shot_data['datetime']

    dtypes = {k: v for k, v in dtypes.items() if k in data}
    data = pd.DataFrame([data]).set_index('shot_id')
    data.to_sql('shots', engine, if_exists='append', dtype=dtypes)

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
    signal_files = Path(config['zarr_store']).glob('*.zarr')
    for file_name in signal_files:
        create_shot_signal_link(file_name, metadata_obj, engine)

def create_signals(metadata_obj, engine, config):
    signal_files = Path(config['zarr_store']).glob('*.zarr')

    for file_name in signal_files:
        create_signal(file_name, metadata_obj, engine)

def create_shots(metadata_obj, engine, config, shot_metadata):
    shot_files = Path(config['hdf_store']).glob('*.h5')
    for file_name in shot_files:
        create_shot(file_name, metadata_obj, engine, shot_metadata)
    
def create_shot_signal_link(file_name, metadata_obj, engine):
    dataset = zarr.open_group(file_name)
    shot_ids = list(dataset.group_keys())

    signals_table = metadata_obj.tables['signals']
    stmt = select(signals_table.c.signal_id).where(signals_table.c.name == file_name.stem)
    with engine.begin() as conn:
        result = conn.execute(stmt).first()
        signal_id = result[0]

    df = pd.DataFrame()
    df['shot_id'] = np.unique(shot_ids)
    df['signal_id'] = signal_id
    df = df.set_index('shot_id')
    df.to_sql('shot_signal_link', engine, if_exists='append')

def create_cpf_summary(metadata_obj, engine):
    shot_files = list(Path('data/mast/mast2HDF5/').glob('*.h5'))
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
    create_cpf_summary(metadata_obj, engine)
    create_scenarios(metadata_obj, engine, shot_metadata)
    create_shots(metadata_obj, engine, config, shot_metadata)
    create_signals(metadata_obj, engine, config)
    create_shot_signal_links(metadata_obj, engine, config)


if __name__ == "__main__":
    main()