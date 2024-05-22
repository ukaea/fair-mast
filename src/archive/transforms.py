from typing import Any, Optional
import pint
import re
import json
import numpy as np
import xarray as xr
from pathlib import Path


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
        with Path("mappings/dim_names.json").open("r") as handle:
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
        return dataset


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
        dataset = dataset.squeeze(drop=True)

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
        dataset = dataset.chunk("auto")
        dataset = self._drop_unused_coords(dataset)
        if "time" in dataset.dims:
            dataset = dataset.drop_duplicates(dim="time")

        # Update attributes
        attrs = dataset.attrs
        attrs["name"] = self.source + "/" + new_names["data"]
        attrs["dims"] = list(dataset.sizes.keys())
        dataset[new_names["data"]].attrs = attrs
        return dataset

    def _drop_unused_coords(self, data: xr.Dataset) -> xr.Dataset:
        used_coords = set()
        for var in data.data_vars.values():
            used_coords.update(var.dims)

        # Drop coordinates that are not used
        unused_coords = set(data.coords) - used_coords
        data = data.drop_vars(unused_coords)
        return data


class MergeDatasets:

    def __call__(self, dataset_dict: dict[str, xr.Dataset]) -> xr.Dataset:
        dataset = xr.merge(dataset_dict.values())
        dataset.attrs = {}
        return dataset


class TensorizeChannels:
    def __init__(
        self,
        stem: str,
        regex: Optional[str] = None,
        dim_name: Optional[str] = None,
        assign_coords: bool = True,
    ) -> None:
        self.stem = stem
        self.regex = regex if regex is not None else stem + "(\d+)"
        self.dim_name = f"{self.stem}_channel" if dim_name is None else dim_name
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
        attrs = channels[0].attrs
        dataset[self.stem].attrs = attrs
        dataset = dataset.drop_vars(group_keys)
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
        with Path("mappings/units.json").open("r") as handle:
            self.units_map = json.load(handle)

        self.ureg = pint.UnitRegistry()
        self.ureg.load_definitions("mappings/custom_units.txt")

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        for key, array in dataset.data_vars.items():
            units = array.attrs["units"]
            units = self.units_map.get(units, units)
            units = self._parse_units(units)
            array.attrs["units"] = units

        return dataset

    def _parse_units(self, unit: str) -> str:
        try:
            unit = self.ureg.parse_units(unit)
            unit = format(unit, "~")
            return unit
        except:
            return unit


class ASXTransform:
    """ASX is very special.

    The time points are actually the data and the data is blank.
    This transformation renames them and used the correct dimension mappings.
    """

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


