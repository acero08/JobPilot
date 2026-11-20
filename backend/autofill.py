"""Playwright autofill engine.

Opens the application page in a visible Chromium window, fills the fields it
can match from the selected profile, attaches the resume, and stops. It never
submits a form: the applicant reviews the page and submits it manually.
Unmatched fields are returned in the report so they can be completed by hand.
EEO and demographic questions (gender, race, veteran, disability) are never
filled, because those answers should always be an explicit personal choice.
"""
import re

from playwright.async_api import async_playwright

from config import HEADLESS, PAGE_SETTLE_MS
from db import DATA_DIR, RESUME_DIR

# A persistent profile keeps job-site sessions, so sign-in is needed only once.
BROWSER_DIR = DATA_DIR / "browser-profile"

_pw = None
_ctx = None

# (key, regex) pairs. The first match wins, so more specific patterns come first.
RULES = [
    ("sponsorship", r"sponsor|require.*visa|visa.*(status|require)"),
    ("work_authorized", r"authori[sz]ed to work|legally (authori[sz]ed|eligible)|eligible to work|right to work"),
    ("relocate", r"relocat"),
    ("first_name", r"first.?name|given.?name|\bfname\b"),
    ("last_name", r"last.?name|family.?name|surname|\blname\b"),
    ("email", r"e-?mail"),
    ("phone", r"phone|mobile|\btel\b|cell"),
    ("linkedin", r"linkedin"),
    ("github", r"github"),
    ("portfolio", r"portfolio|website|personal (site|url)|\burl\b"),
    ("zip", r"zip|postal"),
    ("city", r"\bcity\b|town"),
    ("state", r"\bstate\b|province|region"),
    ("country", r"country"),
    ("address", r"address|street"),
    ("current_company", r"current (company|employer)|employer"),
    ("current_title", r"current (title|position)|job title"),
    ("salary", r"salary|compensation|pay expectation"),
    ("start_date", r"start date|available to start|earliest start|notice period"),
    ("how_heard", r"how did you (hear|find)|referral source|source"),
    ("cover_letter", r"cover.?letter|why .*(want|interested)|additional information"),
    ("full_name", r"^\s*(full|legal|your)?\s*name\b|\bname\s*\*?$"),
]

COLLECT_JS = """
() => {
  const out = [];
  const els = document.querySelectorAll('input, textarea, select');
  const txt = n => (n && n.textContent || '').replace(/\\s+/g,' ').trim();
  let i = 0;
  for (const el of els) {
    const type = (el.getAttribute('type') || el.tagName).toLowerCase();
    if (['hidden','submit','button','image','reset','password','search'].includes(type)) continue;
    const r = el.getBoundingClientRect();
    const visible = (r.width > 0 && r.height > 0) || type === 'file';
    if (!visible || el.disabled) continue;
    const parts = [];
    if (el.id) { const l = document.querySelector('label[for="' + CSS.escape(el.id) + '"]'); if (l) parts.push(txt(l)); }
    const wrap = el.closest('label'); if (wrap) parts.push(txt(wrap));
    const lb = el.getAttribute('aria-labelledby');
    if (lb) lb.split(' ').forEach(id => parts.push(txt(document.getElementById(id))));
    ['aria-label','placeholder','name','id','autocomplete','data-qa','data-testid'].forEach(a => { const v = el.getAttribute(a); if (v) parts.push(v); });
    // Radios and unlabeled controls carry their question text on the enclosing group.
    const grp = el.closest('fieldset');
    let question = '';
    if (grp) { const lg = grp.querySelector('legend'); question = txt(lg) || ''; }
    if (!question && (type === 'radio')) {
      const c = el.closest('[class*="field"], [class*="question"], div');
      if (c) question = txt(c.querySelector('label, legend, .label, [class*="label"]'));
    }
    el.setAttribute('data-jp-idx', String(i));
    out.push({ idx: i, type, tag: el.tagName.toLowerCase(), name: el.getAttribute('name') || '',
               desc: parts.join(' | ').toLowerCase(), question: question.toLowerCase(),
               value: el.tagName === 'SELECT' ? (el.selectedIndex > 0 && el.value ? el.value : '') : (el.value || ''), options: el.tagName === 'SELECT' ? [...el.options].map(o => o.text.trim()) : [],
               optionLabel: type === 'radio' ? parts.join(' ').toLowerCase() : '' });
    i++;
  }
  return out;
}
"""


