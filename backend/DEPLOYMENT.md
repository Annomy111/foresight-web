# Deployment Instructions for Foresight Analyzer Backend

## Deploy to Render (Free Tier - Recommended)

### Step 1: Push to GitHub
```bash
# Create a new GitHub repository named "foresight-backend"
# Then run these commands:
git remote add origin https://github.com/YOUR_USERNAME/foresight-backend.git
git push -u origin main
```

### Step 2: Deploy to Render
1. Go to [render.com](https://render.com) and sign up (no credit card needed!)
2. Click "New +" → "Web Service"
3. Connect your GitHub account
4. Select your `foresight-backend` repository
5. Render will auto-detect the configuration from `render.yaml`
6. Click "Create Web Service"

### Step 3: Add API Key
1. In Render dashboard, go to your service
2. Click "Environment" tab
3. Add environment variable:
   - Key: `OPENROUTER_API_KEY`
   - Value: `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`
4. Click "Save Changes"

### Step 4: Get Your Backend URL
Once deployed, your backend URL will be:
```
https://foresight-analyzer-api.onrender.com
```

### Step 5: Keep It Awake (Important!)
To prevent the free tier from sleeping:
1. Go to [uptimerobot.com](https://uptimerobot.com) (free)
2. Create account
3. Add New Monitor:
   - Monitor Type: HTTP(s)
   - Friendly Name: Foresight Backend
   - URL: `https://foresight-analyzer-api.onrender.com/health`
   - Monitoring Interval: 5 minutes
4. Click "Create Monitor"

This will ping your service every 5 minutes, keeping it awake 24/7 for free!

### Step 6: Update Netlify Function
Once deployed, update your Netlify function:
1. Go to Netlify dashboard
2. Site Settings → Environment variables
3. Add: `BACKEND_URL = https://foresight-analyzer-api.onrender.com`
4. Redeploy your site

## Total Cost: $0/month 🎉

Your backend will be running 24/7 at no cost with:
- Render free tier hosting
- UptimeRobot keeping it awake
- 8 free AI models via OpenRouter
- Full Excel export functionality
- Real-time progress tracking ready