import pytest


# Fixture to get data path from command line
def pytest_addoption(parser):
    parser.addoption(
        "--data-path",
        action="store",
        default="./tests/mock_data/index",
        help="Path to mini data directory",
    )


@pytest.fixture(scope="session")
def data_path(request):
    return request.config.getoption("--data-path")