# JobPilot

JobPilot fills out job applications for you. You keep a few profiles (resume,
the kinds of jobs you're after, locations, answers to the usual questions),
paste an application link, and it fills in the form from the profile that fits
best. It doesn't submit anything. You look it over and hit submit yourself.

Everything runs on your own computer.

## Setup

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

## Running it

```
cd backend
python main.py
```

Then open http://localhost:8000.

If you're working on the UI, run `npm run dev` in `frontend/` while the backend
is running and use http://localhost:5173 instead.

## How to use it

1. Make a profile for each kind of job you apply to, like "Software Engineer –
   Springfield" or "Data Analyst – Remote", and upload a resume to each one.
2. Find a job and copy the link to its application page.
3. Type in the job title and location and click "Suggest best profile", or just
   pick one.
4. Paste the link and click "Open & autofill".
5. A browser window opens and fills in what it can. Anything it couldn't fill
   shows up under "Needs you". Finish those and submit.

The browser remembers your logins, so you only sign in to each job site once.

## What it won't do

- Submit an application. That's always up to you, and it should stay that way.
- Answer gender, race, veteran or disability questions.
- Fill in hidden fields or password fields.
- Fill forms embedded from other sites, unless they come from a known job
  application system like Greenhouse, Lever, Ashby or Workday. The full list is
  `ATS_DOMAINS` in `backend/config.py`.

The panel shows which site got your info. If the link isn't from a known job
application system, you get a warning first, but you can still go ahead.

## Settings

Settings go in `backend/.env` and `frontend/.env`. The `.env.example` files
show every option.

## Where your data lives

Profiles, resumes, browser logins and the API token are all in `backend/data/`.
Your info only goes to the job sites you autofill.

## API token

The backend only accepts requests that include its token in an
`X-JobPilot-Token` header. It creates a random token the first time it runs and
saves it to `backend/data/api-token`. Other websites open in your browser can't
use the API this way.

- With the built UI, the backend puts the token in the page and the UI sends it.
- With `npm run dev`, Vite reads the token file and adds the header. If you
  move the data folder, set `VITE_TOKEN_FILE` in `frontend/.env`.

To get a new token, stop the backend, delete `backend/data/api-token` and start
it again.

## Tests

```
cd backend
pip install -r requirements-dev.txt
python -m pytest
```

## Notes

- Works best on Greenhouse, Lever, Ashby and other single-page forms. Workday
  and other multi-step forms only get partly filled.
- Profile matching is in `backend/suggest.py`.
- See [SECURITY.md](SECURITY.md) for more on security.
