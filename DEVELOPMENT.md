# Development Guide

## Local Development Setup

### 1. Install pnpm (if not already installed)
```bash
npm install -g pnpm
```

### 2. Install Root Dependencies
```bash
pnpm install
```

### 3. Frontend Setup
```bash
cd bargain-web
pnpm install
cp .env.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Backend Setup
```bash
cd bargain-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/bargainhuntrs
SECRET_KEY=dev-secret-key-change-in-production
```

### 5. Database Setup (Railway)
1. Create Railway account
2. Create new PostgreSQL project
3. Copy connection string to `.env`

Or use local PostgreSQL:
```bash
# Install PostgreSQL locally
brew install postgresql  # macOS
# or use Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15
```

## Running Services

### All Services (from root)
```bash
npm run dev
```

### Individual Services

**Frontend:**
```bash
cd bargain-web
pnpm run dev
# Visit http://localhost:3000
```

**Backend:**
```bash
cd bargain-api
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 4030
# Visit http://localhost:4030/docs for API docs
```

## Common Tasks

### Add New Shared Type
```bash
cd packages/shared
# Edit src/index.ts
cd ../..
npm run build
```

### Run Linting
```bash
npm run lint
```

### Format Code
```bash
npm run format
```

### Clean Everything
```bash
npm run clean
```

## API Development

### Add New Endpoint
1. Create route file in `bargain-api/app/api/v1/`
2. Import and register in `bargain-api/app/main.py`
3. Add Pydantic models in `bargain-api/app/schemas/`

### Database Migration
```bash
cd bargain-api
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Frontend Development

### Add New Page
```bash
cd bargain-web
# Create page in app/ directory
# Next.js App Router handles routing automatically
```

### Add API Call
```typescript
// Use fetch or axios with API URL from env
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/endpoint`);
```

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 4030
lsof -ti:4030 | xargs kill -9
```

### Python Virtual Environment Issues
```bash
# Recreate venv
cd bargain-api
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Node Modules Issues
```bash
# Clean and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Production Deployment

### Full Railway Deployment
See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) for complete guide.

### Quick Railway Setup
1. Create Railway account at [railway.app](https://railway.app)
2. Create new project from GitHub repo
3. Add 3 services:
   - **bargain-api**: Root `bargain-api`, Port 8000, Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **bargain-web**: Root `bargain-web`, Port 3000, Start `next start -p $PORT`
   - **PostgreSQL**: Database service
4. Configure environment variables (see RAILWAY_DEPLOYMENT.md)
5. Run migrations: `alembic upgrade head` in backend console
6. Deploy all services
