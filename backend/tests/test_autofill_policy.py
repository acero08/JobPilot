import pytest

from autofill import frame_policy, is_ats_host

TOP = "https://careers.example.com/jobs/123"


@pytest.mark.parametrize("host", [
    "boards.greenhouse.io", "greenhouse.io", "jobs.lever.co", "jobs.ashbyhq.com",
    "acme.wd5.myworkdayjobs.com",
])
def test_known_ats_hosts_match(host):
    assert is_ats_host(host)


@pytest.mark.parametrize("host", [
    "evilgreenhouse.io", "greenhouse.io.attacker.example", "lever.co.example", "", None,
])
def test_lookalike_hosts_do_not_match(host):
    assert not is_ats_host(host)


def test_same_origin_frame_is_allowed():
    assert frame_policy(TOP, "https://careers.example.com/embed/form") == (True, None)


def test_ats_frame_is_allowed():
    assert frame_policy(TOP, "https://boards.greenhouse.io/embed/job_app?for=acme")[0]


def test_other_cross_origin_frame_is_skipped_with_reason():
    allowed, reason = frame_policy(TOP, "https://ads.tracker.example/frame")
    assert not allowed
    assert "ads.tracker.example" in reason


def test_different_port_is_cross_origin():
    assert not frame_policy(TOP, "https://careers.example.com:8443/form")[0]


def test_blank_frames_are_skipped_silently():
    assert frame_policy(TOP, "about:blank") == (False, None)


def test_ats_domain_list_is_exposed(client):
    r = client.get("/api/ats-domains")
    assert r.status_code == 200
    assert "greenhouse.io" in r.json()
