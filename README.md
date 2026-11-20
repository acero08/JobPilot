# JobPilot

Local app: save profiles (resume + target job types + locations + common answers),
then open any application page and autofill it from the best-matching profile.
It fills the form and stops. **You review and click Submit.**

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

Logins persist in `backend/data/browser-profile`, so sign in to a job site once.
Data (profiles, resumes) lives in `backend/data/`. Nothing leaves your machine.

## Notes
- Gender/race/veteran/disability questions are deliberately never filled.
- Works best on Greenhouse, Lever, Ashby and similar plain forms; Workday multi-step flows will be partial.
- Matching lives in `backend/suggest.py`. Job feeds (Greenhouse/Lever/Ashby APIs) plug in there next.
