#!/usr/bin/env python3
"""
CARMA Compare API - Flask Version (No host header issues)
Simple Flask API for Azure Container Apps
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow all origins for Container Apps

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
            import re
            price_str = str(vehicle['price'])
            price_clean = re.sub(r'[^0-9,]', '', price_str).replace(',', '.')
            price_numeric = float(price_clean) if price_clean else 0
            price_hat = price_numeric * 0.95
            deal_score = (price_hat - price_numeric) / price_numeric if price_numeric > 0 else 0
            
            # Parse year from first_registration_raw
            year = None
            try:
                if vehicle['year']:
                    # Try to extract year from date string like '2019-03-01' or just '2019'
                    year_str = str(vehicle['year'])[:4]
                    year = int(year_str)
            except (ValueError, TypeError):
                pass
            
            # Process images field (might be JSON, string, or None)
            images_data = vehicle.get('images') or []
            if isinstance(images_data, str):
                try:
                    import json as json_lib
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
    """Get comparable vehicles"""
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
                    fuel_type as fuel_group,
                    transmission as transmission_group,
                    body_type as body_group,
                    power_kw,
                    mileage_km
                FROM vehicle_marketplace.vehicle_data
                WHERE vehicle_id = %s AND is_vehicle_available = true
            """, (vehicle_id,))
            
            target = cursor.fetchone()
            
            if not target:
                return jsonify({"error": f"Vehicle {vehicle_id} not found"}), 404
            
            # Extract year from target first_registration_raw
            target_year = None
            try:
                if target['first_registration_raw']:
                    target_year = int(str(target['first_registration_raw'])[:4])
            except (ValueError, TypeError):
                pass
            
            # Find similar vehicles
            cursor.execute("""
                SELECT 
                    vehicle_id as id,
                    listing_url as url,
                    price,
                    mileage_km,
                    first_registration_raw as year_raw,
                    make,
                    model,
                    fuel_type as fuel_group,
                    transmission as transmission_group,
                    body_type as body_group,
                    description,
                    data_source,
                    power_kw,
                    images
                FROM vehicle_marketplace.vehicle_data
                WHERE is_vehicle_available = true
                AND vehicle_id != %s
                AND (
                    (make = %s AND model = %s) OR
                    (make = %s AND fuel_type = %s AND transmission = %s) OR
                    (make = %s AND first_registration_raw IS NOT NULL)
                )
                ORDER BY 
                    CASE 
                        WHEN make = %s AND model = %s THEN 1
                        WHEN make = %s AND fuel_type = %s AND transmission = %s THEN 2
                        ELSE 3
                    END,
                    mileage_km
                LIMIT %s
            """, (
                vehicle_id,
                target['make'], target['model'],
                target['make'], target['fuel_group'], target['transmission_group'],
                target['make'],
                target['make'], target['model'],
                target['make'], target['fuel_group'], target['transmission_group'],
                top
            ))
            
            comparables = cursor.fetchall()
            
            if not comparables:
                return jsonify({"error": "No comparable vehicles found"}), 404
            
            # Format results
            result = []
            for i, comp in enumerate(comparables):
                # Parse price from string
                try:
                    import re
                    price_str = str(comp['price'])
                    price_clean = re.sub(r'[^0-9,]', '', price_str).replace(',', '.')
                    price_numeric = float(price_clean) if price_clean else 0
                except (ValueError, TypeError):
                    price_numeric = 0
                
                price_hat = price_numeric * 0.95
                deal_score = (price_hat - price_numeric) / price_numeric if price_numeric > 0 else 0
                similarity_score = max(0, 1.0 - (i * 0.1))
                
                # Extract year from year_raw
                comp_year = None
                try:
                    if comp['year_raw']:
                        comp_year = int(str(comp['year_raw'])[:4])
                except (ValueError, TypeError):
                    pass
                
                # Process images field (might be JSON, string, or None)
                comp_images = comp.get('images') or []
                if isinstance(comp_images, str):
                    try:
                        import json as json_lib
                        comp_images = json_lib.loads(comp_images)
                    except:
                        comp_images = []
                elif not isinstance(comp_images, list):
                    comp_images = []
                
                result.append({
                    "id": comp['id'],
                    "url": comp['url'],
                    "price_eur": float(price_numeric),
                    "price_hat": float(price_hat),
                    "deal_score": float(deal_score),
                    "score": float(similarity_score),
                    "year": comp_year,
                    "power_kw": float(comp['power_kw']) if comp['power_kw'] else None,
                    "mileage_km": float(comp['mileage_km']),
                    "make": comp['make'],
                    "model": comp['model'],
                    "fuel_group": comp['fuel_group'],
                    "transmission_group": comp['transmission_group'],
                    "body_group": comp['body_group'],
                    "description": comp['description'] or "",
                    "data_source": comp['data_source'],
                    "images": comp_images
                })
            
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in get_comparables: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/sample-vehicles', methods=['GET'])
def get_sample_vehicles():
    """Get sample vehicle IDs"""
    try:
        limit = int(request.args.get('limit', 10))
        
        conn = get_database_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    vehicle_id,
                    make,
                    model,
                    first_registration_raw as year,
                    listing_url
                FROM vehicle_marketplace.vehicle_data
                WHERE is_vehicle_available = true
                AND vehicle_id IS NOT NULL
                AND make IS NOT NULL
                AND model IS NOT NULL
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            vehicles = cursor.fetchall()
            
            if not vehicles:
                return jsonify({"error": "No vehicles found"}), 404
            
            return jsonify({
                "sample_vehicles": [dict(v) for v in vehicles],
                "total_found": len(vehicles),
                "timestamp": datetime.now().isoformat()
            }), 200
            
    except Exception as e:
        logger.error(f"Error in get_sample_vehicles: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
