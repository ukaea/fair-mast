import pandas as pd
import xarray as xr
from dataclasses import asdict

from src.archive.mast import MASTClient, SignalInfo


class SignalMetadataReader:
    def __init__(self, shot: int):
        self.shot = shot
        self.client = MASTClient()

    def list_datasets(self, exclude_raw: bool = False) -> list[SignalInfo]:
        signal_infos = self.client.get_signal_infos(self.shot)
        image_infos = self.client.get_image_infos(self.shot)
        infos = signal_infos + image_infos
        if exclude_raw:
            infos = filter(lambda info: info.signal_type != "Raw", infos)
            infos = list(infos)
        return infos

    def read_metadata(self) -> pd.DataFrame:
        infos = self.list_datasets()
        infos = [asdict(info) for info in infos]
        return pd.DataFrame(infos)


class SourceMetadataReader:
    def __init__(self, shot: int):
        self.shot = shot
        self.client = MASTClient()

    def read_metadata(self) -> pd.DataFrame:
        infos = self.client.get_source_infos(self.shot)
        infos = [asdict(info) for info in infos]
        return pd.DataFrame(infos)


class DatasetReader:

    def __init__(self, shot: int):
        self.shot = shot
        self.client = MASTClient()

    def list_datasets(self, exclude_raw: bool = False) -> list[SignalInfo]:
        signal_infos = self.client.get_signal_infos(self.shot)
        image_infos = self.client.get_image_infos(self.shot)
        infos = signal_infos + image_infos
        if exclude_raw:
            infos = filter(lambda info: info.signal_type != "Raw", infos)
            infos = list(infos)
        return infos

    def read_dataset(self, info: dict) -> xr.Dataset:
        if info["signal_type"] != "Image":
            dataset = self.client.get_signal(
                self.shot, info["uda_name"], info["format"]
            )
        else:
            dataset = self.client.get_image(self.shot, info["uda_name"])

        dataset.attrs.update(info)
        return dataset
