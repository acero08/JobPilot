# JobPilot

A local app for job applications. Save profiles (resume, target job types,
locations and common answers), then open an application page and fill it from
the best-matching profile. JobPilot fills the form and stops: it never submits
an application. Submission is always a manual step.

## Setup (once)
```
cd backend
cp .env.example .env
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
Open http://localhost:8000 (host/port come from `backend/.env`). (For UI development: `npm run dev` in frontend, opens on :5173.)

## Configuration
Settings live in `backend/.env` and `frontend/.env` (never committed). See the `.env.example` files for every option.

## Workflow
1. Create profiles, e.g. "SWE – San Diego", "Data Analyst – Remote". Upload a resume to each.
2. Find a job yourself, copy the application URL.
3. Enter title + location, click "Suggest best profile" (or pick one), paste URL, "Open & autofill".
4. A Chrome window opens, fills the form and uploads the resume. Fix anything listed under "Needs you", then submit.

Sign-ins persist in `backend/data/browser-profile`, so each job site needs a login only once.
Profiles and resumes are stored in `backend/data/` and are sent only to the job sites you open for autofill.

## Notes
- Gender/race/veteran/disability questions are deliberately never filled.
- Works best on Greenhouse, Lever, Ashby and similar single-page forms; multi-step flows such as Workday are filled only partially.
- Profile matching is implemented in `backend/suggest.py`.
