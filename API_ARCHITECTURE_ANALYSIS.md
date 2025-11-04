# CARMA API - Complete Architecture Analysis

**Date:** December 3, 2024  
**Purpose:** Document current API before rebuilding

---

## 🏗️ **Overall Architecture**

### **Stack:**
- **Framework:** Flask 3.0.3 (Python)
- **Database:** Azure PostgreSQL (277,502 vehicles)
- **Connection:** Connection pooling (psycopg2.pool.ThreadedConnectionPool, 2-20 connections)
- **Scoring:** Custom SimilarityEngine (weighted feature matching)

---

## 📡 **API Endpoints**

### **1. `/health` (GET)**
- **Purpose:** Health check
- **Returns:** Database status, vehicle count, timestamp
- **SQL:** Simple COUNT query

### **2. `/stats` (GET)**
- **Purpose:** Database statistics
- **Returns:** Total vehicle count, timestamp
- **SQL:** COUNT query

### **3. `/listings/<vehicle_id>` (GET)**
- **Purpose:** Get single vehicle details
- **Returns:** Vehicle data (price, make, model, images, etc.)
- **SQL:** Simple SELECT with vehicle_id filter
- **Processing:** Parses price string to float, calculates deal_score

### **4. `/listings/<vehicle_id>/comparables` (GET)**
- **Purpose:** Find comparable vehicles (THE MAIN LOGIC)
- **Returns:** Ranked list of comparable vehicles with scores
- **Query param:** `top` (1-50, default 10)

### **5. `/sample-vehicles` (GET)**
- **Purpose:** Get sample vehicle IDs for testing
- **Returns:** List of recent vehicles with metadata
- **Query param:** `limit` (1-50, default 10)

---

## 🔍 **Comparables Endpoint - Detailed Logic**

### **Step 1: Get Target Vehicle**
```sql
SELECT vehicle_id, make, model, first_registration_raw, fuel_type, 
       transmission, body_type, power_kw, mileage_km, price, color
FROM vehicle_marketplace.vehicle_data
WHERE vehicle_id = %s AND is_vehicle_available = true
```

### **Step 2: Build STRICT SQL Filters**
**Required (always applied):**
- `make = target.make` (EXACT match)
- `model = target.model` (EXACT match)

**Optional (if target has value):**
- `fuel_type = target.fuel_type` (EXACT match)
- `transmission = target.transmission` (EXACT match)
- `body_type = target.body_type` (EXACT match)
- **`color = target.color`** (REMOVED - was too restrictive)

**Range Filters (if target has value):**
- Year: `target_year ± 2 years`
- Mileage: `<= target_mileage * 1.5`
- Price: `60% to 140% of target_price`
- Power: `90% to 110% of target_power`

### **Step 3: Query Candidates (LIMIT 200)**
```sql
SELECT vehicle_id, listing_url, price, mileage_km, first_registration_raw,
       make, model, fuel_type, transmission, body_type, description,
       data_source, power_kw, images, color
FROM vehicle_marketplace.vehicle_data
WHERE [strict filters]
ORDER BY price ASC, mileage_km ASC
LIMIT 200
```

### **Step 4: Rank with Similarity Engine**
For each candidate vehicle:
1. **Calculate Similarity Score** (0-1):
   - Make match: 25% (1.0 if match, 0.0 if not)
   - Model match: 25% (1.0 if match, 0.0 if not)
   - Age distance: 20% (normalized year difference, 1.0 = same year)
   - Mileage distance: 20% (normalized mileage difference, 1.0 = same mileage)
   - Fuel match: 5% (1.0 if match, 0.0 if not)
   - Transmission match: 5% (1.0 if match, 0.0 if not)
   - **Formula:** `similarity = sum(weight * score)`

2. **Calculate Deal Score** (0-1):
   - Extract prices from all candidates
   - Calculate price percentile (where does this vehicle sit in market?)
   - Lower percentile = better deal (cheaper)
   - Adjust for mileage: lower mileage at same price = better deal
   - **Formula:** `deal_score = 1.0 - percentile + mileage_adjustment`

3. **Calculate Final Score** (0-1):
   - **Formula:** `final_score = (0.60 * similarity) + (0.40 * deal_score)`
   - 60% weight on similarity (how similar is it?)
   - 40% weight on deal (how good is the price?)

### **Step 5: Sort & Return**
- Sort by `final_score` (descending)
- Take top N (based on `top` parameter)
- Return with all scores and vehicle data

---

## 🎯 **Scoring Model Details**

