import os

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--ref",
        action="store",
        default=None,
        help="Path to reference data. overwrites --shot",
    )
    parser.addoption(
        "--test",
        action="store",
        default=None,
        help="Path to data to test. overwrites --shot",
    )
    parser.addoption(
        "--shot",
        action="store",
        default="30120",
        help="Shot to process. From default directory, i.e: /home/hs4081/References/(shot).h5 and/or output/(shot.h5)",
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
