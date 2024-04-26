import xarray as xr
from dataclasses import dataclass, asdict

from src.archive.mast import MASTClient, SignalInfo


class DatasetReader:

    def __init__(self, shot: int):
        self.shot = shot
        self.client = MASTClient()

    def list_datasets(self, exclude_raw: bool = False) -> list[SignalInfo]:
        signal_infos = self.client.get_signal_infos(self.shot)
        image_infos = self.client.get_image_infos(self.shot)
        infos = signal_infos + image_infos
        if exclude_raw:
            infos = filter(lambda info: info.type != "Raw", infos)
            infos = list(infos)
        return infos

    def read_dataset(self, info: SignalInfo) -> xr.Dataset:
        if info.type != "Image":
            dataset = self.client.get_signal(self.shot, info.name)
        else:
            dataset = self.client.get_image(self.shot, info.name)

        dataset.attrs.update(asdict(info))
        return dataset
