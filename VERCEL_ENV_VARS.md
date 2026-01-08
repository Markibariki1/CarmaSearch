# 🔑 Vercel Environment Variables - Copy & Paste

**Use these exact values when deploying to Vercel**

---

## 📋 Environment Variables to Add in Vercel:

When you deploy to Vercel, go to **Settings → Environment Variables** and add these:

---

### 1. API Base URL

**Variable Name:**
```
NEXT_PUBLIC_API_BASE_URL
```

**Value:**
```
https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io
```

---

### 2. Supabase URL

**Variable Name:**
```
NEXT_PUBLIC_SUPABASE_URL
```

**Value:**
```
https://fdbvcxgnsjwyhygkaggd.supabase.co
```

---

### 3. Supabase Anon Key

**Variable Name:**
```
NEXT_PUBLIC_SUPABASE_ANON_KEY
```

**Value:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkYnZjeGduc2p3eWh5Z2thZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkzNzkzNDgsImV4cCI6MjA3NDk1NTM0OH0.3yOZPZdrVnuH3q1Q1UjVM0kFj92Bshj2URoNCDpuSlA
```

---

### 4. Environment

**Variable Name:**
```
NEXT_PUBLIC_ENVIRONMENT
```

**Value:**
```
production
```

---

## ⚙️ How to Add in Vercel:

### Option A: Via Dashboard (After Deployment)

1. Go to your Vercel project dashboard
2. Click **Settings** → **Environment Variables**
3. For each variable above:
   - Click **Add New**
   - Paste the **Variable Name**
   - Paste the **Value**
   - Select: **Production**, **Preview**, and **Development** (all three)
   - Click **Save**
4. After adding all variables, go to **Deployments**
5. Click the **︙** menu on your latest deployment
6. Click **Redeploy** → **Use existing Build Cache** → **Redeploy**

### Option B: During Initial Deployment

1. When importing from GitHub, Vercel will show configuration page
2. Click **Environment Variables** section
3. Add each variable one by one as shown above
4. Click **Deploy**

---

## 🔧 After Deployment:

### Update Supabase Redirect URLs:

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Select project: `fdbvcxgnsjwyhygkaggd`
3. Go to: **Authentication** → **URL Configuration**
4. Add your Vercel URL to **Redirect URLs**:
   ```
   https://your-app.vercel.app/auth/callback
   https://your-app.vercel.app/auth/confirm
   ```
5. Click **Save**

---

## ✅ Verification:

After deployment, test these:

1. **API Connection:**
   - Open browser console on your Vercel site
   - Run:
     ```javascript
     fetch('https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io/health')
       .then(r => r.json())
       .then(d => console.log(d))
     ```
   - Should return: `{ status: "healthy", database_connected: true }`

2. **Homepage:**
   - Counter should show 257k+
   - Logo scroll wheel should animate
   - All navigation should work

3. **Authentication:**
   - Click "Sign In"
   - Try logging in
   - Should redirect properly

4. **Compare:**
   - Sign in first
   - Click "Compare"
   - Paste a vehicle URL
   - Should fetch and display data

---

## 🐛 Troubleshooting:

### If environment variables don't work:
- Make sure you clicked **Redeploy** after adding them
- Environment variables only take effect after a new deployment

### If API calls fail:
- Check that `NEXT_PUBLIC_API_BASE_URL` is exactly as shown above
- Test the API directly in browser: `https://carma-ml-api.../health`

### If authentication doesn't work:
- Verify Supabase credentials are correct
- Make sure you added your Vercel URL to Supabase redirect URLs
- Check Supabase dashboard for auth errors

---

**That's it! Your CARMA platform will be fully functional on Vercel! 🚀**
