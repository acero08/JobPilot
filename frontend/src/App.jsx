import { useEffect, useState } from "react";
import { api } from "./api";

const blank = () => ({
  name: "New profile", job_types: [], locations: [], keywords: [], accepts_remote: true,
  personal: { first_name: "", last_name: "", email: "", phone: "", address: "", city: "", state: "", zip: "", country: "United States", linkedin: "", github: "", portfolio: "", current_company: "", current_title: "" },
  answers: { work_authorized: "Yes", needs_sponsorship: "No", willing_relocate: "Yes", salary: "", start_date: "", how_heard: "" },
  cover_letter: "",
});

const csv = (a) => (a || []).join(", ");
const unCsv = (s) => s.split(",").map((x) => x.trim()).filter(Boolean);

function Field({ label, value, onChange, wide, area }) {
  const Tag = area ? "textarea" : "input";
  return (
    <label className={"field" + (wide ? " wide" : "")}>
      <span>{label}</span>
      <Tag value={value || ""} onChange={(e) => onChange(e.target.value)} rows={area ? 6 : undefined} />
    </label>
  );
}

function YesNo({ label, value, onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option>Yes</option><option>No</option>
      </select>
    </label>
  );
}

function Editor({ profile, onSaved, onDeleted }) {
  const [p, setP] = useState(profile);
  const [msg, setMsg] = useState("");
  useEffect(() => { setP(profile); setMsg(""); }, [profile.id]);
  const set = (k, v) => setP({ ...p, [k]: v });
  const sub = (g, k, v) => setP({ ...p, [g]: { ...p[g], [k]: v } });

  const save = async () => { const s = await api.save(p.id, p); setP(s); onSaved(s); setMsg("Saved"); };
  const upload = async (e) => {
    const f = e.target.files[0]; if (!f) return;
    await save();
    const s = await api.upload(p.id, f); setP(s); onSaved(s); setMsg("Resume uploaded");
  };

  return (
    <div className="editor">
      <div className="row">
        <Field label="Profile name" value={p.name} onChange={(v) => set("name", v)} />
        <button className="danger" onClick={async () => { if (confirm("Delete this profile?")) { await api.remove(p.id); onDeleted(p.id); } }}>Delete</button>
      </div>

      <h3>Targeting</h3>
      <div className="grid">
        <Field label="Job types (comma separated)" value={csv(p.job_types)} onChange={(v) => set("job_types", unCsv(v))} />
        <Field label="Locations (comma separated)" value={csv(p.locations)} onChange={(v) => set("locations", unCsv(v))} />
        <Field label="Extra keywords" value={csv(p.keywords)} onChange={(v) => set("keywords", unCsv(v))} />
        <label className="field"><span>Remote roles</span>
          <select value={p.accepts_remote ? "Yes" : "No"} onChange={(e) => set("accepts_remote", e.target.value === "Yes")}><option>Yes</option><option>No</option></select>
        </label>
      </div>

      <h3>Resume</h3>
      <div className="row">
        <span>{p.resume_name ? `📄 ${p.resume_name}` : "No resume uploaded yet"}</span>
        <input type="file" accept=".pdf,.doc,.docx" onChange={upload} />
      </div>

      <h3>Personal info</h3>
      <div className="grid">
        {Object.keys(p.personal).map((k) => (
          <Field key={k} label={k.replace(/_/g, " ")} value={p.personal[k]} onChange={(v) => sub("personal", k, v)} />
        ))}
      </div>

      <h3>Common answers</h3>
      <div className="grid">
        <YesNo label="Authorized to work" value={p.answers.work_authorized} onChange={(v) => sub("answers", "work_authorized", v)} />
        <YesNo label="Needs sponsorship" value={p.answers.needs_sponsorship} onChange={(v) => sub("answers", "needs_sponsorship", v)} />
        <YesNo label="Willing to relocate" value={p.answers.willing_relocate} onChange={(v) => sub("answers", "willing_relocate", v)} />
        <Field label="Salary expectation" value={p.answers.salary} onChange={(v) => sub("answers", "salary", v)} />
        <Field label="Start date" value={p.answers.start_date} onChange={(v) => sub("answers", "start_date", v)} />
        <Field label="How did you hear about us" value={p.answers.how_heard} onChange={(v) => sub("answers", "how_heard", v)} />
      </div>

      <h3>Cover letter</h3>
      <Field label="Template text" area wide value={p.cover_letter} onChange={(v) => set("cover_letter", v)} />

      <div className="row"><button className="primary" onClick={save}>Save profile</button><span className="ok">{msg}</span></div>
    </div>
  );
}

