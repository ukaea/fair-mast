import re
from multiprocessing import Process
import typing as t
import numpy as np
import xarray as xr
import uuid
import pyuda
from typing import Optional
from dataclasses import dataclass


LAST_MAST_SHOT = 30473


@dataclass
class SignalInfo:
    uda_name: str
    uuid: uuid.UUID
    shot_id: int
    name: str
    version: int
    quality: int
    description: str
    signal_type: str
    mds_name: str
    format: str
    source: str
    mds_name: Optional[str]
    format: Optional[str]
    file_name: Optional[str]


def lookup_status_code(status):
    """Status code mapping from the numeric representation to the meaning"""
    lookup = {-1: "Very Bad", 0: "Bad", 1: "Not Checked", 2: "Checked", 3: "Validated"}
    return lookup[status]


def harmonise_name(name: str) -> str:
    name = name.replace("/", "_")
    name = name.replace(" ", "_")
    name = name.replace("(", "")
    name = name.replace(")", "")
    name = name.replace(",", "")

    if name.startswith("_"):
        name = name[1:]

    parts = name.split("_")
    if len(parts) > 1:
        name = parts[0] + "/" + "_".join(parts[1:])

    name = name.lower()
    return name


def get_dataset_item_uuid(name: str, shot: int) -> str:
    oid_name = name + "/" + str(shot)
    return str(uuid.uuid5(uuid.NAMESPACE_OID, oid_name))


def create_signal_info(item) -> SignalInfo:
    mds_name = item.mds_name if hasattr(item, "mds_name") else None
    return SignalInfo(
        uda_name=item.signal_name,
        uuid=get_dataset_item_uuid(item.signal_name, item.shot),
        shot_id=item.shot,
        name=harmonise_name(item.signal_name),
        version=int(item.pass_),
        quality=lookup_status_code(int(item.signal_status)),
        signal_type=item.type,
        description=item.description,
        format=None,
        source=str(item.source_alias).lower(),
        mds_name=mds_name,
        file_name=None,
    )


def create_image_info(item) -> SignalInfo:
    name = item.source_alias.upper()
    return SignalInfo(
        uda_name=name,
        uuid=get_dataset_item_uuid(name, item.shot),
        shot_id=item.shot,
        name=harmonise_name(name),
        version=int(item.pass_),
        quality=lookup_status_code(int(item.status)),
        signal_type=item.type,
        description=item.description,
        format=None,
        source=harmonise_name(name),
        mds_name=None,
        file_name=item.filename,
    )


def create_source_info(item) -> SignalInfo:
    name = item.source_alias.upper()
    return SignalInfo(
        uda_name=name,
        uuid=get_dataset_item_uuid(name, item.shot),
        shot_id=item.shot,
        name=harmonise_name(name),
        version=int(item.pass_),
        quality=lookup_status_code(int(item.status)),
        signal_type=item.type,
        description=item.description,
        format=item.format,
        source=harmonise_name(name),
        mds_name=None,
        file_name=item.filename,
    )


