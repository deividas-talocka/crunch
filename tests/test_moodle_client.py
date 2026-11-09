import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import moodle_client  # noqa: E402


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"sitename": "Test"}


@pytest.fixture(autouse=True)
def settings(monkeypatch):
    monkeypatch.setattr(moodle_client, "_settings", lambda: ("https://moodle.example", "secret-token"))


def test_call_retries_after_a_stalled_request(monkeypatch):
    attempts = []

    def flaky_get(*args, **kwargs):
        attempts.append(1)
        if len(attempts) < 3:
            raise requests.Timeout("stalled")
        return FakeResponse()

    monkeypatch.setattr(moodle_client.requests, "get", flaky_get)
    assert moodle_client.call("core_webservice_get_site_info") == {"sitename": "Test"}
    assert len(attempts) == 3


def test_call_gives_up_without_leaking_the_token(monkeypatch):
    attempts = []

    def dead_get(*args, **kwargs):
        attempts.append(1)
        raise requests.ConnectionError("https://moodle.example/?wstoken=secret-token")

    monkeypatch.setattr(moodle_client.requests, "get", dead_get)
    with pytest.raises(moodle_client.MoodleError) as error:
        moodle_client.call("core_webservice_get_site_info")
    assert len(attempts) == moodle_client.ATTEMPTS
    assert "secret-token" not in str(error.value)