class LCFSTransform:
    """LCFS transform for LCFS coordinates

    In MAST, the LCFS coordinates have a lot of padding.
    This transform groups the r and z parameters and crops the padding.
    """

    def __call__(self, dataset: xr.Dataset) -> xr.Dataset:
        fill_value = np.max(dataset["efm/lcfsr_c"].values)
        max_index = np.max(np.argmax(dataset["efm/lcfsr_c"].values, axis=1))
        dataset = dataset.sel(lcfs_coords=dataset.lcfs_coords[:max_index])
        dataset["efm/lcfsr_c"].values[dataset.values == fill_value] = np.nan
        dataset["efm/lcfsz_c"].values[dataset.values == fill_value] = np.nan
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
                    TransformUnits(),
                ]
            ),
            "ada": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("ada")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "aga": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("aga")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "adg": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("adg")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ahx": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("ahx")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "aim": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("aim")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "air": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("air")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ait": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("ait")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "alp": Pipeline(
                [
                    MapDict(DropZeroDimensions()),
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("alp")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ama": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("ama")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "amb": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("abm")),
                    MergeDatasets(),
                    TensorizeChannels("amb/ccbv"),
                    TensorizeChannels("amb/obr"),
                    TensorizeChannels("amb/obv"),
                    TensorizeChannels("amb/fl_cc"),
                    TensorizeChannels("amb/fl_p"),
                    TransformUnits(),
                ]
            ),
            "amc": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("amc")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "amh": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("amh")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "amm": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("amm")),
                    MergeDatasets(),
                    TensorizeChannels("amm/incon"),
                    TensorizeChannels("amm/mid"),
                    TensorizeChannels("amm/ring"),
                    TensorizeChannels("amm/rodgr"),
                    TensorizeChannels("amm/vertw"),
                    TensorizeChannels("amm/lhorw"),
                    TensorizeChannels("amm/uhorw"),
                    TransformUnits(),
                ]
            ),
            "ams": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("ams")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "anb": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("amb")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ane": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("ane")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ant": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("ant")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "anu": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("anu")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "aoe": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("aoe")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "arp": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("arp")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "asb": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("asb")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "asm": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("asm")),
                    MergeDatasets(),
                    TensorizeChannels("asm/sad_m"),
                    TransformUnits(),
                ]
            ),
            "asx": Pipeline(
                [
                    MapDict(ASXTransform()),
                    MapDict(StandardizeSignalDataset("asx")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "ayc": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("ayc")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "aye": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("aye")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
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
                    MapDict(DropZeroDimensions()),
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("efm")),
                    MergeDatasets(),
                    LCFSTransform(),
                    TransformUnits(),
                ]
            ),
            "esm": Pipeline(
                [
                    MapDict(DropZeroDimensions()),
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("esm")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "esx": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("esx")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "xdc": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("xdc")),
                    MergeDatasets(),
                    TensorizeChannels(
                        "xdc/ai_cpu1_ccbv",
                        dim_name="ai_ccbv_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu1_flcc",
                        dim_name="ai_flcc_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu1_incon",
                        dim_name="ai_incon_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu1_lhorw",
                        dim_name="ai_lhorw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu1_mid",
                        dim_name="ai_mid_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu1_obr",
                        dim_name="ai_obr_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu1_obv",
                        dim_name="ai_obv_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu1_ring",
                        dim_name="ai_ring_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu1_rodgr",
                        dim_name="ai_rodgr_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu1_uhorw",
                        dim_name="ai_uhorw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu1_vertw",
                        dim_name="ai_vertw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu2_ccbv",
                        dim_name="ai_ccbv_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu2_flcc",
                        dim_name="ai_flcc_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu2_incon",
                        dim_name="ai_incon_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu2_lhorw",
                        dim_name="ai_lhorw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu2_mid",
                        dim_name="ai_mid_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu2_obr",
                        dim_name="ai_obr_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu2_obv",
                        dim_name="ai_obv_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu2_ring",
                        dim_name="ai_ring_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu2_rodgr",
                        dim_name="ai_rodgr_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu2_uhorw",
                        dim_name="ai_uhorw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu2_vertw",
                        dim_name="ai_vertw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu3_ccbv",
                        dim_name="ai_ccbv_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu3_flcc",
                        dim_name="ai_flcc_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu3_incon",
                        dim_name="ai_incon_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu3_lhorw",
                        dim_name="ai_lhorw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu3_mid",
                        dim_name="ai_mid_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu3_obr",
                        dim_name="ai_obr_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu3_obv",
                        dim_name="ai_obv_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu3_ring",
                        dim_name="ai_ring_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu3_rodgr",
                        dim_name="ai_rodgr_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu3_uhorw",
                        dim_name="ai_uhorw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu3_vertw",
                        dim_name="ai_vertw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu4_ccbv",
                        dim_name="ai_ccbv_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu4_flcc",
                        dim_name="ai_flcc_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu4_incon",
                        dim_name="ai_incon_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu4_lhorw",
                        dim_name="ai_lhorw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu4_mid",
                        dim_name="ai_mid_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu4_obr",
                        dim_name="ai_obr_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu4_obv",
                        dim_name="ai_obv_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu4_ring",
                        dim_name="ai_ring_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu4_rodgr",
                        dim_name="ai_rodgr_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu4_uhorw",
                        dim_name="ai_uhorw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_cpu4_vertw",
                        dim_name="ai_vertw_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_raw_ccbv", dim_name="ai_ccbv", assign_coords=False
                    ),
                    TensorizeChannels(
                        "xdc/ai_raw_flcc",
                        dim_name="ai_flcc_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/ai_raw_obv", dim_name="ai_obv_channel", assign_coords=False
                    ),
                    TensorizeChannels(
                        "xdc/ai_raw_obr", dim_name="ai_obr_channel", assign_coords=False
                    ),
                    TensorizeChannels(
                        "xdc/equil_s_seg",
                        regex=r"equil_s_seg(\d+)$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/equil_s_seg_at",
                        regex=r"equil_s_seg(\d+)at$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/equil_s_seg_rt",
                        regex=r"equil_s_seg(\d+)rt$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/equil_s_seg_zt",
                        regex=r"equil_s_seg(\d+)zt$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/equil_s_segb",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/equil_t_seg",
                        regex=r"equil_t_seg(\d+)$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels(
                        "xdc/equil_t_seg_u",
                        regex=r"equil_t_seg(\d+)u$",
                        dim_name="equil_seg_channel",
                        assign_coords=False,
                    ),
                    TensorizeChannels("isoflux_e_seg"),
                    TensorizeChannels(
                        "xdc/isoflux_t_rpsh_n",
                        regex=r"isoflux_t_rpsh(\d+)n",
                    ),
                    TensorizeChannels(
                        "xdc/isoflux_t_rpsh_p",
                        regex=r"isoflux_t_rpsh(\d+)p",
                    ),
                    TensorizeChannels("isoflux_t_seg", regex=r"isoflux_t_seg(\d+)$"),
                    TensorizeChannels(
                        "xdc/isoflux_t_seg_gd", regex=r"isoflux_t_seg(\d+)gd$"
                    ),
                    TensorizeChannels(
                        "xdc/isoflux_t_seg_gi", regex=r"isoflux_t_seg(\d+)gi$"
                    ),
                    TensorizeChannels(
                        "xdc/isoflux_t_seg_gp", regex=r"isoflux_t_seg(\d+)gp$"
                    ),
                    TensorizeChannels(
                        "xdc/isoflux_t_seg_td", regex=r"isoflux_t_seg(\d+)td$"
                    ),
                    TensorizeChannels(
                        "xdc/isoflux_t_seg_ti", regex=r"isoflux_t_seg(\d+)ti$"
                    ),
                    TensorizeChannels(
                        "xdc/isoflux_t_seg_tp", regex=r"isoflux_t_seg(\d+)tp$"
                    ),
                    TensorizeChannels("isoflux_t_seg_u", regex=r"isoflux_t_seg(\d+)u$"),
                    TensorizeChannels(
                        "xdc/isoflux_t_zpsh_n",
                        regex=r"isoflux_t_zpsh(\d+)n",
                    ),
                    TensorizeChannels(
                        "xdc/isoflux_t_zpsh_p",
                        regex=r"isoflux_t_zpsh(\d+)p",
                    ),
                    TransformUnits(),
                ]
            ),
            "xpc": Pipeline(
                [
                    MapDict(RenameDimensions()),
                    MapDict(StandardizeSignalDataset("xpc")),
                    MergeDatasets(),
                    TransformUnits(),
                ]
            ),
            "xsx": Pipeline(
                [
                    MapDict(StandardizeSignalDataset("xsx")),
                    MergeDatasets(),
                    TensorizeChannels("xsx/hcam_l", regex=r"hcam_l_(\d+)"),
                    TensorizeChannels("xsx/hcam_u", regex=r"hcam_u_(\d+)"),
                    TensorizeChannels("xsx/tcam", regex=r"tcam_(\d+)"),
                    TransformUnits(),
                ]
            ),
        }

    def get(self, name: str) -> Pipeline:
        if name not in self.pipelines:
            raise RuntimeError(f"{name} is not a registered source!")
        return self.pipelines[name]
