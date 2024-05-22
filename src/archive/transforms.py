from typing import Any
import json
import xarray as xr
from pathlib import Path


class MapDict:

    def __init__(self, transform) -> None:
        self.transform = transform

    def __call__(self, datasets: dict[str, xr.Dataset]) -> dict[str, xr.Dataset]:
        datasets = {key: self.transform(dataset) for key, dataset in datasets.items()}
        return datasets


class RenameDimensions:

    def __init__(self) -> None:
        with Path("mappings/dim_names.json").open("r") as handle:
            self.dimension_mapping = json.load(handle)

    def __call__(self, ds: xr.Dataset) -> xr.Dataset:
        name = ds.attrs["name"]
        ds = ds.squeeze()
        if name in self.dimension_mapping:
            ds = ds.rename_dims(self.dimension_mapping[name])
            if name in ds.data_vars or name in ds.coords:
                ds = ds.rename_vars(self.dimension_mapping[name])
        ds.attrs["dims"] = list(ds.sizes.keys())
        return ds


class DropZeroDimensions:

    def __call__(self, dataset: xr.Dataset) -> Any:
        for key, coord in dataset.coords.items():
            if (coord.values == 0).all():
                dataset = dataset.drop_vars(key)
        return dataset


class DropDatasets:

    def __init__(self, keys: list[str]) -> None:
        self.keys = keys

    def __call__(self, datasets: dict[str, xr.Dataset]) -> dict[str, xr.Dataset]:
        for key in self.keys:
            datasets.pop(key)
        return datasets


class StandardizeSignalDataset:

    def __init__(self, source: str) -> None:
        self.source = source

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        name = dataset.attrs["name"]
        # Drop error if all zeros
        if (dataset["error"].values == 0).all():
            dataset = dataset.drop_vars("error")

        # Rename variables
        new_names = {}
        if "error" in dataset:
            new_names["data"] = name
            new_names["error"] = "_".join([name, "error"])
        else:
            name = name + "_" if name == "time" else name
            new_names["data"] = name

        dataset = dataset.rename(new_names)

        # Update attributes
        attrs = dataset.attrs
        attrs["name"] = self.source + "/" + new_names["data"]
        dataset[new_names["data"]].attrs = attrs
        return dataset


class MergeDatasets:

    def __call__(self, dataset_dict: dict[str, xr.Dataset]) -> xr.Dataset:
        dataset = xr.merge(dataset_dict.values())
        dataset.attrs = {}
        return dataset


class TensorizeChannels:
    def __init__(self, stem: str) -> None:
        self.stem = stem

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        dim_name = f"{self.stem}_channel"
        group_keys = [key for key in dataset.data_vars.keys() if self.stem in key]
        channels = [dataset[key] for key in group_keys]
        dataset[self.stem] = xr.combine_nested(channels, concat_dim=dim_name)
        dataset[self.stem] = dataset[self.stem].assign_coords({dim_name: group_keys})
        dataset[self.stem] = dataset[self.stem].chunk("auto")
        dataset = dataset.drop_vars(group_keys)
        return dataset


class ASXTransform:
    def __init__(self) -> None:
        with Path("mappings/dim_names.json").open("r") as handle:
            self.dimension_mapping = json.load(handle)

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        dataset = dataset.squeeze()
        name = dataset.attrs["name"]

        if not name in self.dimension_mapping:
            return dataset

        dataset = dataset.rename_dims(self.dimension_mapping[name])
        dataset = dataset.drop("data")
        dataset["data"] = dataset["time"]
        dataset = dataset.drop("time")
        return dataset


class Pipeline:

    def __init__(self, transforms: list):
        self.transforms = transforms

    def __call__(self, x: Any) -> Any:
        for transform in self.transforms:
            x = transform(x)
        return x


