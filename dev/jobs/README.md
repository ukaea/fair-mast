# Jobscripts for CSD3

This folder contains a number of different job scripts to assist with processing archived data

 - `consolidate.job` - this job script will consolidate Zarr files after writing using the script `src/metadata/consolidate_zarr.py`. 
 - `start_cluster.job` - this job script will start an independant dask server on CSD3 that can have job submitted to it.