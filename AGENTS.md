# Project Notes for AI Agents

## SMS Provider: Telnyx ONLY

**NEVER use Twilio.** Twilio is not used in any project. All SMS, MMS, and messaging functionality uses **Telnyx** exclusively.

- Use the Telnyx API (`https://api.telnyx.com/v2/messages`) for sending SMS
- Env vars: `TELNYX_API_KEY`, `TELNYX_FROM_NUMBER`, `TELNYX_MESSAGING_PROFILE_ID`
- Do not suggest, install, or reference Twilio in any code, config, or documentation

## Package Manager

- Backend (bargain-api): Python with pip, FastAPI
- Frontend (bargain-web): Next.js with pnpm (NEVER use npm)

## Deployment: Render ONLY

**NEVER reference Railway.** The project has migrated from Railway to **Render** for both backend and frontend.

- Backend: Render (Docker-based, Python 3.11, port 4030)
- Frontend: Render (Next.js, port 3030)
- Database: Render PostgreSQL
- Backend URL: `https://api.bargainhuntrs.com`
- Frontend URL: `https://bargain-web.onrender.com`
- Configured via `Dockerfile` (backend) and `render.yaml` (frontend)
- Render auto-deploys from `main` branch

## SQL Logging

- `SQL_ECHO` env var controls SQLAlchemy query logging (default: `false`)
- **Never set `SQL_ECHO=true` in production** — it floods logs at ~500/sec and causes Render to drop scheduler/error messages
