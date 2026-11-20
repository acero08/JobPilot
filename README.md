# JobPilot

A local app for job applications. Save profiles (resume, target job types,
locations and common answers), then open an application page and fill it from
the best-matching profile. JobPilot fills the form and stops: it never submits
an application. Submission is always a manual step.

## Setup (once)
```
cd backend
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
cd ../frontend
cp .env.example .env
npm install
npm run build
```

## Run
```
cd backend
python main.py
```
Open http://localhost:8000. Host and port come from `backend/.env`; the server
listens on loopback only.

For UI development, keep the backend running and start Vite in `frontend/`:
```
npm run dev
```
This serves the UI on http://localhost:5173 and proxies `/api` to the backend.

## Configuration
Settings live in `backend/.env` and `frontend/.env`, which are never committed.
The `.env.example` files list every option with safe defaults.

## API token
Every `/api` request must include an `X-JobPilot-Token` header. The backend
creates a random token in `backend/data/api-token` (mode 600) on first run.

- **Production build:** the backend inserts the token into `index.html` as a
  `<meta name="jobpilot-token">` tag, and the UI sends it with each request.
- **Development:** the Vite proxy reads the token file and adds the header to
  proxied requests. Set `VITE_TOKEN_FILE` if the backend data directory moves.

To rotate the token, stop the backend, delete `backend/data/api-token` and
start it again.

## Tests
```
cd backend
pip install -r requirements-dev.txt
python -m pytest
```

## Workflow
1. Create profiles, e.g. "Software Engineer – Springfield", "Data Analyst – Remote". Upload a resume to each.
2. Find a job yourself, copy the application URL.
3. Enter title + location, click "Suggest best profile" (or pick one), paste URL, "Open & autofill".
4. A Chrome window opens, fills the form and uploads the resume. Fix anything listed under "Needs you", then submit.

Sign-ins persist in `backend/data/browser-profile`, so each job site needs a login only once.
Profiles and resumes are stored in `backend/data/` and are sent only to the job sites you open for autofill.

## Safety conventions
- **No automatic submission.** JobPilot fills fields and stops. Submitting an
  application is always a manual action, and changes must not add auto-submit.
- The panel shows the host that received the data. URLs outside the known
  applicant tracking systems (`ATS_DOMAINS` in `backend/config.py`) show a
  warning first; autofill is still allowed.
- Embedded frames are filled only when they are same-origin with the page or
  hosted by a known applicant tracking system. Other frames are listed as skipped.
- Hidden, invisible and password fields are never filled.
- Gender, race, veteran and disability questions are never filled.

See [SECURITY.md](SECURITY.md) for the threat model.

## Notes
- Works best on Greenhouse, Lever, Ashby and similar single-page forms; multi-step flows such as Workday are filled only partially.
- Profile matching is implemented in `backend/suggest.py`.
