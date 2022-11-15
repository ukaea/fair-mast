"""pytest tests for comparing an output .h5 file to a reference

command line args examples:

>... --shot 30119
compares output/30119.h5 against /home/hs4081/References/30119.h5

>... --test /scratch/hs4081/
compares /scratch/hs4081/30120.h5 against /home/hs4081/References/30120.h5

>... --test /scratch/hs4081/ --shot 30119
compares /scratch/hs4081/30119.h5 against /home/hs4081/References/30119.h5

>... --ref /scratch/hs4081/References/30100.h5  --test /home/hs4081/References/30100.h5
compares /scratch/hs4081/References/30100.h5 against /home/hs4081/References/30100.h5
"""

import os

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--ref",
        action="store",
        default=None,
        help="Path to reference data or directory.",
    )
    parser.addoption(
        "--test",
        action="store",
        default=None,
        help="Path to data to test or directory.",
    )
    parser.addoption(
        "--shot",
        action="store",
        default="30120",
        help="Shot to process. From default directories. Default = 30120",
    )


@pytest.fixture(scope="session")
def get_expected_path(request):
    DEFAULT_PATH = "/home/hs4081/References/"

    shot = request.config.getoption("--shot")
    path = request.config.getoption("--ref")
    if path is None:
        path = os.path.join(DEFAULT_PATH, f"{shot}.h5")
    if path[-1] == "/":
        path = os.path.join(DEFAULT_PATH, f"{shot}.h5")
    return path


@pytest.fixture(scope="session")
def get_input_path(request):
    DEFAULT_PATH = "output/"

    shot = request.config.getoption("--shot")
    path = request.config.getoption("--test")
    if path is None:
        path = os.path.join(DEFAULT_PATH, f"{shot}.h5")
    if path[-1] == "/":
        path = os.path.join(DEFAULT_PATH, f"{shot}.h5")
    return path
