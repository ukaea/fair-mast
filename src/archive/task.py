from src.archive.transforms import PipelineRegistry
from src.archive.mast import MASTClient
from src.archive.reader import DatasetReader, SignalMetadataReader, SourceMetadataReader
from src.archive.writer import DatasetWriter
from src.archive.uploader import UploadConfig
from pathlib import Path
import xarray as xr
import pandas as pd
import json
import shutil
import subprocess
import logging

logging.basicConfig(level=logging.INFO)


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
        logging.info(f"Uploading {self.local_file}")
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
        metadata_dir: str,
        dataset_dir: str,
        shot: int,
        signal_names: list[str] = [],
        source_names: list[str] = [],
    ):
        self.shot = shot
        self.metadata_dir = Path(metadata_dir)
        self.reader = DatasetReader(shot)
        self.writer = DatasetWriter(shot, dataset_dir)
        self.signal_names = signal_names
        self.source_names = source_names
        self.pipelines = PipelineRegistry()

    def __call__(self):
        signal_infos = self.read_signal_info()
        source_infos = self.read_source_info()

        if len(self.signal_names) > 0:
            signal_infos = signal_infos.loc[signal_infos.name.isin(self.signal_names)]

        if len(self.source_names) > 0:
            signal_infos = signal_infos.loc[signal_infos.source.isin(self.source_names)]

        self.writer.write_metadata()

        for key, group_index in signal_infos.groupby("source").groups.items():
            signal_infos_for_source = signal_infos.loc[group_index]
            signal_datasets = self.load_source(signal_infos_for_source)
            pipeline = self.pipelines.get(key)
            dataset = pipeline(signal_datasets)
            source_info = source_infos.loc[source_infos["name"] == key].iloc[0]
            source_info = source_info.to_dict()
            dataset.attrs.update(source_info)
            self.writer.write_dataset(dataset)

        self.writer.consolidate_dataset()

    def load_source(self, group: pd.DataFrame) -> dict[str, xr.Dataset]:
        datasets = {}
        for _, info in group.iterrows():
            info = info.to_dict()
            name = info["name"]
            format = info["format"]
            format = format if format is not None else ""

            try:
                client = MASTClient()
                if info["signal_type"] != "Image":
                    dataset = client.get_signal(
                        shot_num=self.shot, name=info["uda_name"], format=format
                    )
                else:
                    dataset = client.get_image(
                        shot_num=self.shot, name=info["uda_name"]
                    )
            except Exception as e:
                logging.error(f"Error reading dataset {name} for shot {self.shot}: {e}")
                continue

            dataset.attrs.update(info)
            dataset.attrs["dims"] = list(dataset.sizes.keys())
            datasets[name] = dataset
        return datasets

    def read_signal_info(self) -> pd.DataFrame:
        return pd.read_parquet(self.metadata_dir / f"signals/{self.shot}.parquet")

    def read_source_info(self) -> pd.DataFrame:
        return pd.read_parquet(self.metadata_dir / f"sources/{self.shot}.parquet")


class CreateSignalMetadataTask:
    def __init__(self, data_dir: str, shot: int):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.shot = shot
        self.reader = SignalMetadataReader(shot)

    def __call__(self):
        df = self.reader.read_metadata()
        if len(df) > 0:
            df.to_parquet(self.data_dir / f"{self.shot}.parquet")


class CreateSourceMetadataTask:
    def __init__(self, data_dir: str, shot: int):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.shot = shot
        self.reader = SourceMetadataReader(shot)

    def __call__(self):
        df = self.reader.read_metadata()
        if len(df) > 0:
            df.to_parquet(self.data_dir / f"{self.shot}.parquet")
