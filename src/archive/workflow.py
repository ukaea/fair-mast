import s3fs
import logging
from pathlib import Path
from dask.distributed import Client, as_completed
from src.archive.task import CreateDatasetTask, UploadDatasetTask, CleanupDatasetTask
from src.archive.uploader import UploadConfig

logging.basicConfig(level=logging.INFO)


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
