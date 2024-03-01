#!/bin/bash

sbatch dev/jobs/create_signal_dataset_metadata.job 
CAMPAIGN="M9" sbatch dev/jobs/create_signal_metadata.job
CAMPAIGN="M8" sbatch dev/jobs/create_signal_metadata.job
CAMPAIGN="M7" sbatch dev/jobs/create_signal_metadata.job