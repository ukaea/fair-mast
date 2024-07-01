import xarray as xr
from src.archive.transforms import (
    AddXSXCameraParams,
    DropDatasets,
    DropZeroDimensions,
    MergeDatasets,
    RenameDimensions,
    RenameVariables,
    StandardiseSignalDataset,
    TensoriseChannels,
    TransformUnits,
    ProcessImage,
)


def test_drop_datasets(fake_dataset):
    datasets = dict(a=fake_dataset, b=fake_dataset)

    transform = DropDatasets(["a"])
    datasets = transform(datasets)

    assert len(datasets) == 1
    assert "a" not in datasets


def test_rename_dimensions(fake_dataset):
    fake_dataset = fake_dataset.rename_dims({"time": "timesec"})
    fake_dataset = fake_dataset.rename_vars({"time": "timesec"})

    transform = RenameDimensions()
    dataset = transform(fake_dataset)

    assert "time" in dataset.sizes


def test_drop_zero_dimensions(fake_dataset):
    fake_dataset["time"] = fake_dataset["time"] * 0

    transform = DropZeroDimensions()
    dataset = transform(fake_dataset)

    assert len(dataset.coords) == 0


def test_rename_variables(fake_dataset):
    transform = RenameVariables({"data": "hello"})
    dataset = transform(fake_dataset)
    assert "hello" in dataset.data_vars


def test_tensorise_channels(fake_channel_dataset):
    transform = TensoriseChannels("channel")
    dataset = transform(fake_channel_dataset)
    assert "channel" in dataset.data_vars
    assert "channel_channel" in dataset.coords


def test_transform_units(fake_dataset):
    fake_dataset["data"].attrs["units"] = "Tesla"
    transform = TransformUnits()
    dataset = transform(fake_dataset)
    assert dataset["data"].attrs["units"] == "T"


def test_merge_datasets(fake_dataset):
    a = fake_dataset.rename_dims({"time": "time_a"})
    b = fake_dataset.rename_dims({"time": "time_b"})
    a = a.rename_vars({"data": "data_a", "time": "time_a", "error": "error_a"})
    b = b.rename_vars({"data": "data_b", "time": "time_b", "error": "error_b"})
    datasets = dict(a=a, b=b)

    transform = MergeDatasets()
    dataset = transform(datasets)

    assert isinstance(dataset, xr.Dataset)
    assert "data_a" in dataset.data_vars
    assert "data_b" in dataset.data_vars


def test_standardise_dataset(fake_dataset):
    transform = StandardiseSignalDataset("amc")
    dataset = transform(fake_dataset)

    assert "plasma_current" in dataset.data_vars
    assert "plasma_current_error" in dataset.data_vars


def test_xsx_camera_params(fake_dataset):
    transform = AddXSXCameraParams("tcam", "parameters/xsx_camera_t.csv")
    dataset = transform(fake_dataset)

    assert "tcam_r1" in dataset.data_vars
    assert "tcam_r2" in dataset.data_vars

    assert "tcam_z1" in dataset.data_vars
    assert "tcam_z2" in dataset.data_vars


def test_process_image(fake_image):
    transform = ProcessImage()
    dataset = transform({"rbb": fake_image})
    assert isinstance(dataset, xr.Dataset)
