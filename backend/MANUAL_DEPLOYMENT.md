# Manual Deployment to Render (Free Tier)

Since Render's API doesn't support free tier deployment, you'll need to deploy manually through the web interface.

## Quick Steps (5 minutes)

### 1. Go to Render Dashboard
Open: https://dashboard.render.com

### 2. Create New Web Service
- Click "New +" button
- Select "Web Service"
- Connect your GitHub account if not already connected

### 3. Select Repository
- Choose: `https://github.com/Annomy111/foresight-backend`
- Click "Connect"

### 4. Configure Service
Render will auto-detect settings from `render.yaml`, but verify:

**Basic Settings:**
- **Name**: `foresight-analyzer-api`
- **Region**: Oregon (US West)
- **Branch**: main
- **Runtime**: Python 3

**Build & Deploy:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 5. Select Free Plan
- Choose **"Free"** plan ($0/month)
- Note: Includes 750 hours/month, auto-sleeps after 15 min inactivity

### 6. Add Environment Variable
Click "Advanced" and add:
- **Key**: `OPENROUTER_API_KEY`
- **Value**: `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`

### 7. Create Web Service
- Click "Create Web Service"
- Deployment will start automatically
- First deployment takes 5-10 minutes

## Your Service URLs

Once deployed, your service will be available at:
- **API**: `https://foresight-analyzer-api.onrender.com`
- **Health**: `https://foresight-analyzer-api.onrender.com/health`
- **Docs**: `https://foresight-analyzer-api.onrender.com/docs`

## Keep Service Awake (Important!)

Free tier services sleep after 15 minutes of inactivity. To keep it awake 24/7:

### Option 1: UptimeRobot (Recommended - Free)
1. Go to https://uptimerobot.com
2. Create free account
3. Add New Monitor:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Foresight Backend
   - **URL**: `https://foresight-analyzer-api.onrender.com/health`
   - **Monitoring Interval**: 5 minutes
4. Click "Create Monitor"

### Option 2: Cron-job.org (Alternative - Free)
1. Go to https://cron-job.org
2. Create free account
3. Create new job:
   - **URL**: `https://foresight-analyzer-api.onrender.com/health`
   - **Schedule**: Every 5 minutes
   - **Method**: GET

## Update Netlify Function

After deployment, update your Netlify site:

1. Go to Netlify dashboard
2. Site Settings → Environment variables
3. Add:
   - **Key**: `BACKEND_URL`
   - **Value**: `https://foresight-analyzer-api.onrender.com`
4. Trigger redeploy from Deploys tab

## Verify Deployment

Test your deployment:

```bash
# Check health
curl https://foresight-analyzer-api.onrender.com/health

# Test forecast endpoint
curl -X POST https://foresight-analyzer-api.onrender.com/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Will AI surpass human intelligence by 2030?",
    "timeframe": "2030",
    "iterations": 3
  }'
```

## Troubleshooting

### If deployment fails:
1. Check Render dashboard logs
2. Verify Python version is 3.11
3. Ensure all files are pushed to GitHub
4. Check environment variable is set correctly

### If service sleeps:
1. Verify UptimeRobot is configured
2. Check monitor is active
3. Increase ping frequency if needed

### If API returns errors:
1. Check `/health` endpoint first
2. Verify OPENROUTER_API_KEY is set
3. Check Render logs for errors
4. Test with fewer iterations initially

## Total Cost: $0/month! 🎉

You get:
- ✅ 750 hours/month (enough for 24/7 operation)
- ✅ 100 GB bandwidth
- ✅ Automatic HTTPS
- ✅ Auto-deploy from GitHub
- ✅ 8 free AI models via OpenRouter
- ✅ Full Excel export functionality
- ✅ Real-time progress tracking ready