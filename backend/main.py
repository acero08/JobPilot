import re
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
import db
import security
import suggest
import uploads
from autofill import autofill

db.init()
app = FastAPI(title="JobPilot")
app.middleware("http")(security.guard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", security.TOKEN_HEADER],
)


class AutofillReq(BaseModel):
    url: str


@app.get("/api/profiles")
def list_profiles():
    return db.list_profiles()


# Fields only the server may set. Client values are dropped so a crafted
# profile cannot point resume_file at an arbitrary file on disk.
SERVER_FIELDS = ("resume_file", "resume_name")


def _client_fields(body):
    return {k: v for k, v in body.items() if k not in SERVER_FIELDS and k != "id"}


@app.post("/api/profiles")
def create_profile(body: dict):
    pid = db.create_profile(_client_fields(body))
    return db.get_profile(pid)


@app.put("/api/profiles/{pid}")
def update_profile(pid: int, body: dict):
    existing = db.get_profile(pid)
    if not existing:
        raise HTTPException(404, "Profile not found")
    data = _client_fields(body)
    data.update({k: existing[k] for k in SERVER_FIELDS if k in existing})
    db.update_profile(pid, data)
    return db.get_profile(pid)


@app.delete("/api/profiles/{pid}")
def delete_profile(pid: int):
    p = db.get_profile(pid)
    if p and (old := uploads.stored_path(p.get("resume_file"))):
        old.unlink(missing_ok=True)
    db.delete_profile(pid)
    return {"ok": True}


@app.post("/api/profiles/{pid}/resume")
async def upload_resume(pid: int, file: UploadFile = File(...)):
    p = db.get_profile(pid)
    if not p:
        raise HTTPException(404, "Profile not found")
    try:
        data = await uploads.read_limited(file)
        ext = uploads.validate(file.filename, data)
    except uploads.UploadError as e:
        raise HTTPException(e.status, e.detail)
    if old := uploads.stored_path(p.get("resume_file")):
        old.unlink(missing_ok=True)
    p["resume_file"] = uploads.store(ext, data)
    p["resume_name"] = uploads.display_name(file.filename)
    db.update_profile(pid, p)
    return db.get_profile(pid)


@app.post("/api/profiles/{pid}/autofill")
async def run_autofill(pid: int, req: AutofillReq):
    p = db.get_profile(pid)
    if not p:
        raise HTTPException(404, "Profile not found")
    if not re.match(r"^https?://", req.url):
        raise HTTPException(400, "URL must start with http:// or https://")
    try:
        return await autofill(req.url, p)
    except Exception as e:
        raise HTTPException(500, f"Autofill failed: {e}")


@app.get("/api/suggest")
def suggest_profile(title: str = "", location: str = "", remote: bool = False):
    return suggest.rank(db.list_profiles(), title, location, remote)


# Serve the production UI build when it exists.
# The token is embedded in index.html as a meta tag. Only same-origin pages can
# read this response, and the Host check blocks rebinding, so other sites never see it.
dist = Path(__file__).parent.parent / "frontend" / "dist"
if dist.exists():
    @app.get("/", include_in_schema=False)
    def index():
        html = (dist / "index.html").read_text()
        meta = f'<meta name="jobpilot-token" content="{security.API_TOKEN}">'
        return HTMLResponse(html.replace("</head>", meta + "</head>", 1),
                            headers={"Cache-Control": "no-store"})

    app.mount("/", StaticFiles(directory=dist), name="ui")


if __name__ == "__main__":
    import uvicorn

    config.check_bind_host(config.HOST)
    uvicorn.run(app, host=config.HOST, port=config.PORT)
