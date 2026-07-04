# Deployment Guide

## ⚠️ CRITICAL: Package Manager
**PERMANENT RULE: Always use pnpm 9.15.5 - NEVER use npm**

## Current Deployment Architecture

```
Frontend: Render (free tier)
  - Next.js on port 3030
  - bargain-web.onrender.com
  - Configured via render.yaml
  - Connects to Railway backend

Backend: Railway (already deployed)
  - FastAPI on port 4030
  - bargainhuntrs.com
  - Configured via Dockerfile + railway.toml
  - Railway PostgreSQL (future)
```

## Backend Deployment (Railway)

### Status: ✅ Already Deployed
The backend is currently deployed and operational at bargainhuntrs.com.

### Configuration
- **Root Directory**: `bargain-api`
- **Port**: 4030
- **Domain**: bargainhuntrs.com
- **Dockerfile**: Root Dockerfile with Python 3.11
- **Healthcheck**: `/health` endpoint

### Environment Variables
- `PORT=4030`
- `DATABASE_URL` (PostgreSQL connection string - to be added)

### To Update Backend
```bash
git push origin main
# Railway auto-deploys from main branch
```

### Railway Configuration Files
- `Dockerfile` - Python 3.11 FastAPI setup
- `railway.toml` - Deployment configuration
- Root directory set to `bargain-api` in Railway dashboard

## Frontend Deployment (Render)

### Status: ⏳ Being Configured
The frontend is being deployed on Render using render.yaml.

### Configuration
- **Root Directory**: `bargain-web`
- **Port**: 3030
- **Build Command**: `corepack enable && corepack prepare pnpm@9.15.5 --activate && pnpm install --frozen-lockfile=false && pnpm run build`
- **Start Command**: `cd bargain-web && pnpm start`

### Environment Variables
- `NEXT_PUBLIC_API_URL=https://bargainhuntrs.com`
- `NODE_VERSION=24`

### Render Configuration File
- `render.yaml` - Complete Render deployment configuration
- Automatically detected by Render
- Handles pnpm setup via corepack

### To Update Frontend
```bash
git push origin main
# Render auto-deploys from main branch
```

## Important Deployment Rules

### 1. Package Manager (CRITICAL)
- **ALWAYS** use pnpm 9.15.5
- **NEVER** use npm for any reason
- This is permanent for the entire project

### 2. Port Configuration
- **Frontend**: Port 3030 (permanent)
- **Backend**: Port 4030 (permanent)
- Never change these ports

### 3. Corepack for pnpm
- Corepack must be enabled for pnpm support
- Render build command includes: `corepack enable && corepack prepare pnpm@9.15.5 --activate`
- This ensures proper pnpm setup in deployment environments

### 4. Lockfile Handling
- Use `--frozen-lockfile=false` for Render deployment
- Handles lockfile compatibility issues
- Prevents deployment failures

## Deployment Workflow

### 1. Make Changes
```bash
# Make your changes
git add .
git commit -m "Your commit message"
```

### 2. Push to GitHub
```bash
git push origin main
```

### 3. Automatic Deployment
- **Railway**: Auto-deploys backend from main branch
- **Render**: Auto-deploys frontend from main branch
- Both platforms monitor the GitHub repository

### 4. Monitor Deployment
- **Railway**: Check Railway dashboard for backend status
- **Render**: Check Render dashboard for frontend status
- Both platforms provide real-time logs

## Troubleshooting

### Backend Deployment Issues

**Healthcheck Failing:**
- Check port is set to 4030 in Railway dashboard
- Verify `/health` endpoint exists in FastAPI app
- Check Railway logs for startup errors

**Database Connection Issues:**
- Verify DATABASE_URL environment variable is set
- Check PostgreSQL database is running
- Test connection string format

### Frontend Deployment Issues

**Build Failing:**
- Verify pnpm is being used (not npm)
- Check corepack is enabled in build command
- Ensure `--frozen-lockfile=false` is included
- Check Render logs for specific errors

**Start Command Failing:**
- Verify start command uses pnpm
- Check working directory is correct
- Ensure port 3030 is not blocked

**Package Manager Issues:**
- If npm is being used instead of pnpm, check render.yaml
- Verify corepack commands are correct
- Ensure NODE_VERSION is set to 24

## Local Development vs Production

### Local Development
```bash
# Frontend (port 3030)
cd bargain-web
pnpm run dev
# Visit http://localhost:3030

# Backend (port 4030)
cd bargain-api
uvicorn app.main:app --reload --host 0.0.0.0 --port 4030
# Visit http://localhost:4030
```

### Production URLs
- **Frontend**: https://bargain-web.onrender.com
- **Backend**: https://bargainhuntrs.com
- **API**: https://bargainhuntrs.com/health

## Future Enhancements

### Planned Additions
- Railway PostgreSQL database for backend
- Custom domain for frontend (bargainhuntrs.com)
- CDN configuration for static assets
- Monitoring and logging setup
- CI/CD pipeline enhancements

### Database Migration
When adding Railway PostgreSQL:
1. Create PostgreSQL service in Railway
2. Add DATABASE_URL to backend environment variables
3. Run Alembic migrations
4. Update connection string in configuration

## Support

For deployment issues:
1. Check platform-specific logs (Railway/Render dashboards)
2. Verify environment variables are correctly set
3. Ensure pnpm is being used (not npm)
4. Check port configurations (3030/4030)
5. Review this documentation for common issues

---

**Remember: pnpm 9.15.5 is permanent - never use npm!**
