import pytest
from src.source import HDFSource, NetCDFSource, ZarrSource

HDF_DIR = './data/hdf/'
NETCDF_DIR = './data/netcdf'
ZARR_DIR = './data/zarr'

@pytest.fixture()
def hdf_source():
    source = HDFSource(HDF_DIR)
    return source

@pytest.fixture()
def netcdf_source():
    source = NetCDFSource(NETCDF_DIR)
    return source

@pytest.fixture()
def zarr_source():
    source = ZarrSource(ZARR_DIR)
    return source

# def test_open_shot_all_signals(benchmark, hdf_source):
#     benchmark.pedantic(source.read_shot_all_signals, kwargs=dict(shot='30123'), iterations=1, rounds=1)

def test_hdf_open_signal_all_shots(benchmark, hdf_source):
    name = 'aoe/FAST_K/data'
    benchmark(hdf_source.read_signal_all_shots, name=name)

def test_hdf_read_signal_all_shots(benchmark, hdf_source):
    name = 'aoe/FAST_K/data'

    def _read_signal(name):
        result = hdf_source.read_signal_all_shots(name)
        result.compute()

    benchmark(_read_signal, name=name)

def test_netcdf_open_signal_all_shots(benchmark, netcdf_source):
    name = 'aoe_FAST_K.nc'
    benchmark(netcdf_source.read_signal_all_shots, name=name)

def test_netcdf_read_signal_all_shots(benchmark, netcdf_source):
    name = 'aoe_FAST_K.nc'

    def _read_signal(name):
        result = netcdf_source.read_signal_all_shots(name)
        result.compute()

    benchmark(_read_signal, name=name)

def test_zarr_open_signal_all_shots(benchmark, zarr_source):
    name = 'aoe_FAST_K.zarr'
    benchmark(zarr_source.read_signal_all_shots, name=name)

def test_zarr_read_signal_all_shots(benchmark, zarr_source):
    name = 'aoe_FAST_K.zarr'

    def _read_signal(name):
        result = zarr_source.read_signal_all_shots(name)
        result.compute()

    benchmark(_read_signal, name=name)
