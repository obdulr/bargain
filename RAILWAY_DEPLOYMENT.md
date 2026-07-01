# Railway Deployment Guide

This guide covers deploying BargainHuntrs to Railway for both frontend and backend.

## Prerequisites

- Railway account ([railway.app](https://railway.app))
- GitHub account with BargainHuntrs repository
- pnpm >= 8.0.0 (package manager)
- Stripe account (for payments)
- Firebase account (for SMS/push)
- Resend account (for email)

## Architecture on Railway

```
Railway Project: BargainHuntrs
├── Service 1: bargain-web (Next.js frontend)
├── Service 2: bargain-api (FastAPI backend)
└── Service 3: PostgreSQL Database
```

## Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `bargain` repository
4. Railway will analyze your monorepo

## Step 2: Deploy Backend (bargain-api)

### Create Backend Service

1. In your Railway project, click "New Service"
2. Select "Deploy from GitHub repo"
3. Select the same repository
4. Click "Settings" → "General"
5. Set **Root Directory** to: `bargain-api`
6. Set **Start Command** to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Add PostgreSQL Database

1. In your Railway project, click "New Service"
2. Select "Database" → "PostgreSQL"
3. Railway will create a PostgreSQL instance
4. Click on the database service → "Variables"
5. Copy the `DATABASE_URL` (you'll need this for the backend)

### Configure Backend Environment Variables

1. Go to your `bargain-api` service
2. Click "Variables" tab
3. Add these variables:

```env
# Database (Railway provides this automatically via reference)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# API Configuration
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (Add your Railway frontend URL after deploying)
ALLOWED_ORIGINS=["https://your-frontend-url.railway.app"]

# Stripe
STRIPE_API_KEY=sk_test_your_stripe_api_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Firebase
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# Resend
RESEND_API_KEY=re_your_resend_api_key

# Railway (automatically set)
PORT=8000
```

### Run Database Migrations

1. Go to your `bargain-api` service
2. Click "Console" tab
3. Click "New Console"
4. Run:
```bash
cd /app
alembic upgrade head
```

### Deploy Backend

1. Click "Deploy" tab
2. Click "Trigger Deploy"
3. Wait for deployment to complete
4. Copy the backend URL (e.g., `https://bargain-api-production.railway.app`)

## Step 3: Deploy Frontend (bargain-web)

### Create Frontend Service

1. In your Railway project, click "New Service"
2. Select "Deploy from GitHub repo"
3. Select the same repository
4. Click "Settings" → "General"
5. Set **Root Directory** to: `bargain-web`
6. Set **Start Command** to: `next start -p $PORT`
7. Set **Port** to: `3000`

### Configure Frontend Environment Variables

1. Go to your `bargain-web` service
2. Click "Variables" tab
3. Add these variables:

```env
# API URL (use your backend Railway URL)
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app

# Stripe (optional for frontend)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
```

### Deploy Frontend

1. Click "Deploy" tab
2. Click "Trigger Deploy"
3. Wait for deployment to complete
4. Copy the frontend URL (e.g., `https://bargain-web-production.railway.app`)

## Step 4: Update CORS Configuration

1. Go back to your `bargain-api` service
2. Click "Variables" tab
3. Update `ALLOWED_ORIGINS` to include your frontend URL:

```env
ALLOWED_ORIGINS=["https://your-frontend-url.railway.app","https://bargainhuntrs.com"]
```

4. Trigger a new deployment for the backend

## Step 5: Set Up Custom Domain (Optional)

### For Frontend

1. Go to your `bargain-web` service
2. Click "Settings" → "Networking"
3. Click "Generate Domain" or add custom domain
4. Follow Railway's DNS instructions

### For Backend

1. Go to your `bargain-api` service
2. Click "Settings" → "Networking"
3. Add custom domain if desired

## Step 6: Configure Stripe Webhooks

1. Go to Stripe Dashboard → Webhooks
2. Add endpoint: `https://your-backend-url.railway.app/api/v1/subscriptions/webhook`
3. Select events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
4. Copy the webhook signing secret
5. Add to Railway backend variables: `STRIPE_WEBHOOK_SECRET`

## Step 7: Configure Firebase

1. Download Firebase service account JSON
2. Upload to Railway (or set as environment variable)
3. Update backend `FIREBASE_CREDENTIALS_PATH` variable

## Step 8: Configure Resend

1. Get API key from Resend dashboard
2. Add to Railway backend: `RESEND_API_KEY`

## Monitoring & Logs

### View Logs

1. Go to any service in Railway
2. Click "Logs" tab
3. View real-time logs

### View Metrics

1. Go to any service
2. Click "Metrics" tab
3. View CPU, memory, and network usage

### Database Access

1. Go to PostgreSQL service
2. Click "Connect" tab
3. Use provided connection string or Railway's built-in query editor

## Troubleshooting

### Backend Not Starting

- Check logs for errors
- Verify `DATABASE_URL` is set correctly
- Ensure port is set to `8000`
- Check Python dependencies are installing

### Frontend Not Starting

- Check logs for build errors
- Verify `NEXT_PUBLIC_API_URL` is set
- Ensure port is set to `3000`

### Database Connection Issues

- Verify database service is running
- Check `DATABASE_URL` format
- Ensure backend can reach database (Railway handles this automatically)

### CORS Errors

- Verify `ALLOWED_ORIGINS` includes frontend URL
- Check frontend is using correct API URL
- Restart backend after updating CORS settings

### Migration Issues

- Access backend console
- Run `alembic current` to check migration status
- Run `alembic upgrade head` to apply migrations
- Check database connection string

## Scaling

### Automatic Scaling

Railway automatically scales based on traffic. Configure in service settings:

1. Go to service → "Settings" → "Scaling"
2. Set min/max instances
3. Configure CPU/RAM limits

### Database Scaling

1. Go to PostgreSQL service
2. Click "Settings" → "Scaling"
3. Upgrade to higher tier if needed

## Cost Estimation

Railway pricing (as of 2024):
- **Free tier**: $5/month credit
- **Backend**: ~$5-20/month depending on usage
- **Frontend**: ~$5-20/month depending on usage
- **PostgreSQL**: ~$5-20/month depending on storage/usage

Estimated total: **$15-60/month** for production

## Local Development with Railway

### Use Railway Database Locally

1. Go to PostgreSQL service in Railway
2. Click "Connect" tab
3. Copy connection string
4. Update local `.env`:

```env
DATABASE_URL=railway-provided-connection-string
```

### Deploy Preview Branches

Railway automatically creates preview deployments for pull requests:
1. Create a new branch
2. Push to GitHub
3. Railway creates preview URL
4. Test changes before merging

## Continuous Deployment

Railway provides automatic deployments:
- Every push to `main` triggers deployment
- Pull requests create preview deployments
- Configure branch-specific settings if needed

## Backup & Recovery

### Database Backups

Railway automatically backs up PostgreSQL:
- Daily backups retained for 7 days
- Manual backups available in database settings

### Recovery

1. Go to PostgreSQL service
2. Click "Backups" tab
3. Select backup to restore
4. Click "Restore"

## Security Best Practices

1. **Never commit secrets** to git
2. Use Railway's built-in secret management
3. Enable Railway's built-in SSL (automatic)
4. Use environment variables for all sensitive data
5. Rotate API keys regularly
6. Monitor logs for suspicious activity
7. Enable Railway's 2FA

## Next Steps

After deployment:
1. Test all API endpoints
2. Verify database migrations ran successfully
3. Test Stripe checkout flow
4. Test email/SMS notifications
5. Set up monitoring alerts
6. Configure custom domains
7. Set up analytics (optional)

---

For support, check [Railway Documentation](https://docs.railway.app)
