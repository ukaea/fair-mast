# Jobscripts for CSD3

This folder contains a number of different job scripts to assist with processing archived data

 - `consolidate.job` - this job script will consolidate Zarr files after writing using the script `src/metadata/consolidate_zarr.py`. 
 - `start_cluster.job` - this job script will start an independant dask server on CSD3 that can have job submitted to it.
 - `create_signal_dataset_metadata.job` -  this script with scan all files and pull out metadata for each dataset as a parquet file
 - `create_signal_metadata.job` - this script will scan all files and for every group in each dataset it will pull out the metadata for the file as a parquet object