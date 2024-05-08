import pandas as pd
import xarray as xr
from dataclasses import asdict
from src.archive.reader import DatasetReader, SignalMetadataReader, SourceMetadataReader


def test_list_signals():
    shot = 30420
    reader = DatasetReader(shot)
    signals = reader.list_datasets()

    assert isinstance(signals, list)
    assert len(signals) == 11254

    info = signals[0]
    assert info.name == "abm/calib_shot"


def test_list_signals_exclude_raw():
    shot = 30420
    reader = DatasetReader(shot)
    signals = reader.list_datasets(exclude_raw=True)

    assert isinstance(signals, list)
    assert len(signals) == 890

    info = signals[0]
    assert info.name == "abm/calib_shot"


def test_read_signal():
    shot = 30420
    reader = DatasetReader(shot)
    signals = reader.list_datasets()
    info = asdict(signals[0])
    info["format"] = "IDA"
    dataset = reader.read_dataset(info)

    assert isinstance(dataset, xr.Dataset)
    assert dataset.attrs["name"] == "abm/calib_shot"
    assert dataset["time"].shape == (1,)


def test_read_image():
    shot = 30420
    reader = DatasetReader(shot)

    signals = reader.list_datasets()
    signals = filter(lambda x: x.signal_type == "Image", signals)
    signals = list(signals)

    dataset = reader.read_dataset(asdict(signals[0]))

    assert isinstance(dataset, xr.Dataset)
    assert dataset.attrs["name"] == "rba"
    assert dataset["time"].shape == (186,)
    assert dataset["data"].shape == (186, 912, 768)
    assert list(dataset.dims.keys()) == ["time", "height", "width"]


def test_read_signals_metadata():
    shot = 30420
    reader = SignalMetadataReader(shot)
    df = reader.read_metadata()

    assert isinstance(df, pd.DataFrame)


def test_read_sources_metadata():
    shot = 30420
    reader = SourceMetadataReader(shot)
    df = reader.read_metadata()

    assert isinstance(df, pd.DataFrame)
