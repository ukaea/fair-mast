import pytest
from src.source import HDFSource

@pytest.fixture()
def source():
    source = HDFSource('/common/tmp/sjackson/mast2HDF5/')
    return source

def test_open_shot_all_signals(benchmark, source):
    benchmark.pedantic(source.read_shot_all_signals, kwargs=dict(shot='30123'), iterations=1, rounds=1)

def test_open_signal_all_shots(benchmark, source):
    name = 'aoe/AOE_FAST_K/data'
    benchmark(source.read_signal_all_shots, name=name)

def test_read_signal_all_shots(benchmark, source):
    name = 'aoe/AOE_FAST_K/data'

    def _read_signal(name):
        result = source.read_signal_all_shots(name)
        result.compute()

    benchmark(_read_signal, name=name)
