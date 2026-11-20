import os
import stat

import pytest

import config
import security


def test_valid_token_is_accepted(client):
    assert client.get("/api/profiles").status_code == 200


def test_missing_token_is_rejected(anon):
    assert anon.get("/api/profiles").status_code == 401


def test_wrong_token_is_rejected(anon):
    r = anon.get("/api/profiles", headers={security.TOKEN_HEADER: "not-the-token"})
    assert r.status_code == 401


def test_token_file_is_private():
    mode = stat.S_IMODE(os.stat(security.TOKEN_FILE).st_mode)
    assert mode == 0o600


def test_token_is_stable_across_loads():
    assert security.load_or_create_token() == security.API_TOKEN


def test_foreign_host_header_is_rejected(client):
    r = client.get("/api/profiles", headers={"host": "attacker.example"})
    assert r.status_code == 400


def test_localhost_with_port_is_accepted(client):
    r = client.get("/api/profiles", headers={"host": "127.0.0.1:8000"})
    assert r.status_code == 200


def test_disallowed_origin_gets_no_cors_headers(client):
    r = client.options("/api/profiles", headers={
        "origin": "https://attacker.example",
        "access-control-request-method": "POST",
    })
    assert "access-control-allow-origin" not in r.headers


def test_allowed_origin_gets_cors_headers(client):
    origin = config.CORS_ORIGINS[0]
    r = client.options("/api/profiles", headers={
        "origin": origin,
        "access-control-request-method": "POST",
        "access-control-request-headers": "content-type,x-jobpilot-token",
    })
    assert r.headers.get("access-control-allow-origin") == origin


def test_cross_site_request_is_rejected(client):
    r = client.post("/api/profiles", json={"name": "Jane Doe"},
                    headers={"origin": "https://attacker.example"})
    assert r.status_code == 403


def test_non_loopback_bind_is_refused():
    with pytest.raises(SystemExit):
        config.check_bind_host("0.0.0.0")
    config.check_bind_host("127.0.0.1")
