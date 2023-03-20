import numpy as np
import h5py
from datetime import datetime
from pathlib import Path
import pandas as pd
import xarray as xr
from sqlalchemy import create_engine, MetaData, insert, delete, select, text

def create_scenarios(metadata_obj, engine):
    scenario_table = metadata_obj.tables['scenarios']
    shot_table = metadata_obj.tables['shots']

    # Setup a fake scenario
    with engine.connect() as conn:
        stmt = (
            delete(shot_table).
            where(shot_table.c.scenario == 1)
        )
        conn.execute(stmt)
        stmt = (
            delete(scenario_table).
            where(scenario_table.c.id == 1)
        )
        conn.execute(stmt)

        stmt = (
            insert(scenario_table).
            values(id=1, name='Scenario1')
        )

        conn.execute(stmt)

def _is_ragged(df):
    df['ragged'] = len(df['shape'].unique()) > 1
    return df

def create_shot(path, metadata_obj, engine):
    shots_table = metadata_obj.tables['shots']
    dtypes = {c.name: c.type for c in shots_table.columns}

    file_name = Path(path)
    with h5py.File(file_name) as handle:
        data = {}

        data['shot_id'] = int(str(file_name.name).split('.')[0])
        data['timestamp'] = datetime.now()
        data['scenario'] = 1
        data['reference_shot'] = None
        data['current_range'] = '400 kA'
        data['heating'] = '101'
        data['divertor_config'] = 'X Divertor'
        data['pellets'] = False
        data['plasma_shape'] = 'Double Null'
        data['rpm_coil'] = None
        data['preshot_description'] = ''
        data['postshot_description'] = ''
        data['comissioner'] = 'UKAEA'
        data['campaign'] = 'M0'
        data['facility'] = 'MAST'

        # cpf_values = dict(handle.attrs)
        # for key, value in cpf_values.items():
        #     if str(value) != 'NO VALUE':
        #         data[f'cpf_{key}_value'] = value 
            # if str(value) != 'NO VALUE' else None

    dtypes = {k: v for k, v in dtypes.items() if k in data}
    data = pd.DataFrame([data]).set_index('shot_id')
    data.to_sql('shots', engine, if_exists='append', dtype=dtypes)

def create_signal(file_name, metadata_obj, engine):
    data = {}
    data['name'] = file_name.stem
    data['units'] = ''
    data['uri'] = str(file_name.resolve())
    data['description'] = ''
    data['signal_type'] = 'Raw'
    data['quality'] = 'Validated'
    data['doi'] = ''

    signal_table = metadata_obj.tables['signals']
    stmt = (
        insert(signal_table).
        values(**data).returning(signal_table.c.signal_id)
    )

    with engine.connect() as conn:
        result = conn.execute(stmt)
        signal_id = result.all()[0][0]

    return signal_id

def create_signal_link(file_name, signal_id, metadata_obj, engine):
    dataset = xr.open_zarr(file_name) 
    print(f'Ingesting signal {file_name}, {dataset.shot_id.shape}')
    df = dataset.shot_id.drop_duplicates(dim='index').to_dataframe()
    df['shot_id'] = df['shot_id'].astype(int)
    df['signal_id'] = signal_id
    df = df.set_index('shot_id')
    df.to_sql('shot_signal_link', engine, if_exists='append')

def delete_all_shots(metadata_obj, engine):
    shots_table = metadata_obj.tables['shots']
    stmt = (
        delete(shots_table)
    )

    with engine.connect() as conn:
        conn.execute(stmt)

def delete_all(name, metadata_obj, engine):
    table = metadata_obj.tables[name]
    stmt = (
        delete(table)
    )

    with engine.connect() as conn:
        conn.execute(stmt)

def delete_all_signals(metadata_obj, engine):
    signal_table = metadata_obj.tables['signals']
    stmt = (
        delete(signal_table)
    )

    with engine.connect() as conn:
        conn.execute(stmt)

def reset_counter(table_name, id_name, engine):
    with engine.connect() as conn:
        conn.execute(f'ALTER SEQUENCE {table_name}_{id_name}_seq RESTART WITH 1')

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

def create_shot_signal_links(metadata_obj, engine):
    signal_files = Path('data/mast/zarr/').glob('*.zarr')
    for file_name in signal_files:
        create_shot_signal_link(file_name, metadata_obj, engine)

def create_shots(metadata_obj, engine):
    shot_files = Path('data/mast/mast2HDF5/').glob('*.h5')
    for file_name in shot_files:
        create_shot(file_name, metadata_obj, engine)

def create_signals(metadata_obj, engine):
    signal_files = Path('data/mast/zarr/').glob('*.zarr')

    for file_name in signal_files:
        create_signal(file_name, metadata_obj, engine)
    
def create_shot_signal_link(file_name, metadata_obj, engine):
    dataset = xr.open_zarr(file_name)

    signals_table = metadata_obj.tables['signals']
    stmt = select(signals_table.c.signal_id).where(signals_table.c.name == file_name.stem)
    with engine.connect() as conn:
        result = conn.execute(stmt).first()
        signal_id = result[0]

    df = pd.DataFrame()
    df['shot_id'] = np.unique(dataset.shot_id.values)
    df['signal_id'] = signal_id
    df = df.set_index('shot_id')
    df.to_sql('shot_signal_link', engine, if_exists='append')
    
def get_metadata(engine):
    metadata_obj = MetaData()
    metadata_obj.reflect(engine)
    return metadata_obj
    
def execute_script(file_name, engine):
    with engine.connect() as con:
        with open(file_name) as file:
            query = text(file.read())
            con.execute(query)
 

def main():
    from sqlalchemy_utils.functions import drop_database, database_exists, create_database

    URI = 'postgresql://root:root@localhost:5433/mast_db1'
    
    engine = create_engine(URI)
    metadata_obj = get_metadata(engine)
        
    delete_all('shot_signal_link', metadata_obj, engine)
    delete_all('shots', metadata_obj, engine)
    delete_all('signals', metadata_obj, engine)
    delete_all('scenarios', metadata_obj, engine)

    reset_counter('signals', 'signal_id', engine)
    reset_counter('shot_signal_link', 'id', engine)

    create_scenarios(metadata_obj, engine)
    create_shots(metadata_obj, engine)
    create_signals(metadata_obj, engine)

    create_shot_signal_links(metadata_obj, engine)


if __name__ == "__main__":
    main()