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
from typing import Dict, List, Any, Optional, Tuple

from ranking_pipeline import HybridRankingEngine, FilterLevel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow all origins for Container Apps

# Initialize ranking engine with blended weights
ranking_engine = HybridRankingEngine()

# Progressive fallback filter levels - Relaxed for better results
FILTER_LEVELS: List[FilterLevel] = [
    FilterLevel(year_delta=3, mileage_pct=0.35, price_pct=0.25, power_pct=0.20, require_body_type=True, require_transmission=True, require_color=False),
    FilterLevel(year_delta=4, mileage_pct=0.45, price_pct=0.30, power_pct=0.25, require_body_type=True, require_transmission=False, require_color=False),
    FilterLevel(year_delta=5, mileage_pct=0.55, price_pct=0.35, power_pct=0.30, require_body_type=False, require_transmission=False, require_color=False),
    FilterLevel(year_delta=7, mileage_pct=0.70, price_pct=0.45, power_pct=0.40, require_body_type=False, require_transmission=False, require_color=False),
]

MAX_CANDIDATES_PER_LEVEL = 500


def extract_year(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value)[:4])
    except (ValueError, TypeError):
        return None


def build_candidate_query(
    vehicle_id: str,
    target_row: Dict[str, Any],
    level: FilterLevel,
    target_year: Optional[int],
    target_price: Optional[float],
    target_mileage: Optional[float],
    target_power: Optional[float],
) -> Tuple[str, List[Any]]:
    conditions = [
        "is_vehicle_available = true",
        "vehicle_id != %s",
    ]
    params: List[Any] = [vehicle_id]

    make = target_row.get("make")
    model = target_row.get("model")
    fuel = target_row.get("fuel_type")

    if not make or not model:
        raise ValueError("Target vehicle is missing make or model, cannot build filters.")

    conditions.append("make = %s")
    params.append(make)

    # Use LIKE for more flexible model matching (e.g., "GLE 350" matches "GLE 350 d", "GLE 350 4MATIC")
    if model:
        # Try to extract base model (e.g., "GLE 350" from "GLE 350 4MATIC")
        base_model = model.split()[0] if ' ' in model else model
        conditions.append("(model = %s OR model LIKE %s)")
        params.extend([model, f"{base_model}%"])

    if fuel:
        conditions.append("fuel_type = %s")
        params.append(fuel)

    if level.require_body_type and target_row.get("body_type"):
        conditions.append("body_type = %s")
        params.append(target_row['body_type'])

    if level.require_transmission and target_row.get("transmission"):
        conditions.append("transmission = %s")
        params.append(target_row['transmission'])

    if level.require_color and target_row.get("color"):
        conditions.append("color = %s")
        params.append(target_row['color'])

    if target_year is not None:
        year_min = target_year - level.year_delta
        year_max = target_year + level.year_delta
        conditions.append("""
            CAST(SUBSTRING(CAST(first_registration_raw AS TEXT), 1, 4) AS INTEGER) 
            BETWEEN %s AND %s
        """)
        params.extend([year_min, year_max])

    if target_mileage is not None and level.mileage_pct > 0:
        lower = max(0.0, target_mileage * (1 - level.mileage_pct))
        upper = target_mileage * (1 + level.mileage_pct)
        conditions.append("CAST(mileage_km AS FLOAT) BETWEEN %s AND %s")
        params.extend([lower, upper])

    if target_price is not None and level.price_pct > 0:
        lower = max(0.0, target_price * (1 - level.price_pct))
        upper = target_price * (1 + level.price_pct)
        conditions.append("""
            CAST(REGEXP_REPLACE(price, '[^0-9,]', '', 'g') AS FLOAT) BETWEEN %s AND %s
        """)
        params.extend([lower, upper])

    if target_power is not None and level.power_pct > 0:
        lower = target_power * (1 - level.power_pct)
        upper = target_power * (1 + level.power_pct)
        conditions.append("CAST(power_kw AS FLOAT) BETWEEN %s AND %s")
        params.extend([lower, upper])

    where_clause = " AND ".join(conditions)

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
            displacement_ccm,
            images,
            color,
            interior,
            interior_color,
            upholstery,
            drive_train,
            seats,
            doors,
            postal_code,
            country_code,
            city,
            previous_owners,
            had_accident
        FROM vehicle_marketplace.vehicle_data
        WHERE {where_clause}
        ORDER BY 
            CAST(REGEXP_REPLACE(price, '[^0-9,]', '', 'g') AS FLOAT) ASC NULLS LAST,
            CAST(mileage_km AS FLOAT) ASC NULLS LAST
        LIMIT {MAX_CANDIDATES_PER_LEVEL}
    """
    return query, params

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
            "ranking_engine": "hybrid-ranking-v1",
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
    Return ranked comparable vehicles using hybrid similarity and deal scoring.
    """
    try:
        top_param = request.args.get('top', '10')
        try:
            top = max(1, min(int(top_param), 50))
        except ValueError:
            top = 10

        preferred_color = request.args.get('preferred_color')
        preferred_drivetrain = request.args.get('preferred_drivetrain')

        conn = get_database_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
                    color,
                    drive_train,
                    interior,
                    interior_color,
                    upholstery,
                    seats,
                    doors,
                    data_source
                FROM vehicle_marketplace.vehicle_data
                WHERE vehicle_id = %s AND is_vehicle_available = true
            """, (vehicle_id,))

            target_raw = cursor.fetchone()
            if not target_raw:
                return jsonify({"error": f"Vehicle {vehicle_id} not found"}), 404

            target_year = extract_year(target_raw.get('first_registration_raw'))
            target_price = parse_price(target_raw.get('price'))
            target_mileage = float(target_raw['mileage_km']) if target_raw.get('mileage_km') else None
            target_power = float(target_raw['power_kw']) if target_raw.get('power_kw') else None

            target_vehicle: Dict[str, Any] = {
                'id': vehicle_id,
                'make': target_raw['make'],
                'model': target_raw['model'],
                'year': target_year,
                'mileage_km': target_mileage,
                'price': target_price,
                'fuel_type': target_raw['fuel_type'],
                'transmission': target_raw.get('transmission'),
                'body_type': target_raw.get('body_type'),
                'power_kw': target_power,
                'color': target_raw.get('color'),
                'drive_train': target_raw.get('drive_train'),
                'preferred_color': preferred_color,
                'preferred_drivetrain': preferred_drivetrain,
            }

            selected_candidates: List[Dict[str, Any]] = []
            seen_ids = set()
            applied_level: Optional[FilterLevel] = None

            for level in FILTER_LEVELS:
                query, params = build_candidate_query(
                    vehicle_id=vehicle_id,
                    target_row=target_raw,
                    level=level,
                    target_year=target_year,
                    target_price=target_price,
                    target_mileage=target_mileage,
                    target_power=target_power,
                )
                cursor.execute(query, params)
                rows = cursor.fetchall()

                new_rows = [row for row in rows if row['id'] not in seen_ids]
                if new_rows:
                    logger.info(
                        "Filter level %s produced %s candidates",
                        FILTER_LEVELS.index(level) + 1,
                        len(new_rows),
                    )
                    applied_level = level
                    for row in new_rows:
                        seen_ids.add(row['id'])
                    selected_candidates.extend(new_rows)

                if len(selected_candidates) >= top:
                    break

            if not selected_candidates:
                return jsonify({
                    "error": "No comparable vehicles found with current filters.",
                    "suggestion": "Try relaxing filters or choosing a different vehicle."
                }), 404

            candidates: List[Dict[str, Any]] = []
            for row in selected_candidates:
                year = extract_year(row.get('first_registration_raw'))
                price_val = parse_price(row.get('price'))
                mileage_val = float(row['mileage_km']) if row.get('mileage_km') else None
                power_val = float(row['power_kw']) if row.get('power_kw') else None
                displacement = float(row['displacement_ccm']) if row.get('displacement_ccm') else None
                seats = int(row['seats']) if row.get('seats') else None
                doors = int(row['doors']) if row.get('doors') else None

                images = row.get('images') or []
                if isinstance(images, str):
                    try:
                        images = json_lib.loads(images)
                    except Exception:
                        images = []
                elif not isinstance(images, list):
                    images = []

                candidates.append({
                    'id': row['id'],
                    'url': row['url'],
                    'price': price_val,
                    'mileage_km': mileage_val,
                    'year': year,
                    'make': row['make'],
                    'model': row['model'],
                    'fuel_type': row.get('fuel_type'),
                    'transmission': row.get('transmission'),
                    'body_type': row.get('body_type'),
                    'color': row.get('color'),
                    'interior': row.get('interior'),
                    'interior_color': row.get('interior_color'),
                    'upholstery': row.get('upholstery'),
                    'drive_train': row.get('drive_train'),
                    'seats': seats,
                    'doors': doors,
                    'description': row.get('description') or "",
                    'data_source': row.get('data_source'),
                    'power_kw': power_val,
                    'displacement_cc': displacement,
                    'previous_owners': row.get('previous_owners'),
                    'had_accident': row.get('had_accident'),
                    'postal_code': row.get('postal_code'),
                    'country_code': row.get('country_code'),
                    'city': row.get('city'),
                    'images': images,
                })

            ranked = ranking_engine.rank_candidates(target_vehicle, candidates)
            if not ranked:
                return jsonify({
                    "error": "Unable to rank comparable vehicles.",
                    "suggestion": "Try again later or choose a different vehicle."
                }), 500

            final_results = []
            for entry in ranked[:top]:
                vehicle = entry['vehicle']
                scores = entry['scores']
                deal_components = scores['components']['deal']
                median_price = deal_components.get('median_price')
                price_eur = vehicle.get('price')
                price_hat_value = price_eur
                if isinstance(median_price, (int, float)):
                    price_hat_value = median_price

                savings = None
                savings_pct = None
                if isinstance(target_price, (int, float)) and isinstance(price_eur, (int, float)):
                    savings = target_price - price_eur
                    savings_pct = (savings / target_price * 100) if target_price else None

                final_results.append({
                    'id': vehicle['id'],
                    'url': vehicle['url'],
                    'price_eur': float(price_eur) if isinstance(price_eur, (int, float)) else None,
                    'price_hat': float(price_hat_value) if isinstance(price_hat_value, (int, float)) else None,
                    'deal_score': round(float(scores['deal']), 4),
                    'similarity_score': round(float(scores['similarity']), 4),
                    'preference_score': round(float(scores['preference']), 4),
                    'final_score': round(float(scores['final']), 4),
                    'score': round(float(scores['similarity']), 4),
                    'savings': round(float(savings), 2) if isinstance(savings, (int, float)) else None,
                    'savings_percent': round(float(savings_pct), 2) if isinstance(savings_pct, (int, float)) else None,
                    'year': vehicle.get('year'),
                    'power_kw': vehicle.get('power_kw'),
                    'mileage_km': vehicle.get('mileage_km'),
                    'make': vehicle.get('make'),
                    'model': vehicle.get('model'),
                    'fuel_group': vehicle.get('fuel_type'),
                    'transmission_group': vehicle.get('transmission'),
                    'body_group': vehicle.get('body_type'),
                    'color': vehicle.get('color'),
                    'interior': vehicle.get('interior'),
                    'interior_color': vehicle.get('interior_color'),
                    'upholstery': vehicle.get('upholstery'),
                    'drive_train': vehicle.get('drive_train'),
                    'seats': vehicle.get('seats'),
                    'doors': vehicle.get('doors'),
                    'previous_owners': vehicle.get('previous_owners'),
                    'had_accident': vehicle.get('had_accident'),
                    'postal_code': vehicle.get('postal_code'),
                    'country_code': vehicle.get('country_code'),
                    'city': vehicle.get('city'),
                    'description': vehicle.get('description'),
                    'data_source': vehicle.get('data_source'),
                    'images': vehicle.get('images'),
                    'ranking_details': {
                        'filter_level': FILTER_LEVELS.index(applied_level) + 1 if applied_level else None,
                        'score_components': scores['components'],
                    }
                })

            logger.info("Returning %s ranked results for vehicle %s", len(final_results), vehicle_id)
            return jsonify(final_results), 200

    except Exception as e:
        logger.error(f"Error in get_comparables: {e}")
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

@app.route('/sample-vehicles', methods=['GET'])
def get_sample_vehicles():
    """Get sample vehicle IDs for testing"""
    try:
        limit = int(request.args.get('limit', 10))
        limit = max(1, min(limit, 50))  # Cap at 50
        
        conn = get_database_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    vehicle_id,
                    make,
                    model,
                    first_registration_raw as year,
                    price,
                    mileage_km,
                    listing_url,
                    data_source
                FROM vehicle_marketplace.vehicle_data
                WHERE is_vehicle_available = true
                AND vehicle_id IS NOT NULL
                AND make IS NOT NULL
                AND model IS NOT NULL
                AND price IS NOT NULL
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            vehicles = cursor.fetchall()
            
            if not vehicles:
                return jsonify({"error": "No vehicles found"}), 404
            
            sample_list = []
            for v in vehicles:
                sample_list.append({
                    "vehicle_id": v['vehicle_id'],
                    "make": v['make'],
                    "model": v['model'],
                    "year": v['year'],
                    "price": v['price'],
                    "mileage_km": v['mileage_km'],
                    "listing_url": v['listing_url'],
                    "data_source": v['data_source'],
                    "api_url": f"/listings/{v['vehicle_id']}",
                    "comparables_url": f"/listings/{v['vehicle_id']}/comparables"
                })
            
            return jsonify({
                "sample_vehicles": sample_list,
                "total_found": len(vehicles),
                "timestamp": datetime.now().isoformat()
            }), 200
            
    except Exception as e:
        logger.error(f"Error in get_sample_vehicles: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info("Starting CARMA Hybrid Ranking API...")
    logger.info("Progressive filter levels configured: %s", len(FILTER_LEVELS))
    app.run(host="0.0.0.0", port=port, debug=False)
