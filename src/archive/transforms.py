from typing import Any, Optional
import pint
import re
import json
import uuid
import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path

DIMENSION_MAPPING_FILE = "mappings/dimensions.json"
UNITS_MAPPING_FILE = "mappings/units.json"
CUSTOM_UNITS_FILE = "mappings/custom_units.txt"


def get_dataset_item_uuid(name: str, shot: int) -> str:
    oid_name = name + "/" + str(shot)
    return str(uuid.uuid5(uuid.NAMESPACE_OID, oid_name))


class MapDict:

    def __init__(self, transform) -> None:
        self.transform = transform

    def __call__(self, datasets: dict[str, xr.Dataset]) -> dict[str, xr.Dataset]:

        out = {}
        for key, dataset in datasets.items():
            try:
                out[key] = self.transform(dataset)
            except Exception as e:
                raise RuntimeError(f"{key}: {e}")
        return out


class RenameDimensions:

    def __init__(self) -> None:
        with Path(DIMENSION_MAPPING_FILE).open("r") as handle:
            self.dimension_mapping = json.load(handle)

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        name = dataset.attrs["name"]
        dataset = dataset.squeeze()
        if name in self.dimension_mapping:
            dims = self.dimension_mapping[name]
            dataset = dataset.rename_dims(self.dimension_mapping[name])
            for old_name, new_name in dims.items():
                if old_name in dataset.coords:
                    dataset = dataset.rename_vars({old_name: new_name})
            dataset.attrs["dims"] = list(dataset.sizes.keys())
        dataset = dataset.compute()
        return dataset


class DropZeroDimensions:

    def __call__(self, dataset: xr.Dataset) -> Any:
        for key, coord in dataset.coords.items():
            if (coord.values == 0).all():
                dataset = dataset.drop_vars(key)
        dataset = dataset.compute()
        return dataset


class DropDatasets:

    def __init__(self, keys: list[str]) -> None:
        self.keys = keys

    def __call__(self, datasets: dict[str, xr.Dataset]) -> dict[str, xr.Dataset]:
        for key in self.keys:
            datasets.pop(key)
        return datasets


class StandardiseSignalDataset:

    def __init__(self, source: str) -> None:
        self.source = source

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        dataset = dataset.squeeze(drop=True)
        name = dataset.attrs["name"].split("/")[-1]

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
        dataset = self._drop_unused_coords(dataset)

        if "time" in dataset.dims:
            dataset = dataset.drop_duplicates(dim="time")

        # Update attributes
        attrs = dataset.attrs
        attrs["name"] = self.source + "/" + new_names["data"]
        attrs["dims"] = list(dataset.sizes.keys())
        dataset[new_names["data"]].attrs = attrs
        dataset = dataset.compute()
        return dataset

    def _drop_unused_coords(self, data: xr.Dataset) -> xr.Dataset:
        used_coords = set()
        for var in data.data_vars.values():
            used_coords.update(var.dims)

        # Drop coordinates that are not used
        unused_coords = set(data.coords) - used_coords
        data = data.drop_vars(unused_coords)
        return data


class RenameVariables:
    def __init__(self, mapping: dict[str, str]):
        self.mapping = mapping

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        for key, value in self.mapping.items():
            if key in dataset:
                dataset = dataset.rename_vars({key: value})
        dataset = dataset.compute()
        return dataset


class MergeDatasets:

    def __call__(self, dataset_dict: dict[str, xr.Dataset]) -> xr.Dataset:
        dataset = xr.merge(dataset_dict.values())
        dataset = dataset.compute()
        dataset.attrs = {}
        return dataset


