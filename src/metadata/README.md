# Metadata Parsing Tools

Tools to parse metadata for ingestion into the database

- `create_campaign_shot_lists.py` - script to create shot lists as a CSV file for each campaign using the GraphQL API. This requires fully working & setup metadatabase
- `create_cpf_metadata.py` - script to parse CPF data from PyUDA
- `create_signal_metadata.py` - script to create a parquet file summarising the metadata for a induvidual signal from a Zarr file.
- `create_signal_metadata.py` - script to create a parquet file summarising the metadata for a induvidual signal from a HDF file.
- `create_signal_dataset_metadata.py` - script to create a parquet file summarising the metadata for a signal dataset.
- `mast_db.ipynb` - script to parse shot data from the Drupal database - see more below


### Drupal Database Script
Scripts & Tools to parse meta data from the entire MAST shot database. This creates a MySQL server and loads a copy of a backup ata from the Drupal database behind 
the MAST users website into it so we can parse that info.

Warning! This database contains potentially sensitive information such as passwords. Therefore we must ensure we don't parse any information about that.

### Setup

To start the MySQL instance:

```bash
docker-compose up
```

To setup the database:

```bash
docker exec -it mysql mysql -uroot -p create database mast_drupal;
docker exec -it mysql mysql -uroot -p mast_drupal < /data/database.sql;
```

To access the container
```bash
docker exec -it mysql bash
```

To access mysql shell

```bash
docker exec -it mysql mysql -uroot -p
```


### Running

Go and run `mast_db.py` to parse metadata from the database. It will be output as a file called `shot_metadata.parquet`.
