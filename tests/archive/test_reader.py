import xarray as xr
from src.archive.reader import DatasetReader


def test_list_signals():
    shot = 30420
    reader = DatasetReader(shot)
    signals = reader.list_datasets()

    assert isinstance(signals, list)
    assert len(signals) == 11254

    info = signals[0]
    assert info.name == "ABM_CALIB_SHOT"


def test_list_signals_exclude_raw():
    shot = 30420
    reader = DatasetReader(shot)
    signals = reader.list_datasets(exclude_raw=True)

    assert isinstance(signals, list)
    assert len(signals) == 890

    info = signals[0]
    assert info.name == "ABM_CALIB_SHOT"


def test_read_signal():
    shot = 30420
    reader = DatasetReader(shot)
    signals = reader.list_datasets()
    dataset = reader.read_dataset(signals[0])

    assert isinstance(dataset, xr.Dataset)


def test_read_signal():
    shot = 30420
    reader = DatasetReader(shot)
    signals = reader.list_datasets()
    dataset = reader.read_dataset(signals[0])

    assert isinstance(dataset, xr.Dataset)
    assert dataset.attrs["name"] == "ABM_CALIB_SHOT"
    assert dataset["time"].shape == (1,)


def test_read_image():
    shot = 30420
    reader = DatasetReader(shot)

    signals = reader.list_datasets()
    signals = filter(lambda x: x.type == "Image", signals)
    signals = list(signals)

    dataset = reader.read_dataset(signals[0])

    assert isinstance(dataset, xr.Dataset)
    assert dataset.attrs["name"] == "RBA"
    assert dataset["time"].shape == (186,)
    assert dataset["data"].shape == (186, 912, 768)
    assert list(dataset.dims.keys()) == ["time", "height", "width"]
