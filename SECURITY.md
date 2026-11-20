# Security

## Threat model

JobPilot is a single-user application that runs on the user's own computer.
The backend listens on `127.0.0.1` only and serves nobody else. The main risks
are other websites open in the same browser and other local processes, so the
API is protected as follows:

- **Loopback only.** The server refuses to bind to a non-loopback address
  unless `JOBPILOT_ALLOW_NON_LOOPBACK=1` is set.
- **Host header check.** Requests whose `Host` is not `localhost` or
  `127.0.0.1` are rejected, which blocks DNS rebinding.
- **Origin check and strict CORS.** Only the local UI origins may call the API.
  Cross-site requests are rejected even when they would not need a preflight.
- **Per-install API token.** Every `/api` request must carry an
  `X-JobPilot-Token` header. The token is created on first run, stored in
  `data/api-token` with mode 600, and compared in constant time. The production
  UI receives it in a meta tag in `index.html`; in development the Vite proxy
  adds the header.
- **Uploads.** Resumes must be PDF, DOC or DOCX by both extension and file
  signature, are limited in size (`JOBPILOT_MAX_UPLOAD_MB`), and are stored
  under random names chosen by the server. Client filenames are used only as labels.
- **Autofill scope.** Profile data is entered only into the top-level page and
  into frames that are same-origin with it or hosted by a known applicant
  tracking system. Hidden, invisible and password fields are never filled, and
  JobPilot never submits a form.

Out of scope: protecting data from malware or other users with administrator
access to the same machine, and the security of the job sites themselves.

## Data stored locally

All user data lives under `backend/data/` (configurable with
`JOBPILOT_DATA_DIR`) and is excluded from version control:

| Path | Contents |
| --- | --- |
| `jobpilot.db` | Profiles: contact details, answers, cover letter text |
| `resumes/` | Uploaded resume files |
| `browser-profile/` | Chromium profile, including job-site sessions and cookies |
| `api-token` | The per-install API token |

Profile data leaves the machine only when it is entered into a job application
page that the user opened for autofill.

## Repository rules

No secrets, credentials, tokens, `.env` files or personal data belong in this
repository. Tests and examples use placeholder data such as `Jane Doe` and
`jane@example.com`. A gitleaks pre-commit hook and CI job scan for secrets.

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub's
**Security → Report a vulnerability** form on this repository rather than in a
public issue. Include steps to reproduce and the affected version or commit.
