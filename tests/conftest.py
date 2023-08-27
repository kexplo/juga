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
