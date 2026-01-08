# New API Design - Clean Architecture

**Date:** December 3, 2024  
**Approach:** Extract attributes → Search directly

---

## 🎯 **Correct Approach**

### **Current (WRONG - Overcomplicated):**
1. Query target vehicle from `vehicle_marketplace.vehicle_data`
2. Extract attributes
3. Build complex SQL query with those attributes
4. Query again for comparables

### **New (RIGHT - Simple & Clean):**
1. Extract vehicle ID from URL
2. **Query ONCE** to get target vehicle:
   ```sql
   SELECT make, model, first_registration_raw, fuel_type, transmission, 
          body_type, color, interior_color, mileage_km, price, power_kw
   FROM vehicle_marketplace.vehicle_data
   WHERE vehicle_id = ?
   ```
3. Use those attributes **directly** to search for comparables

---

## 🗄️ **Database Schema (Confirmed)**

**Table:** `vehicle_marketplace.vehicle_data`

**Color Columns:**
- `color` (TEXT) - **Exterior color** (e.g., "Blau", "Weiß", "Schwarz")
- `interior_color` (TEXT) - Interior color (may be NULL)
- `upholstery_color` (TEXT) - Upholstery color (e.g., "Grau")
- `upholstery` (TEXT) - Upholstery material (e.g., "Sonstige", "Leder")

**Key Attributes:**
- `make` (TEXT) - e.g., "Volvo"
- `model` (TEXT) - e.g., "V50"
- `first_registration_raw` (TEXT/DATE) - e.g., "2006-03-01"
- `fuel_type` (TEXT) - e.g., "Benzin", "Diesel"
- `transmission` (TEXT) - e.g., "Automatik", "Schaltgetriebe"
- `body_type` (TEXT) - e.g., "Kombi", "Limousine"
- `mileage_km` (TEXT/NUMERIC) - e.g., 208000
- `price` (TEXT) - e.g., "€15.000"
- `power_kw` (NUMERIC) - e.g., 103

---

## 🔍 **Filtering Strategy**

### **HARD MATCH (Exact - Must Match):**
- ✅ `make` = target.make
- ✅ `model` = target.model
- ✅ `fuel_type` = target.fuel_type (if target has it)
- ✅ `transmission` = target.transmission (if target has it)
- ✅ `body_type` = target.body_type (if target has it)
- ✅ `color` = target.color (if target has it) - **EXTERIOR COLOR**
- ✅ `interior_color` = target.interior_color (if target has it, optional/flexible)

### **FLEXIBLE (Range - Can Vary):**
- ⚙️ Year: `target_year ± 2 years`
- ⚙️ Mileage: `<= target_mileage * 1.5` (or ±30%)
- ⚙️ Price: `60% to 140% of target_price`
- ⚙️ Power: `±10% of target_power`

---

## 🧮 **Similarity Scoring (New Design)**

### **Features to Include:**
1. **Categorical Matches (Binary):**
   - Make match (already filtered, so always 1.0)
   - Model match (already filtered, so always 1.0)
   - Fuel match (already filtered, so always 1.0)
   - Transmission match (already filtered, so always 1.0)
   - Body type match (already filtered, so always 1.0)
   - **Color match** (NEW - should be included!)
   - Interior color match (NEW - optional)

2. **Numerical Similarity (Normalized 0-1):**
   - Age similarity (year difference)
   - Mileage similarity (mileage difference)
   - Power similarity (power difference)
   - Price similarity (price difference)

### **Scoring Weights:**
```python
{
    # Categorical (already hard-filtered, but boost perfect matches)
    'color_match': 0.15,          # 15% - NEW!
    'interior_color_match': 0.05,  # 5% - NEW!
    
    # Numerical similarity
    'age_similarity': 0.20,        # 20%
    'mileage_similarity': 0.20,    # 20%
    'power_similarity': 0.10,      # 10%
    
    # Deal quality
    'price_deal': 0.30             # 30% - Lower price = better
}
```

---

## 📋 **Simplified Logic Flow**

```
1. Extract vehicle_id from URL
   ↓
2. Query target vehicle (ONE query):
   SELECT make, model, color, interior_color, fuel_type, 
          transmission, body_type, first_registration_raw,
          mileage_km, price, power_kw
   FROM vehicle_marketplace.vehicle_data
   WHERE vehicle_id = ?
   ↓
3. Parse attributes:
   - year = extract_year(first_registration_raw)
   - price_numeric = parse_price(price)
   - mileage_numeric = parse_float(mileage_km)
   ↓
4. Build comparables query with HARD + FLEXIBLE filters:
   SELECT ...
   FROM vehicle_marketplace.vehicle_data
   WHERE 
     -- HARD MATCHES
     make = target.make AND
     model = target.model AND
     fuel_type = target.fuel_type AND  -- if exists
     transmission = target.transmission AND  -- if exists
     body_type = target.body_type AND  -- if exists
     color = target.color AND  -- if exists (NEW!)
     -- FLEXIBLE RANGES
     year BETWEEN (target.year - 2) AND (target.year + 2) AND
     mileage_km <= target.mileage * 1.5 AND
     price BETWEEN target.price * 0.6 AND target.price * 1.4 AND
     power_kw BETWEEN target.power * 0.9 AND target.power * 1.1
   ORDER BY price ASC, mileage_km ASC
   LIMIT 200
   ↓
5. Score and rank results:
   - Calculate similarity (include color!)
   - Calculate deal score
   - Sort by final score
   ↓
6. Return top N
```

---

## ✅ **Key Improvements**

1. **Simpler Logic:**
   - ✅ One query for target vehicle
   - ✅ Direct attribute extraction
   - ✅ Clear hard vs flexible filters

2. **Color Matching:**
   - ✅ `color` (exterior) as HARD filter when available
   - ✅ `interior_color` as optional/flexible filter
   - ✅ Color included in similarity scoring

3. **Better Performance:**
   - ✅ Simpler queries
   - ✅ Fewer operations
   - ✅ Clear indexing strategy (make, model, color)

4. **More Results:**
   - ✅ Less restrictive (color only if available)
   - ✅ Flexible ranges allow more matches
   - ✅ Better similarity scoring

---

## 🎯 **Implementation Plan**

1. **Extract vehicle_id** from URL (already working)
2. **Single query** to get target attributes
3. **Build search query** with hard + flexible filters
4. **Include color** in both filtering and similarity
5. **Score results** with improved similarity engine
6. **Return ranked results**

---

**This is the correct, clean approach!** 🎯