def _value_for(key, profile):
    p = profile.get("personal", {})
    a = profile.get("answers", {})
    first, last = p.get("first_name", ""), p.get("last_name", "")
    table = {
        "first_name": first, "last_name": last, "full_name": f"{first} {last}".strip(),
        "email": p.get("email"), "phone": p.get("phone"), "linkedin": p.get("linkedin"),
        "github": p.get("github"), "portfolio": p.get("portfolio"), "city": p.get("city"),
        "state": p.get("state"), "zip": p.get("zip"), "country": p.get("country"),
        "address": p.get("address"), "current_company": p.get("current_company"),
        "current_title": p.get("current_title"), "salary": a.get("salary"),
        "start_date": a.get("start_date"), "how_heard": a.get("how_heard"),
        "cover_letter": profile.get("cover_letter"), "work_authorized": a.get("work_authorized"),
        "sponsorship": a.get("needs_sponsorship"), "relocate": a.get("willing_relocate"),
    }
    return (table.get(key) or "").strip()


def _match_key(text):
    for key, rx in RULES:
        if re.search(rx, text):
            return key
    return None


def _yes_no(value):
    v = value.lower()
    if v.startswith("y"):
        return "yes"
    if v.startswith("n"):
        return "no"
    return v


async def _get_context():
    global _pw, _ctx
    if _pw is None:
        _pw = await async_playwright().start()
    if _ctx is not None:
        try:
            await _ctx.new_page()  # raises if the browser window was closed
            pages = _ctx.pages
            await pages[-1].close()
            return _ctx
        except Exception:
            _ctx = None
    _ctx = await _pw.chromium.launch_persistent_context(
        str(BROWSER_DIR), headless=HEADLESS,
        viewport={"width": 1200, "height": 900} if HEADLESS else None,
        args=["--start-maximized"]
    )
    return _ctx


async def _fill_frame(frame, profile, resume_path, report):
    try:
        fields = await frame.evaluate(COLLECT_JS)
    except Exception:
        return
    handled_radio_groups = set()
    for f in fields:
        loc = frame.locator(f'[data-jp-idx="{f["idx"]}"]').first
        label = (f["question"] + " " + f["desc"]).strip()
        shown = (f["question"] or f["desc"].split("|")[0]).strip()[:70] or f["name"]
        try:
            if f["type"] == "file":
                if resume_path and re.search(r"resume|cv|curriculum", label) and "cover" not in label:
                    await loc.set_input_files(str(resume_path))
                    report["filled"].append("resume (file upload)")
                elif not resume_path and re.search(r"resume|cv", label):
                    report["skipped"].append(shown + " (profile has no resume)")
                continue
            if f["type"] == "checkbox":
                continue
            if f["type"] == "radio":
                if f["name"] in handled_radio_groups:
                    continue
                key = _match_key(f["question"] or f["desc"])
                want = _yes_no(_value_for(key, profile)) if key in ("work_authorized", "sponsorship", "relocate") else ""
                if not want:
                    continue
                handled_radio_groups.add(f["name"])
                for g in fields:
                    if g["type"] == "radio" and g["name"] == f["name"] and re.search(rf"\b{want}\b", g["optionLabel"]):
                        await frame.locator(f'[data-jp-idx="{g["idx"]}"]').first.check()
                        report["filled"].append(f"{shown} -> {want}")
                        break
                continue

            key = _match_key(label)
            if not key:
                if f["type"] not in ("file",) and not f["value"]:
                    report["skipped"].append(shown)
                continue
            value = _value_for(key, profile)
            if not value:
                report["skipped"].append(f"{shown} (profile has no {key.replace('_', ' ')})")
                continue
            if f["value"].strip():
                continue  # keep values already present on the page

            if f["tag"] == "select":
                target = _yes_no(value) if key in ("work_authorized", "sponsorship", "relocate") else value.lower()
                pick = next((o for o in f["options"] if o.lower() == target), None) or next(
                    (o for o in f["options"] if target and target in o.lower()), None)
                if pick:
                    await loc.select_option(label=pick)
                    report["filled"].append(f"{shown} -> {pick}")
                else:
                    report["skipped"].append(f"{shown} (no option matching '{value}')")
            else:
                await loc.fill(value)
                report["filled"].append(shown)
        except Exception as e:  # a single failing field should not abort the run
            report["skipped"].append(f"{shown} (error: {type(e).__name__})")


async def autofill(url, profile):
    resume_path = None
    if profile.get("resume_file"):
        cand = RESUME_DIR / profile["resume_file"]
        if cand.exists():
            resume_path = cand
    ctx = await _get_context()
    page = await ctx.new_page()
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(PAGE_SETTLE_MS)  # client-rendered forms appear after the initial load
    report = {"filled": [], "skipped": [], "url": url}
    for frame in page.frames:
        await _fill_frame(frame, profile, resume_path, report)
    await page.bring_to_front()
    report["filled"] = list(dict.fromkeys(report["filled"]))
    report["skipped"] = list(dict.fromkeys(report["skipped"]))
    return report
