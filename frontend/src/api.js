async function req(path, opts = {}) {
  const r = await fetch("/api" + path, opts);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
}
const json = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
export const api = {
  list: () => req("/profiles"),
  create: (p) => req("/profiles", json("POST", p)),
  save: (id, p) => req(`/profiles/${id}`, json("PUT", p)),
  remove: (id) => req(`/profiles/${id}`, { method: "DELETE" }),
  upload: (id, file) => { const f = new FormData(); f.append("file", file); return req(`/profiles/${id}/resume`, { method: "POST", body: f }); },
  autofill: (id, url) => req(`/profiles/${id}/autofill`, json("POST", { url })),
  suggest: (title, location, remote) => req(`/suggest?title=${encodeURIComponent(title)}&location=${encodeURIComponent(location)}&remote=${remote}`),
};
