# ⚡ Quick Deploy - CARMA to Vercel

**Ultra-fast deployment guide - 5 minutes to live!**

---

## 🚀 Step 1: Create GitHub Repo (1 min)

1. Go to: **https://github.com/new**
2. Name: `carma-frontend`
3. Private ✅
4. Don't initialize anything
5. Click "Create repository"

---

## 📤 Step 2: Push Code (1 min)

```bash
cd "/Users/marchaupter/Desktop/C1/Website Homepage"

git remote add origin https://github.com/YOUR_USERNAME/carma-frontend.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

---

## 🌐 Step 3: Deploy to Vercel (2 min)

1. Go to: **https://vercel.com/new**
2. Import your `carma-frontend` repo
3. Click "Deploy" (Vercel auto-detects Next.js)

---

## ⚙️ Step 4: Add Environment Variables (1 min)

In Vercel dashboard → Settings → Environment Variables, add:

```bash
NEXT_PUBLIC_API_BASE_URL
https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io

NEXT_PUBLIC_SUPABASE_URL
https://fdbvcxgnsjwyhygkaggd.supabase.co

NEXT_PUBLIC_SUPABASE_ANON_KEY
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkYnZjeGduc2p3eWh5Z2thZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkzNzkzNDgsImV4cCI6MjA3NDk1NTM0OH0.3yOZPZdrVnuH3q1Q1UjVM0kFj92Bshj2URoNCDpuSlA

NEXT_PUBLIC_ENVIRONMENT
production
```

Then: **Redeploy** (button in Vercel dashboard)

---

## 🔧 Step 5: Configure Supabase (30 sec)

1. **https://supabase.com/dashboard** → Your project
2. Authentication → URL Configuration
3. Add redirect URL: `https://your-app.vercel.app/auth/callback`
4. Save

---

## ✅ Step 6: Test (30 sec)

Visit your Vercel URL and check:
- ✅ Page loads
- ✅ Counter shows 257k+
- ✅ Logo wheel scrolls
- ✅ Sign in works
- ✅ Compare works

---

## 🎉 Done!

Your CARMA platform is live!

**For detailed instructions, see:** `VERCEL_DEPLOYMENT_STEPS.md`

---

## 🐛 Troubleshooting

**Build fails?**
→ Check environment variables are set

**Auth doesn't work?**
→ Add Vercel URL to Supabase redirects

**API fails?**
→ Check `NEXT_PUBLIC_API_BASE_URL` is correct

---

**Total time: ~5 minutes** ⚡