class MASTClient:
    def __init__(self) -> None:
        pass

    def _get_client(self):

        client = pyuda.Client()
        client.set_property("get_meta", True)
        client.set_property("timeout", 10)
        return client

    def get_signal_infos(self, shot_num: int) -> t.List[dict]:
        client = self._get_client()
        signals = client.list_signals(shot=shot_num)
        infos = [create_signal_info(item) for item in signals]
        return infos

    def get_image_infos(self, shot_num: int) -> t.List[SignalInfo]:
        from mast.mast_client import ListType

        client = self._get_client()

        sources = client.list(ListType.SOURCES, shot_num)
        sources = [source for source in sources if source.type == "Image"]
        infos = [create_image_info(item) for item in sources]
        return infos

    def get_source_infos(self, shot_num: int) -> t.List[dict]:
        from mast.mast_client import ListType

        client = self._get_client()
        signals = client.list(ListType.SOURCES, shot=shot_num)
        infos = [create_source_info(item) for item in signals]
        return infos

    def get_signal(self, shot_num: int, name: str, format: str) -> xr.Dataset:
        client = self._get_client()
        # Known PyUDA Bug: Old MAST signals names are truncated to 23 characters!
        # Must truncate name here or we will miss some signals
        if "IDA" in format:
            signal_name = name[:23]
        else:
            signal_name = name

        # Pull the signal on a seperate process first.
        # Sometimes this segfaults, so first we need to check that we can pull it safely
        # To do this we pull the signal on a serperate process and check the error code.
        def _get_signal(signal_name, shot_num):
            client = self._get_client()
            try:
                client.get(signal_name, shot_num)
            except pyuda.ServerException:
                pass

        p = Process(target=_get_signal, args=(signal_name, shot_num))
        p.start()
        p.join()
        code = p.exitcode

        if code < 0:
            raise RuntimeError(
                f"Failed to get data for {signal_name}/{shot_num}. Possible segfault with exitcode: {code}"
            )

        # Now we know it is safe to access the signal and we will not get a segfault
        signal = client.get(signal_name, shot_num)
        dataset = self._convert_signal_to_dataset(name, signal)
        dataset.attrs["shot_id"] = shot_num
        return dataset

    def get_image(self, shot_num: int, name: str) -> xr.Dataset:
        client = self._get_client()
        image = client.get_images(name, shot_num)
        dataset = self._convert_image_to_dataset(image)
        dataset.attrs["shot_id"] = shot_num
        return dataset

    def _convert_signal_to_dataset(self, signal_name, signal):
        dim_names = normalize_dimension_names(signal)
        coords = {
            name: xr.DataArray(
                np.atleast_1d(dim.data), dims=[name], attrs=dict(units=dim.units)
            )
            for name, dim in zip(dim_names, signal.dims)
        }

        data = np.atleast_1d(signal.data)
        errors = np.atleast_1d(signal.errors)

        attrs = self._get_dataset_attributes(signal_name, signal)

        data_vars = dict(
            data=xr.DataArray(data, dims=dim_names),
            error=xr.DataArray(errors, dims=dim_names),
        )
        dataset = xr.Dataset(data_vars, coords=coords, attrs=attrs)
        return dataset

    def _convert_image_to_dataset(self, image):
        attrs = {
            name: getattr(image, name)
            for name in dir(image)
            if not name.startswith("_") and not callable(getattr(image, name))
        }

        attrs.pop("frame_times")
        attrs.pop("frames")

        attrs["CLASS"] = "IMAGE"
        attrs["IMAGE_VERSION"] = "1.2"

        time = np.atleast_1d(image.frame_times)
        coords = {"time": xr.DataArray(time, dims=["time"], attrs=dict(units="s"))}

        if image.is_color:
            frames = [np.dstack((frame.r, frame.g, frame.b)) for frame in image.frames]
            frames = np.stack(frames)
            dim_names = ["time", "height", "width", "channel"]

            attrs["IMAGE_SUBCLASS"] = "IMAGE_TRUECOLOR"
            attrs["INTERLACE_MODE"] = "INTERLACE_PIXEL"
        else:
            frames = [frame.k for frame in image.frames]
            frames = np.stack(frames)
            frames = np.atleast_3d(frames)
            dim_names = ["time", "height", "width"]

            attrs["IMAGE_SUBCLASS"] = "IMAGE_INDEXED"

        data = {"data": (dim_names, frames)}
        dataset = xr.Dataset(data, coords=coords, attrs=attrs)
        return dataset

    def _remove_exceptions(self, signal_name, signal):
        """Handles when signal attributes contain exception objects"""
        signal_attributes = dir(signal)
        for attribute in signal_attributes:
            try:
                getattr(signal, attribute)
            except UnicodeDecodeError as exception:
                print(f"{signal_name} {attribute}: {exception}")
                signal_attributes.remove(attribute)
        return signal_attributes

    def _get_signal_metadata_fields(self, signal, signal_name):
        """Retrieves the appropriate metadata field for a given signal"""
        return [
            attribute
            for attribute in self._remove_exceptions(signal_name, signal)
            if not attribute.startswith("_")
            and attribute not in ["data", "errors", "time", "meta", "dims"]
            and not callable(getattr(signal, attribute))
        ]

    def _get_dataset_attributes(self, signal_name: str, signal) -> dict:
        metadata = self._get_signal_metadata_fields(signal, signal_name)

        attrs = {}
        for field in metadata:
            try:
                attrs[field] = getattr(signal, field)
            except TypeError:
                pass

        for key, attr in attrs.items():
            if isinstance(attr, np.generic):
                attrs[key] = attr.item()
            elif isinstance(attr, np.ndarray):
                attrs[key] = attr.tolist()
            elif isinstance(attr, tuple):
                attrs[key] = list(attr)
            elif attr is None:
                attrs[key] = "null"

        return attrs


def normalize_dimension_names(signal):
    """Make the dimension names sensible"""
    dims = [dim.label for dim in signal.dims]
    count = 0
    dim_names = []
    empty_names = ["", " ", "-"]

    for name in dims:
        # Create names for unlabelled dims
        if name in empty_names:
            name = f"dim_{count}"
            count += 1

        # Normalize weird names to standard names
        dim_names.append(name)

    dim_names = list(map(lambda x: x.lower(), dim_names))
    dim_names = [re.sub("[^a-zA-Z0-9_\n\.]", "", dim) for dim in dim_names]
    return dim_names
