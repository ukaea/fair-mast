import pytest
import zarr
import xarray as xr
from src.archive.writer import DatasetWriter
pyuda_import = pytest.importorskip("pyuda") 

def test_write_metadata(tmpdir):
    shot = 30420
    writer = DatasetWriter(shot, tmpdir)
    writer.write_metadata()
    assert writer.dataset_path.exists()
    f = zarr.open(writer.dataset_path)
    assert "dataset_uuid" in f.attrs
    assert f.attrs["shot_id"] == shot


@pytest.mark.usefixtures("fake_dataset")
def test_write_signal(tmpdir, fake_dataset):
    shot = 30420
    writer = DatasetWriter(shot, tmpdir)
    writer.write_dataset(fake_dataset)

    assert writer.dataset_path.exists()
    dataset = xr.open_dataset(writer.dataset_path, group="acm/fake_dataset")
    assert dataset["time"].shape == (10,)


@pytest.mark.usefixtures("fake_dataset")
def test_write_image(tmpdir, fake_dataset):
    fake_dataset.attrs["name"] = "RIR"

    shot = 30420
    writer = DatasetWriter(shot, tmpdir)
    writer.write_dataset(fake_dataset)

    assert writer.dataset_path.exists()
    dataset = xr.open_dataset(writer.dataset_path, group="rir")
    assert dataset["time"].shape == (10,)


@pytest.mark.usefixtures("fake_dataset")
def test_write_consolidate(tmpdir, fake_dataset):
    shot = 30420
    writer = DatasetWriter(shot, tmpdir)
    writer.write_dataset(fake_dataset)
    writer.consolidate_dataset()

    zarr.open_consolidated(writer.dataset_path)
