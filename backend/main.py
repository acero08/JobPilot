import re
import uuid
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
from autofill import autofill
from db import RESUME_DIR

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


@app.post("/api/profiles")
def create_profile(body: dict):
    pid = db.create_profile(body)
    return db.get_profile(pid)


@app.put("/api/profiles/{pid}")
def update_profile(pid: int, body: dict):
    if not db.get_profile(pid):
        raise HTTPException(404, "Profile not found")
    db.update_profile(pid, body)
    return db.get_profile(pid)


@app.delete("/api/profiles/{pid}")
def delete_profile(pid: int):
    db.delete_profile(pid)
    return {"ok": True}


@app.post("/api/profiles/{pid}/resume")
async def upload_resume(pid: int, file: UploadFile = File(...)):
    p = db.get_profile(pid)
    if not p:
        raise HTTPException(404, "Profile not found")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".pdf", ".doc", ".docx"):
        raise HTTPException(400, "Resume must be PDF, DOC or DOCX")
    stored = f"{uuid.uuid4().hex}{ext}"
    (RESUME_DIR / stored).write_bytes(await file.read())
    old = p.get("resume_file")
    if old:
        (RESUME_DIR / old).unlink(missing_ok=True)
    p["resume_file"] = stored
    p["resume_name"] = re.sub(r"[^\w.\- ]", "_", file.filename or stored)
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
