import pytest
from src.source import HDFSource

@pytest.fixture()
def source():
    source = HDFSource('./data')
    return source
    
def test_read_shot_all_signals(benchmark, source):
    benchmark.pedantic(source.read_shot_all_signals, kwargs=dict(shot='30449'), iterations=1, rounds=1)
    # result = source.read_shot_all_signals(shot='30449')
    # print(result)
    # assert len(result) == 64

def test_read_signal_all_shots(benchmark, source):
    benchmark(source.read_signal_all_shots, name='xyr/TIME1/data')
