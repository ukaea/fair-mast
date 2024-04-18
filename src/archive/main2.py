import argparse
import logging
from dask_mpi import initialize
from src.archive.uploader import UploadConfig
from src.archive.workflow import WorkflowManager


def read_shot_file(shot_file: str) -> list[int]:
    with open(shot_file) as f:
        shot_nums = f.readlines()[1:]
        shot_nums = map(lambda x: x.strip(), shot_nums)
        shot_nums = list(sorted(map(int, shot_nums)))
    return shot_nums


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

    args = parser.parse_args()

    config = UploadConfig(
        credentials_file=".s5cfg.stfc",
        endpoint_url="https://s3.echo.stfc.ac.uk",
        url=args.bucket_path,
    )

    shot_list = read_shot_file(args.shot_file)

    workflow_manager = WorkflowManager(shot_list, args.dataset_path, config)
    workflow_manager.run_workflows()


if __name__ == "__main__":
    main()
