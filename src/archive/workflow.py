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

    def __init__(self, tasks) -> None:
        self.tasks = tasks

    def __call__(self):
        try:
            for task in self.tasks:
                task()
        except Exception as e:
            logging.error(f"Failed to do task {task} with exception {e}")
        finally:
            # Always run the cleanup task
            self.tasks[-1]()


class SimpleWorkflowManager:

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


class WorkflowManager:

    def __init__(
        self,
        shot_list: list[int],
        dataset_path,
        upload_config: UploadConfig,
        force: bool = True,
        exclude_raw: bool = True,
    ):
        self.dataset_path = dataset_path
        self.shot_list = shot_list
        self.upload_config = upload_config
        self.force = force
        self.exclude_raw = exclude_raw

    def create_shot_workflow(self, shot: int):
        local_path = Path(self.dataset_path) / f"{shot}.zarr"

        tasks = [
            CreateDatasetTask(self.dataset_path, shot, self.exclude_raw),
            UploadDatasetTask(local_path, self.upload_config),
            CleanupDatasetTask(local_path),
        ]

        workflow = IngestionWorkflow(tasks)
        return workflow

    def run_workflows(self):
        s3 = s3fs.S3FileSystem(
            anon=True, client_kwargs={"endpoint_url": self.upload_config.endpoint_url}
        )
        dask_client = Client()
        tasks = []
        for shot in self.shot_list:
            url = self.upload_config.url + f"{shot}.zarr"
            if not s3.exists(url) or self.force:
                workflow = self.create_shot_workflow(shot)
                task = dask_client.submit(workflow)
                tasks.append(task)
            else:
                logging.info(f"Skipping shot {shot} as it already exists")

        n = len(tasks)
        for i, task in enumerate(as_completed(tasks)):
            logging.info(f"Transfer shot {i+1}/{n} = {(i+1)/n*100:.2f}%")

        dask_client.shutdown()