class TensoriseChannels:
    def __init__(
        self,
        stem: str,
        regex: Optional[str] = None,
        dim_name: Optional[str] = None,
        assign_coords: bool = True,
    ) -> None:
        self.stem = stem
        self.regex = regex if regex is not None else stem + "(\d+)"
        name = self.stem.split("/")[-1]
        self.dim_name = f"{name}_channel" if dim_name is None else dim_name
        self.assign_coords = assign_coords

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:

        group_keys = self._get_group_keys(dataset)
        channels = [dataset[key] for key in group_keys]
        dataset[self.stem] = xr.combine_nested(channels, concat_dim=self.dim_name)

        if self.assign_coords:
            dataset[self.stem] = dataset[self.stem].assign_coords(
                {self.dim_name: group_keys}
            )

        dataset[self.stem] = dataset[self.stem].chunk("auto")
        dataset[self.stem] = self._update_attributes(dataset[self.stem], channels)
        dataset = dataset.drop_vars(group_keys)
        dataset = dataset.compute()
        return dataset

    def _update_attributes(
        self, dataset: xr.Dataset, channels: list[xr.Dataset]
    ) -> xr.Dataset:
        attrs = channels[0].attrs
        channel_descriptions = [c.attrs.get("description", "") for c in channels]
        description = "\n".join(channel_descriptions)
        attrs["name"] = self.stem
        attrs["description"] = description
        attrs["channel_descriptions"] = channel_descriptions
        attrs["uuid"] = get_dataset_item_uuid(attrs["name"], attrs["shot_id"])
        attrs["shape"] = list(dataset.sizes.values())
        attrs["rank"] = len(attrs["shape"])
        attrs["dims"] = list(dataset.sizes.keys())
        attrs.pop("uda_name", "")
        attrs.pop("mds_name", "")
        dataset.attrs = attrs
        return dataset

    def _get_group_keys(self, dataset: xr.Dataset) -> list[str]:
        group_keys = dataset.data_vars.keys()
        group_keys = [
            key for key in group_keys if re.search(self.regex, key) is not None
        ]
        group_keys = self._sort_numerically(group_keys)
        return group_keys

    def _parse_digits(self, s):
        # Split the string into a list of numeric and non-numeric parts
        parts = re.split(self.regex, s)
        # Convert numeric parts to integers
        return [int(part) if part.isdigit() else part for part in parts]

    def _sort_numerically(self, strings: list[str]) -> list[str]:
        return sorted(strings, key=self._parse_digits)


class TransformUnits:
    def __init__(self):
        with Path(UNITS_MAPPING_FILE).open("r") as handle:
            self.units_map = json.load(handle)

        self.ureg = pint.UnitRegistry()
        self.ureg.load_definitions(CUSTOM_UNITS_FILE)

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        for array in dataset.data_vars.values():
            self._update_units(array)

        for array in dataset.coords.values():
            self._update_units(array)

        dataset = dataset.compute()
        return dataset

    def _update_units(self, array: xr.DataArray):
        units = array.attrs.get("units", "")
        units = self.units_map.get(units, units)
        units = self._parse_units(units)
        array.attrs["units"] = units

    def _parse_units(self, unit: str) -> str:
        try:
            unit = self.ureg.parse_units(unit)
            unit = format(unit, "~")
            return unit
        except Exception:
            return unit


class ASXTransform:
    """ASX is very special.

    The time points are actually the data and the data is blank.
    This transformation renames them and used the correct dimension mappings.
    """

    def __init__(self) -> None:
        with Path(DIMENSION_MAPPING_FILE).open("r") as handle:
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
        dataset = dataset.compute()
        return dataset


class LCFSTransform:
    """LCFS transform for LCFS coordinates

    In MAST, the LCFS coordinates have a lot of padding.
    This transform groups the r and z parameters and crops the padding.
    """

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        if "lcfsr_c" not in dataset.data_vars:
            return dataset

        r = dataset["lcfsr_c"]
        fill_value = np.nanmax(r.values)
        max_index = np.max(np.argmax(r.values, axis=1))
        dataset = dataset.sel(lcfs_coords=dataset.lcfs_coords[:max_index])

        r = dataset["lcfsr_c"]
        z = dataset["lcfsz_c"]
        dataset["lcfsr_c"] = r.where(r.values != fill_value, np.nan)
        dataset["lcfsz_c"] = z.where(z.values != fill_value, np.nan)
        dataset = dataset.compute()
        return dataset


class AddXSXCameraParams:

    def __init__(self, stem: str, path: str):
        cam_data = pd.read_csv(path)
        cam_data.drop("name", inplace=True, axis=1)
        cam_data.drop("comment", inplace=True, axis=1)
        cam_data.columns = [stem + "_" + c for c in cam_data.columns]
        name = stem.split("/")[-1]
        cam_data.index.name = name + "_channel"
        self.stem = stem
        self.cam_data = cam_data.to_xarray()

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        dataset = xr.merge([dataset, self.cam_data], combine_attrs="drop_conflicts")
        dataset = dataset.compute()
        return dataset


class XDCRenameDimensions:
    """XDC is a special boi...

    XDC has dynamically named time dimensions. The same signal can be called 'time2' or 'time4'
    depending on what got written to disk.
    """

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        dataset = dataset.squeeze()
        for dim_name in dataset.sizes.keys():
            if "time" in dim_name and dim_name != "time":
                dataset = dataset.rename_dims({dim_name: "time"})
                dataset = dataset.rename_vars({dim_name: "time"})

        dataset = dataset.compute()
        return dataset


