# ----------------------------------------
# Pytest to compare two .h5 files.
# For best results run using:
# > pytest PATH/output_test.py -s -vv
# ----------------------------------------


import random

import h5py
import numpy as np
import pytest


@pytest.fixture(scope="session")
def expected_data(request):
    path = "/home/hs4081/References/30120.h5"

    file = h5py.File(path, "r")
    request.addfinalizer(file.close)
    return file


@pytest.fixture(scope="session")
def input_data(request):
    path = "output/30120.h5"
    file = h5py.File(path, "r")
    request.addfinalizer(file.close)
    return file


@pytest.fixture(scope="function")
def get_random_signal(expected_data):
    signal_path = []
    ignored_sources = ["RCO"]
    source_name = random.choice(
        [source for source in expected_data.keys() if source not in ignored_sources]
    )
    obj = expected_data[source_name]
    signal_path.append(source_name)
    while type(obj) != h5py.Dataset:
        try:
            parent_obj = obj
            name = random.choice([*parent_obj.keys()])
            obj = parent_obj[name]
            signal_path.append(name)
        except IndexError:  # if group has no child groups or datasets, reset source and start again.
            signal_path = []
            source_name = random.choice([*expected_data.keys()])
            obj = expected_data[source_name]
            signal_path.append(source_name)
    return signal_path


@pytest.fixture
def get_expected_data(get_random_signal, expected_data):
    obj = expected_data
    for x in get_random_signal:
        parent_obj = obj
        obj = parent_obj[x]
    return obj


@pytest.fixture
def get_input_data(get_random_signal, input_data):
    obj = input_data
    for x in get_random_signal:
        parent_obj = obj
        obj = parent_obj[x]
    return obj


def test_cpf(expected_data, input_data):
    assert expected_data.attrs == input_data.attrs


NO_OF_REPEATS = 250


@pytest.mark.parametrize("repeat_count", range(NO_OF_REPEATS))
def test_random_sample(
    get_expected_data, get_input_data, get_random_signal, repeat_count
):
    print("Testing " + str(get_random_signal))

    expected_signal_data = np.nan_to_num(get_expected_data, copy=False)
    input_signal_data = np.nan_to_num(get_input_data, copy=False)
    assert (expected_signal_data[()] == input_signal_data[()]).all()
