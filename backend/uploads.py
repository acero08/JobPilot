"""Resume upload validation and storage.

Stored files are named by the server. The client-supplied filename is used only
as a display label, so it can never influence where a file is written.
"""
import re
import uuid

from config import MAX_UPLOAD_BYTES
from db import RESUME_DIR

# Each allowed extension must start with the matching file signature, so a
# renamed executable or HTML file is not accepted as a resume.
SIGNATURES = {
    ".pdf": [b"%PDF-"],
    ".doc": [bytes.fromhex("D0CF11E0A1B11AE1")],  # OLE compound document
    ".docx": [b"PK\x03\x04"],  # ZIP container (Office Open XML)
}
STORED_NAME = re.compile(r"^[0-9a-f]{32}\.(pdf|doc|docx)$")
CHUNK = 1024 * 1024


class UploadError(ValueError):
    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def extension_of(filename):
    # Only the final path component counts, whichever separator the client used.
    base = re.split(r"[\\/]", filename or "")[-1]
    dot = base.rfind(".")
    return base[dot:].lower() if dot > 0 else ""


def display_name(filename):
    base = re.split(r"[\\/]", filename or "")[-1]
    return re.sub(r"[^\w.\- ]", "_", base)[:120] or "resume"


async def read_limited(upload):
    data = bytearray()
    while chunk := await upload.read(CHUNK):
        data += chunk
        if len(data) > MAX_UPLOAD_BYTES:
            raise UploadError(413, f"Resume is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")
    return bytes(data)


def validate(filename, data):
    ext = extension_of(filename)
    if ext not in SIGNATURES:
        raise UploadError(400, "Resume must be PDF, DOC or DOCX")
    if not any(data.startswith(sig) for sig in SIGNATURES[ext]):
        raise UploadError(400, f"File content does not look like a {ext[1:].upper()} document")
    return ext


def store(ext, data):
    name = f"{uuid.uuid4().hex}{ext}"
    (RESUME_DIR / name).write_bytes(data)
    return name


def stored_path(name):
    """Resolve a stored resume name, or None if it is not one the server created."""
    if not isinstance(name, str) or not STORED_NAME.match(name):
        return None
    return RESUME_DIR / name
