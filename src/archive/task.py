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
import pytokamap

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
        exclude_raw: bool = True,
    ):
        self.shot = shot
        self.metadata_dir = Path(metadata_dir)
        self.reader = DatasetReader(shot)
        self.writer = DatasetWriter(shot, dataset_dir)
        self.exclude_raw = exclude_raw
        self.dims_map = self.read_dimension_mappings()
        self.signal_mapper = pytokamap.load_mapping(
            "mappings/signals.json", "mappings/globals.json"
        )

    def __call__(self):
        signal_infos = self.read_signal_info()
        source_infos = self.read_source_info()
        if self.exclude_raw:
            signal_infos = signal_infos.loc[signal_infos.signal_type != "Raw"]

        self.writer.write_metadata()
        datasets = self.signal_mapper.load(self.shot)

        for index, info in signal_infos.iterrows():
            info = info.to_dict()
            source = source_infos.loc[source_infos["source"] == info["source"]].iloc[0]
            info["format"] = source["format"]
            name = info["name"]
            logging.info(f"Writing {self.reader.shot}/{name}")
            try:
                dataset = datasets[name].compute()
                dataset.attrs["name"] = name
                # dataset = self.reader.read_dataset(info)
            except Exception as e:
                logging.error(f"Error reading dataset {name} for shot {self.shot}: {e}")
                continue

            dataset = self.remap_dimensions(dataset)
            self.writer.write_dataset(dataset)

        self.writer.consolidate_dataset()

    def remap_dimensions(self, dataset: xr.Dataset) -> xr.Dataset:
        new_names = {}
        for name in dataset.sizes.keys():
            if name in self.dims_map:
                new_names[name] = self.dims_map.get(name)
        dataset = dataset.rename_dims(new_names)
        return dataset

    def read_dimension_mappings(self):
        with Path("mappings/dimensions.json").open("r") as f:
            return json.load(f)

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
