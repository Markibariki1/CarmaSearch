#!/usr/bin/env python3
"""
CARMA Compare API - Flask Version v3 with STRICT Filters
Shows the SAME car, but BETTER deals (exact matching)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
import logging
import re
import json as json_lib

# Import our similarity engine
from similarity_engine import SimilarityEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow all origins for Container Apps

# Initialize similarity engine with updated weights
# Focus more on deal quality and less on fuzzy matching
similarity_engine = SimilarityEngine(
    similarity_weights={
        'make_match': 0.25,        # 25% - Must match (hard filter)
        'model_match': 0.25,       # 25% - Must match (hard filter)
        'age_distance': 0.20,      # 20% - Newer is better
        'mileage_distance': 0.20,  # 20% - Lower is better
        'fuel_match': 0.05,        # 5% - Must match (hard filter)
        'transmission_match': 0.05 # 5% - Must match (hard filter)
    },
    final_weights={
        'similarity': 0.60,  # 60% - Feature similarity
        'deal_score': 0.40   # 40% - Price/value
    }
)

def get_database_connection():
    """Get database connection"""
    try:
        db_host = os.getenv('DATABASE_HOST')
        db_name = os.getenv('DATABASE_NAME')
        db_user = os.getenv('DATABASE_USER')
        db_password = os.getenv('DATABASE_PASSWORD')
        db_port = os.getenv('DATABASE_PORT')

        missing = [
            name for name, value in [
                ('DATABASE_HOST', db_host),
                ('DATABASE_NAME', db_name),
                ('DATABASE_USER', db_user),
                ('DATABASE_PASSWORD', db_password),
                ('DATABASE_PORT', db_port),
            ]
            if not value
        ]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

        return psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=int(db_port),
            sslmode='require',
            connect_timeout=30
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        conn = get_database_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_vehicles
                FROM vehicle_marketplace.vehicle_data
                WHERE is_vehicle_available = true
            """)
            result = cursor.fetchone()
        
        return jsonify({
            "status": "healthy",
            "database_connected": True,
            "total_vehicles": result['total_vehicles'],
            "similarity_engine": "v3.0-strict-filters",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        conn = get_database_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_vehicles
                FROM vehicle_marketplace.vehicle_data
                WHERE is_vehicle_available = true
            """)
            result = cursor.fetchone()
        
        return jsonify({
            "total_vehicles": result['total_vehicles'],
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Stats endpoint failed: {e}")
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/listings/<vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    """Get vehicle details"""
    try:
        conn = get_database_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    vehicle_id as id,
                    listing_url as url,
                    price,
                    mileage_km,
                    first_registration_raw as year,
                    make,
                    model,
                    fuel_type,
                    transmission,
                    body_type,
                    description,
                    data_source,
                    power_kw,
                    images,
                    color
                FROM vehicle_marketplace.vehicle_data
                WHERE vehicle_id = %s AND is_vehicle_available = true
            """, (vehicle_id,))
            
            vehicle = cursor.fetchone()
            
            if not vehicle:
                return jsonify({"error": f"Vehicle {vehicle_id} not found"}), 404
            
            # Extract numeric price
            price_str = str(vehicle['price'])
            price_clean = re.sub(r'[^0-9,]', '', price_str).replace(',', '.')
            price_numeric = float(price_clean) if price_clean else 0
            
            # Simple price estimate
            price_hat = price_numeric * 0.95
            deal_score = (price_hat - price_numeric) / price_numeric if price_numeric > 0 else 0
            
            # Parse year
            year = None
            try:
                if vehicle['year']:
                    year_str = str(vehicle['year'])[:4]
                    year = int(year_str)
            except (ValueError, TypeError):
                pass
            
            # Process images
            images_data = vehicle.get('images') or []
            if isinstance(images_data, str):
                try:
                    images_data = json_lib.loads(images_data)
                except:
                    images_data = []
            elif not isinstance(images_data, list):
                images_data = []
            
            return jsonify({
                "id": vehicle['id'],
                "url": vehicle['url'],
                "price_eur": float(price_numeric),
                "price_hat": float(price_hat),
                "deal_score": float(deal_score),
                "mileage_km": float(vehicle['mileage_km']),
                "year": year,
                "make": vehicle['make'],
                "model": vehicle['model'],
                "fuel_group": vehicle['fuel_type'],
                "transmission_group": vehicle['transmission'],
                "body_group": vehicle['body_type'],
                "color": vehicle.get('color'),
                "description": vehicle['description'] or "",
                "data_source": vehicle['data_source'],
                "power_kw": float(vehicle['power_kw']) if vehicle['power_kw'] else None,
                "images": images_data
            }), 200
        
    except Exception as e:
        logger.error(f"Error in get_vehicle: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/listings/<vehicle_id>/comparables', methods=['GET'])
def get_comparables(vehicle_id):
    """
    Get comparable vehicles using STRICT filtering
    Shows the SAME car, but better deals
    """
    try:
        top = int(request.args.get('top', 10))
        if top > 50:
            top = 50
        
        conn = get_database_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get target vehicle with ALL relevant fields
            cursor.execute("""
                SELECT 
                    vehicle_id,
                    make,
                    model,
                    first_registration_raw,
                    fuel_type,
                    transmission,
                    body_type,
                    power_kw,
                    mileage_km,
                    price,
                    color
                FROM vehicle_marketplace.vehicle_data
                WHERE vehicle_id = %s AND is_vehicle_available = true
            """, (vehicle_id,))
            
            target_raw = cursor.fetchone()
            
            if not target_raw:
                return jsonify({"error": f"Vehicle {vehicle_id} not found"}), 404
            
            # Parse target vehicle data
            target_year = None
            try:
                if target_raw['first_registration_raw']:
                    target_year = int(str(target_raw['first_registration_raw'])[:4])
            except (ValueError, TypeError):
                pass
            
            target_price = parse_price(target_raw['price'])
            target_mileage = float(target_raw['mileage_km']) if target_raw['mileage_km'] else None
            target_power = float(target_raw['power_kw']) if target_raw['power_kw'] else None
            
            # STRICT SQL FILTERING
            # HARD FILTERS: EXACT matches required
            year_min = (target_year - 2) if target_year else None
            year_max = (target_year + 2) if target_year else None
            mileage_max = (target_mileage * 1.5) if target_mileage else None
            price_min = (target_price * 0.6) if target_price else None
            price_max = (target_price * 1.4) if target_price else None
            power_min = (target_power * 0.9) if target_power else None
            power_max = (target_power * 1.1) if target_power else None
            
            # Build WHERE clause with STRICT filters
            where_conditions = [
                "is_vehicle_available = true",
                "vehicle_id != %s",
                "make = %s",              # EXACT match
                "model = %s",             # EXACT match
                "fuel_type = %s",         # EXACT match
                "transmission = %s",      # EXACT match
                "body_type = %s",         # EXACT match - NEW!
            ]
            
            params = [
                vehicle_id,
                target_raw['make'],
                target_raw['model'],
                target_raw['fuel_type'],
                target_raw['transmission'],
                target_raw['body_type'],
            ]
            
            # Add color filter if target has color
            if target_raw.get('color'):
                where_conditions.append("color = %s")  # EXACT color match - NEW!
                params.append(target_raw['color'])
            
            # Add year range (±2 years)
            if year_min and year_max:
                where_conditions.append("""
                    CAST(SUBSTRING(CAST(first_registration_raw AS TEXT), 1, 4) AS INTEGER) 
                    BETWEEN %s AND %s
                """)
                params.extend([year_min, year_max])
            
            # Add mileage range
            if mileage_max:
                where_conditions.append("mileage_km <= %s")
                params.append(mileage_max)
            
            # Add price range
            if price_min and price_max:
                where_conditions.append("""
                    CAST(REGEXP_REPLACE(price, '[^0-9,]', '', 'g') AS FLOAT) 
                    BETWEEN %s AND %s
                """)
                params.extend([price_min, price_max])
            
            # Add power range (±10%)
            if power_min and power_max:
                where_conditions.append("""
                    CAST(power_kw AS FLOAT) BETWEEN %s AND %s
                """)
                params.extend([power_min, power_max])
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
                SELECT 
                    vehicle_id as id,
                    listing_url as url,
                    price,
                    mileage_km,
                    first_registration_raw,
                    make,
                    model,
                    fuel_type,
                    transmission,
                    body_type,
                    description,
                    data_source,
                    power_kw,
                    images,
                    color
                FROM vehicle_marketplace.vehicle_data
                WHERE {where_clause}
                ORDER BY 
                    CAST(REGEXP_REPLACE(price, '[^0-9,]', '', 'g') AS FLOAT) ASC,
                    mileage_km ASC
                LIMIT 200
            """
            
            logger.info(f"Finding comparables with STRICT filters for {vehicle_id}")
            logger.info(f"Filters: make={target_raw['make']}, model={target_raw['model']}, "
                       f"fuel={target_raw['fuel_type']}, trans={target_raw['transmission']}, "
                       f"body={target_raw['body_type']}, color={target_raw.get('color')}, "
                       f"year={year_min}-{year_max}")
            
            cursor.execute(query, params)
            candidates_raw = cursor.fetchall()
            
            logger.info(f"Found {len(candidates_raw)} candidates after STRICT filtering")
            
            if not candidates_raw:
                return jsonify({
                    "error": "No comparable vehicles found with exact matching criteria",
                    "suggestion": "Try removing color or expanding year range"
                }), 404
            
            # Convert target to dict for similarity engine
            target = {
                'id': vehicle_id,
                'make': target_raw['make'],
                'model': target_raw['model'],
                'year': target_year,
                'mileage_km': target_mileage,
                'price': target_price,
                'fuel_type': target_raw['fuel_type'],
                'transmission': target_raw['transmission'],
                'body_type': target_raw['body_type'],
                'power_kw': target_power,
                'color': target_raw.get('color')
            }
            
            # Convert candidates to list of dicts
            candidates = []
            for c in candidates_raw:
                # Parse year
                year = None
                try:
                    if c['first_registration_raw']:
                        year = int(str(c['first_registration_raw'])[:4])
                except (ValueError, TypeError):
                    pass
                
                # Parse price
                price = parse_price(c['price'])
                
                # Process images
                images = c.get('images') or []
                if isinstance(images, str):
                    try:
                        images = json_lib.loads(images)
                    except:
                        images = []
                elif not isinstance(images, list):
                    images = []
                
                candidate = {
                    'id': c['id'],
                    'url': c['url'],
                    'price': price,
                    'mileage_km': float(c['mileage_km']) if c['mileage_km'] else None,
                    'year': year,
                    'make': c['make'],
                    'model': c['model'],
                    'fuel_type': c['fuel_type'],
                    'transmission': c['transmission'],
                    'body_type': c['body_type'],
                    'color': c.get('color'),
                    'description': c['description'] or "",
                    'data_source': c['data_source'],
                    'power_kw': float(c['power_kw']) if c['power_kw'] else None,
                    'images': images
                }
                candidates.append(candidate)
            
            # Use similarity engine to rank candidates (focus on deal quality)
            ranked = similarity_engine.rank_candidates(target, candidates, market_vehicles=candidates)
            
            # Format results
            results = []
            for vehicle, similarity_score, deal_score, final_score in ranked[:top]:
                price_eur = vehicle['price'] or 0
                
                # Calculate savings compared to target
                savings = target_price - price_eur if target_price and price_eur else 0
                savings_percent = (savings / target_price * 100) if target_price and target_price > 0 else 0
                
                # Calculate price_hat based on market position
                price_hat = price_eur * (1.0 + (deal_score - 0.5) * 0.2)
                
                result = {
                    'id': vehicle['id'],
                    'url': vehicle['url'],
                    'price_eur': float(price_eur),
                    'price_hat': float(price_hat),
                    'deal_score': float(deal_score),
                    'score': float(similarity_score),
                    'final_score': float(final_score),
                    'savings': float(savings),
                    'savings_percent': float(savings_percent),
                    'year': vehicle['year'],
                    'power_kw': vehicle['power_kw'],
                    'mileage_km': vehicle['mileage_km'],
                    'make': vehicle['make'],
                    'model': vehicle['model'],
                    'fuel_group': vehicle['fuel_type'],
                    'transmission_group': vehicle['transmission'],
                    'body_group': vehicle['body_type'],
                    'color': vehicle.get('color'),
                    'description': vehicle['description'],
                    'data_source': vehicle['data_source'],
                    'images': vehicle['images']
                }
                results.append(result)
            
            logger.info(f"Returning {len(results)} ranked results")
            return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Error in get_comparables: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def parse_price(price_value):
    """Parse price from various formats"""
    if price_value is None:
        return None
    try:
        if isinstance(price_value, (int, float)):
            return float(price_value)
        price_str = str(price_value)
        price_clean = re.sub(r'[^0-9,.]', '', price_str).replace(',', '.')
        return float(price_clean) if price_clean else None
    except (ValueError, TypeError):
        return None

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info("Starting CARMA API v3 with STRICT filtering...")
    logger.info("Hard filters: make, model, fuel_type, transmission, body_type, color")
    logger.info("Year range: ±2 years")
    logger.info("Power range: ±10%")
    app.run(host="0.0.0.0", port=port, debug=False)
