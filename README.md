# BargainHuntrs 🎯

**Find it. Flip it. Profit.**

Arbitrage intelligence platform that monitors pricing anomalies, clearance events, and cross-platform opportunities to help resellers maximize profits.

## 🏗️ Architecture

This is a monorepo built with:

- **Frontend**: Next.js 16 + TypeScript + Tailwind CSS
- **Backend**: Python FastAPI + PostgreSQL
- **Storage**: Supabase (files/images)
- **Payments**: Stripe
- **Alerts**: Resend (email) + Firebase (SMS/push)
- **Hosting**: Railway (frontend + backend + database)
- **Monorepo Tooling**: Turborepo

## 📁 Project Structure

```
bargain/
├── bargain-web/          # Next.js frontend application
├── bargain-api/          # FastAPI backend service
├── packages/
│   ├── shared/          # Shared TypeScript types and utilities
│   └── config/          # Shared ESLint, Prettier, and TSConfig
├── package.json         # Root package.json with workspaces
├── turbo.json           # Turborepo configuration
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Node.js >= 18.0.0
- npm >= 9.0.0
- Python >= 3.11
- PostgreSQL (via Railway)

### Installation

1. **Clone and install dependencies:**
```bash
cd /Volumes/Os_Sites/bargain
npm install
```

2. **Set up frontend:**
```bash
cd bargain-web
npm install
cp .env.example .env.local
# Edit .env.local with your configuration
```

3. **Set up backend:**
```bash
cd bargain-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
```

### Development

Run all services in development mode:

```bash
# From root
npm run dev
```

Or run individually:

```bash
# Frontend (Next.js)
cd bargain-web
pnpm run dev

# Backend (FastAPI)
cd bargain-api
uvicorn app.main:app --reload --host 0.0.0.0 --port 4030
```

### Build

```bash
pnpm run build
```

### Lint & Format

```bash
npm run lint
npm run format
```

## 🎯 Features (Phased Rollout)

### Phase 1 (Weeks 1-2) - MVP
- ✅ Price error / glitch alerts
- ✅ Email/SMS notifications
- ✅ Stripe subscription paywall
- ✅ Landing page + waitlist

### Phase 2 (Month 2)
- Cross-platform arbitrage scanner (eBay ↔ Amazon)
- Price comparison engine

### Phase 3 (Month 3)
- Reseller analytics dashboard
- ROI tracking per user

### Phase 4 (Month 4)
- Brick & mortar clearance alerts
- Zip code based store notifications

### Phase 5 (Months 5-6)
- International arbitrage layer
- Tariff/duty calculator

## 💰 Subscription Tiers

| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | 5 alerts/day, 24hr delay |
| Hustler | $29/mo | 50 alerts, same-day, basic analytics |
| Pro | $79/mo | Unlimited, instant alerts, profit calculator |
| Agency | $199/mo | Multi-user, API access, white label |

## 🔧 Tech Stack Details

### Frontend (bargain-web)
- **Framework**: Next.js 16 with App Router
- **Styling**: Tailwind CSS 4
- **Language**: TypeScript
- **Auth**: NextAuth.js / Clerk
- **Deployment**: Railway

### Backend (bargain-api)
- **Framework**: FastAPI
- **Database**: PostgreSQL (Railway)
- **ORM**: SQLAlchemy 2.0 (async)
- **Authentication**: JWT (python-jose)
- **Deployment**: Railway

### Integrations
- **Payments**: Stripe API
- **Email**: Resend API
- **SMS/Push**: Firebase Cloud Messaging
- **Storage**: Supabase Storage
- **Scraping**: BeautifulSoup4 + httpx

## 📊 Database Schema

Core tables (PostgreSQL):
- `users` - User accounts and subscriptions
- `subscriptions` - Stripe subscription data
- `alerts` - Price alerts and notifications
- `price_snapshots` - Historical price data
- `watchlist_items` - User watchlists

## 🔐 Environment Variables

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:4030
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Backend (.env)
```env
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=your-secret-key
STRIPE_API_KEY=sk_test_...
RESEND_API_KEY=re_...
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```

## 🧪 Testing

```bash
# Frontend
cd bargain-web
pnpm test

# Backend
cd bargain-api
pytest
```

## 📦 Deployment

### Full Railway Deployment
See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) for detailed instructions.

Quick start:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy backend
cd bargain-api
railway up

# Deploy frontend
cd ../bargain-web
railway up
```

### Manual Railway Setup
1. Create Railway project at [railway.app](https://railway.app)
2. Connect GitHub repository
3. Create 3 services:
   - `bargain-api` (root: `bargain-api`, port: 8000)
   - `bargain-web` (root: `bargain-web`, port: 3000)
   - PostgreSQL database
4. Configure environment variables (see RAILWAY_DEPLOYMENT.md)
5. Run database migrations via Railway console
6. Deploy both services

## 🤝 Contributing

This is a proprietary project. For internal team coordination:

1. Create feature branches from `main`
2. Run tests and linting before PRs
3. Use conventional commit messages
4. Update documentation as needed

## 📄 License

Proprietary - All rights reserved

## 🆘 Support

For technical issues or questions, contact the development team.

---

Built with ❤️ for resellers who want to maximize their arbitrage opportunities.
