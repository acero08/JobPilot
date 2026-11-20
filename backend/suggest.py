"""Rank saved profiles for a job (title + location). Simple keyword scoring;
this is the seam where smarter matching / job-feed matching plugs in later."""
import re


def _tokens(s):
    return set(re.findall(r"[a-z0-9+#.]+", (s or "").lower()))


def score_profile(profile, job_title, job_location, remote=False):
    score = 0.0
    reasons = []
    title_t = _tokens(job_title)
    kw = _tokens(" ".join(profile.get("job_types", [])) + " " + " ".join(profile.get("keywords", [])))
    hit = title_t & kw
    if hit:
        score += 3 * len(hit)
        reasons.append("title match: " + ", ".join(sorted(hit)))

    loc_t = _tokens(job_location)
    locs = [l.lower() for l in profile.get("locations", [])]
    if any(_tokens(l) & loc_t for l in locs):
        score += 4
        reasons.append("location match")
    if remote and profile.get("accepts_remote", True):
        score += 2
        reasons.append("remote ok")
    return score, reasons


def rank(profiles, job_title, job_location, remote=False):
    out = []
    for p in profiles:
        s, r = score_profile(p, job_title, job_location, remote)
        out.append({"id": p["id"], "name": p["name"], "score": s, "reasons": r})
    return sorted(out, key=lambda x: -x["score"])
