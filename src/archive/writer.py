import uuid
import shutil
import zarr
import xarray as xr
from pathlib import Path


def get_dataset_uuid(shot: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_OID, str(shot)))


class DatasetWriter:

    def __init__(self, shot: int, dir_name: str):
        self.shot = shot
        self.dir_name = Path(dir_name)
        self.dir_name.mkdir(exist_ok=True, parents=True)
        self.dataset_path = self.dir_name / f"{shot}.zarr"

    def write_metadata(self):
        with zarr.open(self.dataset_path) as f:
            f.attrs["dataset_uuid"] = get_dataset_uuid(self.shot)
            f.attrs["shot_id"] = self.shot

    def write_dataset(self, dataset: xr.Dataset):
        name = self.get_group_name(dataset.attrs["name"])
        dataset.to_zarr(self.dataset_path, group=name, consolidated=False, mode="w")

    def consolidate_dataset(self):
        zarr.consolidate_metadata(self.dataset_path)
        with zarr.open(self.dataset_path) as f:
            for source in f.keys():
                zarr.consolidate_metadata(self.dataset_path / source)

    def get_group_name(self, name: str) -> str:
        name = name.replace("/", "_")
        name = name.replace(" ", "_")
        name = name.replace("(", "")
        name = name.replace(")", "")
        name = name.replace(",", "")

        parts = name.split("_")
        if len(parts) > 1:
            name = parts[0] + "/" + "_".join(parts[1:])

        if name.startswith("_"):
            name = name[1:]

        name = name.lower()
        return name
