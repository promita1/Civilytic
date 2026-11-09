\# Civilytic



A privacy-first tool that helps people in Canada understand which government

programs they \*\*may\*\* qualify for, based on their household, immigration

status and province.



> \*\*Important:\*\* Civilytic provides general information based on official

> sources. It is not legal, immigration or tax advice. Always confirm

> eligibility on the linked official page.



\## Why it exists



Government benefits in Canada are spread across federal, provincial and

territorial sites, each with its own rules, and the rules change. Civilytic

brings them into one place and shows its sources.



\## How it works



Eligibility is decided by \*\*plain, testable code\*\*, not by an AI model.



\- \*\*Rules are data.\*\* Each program stores its conditions as structured rules

&#x20; (field, operator, value), plus a source link and a last-verified date.

\- \*\*Three-way results.\*\* Each rule is `met`, `not\_met` or `unknown` (missing

&#x20; information). A program is `may\_qualify`, `does\_not\_qualify` or `needs\_info`.

&#x20; The app never guesses: missing facts produce `needs\_info`.

\- \*\*Province-aware.\*\* A household is checked against federal programs plus its

&#x20; own province's programs. Adding a province means adding data, not code.

\- \*\*Household model.\*\* Each person has their own status, birth date and

&#x20; residence history.



\## Current features



\- Django REST API with PostgreSQL, running in Docker

\- Rules engine with unit tests

\- Federal, provincial and territorial jurisdictions

\- Old Age Security (OAS) pension rules, checked against the official page

\- Demo households (all fictional)

\- Authenticated API: users can only see their own households



\## Quick start



Requires Docker.



```

git clone <repository-url>

cd Civilytic

cp .env.example .env        # Windows (cmd): copy .env.example .env

docker compose up -d --build

docker compose exec web python manage.py migrate

docker compose exec web python manage.py load\_jurisdictions

docker compose exec web python manage.py load\_programs

docker compose exec web python manage.py load\_demo\_data

```



The `.env.example` values are for local use only. Never reuse them anywhere

public.



`load\_demo\_data` prints the IDs of the demo households. See the results for

one of them:



```

docker compose exec web python manage.py evaluate\_household <id>

```



\## Run the tests



```

docker compose exec web python manage.py test benefits

```



\## API



| Endpoint | Access | Description |

|---|---|---|

| `GET /api/programs/` | Public | List of programs with source links |

| `GET /api/households/<id>/results/` | Owner only | Eligibility results per person |



\## Data and verification



Every program links to its official source and carries a last-verified date.

Rules are checked by hand against the official page before they are added.

Not everything is covered yet, and the app says so instead of guessing.



\## Roadmap



\- \[ ] More federal and Alberta programs, then more provinces

\- \[ ] Household-level rules (child benefits, income thresholds)

\- \[ ] Document upload with OCR and AI field extraction

\- \[ ] Plain-language explanations and cited answers (retrieval + LLM)

\- \[ ] Scheduled checks for changes on official pages

\- \[ ] Web frontend

\- \[ ] Evaluation results (accuracy of extraction and answers)



\## Tech stack



Python, Django, Django REST Framework, PostgreSQL, Docker, WhiteNoise, Gunicorn.

