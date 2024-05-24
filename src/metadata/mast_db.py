#!/usr/bin/env python
# coding: utf-8

# In[356]:


import pandas as pd
import numpy as np
from pprint import pprint
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData, select


def connect(URI):
    engine = create_engine(URI)
    metadata_obj = MetaData()
    metadata_obj.reflect(engine)
    return metadata_obj, engine


def null_bool(item):
    if item is np.nan:
        return None
    else:
        return item != "No"


def comissioner_normalize(item):
    if item == "Internal":
        return "UKAEA"
    elif item == "Eurofusion":
        return "EuroFusion"


URI = "mysql+pymysql://root:root@localhost:3306/mast_drupal"
metadata, engine = connect(URI)
Session = sessionmaker(bind=engine)
session = Session()

# pprint([t for t in list(metadata.tables.keys()) if 'field_data_field' in t])
pprint(list(metadata.tables.keys()))


# In[328]:


table_names = [
    "shot_physics_div_config",
    "shot_physics_heating",
    "shot_physics_ip_range",
    "shot_physics_shape",
    "shot_phys_pellets",
    "shot_phys_rmp_coils",
    "shot_preshot",
    "shot_postshot",
    "shot_owner",
    "shot_reference",
    "shot_scenario",
    "shot_datetime",
    "shot_sessionlog",
]

name_mapping = dict(
    shot_reference="field_shot_reference_target_id",
    shot_scenario="field_shot_scenario_tid",
    shot_phys_pellets="field_shot_phys_pellets_tid",
    shot_phys_rmp_coils="field_shot_phys_rmp_coils_tid",
    shot_sessionlog="field_shot_sessionlog_target_id",
)


# In[365]:


dfs = []
for name in table_names:
    table = metadata.tables[f"field_data_field_{name}"]
    column = name_mapping[name] if name in name_mapping else f"field_{name}_value"
    stmt = select(table.c.entity_id, table.c.bundle, table.columns[column])

    df = pd.read_sql(stmt, con=engine.connect())
    df = df.loc[df.bundle == "mast_shot"]
    df = df.drop("bundle", axis=1)
    df = df.set_index("entity_id")

    if "_tid" in column:
        tname = "taxonomy_term_data"
        table = metadata.tables[tname]
        stmt = select(table.c.tid, table.c.name)
        terms = pd.read_sql(stmt, con=engine.connect())
        terms = terms.set_index("tid")
        df = pd.merge(df, terms, left_on=column, right_index=True)
        s = column.replace("_tid", "_name")
        df = df.rename(dict(name=s), axis=1)

    dfs.append(df)

df = pd.concat(dfs, axis=1).sort_index()

sname = "field_data_field_sllog_campaign"
table = metadata.tables[sname]
stmt = select(table.c.entity_id, table.c.field_sllog_campaign_value)
slog = pd.read_sql(stmt, con=engine.connect())
slog = slog.set_index("entity_id")
df = pd.merge(df, slog, left_on="field_shot_sessionlog_target_id", right_index=True)

df.sample(50)


# In[382]:


name = "node"
table = metadata.tables[name]
stmt = select(table)
pd.set_option("display.max_columns", None)
df_node = pd.read_sql(stmt, con=engine.connect())
df_node = df_node.set_index("nid")
df_node = df_node.loc[df_node.type == "mast_shot"]

df_shot = df_node.join(df)

# Drop uninteresting columns
df_shot = df_shot.drop(
    [
        "vid",
        "type",
        "language",
        "uid",
        "comment",
        "promote",
        "sticky",
        "translate",
        "tnid",
        "status",
        "created",
        "changed",
    ],
    axis=1,
)


# Rename types
df_shot = df_shot.rename(
    {
        key: key.replace("field_shot_", "").replace("_value", "").replace("_name", "")
        for key in df_shot.columns
    },
    axis=1,
)
df_shot = df_shot.rename(
    dict(
        title="shot_id",
        reference_target_id="reference_id",
        owner="comissioner",
        field_sllog_campaign="campaign",
    ),
    axis=1,
)

# Tidy up types
df_shot["shot_id"] = df_shot["shot_id"].astype(int)
df_shot["reference_id"] = df_shot["reference_id"].astype("Int64")
df_shot["datetime"] = pd.to_datetime(df_shot.datetime)

id_columns = [
    "sessionlog_target_id",
    "scenario_tid",
    "phys_rmp_coils_tid",
    "phys_pellets_tid",
]
df_shot = df_shot.drop(id_columns, axis=1)

# Get reference shot ID
ref_index = df_shot["reference_id"].dropna().index
ref_ids = df_shot["reference_id"].dropna().values
ref_shot_ids = df_shot["shot_id"].loc[ref_ids].values
df_shot.loc[ref_index, "reference_shot_id"] = ref_shot_ids
df_shot["reference_shot_id"] = df_shot["reference_shot_id"].astype("Int64")


scenarios = pd.DataFrame(dict(scenario=df_shot.scenario.unique())).reset_index()
scenarios = scenarios.drop(0)
scenarios = scenarios.rename(dict(index="scenario_id"), axis=1)
df_shot = pd.merge(
    df_shot, scenarios, left_on="scenario", right_on="scenario", how="outer"
)


df_shot["phys_rmp_coils"] = df_shot["phys_rmp_coils"].map(null_bool)
df_shot["phys_pellets"] = df_shot["phys_pellets"].map(null_bool)

df_shot["comissioner"] = df_shot["comissioner"].map(comissioner_normalize)

df_shot = df_shot.rename(
    dict(
        reference_shot_id="reference_shot",
        physics_ip_range="current_range",
        physics_div_config="divertor_config",
        physics_heating="heating",
        physics_shape="plasma_shape",
        preshot="preshot_description",
        postshot="postshot_description",
        phys_pellets="pellets",
        phys_rmp_coils="rmp_coil",
        datetime="timestamp",
    ),
    axis=1,
)

df_shot = df_shot.sort_values("shot_id")
df_shot.sample(10)


# In[383]:


df_shot.to_parquet("shot_metadata.parquet")
