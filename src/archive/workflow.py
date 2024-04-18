import logging
from pathlib import Path
from dask.distributed import Client, as_completed
from src.archive.task import CreateDatasetTask, UploadDatasetTask, CleanupDatasetTask
from src.archive.uploader import UploadConfig


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

    def __init__(self, shot_list: list[int], dataset_path, upload_config: UploadConfig):
        self.dataset_path = dataset_path
        self.shot_list = shot_list
        self.upload_config = upload_config

    def create_shot_workflow(self, shot: int):
        local_path = Path(self.dataset_path) / f"{shot}.zarr"

        tasks = [
            CreateDatasetTask(self.dataset_path, shot),
            UploadDatasetTask(local_path, self.upload_config),
            CleanupDatasetTask(local_path),
        ]

        workflow = IngestionWorkflow(tasks)
        return workflow

    def run_workflows(self):
        dask_client = Client()
        tasks = []
        for shot in self.shot_list:
            workflow = self.create_shot_workflow(shot)
            task = dask_client.submit(workflow)
            tasks.append(task)

        n = len(tasks)
        for i, task in enumerate(as_completed(tasks)):
            logging.info(f"Transfer shot {i+1}/{n} = {(i+1)/n*100:.2f}%")
