from http import HTTPStatus


def test_ping(api):
    response = api.get("/ping")

    assert response["API"] == "OK"


def test_error_url(api):
    api.get("/png", expected_status_code=HTTPStatus.NOT_FOUND)
