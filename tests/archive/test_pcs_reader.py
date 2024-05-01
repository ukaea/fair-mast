import xarray as xr
from src.archive.writer import DatasetWriter
from src.archive.pcs_reader import read_pcs_data


def test_read_pcs_data():
    result = read_pcs_data(30420)
    assert isinstance(result, dict)
    for item in result.values():
        assert isinstance(item, xr.Dataset)


def test_write_pcs_data(tmpdir):
    result = read_pcs_data(30420)
    writer = DatasetWriter(30420, tmpdir)

    for dataset in result.values():
        writer.write_dataset(dataset)

    path = tmpdir / "30420.zarr"
    assert path.exists()
    assert (path / "pcs").exists()

    dataset = xr.open_zarr(path, group="pcs/gas_gas1")
    assert dataset.data.shape == (13,)
