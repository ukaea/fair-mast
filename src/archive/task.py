from src.archive.reader import DatasetReader
from src.archive.writer import DatasetWriter
from src.archive.uploader import UploadConfig
from pathlib import Path
import shutil
import subprocess
import logging


class CleanupDatasetTask:

    def __init__(self, path: str) -> None:
        self.path = path

    def __call__(self):
        if Path(self.path).exists():
            shutil.rmtree(self.path)


class UploadDatasetTask:

    def __init__(self, local_file: Path, config: UploadConfig):
        self.config = config
        self.local_file = local_file

    def __call__(self):
        subprocess.run(
            [
                "/home/rt2549/dev/s5cmd",
                "--credentials-file",
                self.config.credentials_file,
                "--endpoint-url",
                self.config.endpoint_url,
                "cp",
                "--acl",
                "public-read",
                self.local_file,
                self.config.url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )


class CreateDatasetTask:

    def __init__(
        self,
        dataset_dir: str,
        shot: int,
        exclude_raw: bool = True,
    ):
        self.reader = DatasetReader(shot)
        self.writer = DatasetWriter(shot, dataset_dir)
        self.exclude_raw = exclude_raw

    def __call__(self):
        signal_infos = self.reader.list_datasets(self.exclude_raw)

        self.writer.write_metadata()

        for info in signal_infos:
            name = info.name
            logging.info(f"Writing {self.reader.shot}/{name}")
            try:
                dataset = self.reader.read_dataset(info)
            except Exception as e:
                logging.error(f"Error reading dataset {name}: {e}")
                continue

            self.writer.write_dataset(dataset)

        self.writer.consolidate_dataset()
