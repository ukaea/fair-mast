import argparse
import logging
from dask_mpi import initialize
from src.archive.uploader import UploadConfig
from src.archive.workflow import IngestionWorkflow, WorkflowManager
from src.archive.utils import read_shot_file


def main():
    initialize()
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        prog="UDA Archive Parser",
        description="Parse the MAST archive and writer to Zarr files. Upload to S3",
    )

    parser.add_argument("dataset_path")
    parser.add_argument("shot_file")
    parser.add_argument("bucket_path")
    parser.add_argument("--metadata_dir", default="data/uda")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--signal_names", nargs="*", default=[])
    parser.add_argument("--source_names", nargs="*", default=[])

    args = parser.parse_args()

    config = UploadConfig(
        credentials_file=".s5cfg.stfc",
        endpoint_url="https://s3.echo.stfc.ac.uk",
        url=args.bucket_path,
    )

    shot_list = read_shot_file(args.shot_file)

    for source in args.source_names:
        logging.info("------------------------")
        logging.info(f"Starting source {source}")

        workflow = IngestionWorkflow(
            args.metadata_dir,
            args.dataset_path,
            config,
            args.force,
            args.signal_names,
            [source],
        )

        workflow_manager = WorkflowManager(workflow)
        workflow_manager.run_workflows(shot_list)
        logging.info(f"Finished source {source}")


if __name__ == "__main__":
    main()
