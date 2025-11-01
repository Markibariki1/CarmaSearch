# CARMA Platform - Local Backup Information

**Date:** November 1, 2025  
**Backup File:** `C1_backup_20251101_171049.tar.gz` (153 MB)  
**Location:** `/Users/marchaupter/Desktop/`

---

## 📦 What's Included in This Backup

### 1. **Flask API (RankingMODEL/autoscout-ml/)**
- ✅ `app_flask.py` - Production Flask API (v6)
- ✅ `similarity_engine.py` - Vehicle similarity matching
- ✅ `ranking_pipeline.py` - Hybrid ranking system
- ✅ `Dockerfile.flask` - Production Docker configuration
- ✅ `requirements_flask.txt` - Python dependencies
- ✅ All backup versions (v2, v3_strict, backup)

### 2. **Next.js Frontend (Website Homepage/)**
- ✅ `app/page.tsx` - Main homepage with memoised filtering
- ✅ `components/compare-modal.tsx` - Vehicle comparison modal
- ✅ `lib/api.ts` - API client with request abort
- ✅ All UI components and utilities
- ✅ `.env.local` (gitignored but backed up)

### 3. **Web Scraper (vehicle_data-main 2/)**
- ✅ AutoScout24 scraper (complete & recent)
- ✅ Mobile.de scraper (complete & recent)
- ✅ Database module with Python 3.8 compatibility fix
- ✅ `.env` configuration (gitignored but backed up)
- ✅ Proxy configuration and utilities

### 4. **Shipping/VICE API (ShippingAPI/)**
- ✅ `vice_standalone.html` - Standalone HTML interface
- ✅ Global trade database schema
- ✅ Vehicle data cleaning reports

### 5. **Documentation**
- ✅ `AZURE_DEPLOYMENT_LOG.md` - Complete deployment history
- ✅ `SIMILARITY_ALGORITHM_ANALYSIS.md`
- ✅ `SIMILARITY_USE_CASE_ANALYSIS.md`
- ✅ `DEPLOYMENT_READY_SUMMARY.md`
- ✅ `FIXES_APPLIED.md`

---

## 🚀 Current Production Status

### Azure Container Apps
- **URL:** `https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io`
- **Image:** `carmaregistry.azurecr.io/carma-api:v6`
- **Revision:** `carma-ml-api--0000019`
- **Status:** ✅ Running
- **Database:** 263,594 vehicles available

### GitHub Repository
- **URL:** `https://github.com/Markibariki1/C1`
- **Branch:** `main`
- **Latest Commit:** `Clean deployment: CARMA platform v6 with hybrid ranking and optimizations`

### Local Development
- **Next.js Dev Server:** Running on `http://localhost:3000`
- **Status:** ✅ Ready for testing

---

## 📊 Database Details

### Azure PostgreSQL
- **Host:** `carma.postgres.database.azure.com`
- **Database:** `postgres`
- **Schema:** `vehicle_marketplace`
- **Table:** `vehicle_data`
- **Total Records:** 263,594 vehicles
- **Sample Data:**
  - BMW 5-series: 2,791 vehicles
  - Mercedes-Benz: Multiple models
  - Audi: Multiple models

---

## 🔧 Key Features Implemented

### 1. Hybrid Ranking Engine
- **Similarity Score (60%):** Vehicle attribute matching
- **Deal Score (35%):** Price positioning vs market
- **Preference Score (5%):** User preference boosts

### 2. Performance Optimizations
- Memoised filtering in frontend
- Request abort on filter changes
- Optimized API calls

### 3. Python 3.8 Compatibility
- Fixed type hints (`str | None` → `Optional[str]`)
- Updated database module

---

## 📝 Configuration Files (Backed Up)

### Environment Files
```
Website Homepage/.env.local           - Supabase & API config
vehicle_data-main 2/.env              - Database & proxy config
RankingMODEL/autoscout-ml/.env.optimized
```

### Important Configs
```
Website Homepage/package.json
RankingMODEL/autoscout-ml/requirements_flask.txt
vehicle_data-main 2/requirements.txt
```

---

## 🗂️ Data Files (Local Only - Not in Git)

These files are **excluded from Git** but **included in the backup**:

### Large Data Files
- `ShippingAPI/massive_vehicle_dataset_cleaned.json` (46 MB)
- `ShippingAPI/global_trade.db`
- `RankingMODEL/autoscout-ml/data/*.xlsx` (sample data)

### Build Artifacts (Excluded from Backup)
- `node_modules/` - Can be restored with `npm install`
- `.next/` - Build cache
- `venv/` - Virtual environment
- `__pycache__/` - Python cache

---

## 🔄 How to Restore from Backup

### Full Restore
```bash
cd /Users/marchaupter/Desktop
tar -xzf C1_backup_20251101_171049.tar.gz
cd C1
```

### Restore Dependencies
```bash
# Frontend
cd "Website Homepage"
npm install

# Scraper
cd "../vehicle_data-main 2"
pip3 install -r requirements.txt
```

### Verify Git Status
```bash
git status
git remote -v
git log --oneline -5
```

---

## 📞 Important Credentials

### Azure
- **Account:** marchaupter@outlook.com
- **Resource Group:** `carma`
- **Container Registry:** `carmaregistry.azurecr.io`

### GitHub
- **Repository:** `Markibariki1/C1`
- **Access:** Via your GitHub account

---

## ✅ Next Steps

1. **Test Local Development:**
   ```bash
   cd "Website Homepage"
   npm run dev
   # Visit http://localhost:3000
   ```

2. **Test Compare Feature:**
   - Use vehicle ID: `19787596-f5d1-43ca-a595-f004f14bce7b`
   - 2014 BMW 530d Touring

3. **Monitor Production:**
   - Health check: `https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io/health`

---

## 🛡️ Backup Recommendations

- **Frequency:** Weekly backups recommended
- **Location:** External drive or cloud storage
- **Git:** Always push to GitHub after significant changes
- **Environment Files:** Keep separate secure backup of `.env` files

---

**✅ Everything is saved and backed up successfully!**

Last updated: November 1, 2025 17:11

