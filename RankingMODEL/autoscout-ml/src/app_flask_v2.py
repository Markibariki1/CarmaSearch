#!/usr/bin/env python3
"""
CARMA Compare API - Flask Version with Weighted Similarity Engine
Advanced ranking using content-based similarity + deal scoring
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

# Import our new similarity engine
from similarity_engine import SimilarityEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow all origins for Container Apps

# Initialize similarity engine
similarity_engine = SimilarityEngine()

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
            "similarity_engine": "v2.0-weighted",
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
                    images
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
            
            # Simple price estimate (will be replaced by market-based scoring)
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
    """Get comparable vehicles using weighted similarity engine"""
    try:
        top = int(request.args.get('top', 10))
        if top > 50:
            top = 50
        
        conn = get_database_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get target vehicle
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
                    price
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
            
            # Find candidate vehicles (SQL filtering for performance)
            cursor.execute("""
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
                    images
                FROM vehicle_marketplace.vehicle_data
                WHERE is_vehicle_available = true
                AND vehicle_id != %s
                AND make = %s
                AND (
                    model = %s OR 
                    (fuel_type = %s AND transmission = %s)
                )
                LIMIT 200
            """, (
                vehicle_id,
                target_raw['make'],
                target_raw['model'],
                target_raw['fuel_type'],
                target_raw['transmission']
            ))
            
            candidates_raw = cursor.fetchall()
            
            if not candidates_raw:
                return jsonify({"error": "No comparable vehicles found"}), 404
            
            # Convert target to dict for similarity engine
            target = {
                'id': vehicle_id,
                'make': target_raw['make'],
                'model': target_raw['model'],
                'year': target_year,
                'mileage_km': float(target_raw['mileage_km']) if target_raw['mileage_km'] else None,
                'price': target_price,
                'fuel_type': target_raw['fuel_type'],
                'transmission': target_raw['transmission'],
                'body_type': target_raw['body_type'],
                'power_kw': float(target_raw['power_kw']) if target_raw['power_kw'] else None
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
                    'description': c['description'] or "",
                    'data_source': c['data_source'],
                    'power_kw': float(c['power_kw']) if c['power_kw'] else None,
                    'images': images
                }
                candidates.append(candidate)
            
            # Use similarity engine to rank candidates
            ranked = similarity_engine.rank_candidates(target, candidates, market_vehicles=candidates)
            
            # Format results
            results = []
            for vehicle, similarity_score, deal_score, final_score in ranked[:top]:
                # Calculate price_hat based on market percentile
                price_eur = vehicle['price'] or 0
                price_hat = price_eur * (1.0 + (deal_score - 0.5) * 0.2)  # Adjust based on deal score
                
                result = {
                    'id': vehicle['id'],
                    'url': vehicle['url'],
                    'price_eur': float(price_eur),
                    'price_hat': float(price_hat),
                    'deal_score': float(deal_score),
                    'score': float(similarity_score),  # Similarity score
                    'final_score': float(final_score),  # Combined score
                    'year': vehicle['year'],
                    'power_kw': vehicle['power_kw'],
                    'mileage_km': vehicle['mileage_km'],
                    'make': vehicle['make'],
                    'model': vehicle['model'],
                    'fuel_group': vehicle['fuel_type'],
                    'transmission_group': vehicle['transmission'],
                    'body_group': vehicle['body_type'],
                    'description': vehicle['description'],
                    'data_source': vehicle['data_source'],
                    'images': vehicle['images']
                }
                results.append(result)
            
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
    app.run(host="0.0.0.0", port=port, debug=False)
