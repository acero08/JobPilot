import pytest

import config
import uploads
from db import RESUME_DIR

PDF = b"%PDF-1.7\n%fake test resume\n"
DOCX = b"PK\x03\x04fake-docx"
DOC = bytes.fromhex("D0CF11E0A1B11AE1") + b"fake-doc"


@pytest.fixture
def profile(client):
    return client.post("/api/profiles", json={"name": "Jane Doe", "personal": {"email": "jane@example.com"}}).json()


def upload(client, pid, filename, data, mime="application/octet-stream"):
    return client.post(f"/api/profiles/{pid}/resume", files={"file": (filename, data, mime)})


@pytest.mark.parametrize("name,data", [("resume.pdf", PDF), ("resume.docx", DOCX), ("resume.doc", DOC)])
def test_allowed_types_are_stored_under_server_name(client, profile, name, data):
    r = upload(client, profile["id"], name, data)
    assert r.status_code == 200
    stored = r.json()["resume_file"]
    assert uploads.STORED_NAME.match(stored)
    assert (RESUME_DIR / stored).read_bytes() == data


def test_path_traversal_filename_cannot_escape_resume_dir(client, profile):
    r = upload(client, profile["id"], "../../../../tmp/evil.pdf", PDF)
    assert r.status_code == 200
    body = r.json()
    path = (RESUME_DIR / body["resume_file"]).resolve()
    assert path.parent == RESUME_DIR.resolve()
    assert body["resume_name"] == "evil.pdf"


def test_windows_style_traversal_is_reduced_to_basename(client, profile):
    r = upload(client, profile["id"], "..\\..\\evil.pdf", PDF)
    assert r.status_code == 200
    assert r.json()["resume_name"] == "evil.pdf"


@pytest.mark.parametrize("name", ["resume.exe", "resume.html", "resume", "resume.pdf.sh"])
def test_disallowed_extension_is_rejected(client, profile, name):
    assert upload(client, profile["id"], name, PDF).status_code == 400


def test_content_must_match_extension(client, profile):
    assert upload(client, profile["id"], "resume.pdf", b"<html>not a pdf</html>").status_code == 400


def test_oversized_upload_is_rejected(client, profile, monkeypatch):
    monkeypatch.setattr(uploads, "MAX_UPLOAD_BYTES", 1024)
    assert upload(client, profile["id"], "resume.pdf", PDF + b"0" * 2048).status_code == 413


def test_replacing_resume_deletes_previous_file(client, profile):
    first = upload(client, profile["id"], "a.pdf", PDF).json()["resume_file"]
    upload(client, profile["id"], "b.pdf", PDF)
    assert not (RESUME_DIR / first).exists()


def test_client_cannot_set_resume_file(client, profile):
    r = client.put(f"/api/profiles/{profile['id']}", json={**profile, "resume_file": "../../secret.txt"})
    assert r.status_code == 200
    assert "resume_file" not in r.json()


def test_save_keeps_server_resume_fields(client, profile):
    stored = upload(client, profile["id"], "resume.pdf", PDF).json()["resume_file"]
    r = client.put(f"/api/profiles/{profile['id']}", json={**profile, "name": "Jane Doe (renamed)"})
    assert r.json()["resume_file"] == stored


def test_stored_path_rejects_unknown_names():
    assert uploads.stored_path("../../etc/passwd") is None
    assert uploads.stored_path("resume.pdf") is None
    assert uploads.stored_path(None) is None


def test_default_size_limit_is_configured():
    assert config.MAX_UPLOAD_BYTES == 10 * 1024 * 1024
