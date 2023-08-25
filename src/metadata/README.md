Tools to parse metadata for ingestion into the database

- `create_signal_metadata.py` - script to create a parquet file summarising the signal metadata
- `parse_cpf.py` - script to parse CPF data from PyUDA
- `mast_db.ipynb` - script to parse shot data from the Drupal database - see more below


### Drupal Database Script
Scripts & Tools to parse meta data from the entire MAST shot database. This creates a MySQL server and loads a copy of a backup from the Drupal database behind 
the MAST website into it.

### Setup

To start the MySQL instance:

```bash
docker compose up
```

To access the container
```bash
sudo docker exec -it mysql bash
```

To access mysql shell

```bash
sudo docker exec -it mysql mysql -uroot -p
```

To setup the database:

```bash
sudo docker exec -it mysql mysql -uroot -p create database mast_drupal;
sudo docker exec -it mysql mysql -uroot -p mast_drupal < /data/database.sql;
```

### Running

Go and run `mast_db.ipynb` to parse metadata from the database.
