# ----------------------------------------
# Pytest to compare two .h5 files.
# For best results run using:
# > pytest PATH/output_test.py -s -vv
# ----------------------------------------


import numpy as np
import pytest
import h5py
import os
import random

from requests import request


@pytest.fixture(scope="session")
def expected_data(request):
    path = "/scratch/hs4081/BM30405.h5"
    file = h5py.File(path, "r")
    request.addfinalizer(file.close)
    return file


@pytest.fixture(scope="session")
def input_data(request):
    path = "/scratch/hs4081/30405.h5"
    file = h5py.File(path, "r")
    request.addfinalizer(file.close)
    return file


@pytest.fixture
def get_random_signal(expected_data):
    signal_path = {}
    source_name = random.choice([*expected_data.keys()])
    obj = expected_data[source_name]
    signal_path[source_name] = obj
    while type(obj) != h5py.Dataset:
        try:
            parent_obj = [*signal_path.values()][-1]
            name = random.choice([*parent_obj.keys()])
            if name in [*signal_path.keys()]:
                raise RuntimeError(
                    "Duplicate key in signal path"
                )  # temporary error to stop infinite looping
            obj = parent_obj[name]
            signal_path[name] = obj
        except IndexError:  # if group has no child groups or datasets, reset source and start again.
            signal_path = {}
            source_name = random.choice([*expected_data.keys()])
            obj = expected_data[source_name]
            signal_path[source_name] = obj
    return signal_path


def test_base_attrs(expected_data, input_data):
    assert expected_data.attrs == input_data.attrs


NO_OF_REPEATS = 100


@pytest.mark.parametrize("repeat_count", range(NO_OF_REPEATS))
def test_random_sample(expected_data, input_data, get_random_signal, repeat_count):
    print("Testing " + str([*get_random_signal.keys()]))

    signal_path = [input_data]
    for key in [*get_random_signal.keys()]:
        obj = signal_path[-1][key]
        signal_path.append(obj)

    expected_signal_data = [*get_random_signal.values()][-1]
    input_signal_data = signal_path[-1]
    expected_signal_data = np.nan_to_num(expected_signal_data, copy=False)
    input_signal_data = np.nan_to_num(input_signal_data, copy=False)
    assert (expected_signal_data[()] == input_signal_data[()]).all()
    print("Complete")
