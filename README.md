# WES350 — Multilingual Verb Conjugation Trainers

[![Render deployment](https://img.shields.io/badge/Deployment-Render-00c7b7)](https://languages-learning-webservice.onrender.com/)
[![WES350 QA](https://github.com/Yevguen/wes350-language-trainers/actions/workflows/qa.yml/badge.svg)](https://github.com/Yevguen/wes350-language-trainers/actions/workflows/qa.yml)

WES350 is a Python web application for practicing English, Spanish, and French verb forms. Its four NiceGUI trainers are public and free to use without registration, login, payment, or an access grant. Public registration is closed; the only account is the site administrator, who uses it for protected user administration.

Try the **[live application on Render](https://languages-learning-webservice.onrender.com/)**. Production persistence uses Neon PostgreSQL through `DATABASE_URL`.

## Four trainers

| Trainer | Practice | Public route |
| --- | --- | --- |
| ES350 | Spanish present indicative | [`/es/presind`](https://languages-learning-webservice.onrender.com/es/presind) |
| ES200 | Spanish preterite | [`/es/preterite`](https://languages-learning-webservice.onrender.com/es/preterite) |
| FR200 | French present indicative, focused on difficult and irregular forms | [`/fr/presind`](https://languages-learning-webservice.onrender.com/fr/presind) |
| EN200 | English irregular verbs: past simple and past participle | [`/en/irrvbs`](https://languages-learning-webservice.onrender.com/en/irrvbs) |

Each trainer provides a searchable verb selector with translations, answer inputs, submitted-answer scoring, corrections, and a reset action. Runtime dictionaries live under [`y_data/`](y_data/); [`dict_converter/`](dict_converter/) contains conversion and validation utilities plus generated data used during dataset preparation.

The verb lists and conjugation data in this repository are original project data composed by the author.

## Architecture and stack

| Area | Implementation |
| --- | --- |
| Web UI | NiceGUI `2.17.0` mounted on the FastAPI application in `main.py` |
| Authentication | FastAPI Users `14.0.1`, secure cookie transport, and JWT strategy |
| Persistence | Async SQLAlchemy; `asyncpg` for PostgreSQL and `aiosqlite` locally |
| Production | Render web service with Neon PostgreSQL supplied through `DATABASE_URL` |
| Schema history | Alembic configuration and migrations under `alembic/` |
| QA | Python 3.12, pytest `>=8,<9`, and GitHub Actions |

`main.py` mounts the public trainer pages, the administrator login page, the login/logout routers, and the NiceGUI application. `db.py` defines the `User`, `Access`, `Quiz`, and `Score` models and the async session infrastructure. The active trainer handlers display per-exercise feedback; they do not currently persist quiz results to `Quiz` or `Score`.

The historical `Access` model and helpers remain for schema compatibility, but no plan or grant lookup controls the four public trainer routes. The `/purchase` compatibility page explains that the trainers are free and that registration is closed.

## Security design

- `SECRET` is required for JWT signing; no application secret is stored in the repository.
- Authentication uses a Secure, `SameSite=lax` cookie and a 14-day JWT lifetime.
- Passwords are hashed through Passlib, using Argon2 by default with bcrypt support.
- Public registration is switched off: no route creates accounts, and `/register` shows a closed notice. Only the administrator can create users, from `/admin`.
- `/admin` requires an authenticated active superuser.
- Administration prevents self-deletion, self-demotion, self-deactivation, and removal or demotion of the last active administrator.
- Login form values are JSON-serialized before use in browser JavaScript.
- SQLAlchemy statement echo is disabled to avoid exposing query parameters in logs.
- Startup admin provisioning runs only when both `ADMIN_EMAIL` and `ADMIN_PASSWORD` are supplied by the environment.

## Deployment configuration

[`render.yaml`](render.yaml) declares a Python web service and runs:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1 --no-access-log
```

Production configuration is supplied outside the repository:

| Variable | Purpose |
| --- | --- |
| `SECRET` | Required JWT signing secret |
| `DATABASE_URL` | PostgreSQL or local SQLite connection URL |
| `ADMIN_EMAIL` | Optional startup administrator email |
| `ADMIN_PASSWORD` | Optional startup administrator password |

Local dotenv files and database files are excluded by [`.gitignore`](.gitignore).

## Tests and continuous integration

The suite contains **49 test cases**. [`.github/workflows/qa.yml`](.github/workflows/qa.yml) runs on pushes and pull requests to `main`, installs the application and development dependencies, compiles every tracked Python file, and executes pytest on Python 3.12.

Run the same checks locally from the repository root:

```bash
python -m compileall -q .
python -m pytest -v
```

Coverage includes password hashing, historical access helpers, dataset invariants, closed registration (no sign-up form, link or endpoint, with administrator login still working), the privacy notice (page, links from every public page, and no access log in the start command), anonymous trainer access, administrator authorization and lifecycle safeguards, login-value serialization, and disabled SQL logging.

The page tests exercise real handler bodies with NiceGUI elements in isolation. They do not provide browser end-to-end coverage, full application authentication against PostgreSQL, deployment verification, payment testing, or exhaustive linguistic validation of every conjugated form. See the migration limitation below before applying the historical migrations to a new database.

## Local setup

Use Python 3.12:

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS or Linux
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
```

Create an untracked `.env` with your own values. This example selects an isolated local SQLite database:

```dotenv
SECRET=replace-with-a-random-local-secret
DATABASE_URL=sqlite+aiosqlite:///./local.db
```

Optionally add `ADMIN_EMAIL` and `ADMIN_PASSWORD` for local administrator provisioning. Then create tables from the current SQLAlchemy models and start the application:

```bash
python db.py
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. Authentication uses a Secure cookie, so authenticated loopback behavior depends on the browser's handling of Secure cookies on local connections.

## Known migration limitation

The historical Alembic chain is not a verified clean-database bootstrap and should not be applied to production without repair and from-zero validation. Static inspection identifies contradictory assumptions in the PostgreSQL revisions:

- `05cfd0319c1b` creates `access.id` as an integer primary key and includes `expires_at`.
- `4c823c60d32f` and `586a555f3122` later assign a UUID default without first converting the integer column.
- `49d9f2dfd935` attempts to add `expires_at` again.
- The chain uses PostgreSQL-specific `pgcrypto` and raw SQL and is not a portable SQLite migration sequence.

Migration execution from a clean PostgreSQL database is not covered by the current CI suite.

## Repository map

| Path | Purpose |
| --- | --- |
| `main.py` | FastAPI app, NiceGUI mounting, navigation, administrator login UI, and auth router wiring |
| `en200_irrvbs.py`, `es200_preterite.py`, `es350_presind.py`, `fr200_presind.py` | Active trainer pages and scoring handlers |
| `auth.py`, `password.py` | Authentication and password helpers |
| `admin_page.py` | Protected user administration |
| `access_utils.py` | Historical access helpers retained for compatibility |
| `db.py`, `alembic/`, `alembic.ini` | Models, sessions, startup admin provisioning, and migrations |
| `y_data/` | Runtime language and conjugation datasets |
| `dict_converter/` | Dataset conversion and validation utilities |
| `pages/purchase_page.py` | Compatibility page describing free access and closed registration |
| `pages/privacy_page.py` | Privacy notice in English and Spanish at `/privacy` |
| `tests/`, `pytest.ini`, `.github/workflows/qa.yml` | Automated tests and CI |
| `render.yaml`, `requirements*.txt` | Deployment declaration and dependencies |

## Copyright and use

Copyright © 2026 Yevhen Babko. All rights reserved. This repository is available for portfolio review and technical evaluation; no open-source license is granted. See [`NOTICE.md`](NOTICE.md).