class PipelineRegistry:

    def __init__(self) -> None:
        self.pipelines = {
            "abm": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(DropZeroDimensions()),
                    MapDict(StandardizeSignalDataset("abm")),
                    MergeDatasets(),
                ]
            ),
            "ada": Pipeline(
                [MapDict(StandardizeSignalDataset("ada")), MergeDatasets()]
            ),
            "aga": Pipeline(
                [MapDict(StandardizeSignalDataset("aga")), MergeDatasets()]
            ),
            "adg": Pipeline(
                [MapDict(StandardizeSignalDataset("adg")), MergeDatasets()]
            ),
            "ahx": Pipeline(
                [MapDict(StandardizeSignalDataset("ahx")), MergeDatasets()]
            ),
            "aim": Pipeline(
                [MapDict(StandardizeSignalDataset("aim")), MergeDatasets()]
            ),
            "air": Pipeline(
                [MapDict(StandardizeSignalDataset("air")), MergeDatasets()]
            ),
            "ait": Pipeline(
                [MapDict(StandardizeSignalDataset("ait")), MergeDatasets()]
            ),
            "alp": Pipeline(
                [
                    MapDict(DropZeroDimensions()),
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("alp")),
                    MergeDatasets(),
                ]
            ),
            "ama": Pipeline(
                [MapDict(StandardizeSignalDataset("ama")), MergeDatasets()]
            ),
            "amb": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("abm")),
                    MergeDatasets(),
                    TensorizeChannels("ccbv"),
                    TensorizeChannels("ob"),
                    TensorizeChannels("fl_cc"),
                    TensorizeChannels("fl_p"),
                ]
            ),
            "amc": Pipeline(
                [MapDict(StandardizeSignalDataset("amc")), MergeDatasets()]
            ),
            "amh": Pipeline(
                [MapDict(StandardizeSignalDataset("amh")), MergeDatasets()]
            ),
            "amm": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("amm")),
                    MergeDatasets(),
                    TensorizeChannels("incon"),
                    TensorizeChannels("mid"),
                    TensorizeChannels("ring"),
                    TensorizeChannels("rodgr"),
                    TensorizeChannels("vertw"),
                    TensorizeChannels("lhorw"),
                    TensorizeChannels("uhorw"),
                ]
            ),
            "ams": Pipeline(
                [MapDict(StandardizeSignalDataset("ams")), MergeDatasets()]
            ),
            "anb": Pipeline(
                [MapDict(StandardizeSignalDataset("amb")), MergeDatasets()]
            ),
            "ane": Pipeline(
                [MapDict(StandardizeSignalDataset("ane")), MergeDatasets()]
            ),
            "ant": Pipeline(
                [MapDict(StandardizeSignalDataset("ant")), MergeDatasets()]
            ),
            "anu": Pipeline(
                [MapDict(StandardizeSignalDataset("anu")), MergeDatasets()]
            ),
            "aoe": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("aoe")),
                    MergeDatasets(),
                ]
            ),
            "arp": Pipeline(
                [MapDict(StandardizeSignalDataset("arp")), MergeDatasets()]
            ),
            "asb": Pipeline(
                [MapDict(StandardizeSignalDataset("asb")), MergeDatasets()]
            ),
            "asm": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("asm")),
                    MergeDatasets(),
                    TensorizeChannels("sad_m"),
                ]
            ),
            "asx": Pipeline(
                [
                    MapDict(ASXTransform()),
                    MapDict(StandardizeSignalDataset("asx")),
                    MergeDatasets(),
                ]
            ),
            "ayc": Pipeline(
                [MapDict(StandardizeSignalDataset("ayc")), MergeDatasets()]
            ),
            "aye": Pipeline(
                [MapDict(StandardizeSignalDataset("aye")), MergeDatasets()]
            ),
            "efm": Pipeline(
                [
                    DropDatasets(
                        [
                            "fcoil_n",
                            "fcoil_segs_n",
                            "limitern",
                            "magpr_n",
                            "silop_n",
                            "shot_number",
                        ]
                    ),
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("efm")),
                    MergeDatasets(),
                ]
            ),
            "esm": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("esm")),
                    MergeDatasets(),
                ]
            ),
        }

    def get(self, name: str) -> Pipeline:
        if name not in self.pipelines:
            raise RuntimeError(f"{name} is not a registered source!")
        return self.pipelines[name]
