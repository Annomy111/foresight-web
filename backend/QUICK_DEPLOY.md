# Quick Deploy to Render - 2 Minutes!

## Step 1: Open Render Dashboard (30 seconds)
1. Open https://dashboard.render.com in your browser
2. Sign in to your account

## Step 2: Create New Web Service (1 minute)
1. Click the **"New +"** button
2. Select **"Web Service"**
3. Connect GitHub:
   - Select **"Connect a repository"**
   - Choose: `Annomy111/foresight-backend`
   - Click **"Connect"**

## Step 3: Quick Configuration (30 seconds)
Most settings will auto-configure from `render.yaml`, just verify:
- **Name**: `foresight-analyzer-api`
- **Region**: Oregon (US West)
- **Plan**: Select **"Free"** ($0/month)

## Step 4: Add API Key (30 seconds)
1. Scroll to **"Environment Variables"**
2. Click **"Add Environment Variable"**
3. Enter:
   - **Key**: `OPENROUTER_API_KEY`
   - **Value**: `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`

## Step 5: Deploy! (Click and Done)
1. Click **"Create Web Service"**
2. Deployment starts automatically
3. First build takes 5-10 minutes

## Your Service URLs
Once deployed, your backend will be at:
```
https://foresight-analyzer-api.onrender.com
```

## That's It! 🎉

Once the service is deployed and running, tell me the URL and I'll:
- Set up UptimeRobot to keep it awake 24/7
- Update Netlify with the backend URL
- Test everything is working
- Show you the live AI forecasting in action!

**Total time: 2 minutes of clicks**
**Total cost: $0/month forever**