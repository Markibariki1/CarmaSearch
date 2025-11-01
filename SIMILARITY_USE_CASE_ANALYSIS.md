# 🔍 CARMA Similarity Algorithm - Use Case Analysis

**Date:** October 28, 2025  
**Goal:** Understand how users will actually use this tool

---

## 🎯 Core Use Case

### **User Journey:**
1. User finds a car they like on AutoScout24/Mobile.de
2. User pastes the URL into CARMA
3. User wants to see: **"The SAME car, but better options"**

### **What "Same Car" Means:**
- ✅ **Exact same make + model** (e.g., VW Golf → VW Golf only)
- ✅ **Same generation/variant** (e.g., Golf VII → Golf VII)
- ✅ **Similar year** (±1-2 years max)
- ✅ **Similar specs** (engine size, power, trim)

### **What "Better Options" Means:**
- 💰 **Lower price** for same/better specs
- 🚗 **Lower mileage** at same/similar price
- ⭐ **Better condition** (fewer owners, no accidents)
- 📍 **Better location** (closer to user)
- 🎨 **Preferred color/interior** (if specified)

---

## 🚫 Current Problem with Our Algorithm

### **Issue: Too Broad**
Our current algorithm would show:
- ❌ VW Golf → VW Passat (same make, different model)
- ❌ Golf VII → Golf VIII (different generation)
- ❌ Golf GTI → Golf TDI (different engine type)
- ❌ 2015 Golf → 2022 Golf (too different in age)

### **User Expectation:**
When user inputs: **"2018 VW Golf VII GTI White with Black Interior"**

They want to see:
- ✅ 2017-2019 VW Golf VII GTI, any color*
- ✅ Same engine (2.0 TSI)
- ✅ Same power (~230 HP)
- ✅ Similar mileage (±30k km)
- ✅ Lower price or better condition

*Unless they specify color filter

---

## 📊 Recommended Filter Strategy

### **Tier 1: HARD FILTERS (Must Match)**

These should be **exact matches** or **very narrow ranges**:

```python
HARD_FILTERS = {
    'make': 'EXACT',              # VW → VW only
    'model': 'EXACT',             # Golf → Golf only
    'year': '±2 years',           # 2018 → 2016-2020
    'fuel_type': 'EXACT',         # Petrol → Petrol only
    'transmission': 'EXACT',      # Automatic → Automatic only
    'body_type': 'EXACT',         # Hatchback → Hatchback only
}
```

### **Tier 2: SOFT FILTERS (Preferences)**

These are used for **ranking**, not filtering:

```python
SOFT_FILTERS = {
    'mileage': 'Similar ±30%',    # Used for scoring
    'price': 'Similar ±20%',      # Used for scoring
    'power_kw': 'Similar ±10%',   # Used for scoring
    'color': 'User preference',   # If specified
    'previous_owners': 'Fewer better', # For scoring
    'accident_history': 'No better',  # For scoring
}
```

### **Tier 3: USER OVERRIDES (Advanced Filters)**

User can optionally specify:
- Color preferences
- Interior color
- Max mileage
- Max price
- Max age
- Min/max power

---

## 🎨 Color Matching Strategy

### **Problem:**
User inputs: "White Golf with Black Interior"

**Question:** Should we ONLY show white cars with black interior?

### **Recommended Approach:**

#### **Option A: Default (Recommended)**
- Show ALL colors
- **Sort by:** Price/Deal quality first
- **Bonus points:** White exterior + Black interior moves up in ranking
- **Why:** User gets best deals, color is preference not requirement

```python
# Pseudo-code
if vehicle.color == target.color:
    similarity_score += 0.05  # 5% bonus
if vehicle.interior_color == target.interior_color:
    similarity_score += 0.05  # 5% bonus
```

#### **Option B: Strict**
- Show ONLY exact color matches
- **Problem:** Might eliminate best deals
- **Use case:** User is very particular about color

#### **Option C: Hybrid (Best)**
- Show top 5 results: ANY color (best deals)
- Show next 5 results: MATCHING colors
- **Label clearly:** "Best Deals" vs "Color Matches"

**Recommendation:** Go with Option C (Hybrid)

---

## 📐 Revised Similarity Weights

### **Current Weights (Too Flexible):**
```python
CURRENT = {
    'make_match': 0.30,        # 30% - Can match different makes
    'model_match': 0.25,       # 25% - Can match different models
    'age_distance': 0.15,      # 15%
    'mileage_distance': 0.15,  # 15%
    'fuel_match': 0.10,        # 10%
    'transmission_match': 0.05 # 5%
}
```

### **Proposed Weights (Stricter):**
```python
PROPOSED = {
    # HARD REQUIREMENTS (Must be 1.0 or vehicle excluded)
    'make_match': REQUIRED,           # Filter, not weight
    'model_match': REQUIRED,          # Filter, not weight
    'fuel_match': REQUIRED,           # Filter, not weight
    'transmission_match': REQUIRED,   # Filter, not weight
    
    # RANKING FACTORS (Used for scoring)
    'age_distance': 0.20,      # 20% - Newer is better
    'mileage_distance': 0.25,  # 25% - Lower mileage is better
    'power_similarity': 0.15,  # 15% - Same power range
    'price_comparison': 0.20,  # 20% - Deal quality
    'condition': 0.10,         # 10% - Accidents, owners
    'color_match': 0.10,       # 10% - Bonus if matches
}
```

