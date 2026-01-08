# CARMA API - Deployment Status

**Last Updated:** December 3, 2024  
**Status:** 🔄 **REBUILDING FROM SCRATCH**

---

## 🗑️ **API Deleted for Rebuild**

All API files have been deleted to rebuild from scratch:
- ❌ `app_flask.py` - Deleted
- ❌ `app_flask_v2.py` - Deleted  
- ❌ `app_flask_v3_strict.py` - Deleted
- ❌ `similarity_engine.py` - Deleted

**Architecture analysis saved in:** `API_ARCHITECTURE_ANALYSIS.md`

---

## 📋 **New API Design**

**Approach:** Extract attributes → Search directly (simpler!)

### **Key Requirements:**
- ✅ **Extract vehicle_id** from URL
- ✅ **Query ONCE** to get target attributes (make, model, color, interior_color, fuel_type, transmission, body_type, year, mileage, price, power)
- ✅ **Search with HARD + FLEXIBLE filters:**
  - **HARD MATCH:** make, model, fuel_type, transmission, body_type, color (exterior)
  - **FLEXIBLE:** year (±2), mileage (≤1.5x), price (60-140%), power (±10%)
- ✅ **Include color** in similarity scoring (not just filtering)
- ✅ **Include interior_color** (optional/flexible)
- ✅ Connection pooling (keep)
- ✅ Type-safe queries (keep)
- ✅ Faster queries (<2s)

---

## ✅ **New API Built**

**File:** `RankingMODEL/autoscout-ml/src/api.py`

**Features Implemented:**
- ✅ Extract vehicle_id from URL
- ✅ Single query to get target vehicle attributes
- ✅ HARD MATCH filters: make, model, fuel_type, transmission, body_type, **color (exterior)**
- ✅ FLEXIBLE filters: year (±2), mileage (≤1.5x), price (60-140%), power (±10%)
- ✅ Similarity scoring with color matching (15% weight)
- ✅ Interior color matching (5% weight, optional)
- ✅ Connection pooling (ThreadedConnectionPool)
- ✅ Type-safe SQL queries with proper casting
- ✅ Updated Dockerfile.flask to use new api.py

**Endpoints:**
- `/health` - Health check
- `/stats` - Database statistics
- `/listings/<vehicle_id>` - Get vehicle details
- `/listings/<vehicle_id>/comparables` - Get comparable vehicles
- `/sample-vehicles` - Get sample vehicle IDs for testing

## ✅ **DEPLOYMENT COMPLETE**

**Version:** `v1-clean-architecture`  
**Deployed:** November 3, 2025  
**Status:** ✅ **LIVE**

**Deployment Details:**
- Image: `carmaregistry.azurecr.io/carma-api:v1-clean-architecture`
- Container App: `carma-ml-api`
- Revision: `carma-ml-api--0000023`
- API URL: `https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io`

**Verification:**
- ✅ Health endpoint responding
- ✅ Database connected (277,502 vehicles)
- ✅ Stats endpoint working

**Next Steps:**
1. Test comparables endpoint with color matching
2. Verify color filtering works correctly
3. Test from frontend

---

**Note:** This file is overwritten with each deployment/update.

