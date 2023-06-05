## MAST Drupal Database

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

To setup the datbase:

```bash
sudo docker exec -it mysql mysql -uroot -p create database mast_drupal;
sudo docker exec -it mysql mysql -uroot -p mast_drupal < /data/database.sql;
```

### Running

Go and run `mast_db.ipynb` to parse metadata from the database.
