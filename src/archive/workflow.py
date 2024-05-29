import s3fs
import logging
from pathlib import Path
from dask.distributed import Client, as_completed
from src.archive.task import (
    CreateDatasetTask,
    UploadDatasetTask,
    CleanupDatasetTask,
    CreateSignalMetadataTask,
    CreateSourceMetadataTask,
)
from src.archive.uploader import UploadConfig

logging.basicConfig(level=logging.INFO)


class MetadataWorkflow:

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def __call__(self, shot: int):
        try:
            signal_metadata = CreateSignalMetadataTask(self.data_dir / "signals", shot)
            signal_metadata()
        except Exception as e:
            logging.error(f"Could not parse signal metadata for shot {shot}: {e}")

        try:
            source_metadata = CreateSourceMetadataTask(self.data_dir / "sources", shot)
            source_metadata()
        except Exception as e:
            logging.error(f"Could not parse source metadata for shot {shot}: {e}")


class IngestionWorkflow:

    def __init__(
        self,
        metadata_dir: str,
        data_dir: str,
        upload_config: UploadConfig,
        force: bool = True,
        signal_names: list[str] = [],
        source_names: list[str] = [],
    ):
        self.metadata_dir = metadata_dir
        self.data_dir = Path(data_dir)
        self.upload_config = upload_config
        self.force = force
        self.signal_names = signal_names
        self.source_names = source_names
        self.s3 = s3fs.S3FileSystem(
            anon=True, client_kwargs={"endpoint_url": self.upload_config.endpoint_url}
        )

    def __call__(self, shot: int):
        local_path = self.data_dir / f"{shot}.zarr"
        create = CreateDatasetTask(
            self.metadata_dir,
            self.data_dir,
            shot,
            self.signal_names,
            self.source_names,
        )
        upload = UploadDatasetTask(local_path, self.upload_config)
        cleanup = CleanupDatasetTask(local_path)

        try:
            create()
            url = self.upload_config.url + f"{shot}.zarr"
            # if self.force or not self.s3.exists(url):
            #     create()
            #     upload()
            # else:
            #     logging.info(f"Skipping shot {shot} as it already exists")
        except Exception as e:
            logging.error(f"Failed to run workflow with error {type(e)}: {e}")
        finally:
            pass
            # cleanup()


class WorkflowManager:

    def __init__(self, workflow):
        self.workflow = workflow

    def run_workflows(self, shot_list: list[int]):
        dask_client = Client()
        tasks = []
        for shot in shot_list:
            task = dask_client.submit(self.workflow, shot)
            tasks.append(task)

        n = len(tasks)
        for i, task in enumerate(as_completed(tasks)):
            logging.info(f"Done shot {i+1}/{n} = {(i+1)/n*100:.2f}%")
