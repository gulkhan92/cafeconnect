# Deployment Guide

This documents how to deploy CafeConnect to free-tier hosting, per the
project plan. **No deployment has actually been performed** — that requires
accounts and credentials on third-party platforms that only the project owner
has, and creating/configuring those accounts is not something to do without
the owner directly involved. Everything below is the exact, ready-to-run
procedure; the Dockerfile, migrations, and env var contract are already in
place and tested locally.

## Recommended platforms (all free-tier)

| Component | Platform | Why |
|---|---|---|
| Backend (FastAPI) | Render or Railway | Free tier, Docker-native, env vars in dashboard |
| Database (Postgres + pgvector) | Supabase or Neon | Free tier includes the pgvector extension |
| Redis | Upstash | Free tier, serverless-friendly, works from Render/Railway |
| Frontend (static build) | Vercel or Netlify | Free tier, automatic HTTPS, git-push deploys |

## 1. Database (Supabase or Neon)

1. Create a free Postgres project.
2. Enable the `pgvector` extension (Supabase: Database → Extensions → `vector`;
   Neon: `CREATE EXTENSION vector;` in the SQL editor — Alembic's own
   migration also does this automatically on first run, so this step is a
   fallback if the platform disables extension creation via migration).
3. Copy the connection string and convert it to the async driver form:
   `postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DBNAME`
   (Supabase/Neon give you the `postgresql://` form — just swap the scheme.)
4. Run migrations against it once, from your machine, before the backend's
   first deploy:
   ```bash
   cd backend
   DATABASE_URL="postgresql+asyncpg://..." alembic upgrade head
   DATABASE_URL="postgresql+asyncpg://..." python -m scripts.seed
   ```

## 2. Redis (Upstash)

1. Create a free Redis database.
2. Copy the `rediss://` (TLS) connection URL it gives you — use it as-is for
   `REDIS_URL`.

## 3. Backend (Render or Railway)

1. Push this repository to GitHub (a separate, deliberate step — not done as
   part of this phase).
2. Create a new **Web Service** from the repo, root directory `backend/`.
3. Build: the platform detects the `Dockerfile` automatically. No build
   command needed.
4. Set environment variables in the platform's dashboard (never in code or
   in a committed file):

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | from step 1, async form |
   | `REDIS_URL` | from step 2 |
   | `JWT_SECRET` | a fresh random value, **32+ characters** — the app refuses to boot in production without one (see `app/core/config.py`) |
   | `JWT_ALGORITHM` | `HS256` |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
   | `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
   | `GROQ_API_KEY` | your Groq free-tier key |
   | `GEMINI_API_KEY` | your Gemini free-tier key |
   | `FRONTEND_ORIGIN` | the deployed frontend's exact HTTPS origin (step 4) |
   | `ENV` | `production` |

   Generate a strong `JWT_SECRET` with, e.g., `openssl rand -hex 32`.

5. Deploy. The platform provides HTTPS automatically on its `*.onrender.com`
   / `*.up.railway.app` subdomain (or your custom domain, with automatic
   cert issuance).
6. Confirm `GET /health` returns `{"status": "ok"}` on the deployed URL.

## 4. Frontend (Vercel or Netlify)

1. Create a new project from the same repo, root directory `frontend/`.
2. Build command: `npm run build`. Output directory: `dist`.
3. Environment variable:

   | Variable | Value |
   |---|---|
   | `VITE_API_BASE_URL` | the backend's deployed HTTPS URL from step 3 |

4. Deploy. Automatic HTTPS is provided by the platform.
5. Go back to the backend's `FRONTEND_ORIGIN` env var (step 3) and set it to
   this exact deployed frontend origin, then redeploy the backend — CORS
   will reject the frontend until these match exactly (scheme + host, no
   trailing slash).

## 5. Post-deploy checklist

- [ ] `GET /health` on the backend returns 200 over HTTPS.
- [ ] The frontend loads and `/menu` successfully fetches from the backend
      (open browser dev tools → Network tab; a CORS error here means
      `FRONTEND_ORIGIN` doesn't exactly match the deployed frontend's origin).
- [ ] Login/register work end-to-end from the deployed frontend.
- [ ] `ENV=production` is set on the backend — if `JWT_SECRET` were left at
      its default, the backend would already have refused to start, so a
      running instance confirms this passed.
- [ ] Cookies/tokens: the app currently returns tokens in the JSON response
      body (not cookies), so there is no cookie `Secure`/`SameSite` flag to
      configure — the access token lives in memory client-side and the
      refresh token in `localStorage`. This works over HTTPS on any domain
      pairing without additional CORS-credential configuration.
- [ ] Confirm rate limiting survives a redeploy: it's Redis-backed
      (`app/core/limiter.py`), not in-memory, so it does.

## 6. What's intentionally not automated here

- Actually creating the Render/Vercel/Supabase/Upstash accounts and
  resources — that requires the project owner's own credentials.
- CI/CD (GitHub Actions) beyond what Phase 0 stubbed — wiring real deploy
  hooks needs the platform accounts from steps 1–4 to exist first.
- A custom domain — both Render/Railway and Vercel/Netlify support adding
  one for free once the project owner has one to point.
