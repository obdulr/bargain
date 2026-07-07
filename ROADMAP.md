# BargainHuntrs Roadmap

> Current implementation status of the BargainHuntrs arbitrage intelligence platform.
> Last updated: 2026-07-09

## Legend

- ✅ Complete / shipped
- 🚧 In progress
- ❌ Not started / planned

---

## Phase 1 — MVP (Weeks 1-2) ✅

The core platform is live: users can sign up, subscribe, and receive alerts.

| Feature | Status | Notes |
|---------|--------|-------|
| Landing page + waitlist | ✅ | Next.js marketing site with waitlist capture |
| JWT authentication (email/password) | ✅ | `bargain-api/app/routers/auth.py` |
| WebAuthn / passkey authentication | ✅ | `bargain-api/app/services/webauthn_service.py` + `PasskeyButton.tsx` |
| Stripe subscription paywall | ✅ | Checkout sessions, webhooks, customer management |
| Billing management page | ✅ | `/billing` with plan status + cancel flow |
| Price error / glitch alerts | ✅ | Alert pipeline + scheduler |
| Email notifications | ✅ | Resend integration |
| SMS / push notifications | ✅ | Firebase Cloud Messaging |
| Watchlist | ✅ | Add/refresh/delete tracked products |
| Database migrations | ✅ | Alembic-managed (001 → 007) |

### Subscription tiers

| Tier | Price | Status |
|------|-------|--------|
| Free | $0/mo | ✅ Active |
| Pro | $29/mo | ✅ Stripe checkout wired |
| Enterprise | $99/mo | ✅ Stripe checkout wired |

> **Note:** The frontend pricing page currently displays four tiers
> (Free / Hustler / Pro / Agency). The backend subscription engine supports
> `free`, `pro`, and `enterprise` plan IDs. Frontend plans map to backend
> plan IDs via `planId` in `bargain-web/src/app/pricing/plans.ts`.

---

## Phase 2 — Arbitrage Scanner (Month 2) ❌

| Feature | Status | Notes |
|---------|--------|-------|
| Cross-platform arbitrage scanner (eBay ↔ Amazon) | ❌ | Planned |
| Price comparison engine | ❌ | Planned |
| Keepa API integration for price history | ❌ | Config stubs exist |
| eBay Browse API integration for sold listings | ❌ | Config stubs exist |

---

## Phase 3 — Analytics (Month 3) ❌

| Feature | Status | Notes |
|---------|--------|-------|
| Reseller analytics dashboard | ❌ | Planned |
| ROI tracking per user | ❌ | Planned |
| Profit calculator (fees + tax + shipping) | ❌ | Planned |

---

## Phase 4 — Brick & Mortar (Month 4) ❌

| Feature | Status | Notes |
|---------|--------|-------|
| Brick & mortar clearance alerts | ❌ | Planned |
| Zip code based store notifications | ❌ | Planned |

---

## Phase 5 — International (Months 5-6) ❌

| Feature | Status | Notes |
|---------|--------|-------|
| International arbitrage layer | ❌ | Planned |
| Tariff / duty calculator | ❌ | Planned |

---

## Architecture overview

```
bargain/
├── bargain-web/     # Next.js 16 frontend (App Router, TypeScript, Tailwind 4)
├── bargain-api/     # FastAPI backend (Python, SQLAlchemy, Alembic)
└── packages/        # Shared workspace packages
```

### Backend services

| Service | File | Purpose |
|---------|------|---------|
| Auth | `app/routers/auth.py` | JWT login/register/refresh |
| WebAuthn | `app/routers/webauthn.py` | Passkey register/login flows |
| Subscriptions | `app/routers/subscriptions.py` | Stripe checkout + billing |
| Stripe | `app/services/stripe_service.py` | Stripe API wrapper + webhooks |
| WebAuthn | `app/services/webauthn_service.py` | WebAuthn challenge/verify |
| Alerts | `app/routers/alerts.py` | Price alert delivery |
| Watchlist | `app/routers/watchlist.py` | Product tracking |
| Arbitrage | `app/routers/arbitrage.py` | Deal detection |

### Frontend pages

| Route | Purpose |
|-------|---------|
| `/` | Landing page |
| `/pricing` | Subscription plans + Stripe checkout |
| `/billing` | Manage subscription + cancel |
| `/billing/success` | Post-checkout success |
| `/billing/cancel` | Checkout canceled |
| `/login` | Email/password + passkey login |
| `/signup` | Registration + passkey setup |
| `/dashboard` | Watchlist + account overview |

### Database migrations

| Revision | Description |
|----------|-------------|
| 001 | Initial schema |
| 002 | User profile fields |
| 003 | Waitlist table |
| 004 | Arbitrage deals table |
| 005 | Alert read status |
| 006 | Stripe subscription fields (`stripe_subscription_id`) |
| 007 | WebAuthn passkey fields (`credential_id`, `public_key`, `sign_count`, `aaguid`) |

---

## Environment variables

### Backend (`bargain-api/.env`)

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key |
| `STRIPE_SECRET_KEY` | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `STRIPE_PRICE_FREE` / `STRIPE_PRICE_PRO` / `STRIPE_PRICE_ENTERPRISE` | Stripe price IDs |
| `FRONTEND_URL` | Frontend origin (checkout redirects) |
| `WEB_AUTHN_RP_ID` | WebAuthn relying party ID |
| `WEB_AUTHN_RP_NAME` | WebAuthn relying party name |
| `WEB_AUTHN_ORIGIN` | WebAuthn expected origin |
| `RESEND_API_KEY` | Email delivery |

### Frontend (`bargain-web/.env.local`)

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key |
