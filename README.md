# 🍯 HoneyChain

**Blockchain-based honey traceability & smart beekeeping management**
Smart India Hackathon 2026 · Problem Statement **SIH26021** · Ministry of MSME · Theme: *Smart Automation*

HoneyChain gives every jar of honey a tamper-proof, QR-scannable history. Each
step of a batch's journey — harvest → extraction → lab test → processing →
packaging → warehouse → transit → retail → sold — is stored as a **SHA-256
hash-linked block**. Change any past record and the chain visibly breaks, so
provenance and purity become verifiable by anyone.

---

## ✨ What's inside

| Area | Details |
|------|---------|
| **Landing page** | Animated hero, problem/solution, features, how-it-works (GSAP + ScrollTrigger) |
| **Trace a jar** | Enter/scan a batch code → full provenance timeline + live chain verification |
| **Chain explorer** | Block-explorer view: indices, nonces, previous-hash → hash links |
| **Producer dashboard** | Manage beekeepers, hives, batches; append mined events to any chain |
| **JSON API** | `GET /api/batch/<code>/` returns the verified chain for scanners/partners |
| **Admin** | Django admin at `/admin/` |

## 🧱 Tech stack

- **Backend:** Django 6 (Python) with **Jinja2** as the template engine
- **Frontend:** HTML + CSS + vanilla JS, **GSAP** (animation), **Lucide** (icons) + **QRCode.js** (via CDN)
- **"Blockchain":** a real per-batch hash-linked ledger with proof-of-work mining
  (`core/blockchain.py`) — see the note on scope below
- **Hosting:** Vercel serverless (Python runtime), static served by WhiteNoise

---

## 🚀 Run locally

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

python manage.py migrate
python manage.py seed            # loads demo beekeepers, hives, batches + chains
python manage.py runserver
```

Open http://127.0.0.1:8000/ . Try tracing **HNY-2026-0001**.

Optional admin login:

```bash
python manage.py createsuperuser
```

---

## ▲ Deploy to Vercel

This repo is preconfigured for Vercel (`vercel.json`). The seeded `db.sqlite3`
is committed so the demo has data on first load.

1. Push this folder to a GitHub repository.
2. On [vercel.com](https://vercel.com) → **Add New → Project** → import the repo.
3. Framework preset: **Other** (the included `vercel.json` handles everything).
4. Add environment variables (Project → Settings → Environment Variables):
   - `DJANGO_SECRET_KEY` → any long random string
   - `DJANGO_DEBUG` → `0`
5. **Deploy.**

> **Python version:** Django 6 needs Python **3.12+**. Vercel's default Python
> runtime (3.12) works. `.python-version` pins it. If your Vercel project is
> stuck on an older Python, either enable 3.12 in project settings or change
> `requirements.txt` to `Django==5.2.*`.

### Database on Vercel (important)

Vercel's filesystem is **read-only** except `/tmp`, which does **not persist**
between cold starts. On boot the app copies the committed `db.sqlite3` to
`/tmp` so the demo is fully browsable and writes work *within a warm instance* —
but new batches/events won't survive a cold start. That's fine for a demo.

**For real persistence**, use an external Postgres (free tiers: Neon, Supabase):

```python
# honeychain/settings.py  → replace the DATABASES block
import dj_database_url  # add dj-database-url + psycopg to requirements.txt
DATABASES = {"default": dj_database_url.config(conn_max_age=600)}
```

then set `DATABASE_URL` in Vercel and run `migrate`/`seed` against it once.

---

## 🔒 Security notes (read before going public)

- The **producer dashboard and data-entry forms have no authentication** so the
  prototype is easy to demo. Before any real deployment, put `/dashboard/`,
  `/batches/new/`, `/hives/new/` and `/batch/<code>/add-event/` behind
  `django.contrib.auth` (login-required), since they create/mutate ledger data.
- Set a real `DJANGO_SECRET_KEY` and keep `DJANGO_DEBUG=0` in production.
- Tighten `DJANGO_ALLOWED_HOSTS` to your domain.

## 📐 Scope / honesty note

This is a hackathon **prototype**. The ledger is a genuine cryptographic
hash-chain with proof-of-work — it demonstrates immutability and tamper
detection — but it is **not** a distributed, multi-node consensus network. The
architecture maps cleanly onto Hyperledger Fabric / Ethereum for a production
build; the data model (batches as assets, events as transactions) is designed
with that migration in mind.

---

## 🗂 Project structure

```
honeychain/        Django project (settings, urls, wsgi, jinja2env)
core/              App: models, views, forms, admin, blockchain.py, seed command
templates/         Jinja2 templates (base, index, verify, trace, dashboard, ...)
static/            css/style.css, js/main.js
vercel.json        Vercel serverless config
requirements.txt   Python dependencies
```

## 🔗 Key routes

| Route | Purpose |
|-------|---------|
| `/` | Landing page |
| `/verify/` | Trace-a-jar search |
| `/trace/<code>/` | Consumer provenance view |
| `/batch/<code>/` | Raw chain explorer |
| `/dashboard/` | Producer dashboard |
| `/batch/<code>/add-event/` | Append a mined block |
| `/api/batch/<code>/` | JSON chain + verification |
| `/admin/` | Django admin |