### **Similarity Weights (Current):**
```python
{
    'make_match': 0.25,        # 25% - Must match (hard filter)
    'model_match': 0.25,       # 25% - Must match (hard filter)
    'age_distance': 0.20,      # 20% - Newer is better
    'mileage_distance': 0.20,  # 20% - Lower is better
    'fuel_match': 0.05,        # 5% - Must match (hard filter)
    'transmission_match': 0.05 # 5% - Must match (hard filter)
}
```

### **Final Score Weights (Current):**
```python
{
    'similarity': 0.60,  # 60% - Feature similarity
    'deal_score': 0.40   # 40% - Price/value
}
```

### **Missing from Similarity:**
- ❌ **Color matching** - NOT included in similarity calculation
- ❌ **Body type matching** - NOT included (only in SQL filter)
- ❌ **Power matching** - NOT included (only in SQL filter)
- ❌ **Price comparison** - Only in deal_score, not similarity

---

## 🔴 **Current Issues**

### **1. Color Filter Removed**
- **Problem:** Color was removed from SQL filter (line 380-381)
- **Impact:** May return vehicles with different colors
- **User Requirement:** Color should be considered

### **2. Color Not in Similarity Engine**
- **Problem:** Color matching not included in similarity scoring
- **Impact:** Vehicles with different colors score same as same color
- **User Requirement:** Color should affect similarity

### **3. Too Restrictive Filters**
- **Problem:** Strict filtering finds 0 candidates for many vehicles
- **Impact:** Returns 404 "No comparable vehicles found"
- **Root Cause:** Multiple exact matches required (make, model, fuel, transmission, body type)

### **4. Performance Issues**
- **Problem:** Queries taking 7-9 seconds
- **Impact:** Slow user experience
- **Possible Causes:**
  - Complex WHERE clause with multiple CASTs
  - Large dataset (277k vehicles)
  - No indexing mentioned

---

## 📊 **Data Flow**

```
User Request
    ↓
Validate vehicle_id
    ↓
Get target vehicle from DB
    ↓
Build STRICT SQL filters (make, model, fuel, transmission, body type, ranges)
    ↓
Query candidates (LIMIT 200)
    ↓
Parse candidate data (year, price, images)
    ↓
For each candidate:
    - Calculate similarity_score (weighted features)
    - Calculate deal_score (price percentile)
    - Calculate final_score (60% similarity + 40% deal)
    ↓
Sort by final_score (descending)
    ↓
Return top N results
```

---

## 🗄️ **Database Schema (Inferred)**

**Table:** `vehicle_marketplace.vehicle_data`

**Key Columns:**
- `vehicle_id` (TEXT/UUID) - Primary identifier
- `listing_url` (TEXT)
- `price` (TEXT) - Stored as string like "€19.500"
- `mileage_km` (TEXT) - Stored as string/number
- `first_registration_raw` (TEXT) - Year data
- `make` (TEXT)
- `model` (TEXT)
- `fuel_type` (TEXT)
- `transmission` (TEXT)
- `body_type` (TEXT)
- `power_kw` (TEXT/NUMERIC)
- `color` (TEXT)
- `images` (JSON/TEXT) - Array of image URLs
- `description` (TEXT)
- `data_source` (TEXT) - "autoscout24" or "mobile.de"
- `is_vehicle_available` (BOOLEAN)
- `created_at` (TIMESTAMP)

---

## 🔧 **Technical Details**

### **Connection Pooling:**
- Type: ThreadedConnectionPool
- Min connections: 2
- Max connections: 20
- Timeout: 10 seconds connection, 30 seconds statement

### **Type Safety:**
- All TEXT columns cast to FLOAT/INTEGER before comparison
- NULL checks before all CAST operations
- Empty string validation for price

### **Error Handling:**
- Vehicle ID validation (UUID or alphanumeric)
- Try/catch blocks around all DB operations
- Proper HTTP status codes (400, 404, 500, 503)

---

## ✅ **What Works:**
1. ✅ Connection pooling (improves performance)
2. ✅ Type-safe SQL queries (after fixes)
3. ✅ Similarity engine (weighted scoring)
4. ✅ Deal scoring (price percentile based)
5. ✅ Input validation

## ❌ **What Doesn't Work:**
1. ❌ Color matching (removed from filters, not in similarity)
2. ❌ Returns 0 results for many vehicles (too restrictive)
3. ❌ Slow queries (7-9 seconds)
4. ❌ Color not considered in similarity calculation

---

**This analysis complete. Ready to delete and rebuild.**

