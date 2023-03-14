# README

## Setup

Start the postgres and pg_admin by using docker compose

```bash
sudo docker compose up
```

To access the postgres shell we need to ssh into the running container:

```bash
sudo docker exec -it pg_container /bin/bash
```

Change directory to the mounted folder

```bash
cd /app
```

Create the database:

```bash
psql -U root postgres -f create_db.sql
psql -U root -d mast_db1 -f create_tables.sql
psql -U root -d mast_db1 -f create_cpf.sql
```