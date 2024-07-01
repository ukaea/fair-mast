# Ingestion

## Step 1

```sh
mpirun -n 16 python3 -m src.archive.create_uda_metadata data/uda campaign_shots/M9.csv 
```

## Step 2

```sh
mpirun -np 16 \
    python3 -m src.archive.main \
        /common/tmp/sjackson/local_cache campaign_shots/M8.csv s3://mast/level1/shots/ \
        --force --source_names amc ayc efm xsx
```