class ProcessImage:
    def __call__(self, dataset: dict[str, xr.Dataset]) -> xr.Dataset:
        dataset: xr.Dataset = list(dataset.values())[0]
        dataset.attrs["units"] = "pixels"
        dataset.attrs["shape"] = list(dataset.sizes.values())
        dataset.attrs["rank"] = len(dataset.sizes.values())
        dataset = dataset.compute()
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
                    MapDict(StandardiseSignalDataset("abm")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ada": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("ada")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "aga": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("aga")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "adg": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("adg")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ahx": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("ahx")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "aim": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("aim")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "air": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("air")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ait": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("ait")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "alp": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(DropZeroDimensions()),
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("alp")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ama": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("ama")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "amb": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("abm")),
                    MergeDatasets(),
                    TensoriseChannels("ccbv"),
                    TensoriseChannels("obr"),
                    TensoriseChannels("obv"),
                    TensoriseChannels("fl_cc"),
                    TensoriseChannels("fl_p"),
                    TransformUnits(),
                ]
            ),
            "amc": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("amc")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "amh": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("amh")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "amm": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("amm")),
                    MergeDatasets(),
                    TensoriseChannels("incon"),
                    TensoriseChannels("mid"),
                    TensoriseChannels("ring"),
                    TensoriseChannels("rodgr"),
                    TensoriseChannels("vertw"),
                    TensoriseChannels("lhorw"),
                    TensoriseChannels("uhorw"),
                    TransformUnits(),
                ]
            ),
            "ams": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("ams")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "anb": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("amb")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ane": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("ane")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ant": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("ant")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "anu": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("anu")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "aoe": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("aoe")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "arp": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("arp")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "asb": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("asb")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "asm": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("asm")),
                    MergeDatasets(),
                    TensoriseChannels("sad_m"),
                    TransformUnits(),
                ]
            ),
            "asx": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(ASXTransform()),
                    MapDict(StandardiseSignalDataset("asx")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ayc": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("ayc")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "aye": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("aye")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "efm": Pipeline(
                [
                    DropDatasets(
                        [
                            "efm/fcoil_n",
                            "efm/fcoil_segs_n",
                            "efm/limitern",
                            "efm/magpr_n",
                            "efm/silop_n",
                            "efm/shot_number",
                        ]
                    ),
                    MapDict(DropZeroDimensions()),
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("efm")),
                    MergeDatasets(),
                    LCFSTransform(),
                    TransformUnits(),
                    RenameVariables(
                        {
                            "plasma_currc": "plasma_current_c",
                            "plasma_currx": "plasma_current_x",
                            "plasma_currrz": "plasma_current_rz",
                            "lcfsr_c": "lcfs_r",
                            "lcfsz_c": "lcfs_z",
                        }
                    ),
                ]
            ),
            "esm": Pipeline(
                [
                    MapDict(DropZeroDimensions()),
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("esm")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "esx": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("esx")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "rba": Pipeline([ProcessImage()]),
            "rbb": Pipeline([ProcessImage()]),
            "rbc": Pipeline([ProcessImage()]),
            "rca": Pipeline([ProcessImage()]),
            "rco": Pipeline([ProcessImage()]),
            "rgb": Pipeline([ProcessImage()]),
            "rgc": Pipeline([ProcessImage()]),
            "rir": Pipeline([ProcessImage()]),
            "rit": Pipeline([ProcessImage()]),
            "xdc": Pipeline(
                [
                    MapDict(XDCRenameDimensions()),
                    MapDict(StandardiseSignalDataset("xdc")),
                    MergeDatasets(),
                    TensoriseChannels(
                        "ai_cpu1_ccbv",
                        dim_name="ai_ccbv_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu1_flcc",
                        dim_name="ai_flcc_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu1_incon",
                        dim_name="ai_incon_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu1_lhorw",
                        dim_name="ai_lhorw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu1_mid",
                        dim_name="ai_mid_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu1_obr",
                        dim_name="ai_obr_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu1_obv",
                        dim_name="ai_obv_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu1_ring",
                        dim_name="ai_ring_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu1_rodgr",
                        dim_name="ai_rodgr_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu1_uhorw",
                        dim_name="ai_uhorw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu1_vertw",
                        dim_name="ai_vertw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu2_ccbv",
                        dim_name="ai_ccbv_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu2_flcc",
                        dim_name="ai_flcc_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu2_incon",
                        dim_name="ai_incon_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu2_lhorw",
                        dim_name="ai_lhorw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu2_mid",
                        dim_name="ai_mid_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu2_obr",
                        dim_name="ai_obr_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu2_obv",
                        dim_name="ai_obv_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu2_ring",
                        dim_name="ai_ring_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu2_rodgr",
                        dim_name="ai_rodgr_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu2_uhorw",
                        dim_name="ai_uhorw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu2_vertw",
                        dim_name="ai_vertw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu3_ccbv",
                        dim_name="ai_ccbv_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu3_flcc",
                        dim_name="ai_flcc_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu3_incon",
                        dim_name="ai_incon_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu3_lhorw",
                        dim_name="ai_lhorw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu3_mid",
                        dim_name="ai_mid_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu3_obr",
                        dim_name="ai_obr_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu3_obv",
                        dim_name="ai_obv_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu3_ring",
                        dim_name="ai_ring_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu3_rodgr",
                        dim_name="ai_rodgr_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu3_uhorw",
                        dim_name="ai_uhorw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu3_vertw",
                        dim_name="ai_vertw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu4_ccbv",
                        dim_name="ai_ccbv_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu4_flcc",
                        dim_name="ai_flcc_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu4_incon",
                        dim_name="ai_incon_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu4_lhorw",
                        dim_name="ai_lhorw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu4_mid",
                        dim_name="ai_mid_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu4_obr",
                        dim_name="ai_obr_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu4_obv",
                        dim_name="ai_obv_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu4_ring",
                        dim_name="ai_ring_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu4_rodgr",
                        dim_name="ai_rodgr_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu4_uhorw",
                        dim_name="ai_uhorw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_cpu4_vertw",
                        dim_name="ai_vertw_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_raw_ccbv", dim_name="ai_ccbv", assign_coords=False
                    ),
                    TensoriseChannels(
                        "ai_raw_flcc",
                        dim_name="ai_flcc_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "ai_raw_obv", dim_name="ai_obv_channel", assign_coords=False
                    ),
                    TensoriseChannels(
                        "ai_raw_obr", dim_name="ai_obr_channel", assign_coords=False
                    ),
                    TensoriseChannels(
                        "equil_s_seg",
                        regex=r"equil_s_seg(\d+)$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "equil_s_seg_at",
                        regex=r"equil_s_seg(\d+)at$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "equil_s_seg_rt",
                        regex=r"equil_s_seg(\d+)rt$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "equil_s_seg_zt",
                        regex=r"equil_s_seg(\d+)zt$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "equil_s_segb",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "equil_t_seg",
                        regex=r"equil_t_seg(\d+)$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels(
                        "equil_t_seg_u",
                        regex=r"equil_t_seg(\d+)u$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensoriseChannels("isoflux_e_seg"),
                    TensoriseChannels(
                        "isoflux_t_rpsh_n",
                        regex=r"isoflux_t_rpsh(\d+)n",
                    ),
                    TensoriseChannels(
                        "isoflux_t_rpsh_p",
                        regex=r"isoflux_t_rpsh(\d+)p",
                    ),
                    TensoriseChannels("isoflux_t_seg", regex=r"isoflux_t_seg(\d+)$"),
                    TensoriseChannels(
                        "isoflux_t_seg_gd", regex=r"isoflux_t_seg(\d+)gd$"
                    ),
                    TensoriseChannels(
                        "isoflux_t_seg_gi", regex=r"isoflux_t_seg(\d+)gi$"
                    ),
                    TensoriseChannels(
                        "isoflux_t_seg_gp", regex=r"isoflux_t_seg(\d+)gp$"
                    ),
                    TensoriseChannels(
                        "isoflux_t_seg_td", regex=r"isoflux_t_seg(\d+)td$"
                    ),
                    TensoriseChannels(
                        "isoflux_t_seg_ti", regex=r"isoflux_t_seg(\d+)ti$"
                    ),
                    TensoriseChannels(
                        "isoflux_t_seg_tp", regex=r"isoflux_t_seg(\d+)tp$"
                    ),
                    TensoriseChannels("isoflux_t_seg_u", regex=r"isoflux_t_seg(\d+)u$"),
                    TensoriseChannels(
                        "isoflux_t_zpsh_n",
                        regex=r"isoflux_t_zpsh(\d+)n",
                    ),
                    TensoriseChannels(
                        "isoflux_t_zpsh_p",
                        regex=r"isoflux_t_zpsh(\d+)p",
                    ),
                    TransformUnits(),
                ]
            ),
            "xmo": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("xmo")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "xpc": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("xpc")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "xsx": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardiseSignalDataset("xsx")),
                    MergeDatasets(),
                    TensoriseChannels("hcam_l", regex=r"hcam_l_(\d+)"),
                    TensoriseChannels("hcam_u", regex=r"hcam_u_(\d+)"),
                    TensoriseChannels("tcam", regex=r"tcam_(\d+)"),
                    TransformUnits(),
                    AddXSXCameraParams("hcam_l", "parameters/xsx_camera_l.csv"),
                    AddXSXCameraParams("hcam_u", "parameters/xsx_camera_u.csv"),
                    AddXSXCameraParams("tcam", "parameters/xsx_camera_t.csv"),
                ]
            ),
        }

    def get(self, name: str) -> Pipeline:
        if name not in self.pipelines:
            raise RuntimeError(f"{name} is not a registered source!")
        return self.pipelines[name]
