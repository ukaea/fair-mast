from sqlalchemy import create_engine, MetaData, insert, delete, select, text

def execute_script(file_name, engine):
    con = engine.raw_connection()
    with open(file_name) as handle:
        cursor = con.cursor()
        cursor.execute(handle.read())
    con.commit() 

def connect(URI):
    engine = create_engine(URI)
    metadata_obj = MetaData()
    metadata_obj.reflect(engine)
    return metadata_obj, engine

def delete_all(name, metadata_obj, engine):
    table = metadata_obj.tables[name]
    stmt = (
        delete(table)
    )

    with engine.begin() as conn:
        conn.execute(stmt)

def reset_counter(table_name, id_name, engine):
    with engine.begin() as conn:
        conn.execute(text(f'ALTER SEQUENCE {table_name}_{id_name}_seq RESTART WITH 1'))