function AutofillPanel({ profiles, selectedId }) {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [loc, setLoc] = useState("");
  const [remote, setRemote] = useState(false);
  const [ranked, setRanked] = useState([]);
  const [pid, setPid] = useState(selectedId);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => { if (selectedId) setPid(selectedId); }, [selectedId]);

  const suggest = async () => {
    const r = await api.suggest(title, loc, remote); setRanked(r);
    if (r.length && r[0].score > 0) setPid(r[0].id);
  };
  const run = async () => {
    setBusy(true); setErr(""); setReport(null);
    try { setReport(await api.autofill(pid, url)); } catch (e) { setErr(e.message); }
    setBusy(false);
  };

  return (
    <div className="panel">
      <h2>Autofill a job</h2>
      <div className="grid">
        <Field label="Job title" value={title} onChange={setTitle} />
        <Field label="Job location" value={loc} onChange={setLoc} />
      </div>
      <div className="row">
        <label><input type="checkbox" checked={remote} onChange={(e) => setRemote(e.target.checked)} /> Remote</label>
        <button onClick={suggest}>Suggest best profile</button>
      </div>
      {ranked.length > 0 && (
        <ul className="ranked">
          {ranked.map((r) => (
            <li key={r.id} className={r.id === pid ? "sel" : ""} onClick={() => setPid(r.id)}>
              <b>{r.name}</b> · score {r.score} <small>{r.reasons.join("; ")}</small>
            </li>
          ))}
        </ul>
      )}
      <label className="field wide"><span>Profile to use</span>
        <select value={pid || ""} onChange={(e) => setPid(Number(e.target.value))}>
          <option value="">Select…</option>
          {profiles.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </label>
      <Field label="Application page URL" wide value={url} onChange={setUrl} />
      <button className="primary" disabled={!pid || !url || busy} onClick={run}>{busy ? "Filling…" : "Open & autofill"}</button>
      <p className="hint">A browser window opens, fills what it can and stops. You review and click Submit yourself.</p>
      {err && <p className="err">{err}</p>}
      {report && (
        <div className="report">
          <b>Filled ({report.filled.length})</b>
          <ul>{report.filled.map((x, i) => <li key={i}>✓ {x}</li>)}</ul>
          <b>Needs you ({report.skipped.length})</b>
          <ul>{report.skipped.map((x, i) => <li key={i}>• {x}</li>)}</ul>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [profiles, setProfiles] = useState([]);
  const [sel, setSel] = useState(null);
  const load = async () => { const l = await api.list(); setProfiles(l); return l; };
  useEffect(() => { load().then((l) => l[0] && setSel(l[0].id)); }, []);
  const current = profiles.find((p) => p.id === sel);

  const add = async () => { const p = await api.create(blank()); await load(); setSel(p.id); };
  const dup = async () => { const { id, resume_file, resume_name, ...rest } = current; const p = await api.create({ ...rest, name: rest.name + " (copy)" }); await load(); setSel(p.id); };

  return (
    <div className="app">
      <aside>
        <h1>JobPilot</h1>
        {profiles.map((p) => (
          <div key={p.id} className={"item" + (p.id === sel ? " active" : "")} onClick={() => setSel(p.id)}>
            <b>{p.name}</b>
            <small>{csv(p.job_types) || "no job types"} · {csv(p.locations) || "no locations"}</small>
          </div>
        ))}
        <button onClick={add}>+ New profile</button>
        {current && <button onClick={dup}>Duplicate selected</button>}
      </aside>
      <main>
        {current ? <Editor profile={current} onSaved={load} onDeleted={async () => { const l = await load(); setSel(l[0]?.id ?? null); }} /> : <p>Create your first profile to get started.</p>}
      </main>
      <section><AutofillPanel profiles={profiles} selectedId={sel} /></section>
    </div>
  );
}
