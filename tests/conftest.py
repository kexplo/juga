import functools
import json
from pathlib import Path

from aioresponses import aioresponses
import pytest


@pytest.fixture()
def mock_aioresponse():
    with aioresponses() as m:
        yield m


@pytest.fixture()
def read_testdata(request):
    @functools.wraps(request)
    def read_testdata_json(filename: str) -> dict:
        data_path = Path(request.fspath).resolve().parent / filename
        with open(data_path, "r") as f:
            return json.loads(f.read())

    return read_testdata_json


def pytest_addoption(parser):
    parser.addoption("--webtest", action="store_true", default=False, help="run webtest marked tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "webtest: mark test as a webtest")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--webtest"):
        # --webtest  given in cli: do not skip webtest tests
        return
    skip_webtest = pytest.mark.skip(reason="need --webtest option to run")
    for item in items:
        if "webtest" in item.keywords:
            item.add_marker(skip_webtest)
