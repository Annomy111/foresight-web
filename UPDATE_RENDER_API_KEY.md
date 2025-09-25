# 🔧 Update OpenRouter API Key on Render

## Quick Steps to Fix the Backend

The backend is still using the old invalid API key. You need to update it on Render:

### 1. Go to Render Dashboard
- Open: https://dashboard.render.com
- Find your service: **foresight-backend-api**

### 2. Update Environment Variable
- Click on your service
- Go to **Environment** tab
- Find `OPENROUTER_API_KEY`
- Click the edit button (pencil icon)
- Replace with new key:
```
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
```
- Click **Save Changes**

### 3. Redeploy
- The service should auto-redeploy after saving
- If not, click **Manual Deploy** → **Deploy**

### 4. Wait for Deployment
- Takes about 2-3 minutes
- Check the **Events** tab for deployment status

### 5. Test the API
Once deployed, test here:
```bash
curl -X POST https://foresight-backend-api.onrender.com/forecast \
  -H "Content-Type: application/json" \
  -d '{"question":"Test","definition":"","timeframe":"2026","iterations":1}'
```

You should get a successful response with a probability value!

---

## Alternative: Update via Script

If you have the Render API key, you can run:
```bash
python3 backend/update_render_env.py
```

But manual update is faster and easier.

---

## 🎯 Expected Result

After updating, the backend should return:
```json
{
  "success": true,
  "result": {
    "ensemble_probability": 45.2,
    "statistics": {...}
  }
}
```

Instead of the current error:
```json
{
  "error": "No valid model results obtained"
}
```