---

## 🔍 Exploratory Questions to Answer

To build the right algorithm, we need to understand:

### **1. Data Distribution**
- How many vehicles per make/model?
- How many exact duplicates (same specs)?
- Price variation within same make/model/year?

### **2. User Behavior (If we had data)**
- Do users care more about price or mileage?
- How important is color?
- Would they accept different generation for better deal?

### **3. Market Dynamics**
- What's typical mileage range for same year?
- What's typical price range for same specs?
- How much do colors affect price?

---

## 🎯 Recommended Implementation

### **Step 1: SQL Pre-filtering (Fast)**

```sql
SELECT * FROM vehicles
WHERE make = target.make
  AND model = target.model              -- EXACT match
  AND fuel_type = target.fuel_type      -- EXACT match
  AND transmission = target.transmission -- EXACT match
  AND body_type = target.body_type      -- EXACT match
  AND year BETWEEN target.year - 2 AND target.year + 2  -- ±2 years
  AND mileage_km BETWEEN target.mileage * 0.5 AND target.mileage * 2  -- ±50%
  AND price BETWEEN target.price * 0.6 AND target.price * 1.4  -- ±40%
  AND is_vehicle_available = true
LIMIT 100
```

**Result:** ~50-100 candidates that are ACTUALLY similar

### **Step 2: Python Ranking**

```python
for candidate in candidates:
    # Calculate deal score
    deal_score = calculate_deal_score(candidate, market_data)
    
    # Calculate condition score
    condition_score = calculate_condition_score(candidate)
    
    # Calculate feature similarity
    feature_score = calculate_feature_similarity(candidate, target)
    
    # Color bonus (optional)
    color_bonus = 0.05 if matches_color(candidate, target) else 0.0
    
    # Final score
    final_score = (
        0.40 * deal_score +        # 40% - Price/value
        0.30 * feature_score +     # 30% - Specs match
        0.20 * (1 - mileage_norm) + # 20% - Lower mileage
        0.10 * condition_score +   # 10% - Better condition
        color_bonus                # Bonus - Preferred color
    )
```

### **Step 3: Return Results**

```python
results = {
    "target": target_vehicle,
    "comparables": [
        {
            "vehicle": vehicle_data,
            "scores": {
                "deal_score": 0.85,      # Great price
                "feature_score": 0.95,   # Very similar specs
                "mileage_score": 0.70,   # Decent mileage
                "condition_score": 0.90, # Excellent condition
                "color_match": True,     # Matches preferred color
                "final_score": 0.87      # Overall ranking
            },
            "highlights": [
                "15% cheaper than target",
                "10k km less mileage",
                "No accidents",
                "Matches preferred color"
            ]
        }
    ]
}
```

---

## 🎨 Color Handling - Final Recommendation

### **Implementation:**

```python
# Default behavior (no color filter)
if not user_specified_color:
    # Show best deals regardless of color
    # But give small bonus for color matches
    results = rank_by_deal_quality()
    
    # Annotate which ones match color
    for result in results:
        result['color_match'] = (result.color == target.color)

# User specified color filter
else:
    # Hard filter: ONLY show specified colors
    results = filter_by_color(user_color)
    results = rank_by_deal_quality()
```

### **Frontend Display:**

```
🏆 Best Deals (All Colors)
   1. VW Golf GTI - €18,500 (Save €3,000!) - Silver
   2. VW Golf GTI - €19,200 (Save €2,300!) - White ⭐ Matches your color!
   3. VW Golf GTI - €19,800 (Save €1,700!) - Black

🎨 Color Matches (White Only)
   1. VW Golf GTI - €19,200 - White
   2. VW Golf GTI - €20,500 - White
   3. VW Golf GTI - €21,000 - White
```

---

## 🚀 Action Items

### **To Implement This Properly:**

1. ✅ **Tighten SQL filters** - Make/Model/Fuel/Trans EXACT
2. ✅ **Reduce year range** - ±2 years max (not ±3)
3. ✅ **Add power_kw similarity** - Same engine size
4. ✅ **Implement condition scoring** - Owners, accidents
5. ✅ **Add color bonus** - Not filter, just ranking boost
6. ✅ **Update weights** - Focus on deal quality + mileage
7. ⏳ **Do EDA** - Analyze actual data distribution
8. ⏳ **Test with real examples** - Use actual listings
9. ⏳ **A/B test** - Compare with simple rule-based

---

## 📊 Data Analysis Needed

To finalize the algorithm, we need to:

1. **Sample 1000 vehicles** from database
2. **Analyze:**
   - Price distribution per make/model
   - Mileage distribution per year
   - Color popularity
   - Feature completeness (missing data)
3. **Test Cases:**
   - Pick 10 popular vehicles
   - Run similarity search
   - Manually verify results make sense

**Should I build a data analysis script to explore the actual data?**

---

## 💡 Key Insight

**The user wants:** "Show me the SAME car I'm looking at, but find me a BETTER DEAL"

**Not:** "Show me SIMILAR cars"

This is more like a **deal finder** than a **recommendation engine**.

The algorithm should be **strict on matching** and **flexible on ranking**.

---

**Next Steps:**
1. Tighten the filters (make/model/fuel EXACT)
2. Do EDA on real data
3. Test with actual vehicle listings
4. Implement hybrid color matching

**Ready to proceed?**
