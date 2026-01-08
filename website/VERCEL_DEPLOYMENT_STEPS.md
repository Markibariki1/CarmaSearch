# 🚀 CARMA Frontend - Vercel Deployment Steps

**Step-by-step guide to deploy CARMA to Vercel and connect with GitHub**

---

## ✅ **Pre-Deployment Checklist:**

- ✅ Git repository initialized
- ✅ Initial commit created (143 files)
- ✅ `.gitignore` configured
- ✅ `.env.example` created
- ✅ API running on Azure Container Apps
- ✅ Supabase authentication configured
- ✅ All frontend files ready

---

## 📤 **Step 1: Push to GitHub**

### 1.1 Create GitHub Repository:

Go to [github.com/new](https://github.com/new) and create a new repository:
- **Name:** `carma-frontend` (or any name you prefer)
- **Description:** "CARMA Vehicle Comparison Platform - Frontend"
- **Visibility:** Private (recommended) or Public
- **DO NOT** initialize with README, .gitignore, or license (we already have these)

### 1.2 Connect Local Repo to GitHub:

```bash
# Navigate to frontend folder
cd "/Users/marchaupter/Desktop/C1/Website Homepage"

# Add GitHub remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/carma-frontend.git

# Or use SSH if you have it configured:
# git remote add origin git@github.com:YOUR_USERNAME/carma-frontend.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 1.3 Verify on GitHub:

Go to `https://github.com/YOUR_USERNAME/carma-frontend` and verify all files are pushed.

---

## 🔗 **Step 2: Deploy to Vercel**

### Option A: Deploy via Vercel Dashboard (Recommended)

1. **Go to Vercel:**
   - Visit [vercel.com](https://vercel.com)
   - Sign in with your GitHub account

2. **Import Project:**
   - Click "Add New..." → "Project"
   - Select "Import Git Repository"
   - Find and select your `carma-frontend` repository
   - Click "Import"

3. **Configure Project:**
   - **Framework Preset:** Next.js (auto-detected)
   - **Root Directory:** `./` (leave as is)
   - **Build Command:** `npm run build` (auto-detected)
   - **Output Directory:** `.next` (auto-detected)
   - **Install Command:** `npm install` (auto-detected)

4. **Add Environment Variables:**
   Click "Environment Variables" and add these:

   | Name | Value |
   |------|-------|
   | `NEXT_PUBLIC_API_BASE_URL` | `https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io` |
   | `NEXT_PUBLIC_SUPABASE_URL` | `https://fdbvcxgnsjwyhygkaggd.supabase.co` |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkYnZjeGduc2p3eWh5Z2thZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkzNzkzNDgsImV4cCI6MjA3NDk1NTM0OH0.3yOZPZdrVnuH3q1Q1UjVM0kFj92Bshj2URoNCDpuSlA` |
   | `NEXT_PUBLIC_ENVIRONMENT` | `production` |

5. **Deploy:**
   - Click "Deploy"
   - Wait 2-3 minutes for deployment to complete
   - You'll get a URL like: `https://carma-frontend.vercel.app`

### Option B: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
cd "/Users/marchaupter/Desktop/C1/Website Homepage"
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? (select your account)
# - Link to existing project? No
# - What's your project's name? carma-frontend
# - In which directory is your code located? ./
# - Want to override settings? No

# Add environment variables
vercel env add NEXT_PUBLIC_API_BASE_URL production
# Paste: https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io

vercel env add NEXT_PUBLIC_SUPABASE_URL production
# Paste your Supabase URL

vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
# Paste your Supabase anon key

vercel env add NEXT_PUBLIC_ENVIRONMENT production
# Type: production

# Deploy to production
vercel --prod
```

---

## 🔧 **Step 3: Configure Supabase Redirects**

After deployment, update Supabase with your new Vercel URL:

1. **Go to Supabase Dashboard:**
   - Visit [supabase.com/dashboard](https://supabase.com/dashboard)
   - Select your project: `fdbvcxgnsjwyhygkaggd`

2. **Update Authentication URLs:**
   - Go to: Authentication → URL Configuration
   - **Site URL:** `https://your-app.vercel.app`
   - **Redirect URLs:** Add these:
     ```
     https://your-app.vercel.app/auth/callback
     https://your-app.vercel.app/auth/confirm
     http://localhost:3000/auth/callback
     http://localhost:3000/auth/confirm
     ```

3. **Save Changes**

---

## ✅ **Step 4: Post-Deployment Verification**

### 4.1 Test Homepage:
- Visit your Vercel URL
- Check that the page loads
- Verify animated counter is working (should show 257k+)
- Check logo scroll wheel is animating

### 4.2 Test Authentication:
- Click "Get Started" or "Sign In"
- Try signing up with email/password
- Try social login (Google/GitHub)
- Verify you get redirected after login

### 4.3 Test Compare Functionality:
- Sign in to your account
- Click "Compare Now"
- Paste a vehicle URL from AutoScout24 or Mobile.de
- Example URL: `https://www.autoscout24.de/angebote/...`
- Verify vehicle details load
- Check that comparable vehicles appear
- Verify images are displayed

### 4.4 Test API Connection:
Open browser console and run:
```javascript
fetch('https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io/health')
  .then(r => r.json())
  .then(d => console.log(d))
// Should show: { status: "healthy", database_connected: true, total_vehicles: 257341 }
```

---

## 🔄 **Step 5: Enable Auto-Deploy (Continuous Deployment)**

Once connected to GitHub, Vercel automatically deploys on every push to `main`:

1. **Make a change:**
   ```bash
   cd "/Users/marchaupter/Desktop/C1/Website Homepage"
   # Edit any file
   git add .
   git commit -m "Update: your change description"
   git push
   ```

2. **Vercel auto-deploys:**
   - Vercel detects the push
   - Builds automatically
   - Deploys to production
   - You get a notification when complete

---

## 📊 **Step 6: Monitor Your Deployment**

### Vercel Dashboard:
- **Deployments:** See all deployments and their status
- **Analytics:** View page views, performance metrics
- **Logs:** Check build and runtime logs
- **Domains:** Add custom domains

### Check Performance:
- **Lighthouse:** Run in Chrome DevTools
- **Core Web Vitals:** Check in Vercel Analytics
- **API Response Times:** Monitor in browser network tab

---

## 🐛 **Troubleshooting:**

### Issue: Build fails on Vercel
**Check:**
1. Are all dependencies in `package.json`?
2. Does `npm run build` work locally?
3. Are environment variables set correctly?

### Issue: Page loads but API calls fail
**Check:**
1. Is `NEXT_PUBLIC_API_BASE_URL` set in Vercel?
2. Is the API healthy? Test: `curl https://carma-ml-api.../health`
3. Check browser console for CORS errors

### Issue: Authentication doesn't work
**Check:**
1. Are Supabase env vars set in Vercel?
2. Is your Vercel URL added to Supabase redirect URLs?
3. Check Supabase dashboard for auth logs

### Issue: Images or logos not showing
**Check:**
1. Are files in `/public/` folder?
2. Are file paths correct? (use `/filename.png`, not `./filename.png`)
3. Check browser console for 404 errors

### Issue: Environment variables not working
**Solution:**
- Environment variables only update after redeployment
- After adding/changing env vars, click "Redeploy" in Vercel dashboard

---

## 🎯 **Custom Domain (Optional):**

### Add Your Own Domain:

1. **In Vercel Dashboard:**
   - Go to your project → Settings → Domains
   - Click "Add Domain"
   - Enter your domain: `carma.com` or `www.carma.com`

2. **Configure DNS:**
   - Add CNAME record pointing to: `cname.vercel-dns.com`
   - Or A record to Vercel's IP address

3. **SSL Certificate:**
   - Vercel automatically provisions SSL certificate
   - HTTPS will work within minutes

4. **Update Supabase:**
   - Add your custom domain to Supabase redirect URLs

---

## 📈 **Performance Optimization:**

### Already Optimized:
- ✅ Next.js automatic code splitting
- ✅ Image optimization (Next.js Image component)
- ✅ Static page generation where possible
- ✅ Vercel Edge Network (CDN)
- ✅ Gzip/Brotli compression

### Optional Improvements:
- **Use Next.js Image for logos:** Replace `<img>` with `<Image>` in logo scroll wheel
- **Add loading states:** Show skeleton loaders while API fetches data
- **Cache API responses:** Use SWR or React Query for client-side caching
- **Optimize bundle size:** Analyze with `npm run build` and remove unused dependencies

---

## 🔒 **Security Checklist:**

- ✅ API keys in environment variables (not in code)
- ✅ `.env.local` ignored by git
- ✅ CORS configured on API
- ✅ HTTPS enforced (Vercel automatic)
- ✅ Supabase RLS enabled
- ✅ No sensitive data in client-side code

---

## 📝 **Deployment Summary:**

| Component | Status | URL |
|-----------|--------|-----|
| **Frontend** | ⏳ Ready to deploy | `https://your-app.vercel.app` |
| **API** | ✅ Deployed | `https://carma-ml-api...azurecontainerapps.io` |
| **Database** | ✅ Running | Azure PostgreSQL (257k vehicles) |
| **Auth** | ✅ Configured | Supabase |
| **GitHub** | ⏳ Ready to push | `github.com/YOUR_USERNAME/carma-frontend` |

---

## 🎉 **You're Ready to Deploy!**

### Quick Commands:

```bash
# 1. Push to GitHub
cd "/Users/marchaupter/Desktop/C1/Website Homepage"
git remote add origin https://github.com/YOUR_USERNAME/carma-frontend.git
git push -u origin main

# 2. Deploy to Vercel (via CLI)
vercel login
vercel
vercel env add NEXT_PUBLIC_API_BASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add NEXT_PUBLIC_ENVIRONMENT production
vercel --prod

# 3. Done! 🚀
```

---

## 📞 **Need Help?**

- **Vercel Docs:** [vercel.com/docs](https://vercel.com/docs)
- **Next.js Docs:** [nextjs.org/docs](https://nextjs.org/docs)
- **Supabase Docs:** [supabase.com/docs](https://supabase.com/docs)

---

**Your CARMA platform is ready for the world! 🚗✨**



