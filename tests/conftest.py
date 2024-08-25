from functools import cached_property
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from src.application import create_app


class AppTestClient:
    @cached_property
    def api_client(self) -> TestClient:
        return TestClient(create_app())

    def get(self, *args, expected_status_code=HTTPStatus.OK, **kwargs):
        result = self.api_client.get(*args, **kwargs)

        assert result.status_code == expected_status_code
        return result.json()


@pytest.fixture
def api():
    return AppTestClient()
