#!/usr/bin/env python3
"""
Cloud Database Setup Script
==========================

This script sets up a cloud PostgreSQL database using Supabase
for deployment without requiring local database access.
"""

import os

def create_env_template():
    """Create a template .env file for cloud deployment."""
    env_content = """# Cloud Database Configuration (Supabase)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_DB_URL=postgresql://postgres:your_password@db.your_project_ref.supabase.co:5432/postgres

# Fallback to original Azure (if it becomes available)
DATABASE_HOST=carma.postgres.database.azure.com
DATABASE_PORT=5432
DATABASE_USER=carmaadmin
DATABASE_PASSWORD=Hosthunter1221!
DATABASE_NAME=postgres

# WebShare Proxy Configuration
WEBSHARE_PROXY_USER=tjhtsouc-rotate
WEBSHARE_PROXY_PASSWORD=a7ijmxf0dczj
WEBSHARE_PROXY_HOST=p.webshare.io
WEBSHARE_PROXY_PORT=80

# Scraping Configuration
SCRAPE_DO_TOKEN=6b1f1d097e5c4a5685c6ceb84319be604126f94dbc8
AUTOSCOUT_THREAD_COUNT=50
MOBILE_THREAD_COUNT=20
"""
    
    with open('.env.cloud', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env.cloud template")
    return True

def create_cloud_database_manager():
    """Create a cloud database manager that can work with Supabase."""
    manager_code = '''#!/usr/bin/env python3
"""
Cloud Database Manager
=====================

This module provides database connectivity using Supabase cloud PostgreSQL.
"""

import psycopg2
import psycopg2.pool
import os
from dotenv import load_dotenv
import logging
import time
from typing import Optional, Dict, Any

load_dotenv()

class CloudDatabaseManager:
    """Manages cloud database connections with Supabase fallback."""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.connection_pool = None
        self.using_supabase = False
        self._setup_connection()
    
    def _setup_connection(self):
        """Setup cloud database connection."""
        # Try Supabase first
        supabase_db_url = os.getenv('SUPABASE_DB_URL')
        if supabase_db_url:
            try:
                self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=supabase_db_url,
                    sslmode='require',
                    connect_timeout=30,
                    application_name='carma_cloud_manager'
                )
                
                # Test connection
                conn = self.connection_pool.getconn()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                self.connection_pool.putconn(conn)
                
                self.logger.info("✅ Supabase cloud database connection established")
                self.using_supabase = True
                return
                
            except Exception as e:
                self.logger.warning(f"⚠️ Supabase connection failed: {e}")
        
        # Fallback to Azure (if available)
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dbname=os.getenv('DATABASE_NAME', 'postgres'),
                user=os.getenv('DATABASE_USER', 'carmaadmin'),
                password=os.getenv('DATABASE_PASSWORD', 'Hosthunter1221!'),
                host=os.getenv('DATABASE_HOST', 'carma.postgres.database.azure.com'),
                port=int(os.getenv('DATABASE_PORT', '5432')),
                sslmode='require',
                connect_timeout=30,
                application_name='carma_azure_fallback'
            )
            
            # Test connection
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            self.connection_pool.putconn(conn)
            
            self.logger.info("✅ Azure database connection established")
            self.using_supabase = False
            
        except Exception as e:
            self.logger.error(f"❌ All database connections failed: {e}")
            raise Exception("No database connections available")
    
    def get_connection(self):
        """Get a database connection."""
        if not self.connection_pool:
            raise Exception("No database connection pool available")
        return self.connection_pool.getconn()
    
    def put_connection(self, conn):
        """Return a database connection to the pool."""
        if self.connection_pool:
            self.connection_pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = None) -> list:
        """Execute a query and return results."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            self.logger.error(f"❌ Query execution failed: {e}")
            raise
        finally:
            if conn:
                self.put_connection(conn)
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an update query and return affected rows."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            conn.commit()
            cursor.close()
            return affected_rows
        except Exception as e:
            self.logger.error(f"❌ Update execution failed: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.put_connection(conn)
    
    def setup_schema(self):
        """Setup the database schema."""
        try:
            # Create schema
            self.execute_update('CREATE SCHEMA IF NOT EXISTS vehicle_marketplace;')
            
            # Create table
            create_table_sql = "CREATE TABLE IF NOT EXISTS vehicle_marketplace.vehicle_data (vehicle_id VARCHAR(255) PRIMARY KEY, listing_url TEXT, price DECIMAL(10,2), mileage_km INTEGER, year INTEGER, make VARCHAR(100), model VARCHAR(100), fuel_group VARCHAR(50), transmission_group VARCHAR(50), body_group VARCHAR(50), description TEXT, data_source VARCHAR(100), power_kw INTEGER, is_vehicle_available BOOLEAN DEFAULT true, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
            self.execute_update(create_table_sql)
            
            # Create indexes
            self.execute_update('CREATE INDEX IF NOT EXISTS idx_vehicle_available ON vehicle_marketplace.vehicle_data(is_vehicle_available);')
            self.execute_update('CREATE INDEX IF NOT EXISTS idx_created_at ON vehicle_marketplace.vehicle_data(created_at);')
            
            self.logger.info("✅ Database schema setup complete")
            
        except Exception as e:
            self.logger.error(f"❌ Schema setup failed: {e}")
            raise
    
    def get_vehicle_count(self) -> int:
        """Get total vehicle count."""
        try:
            results = self.execute_query(
                "SELECT COUNT(*) FROM vehicle_marketplace.vehicle_data WHERE is_vehicle_available = true"
            )
            return results[0][0] if results else 0
        except Exception as e:
            self.logger.error(f"❌ Failed to get vehicle count: {e}")
            return 0
    
    def get_recent_vehicles(self, hours: int = 24) -> int:
        """Get count of vehicles added in the last N hours."""
        try:
            results = self.execute_query(
                "SELECT COUNT(*) FROM vehicle_marketplace.vehicle_data WHERE created_at >= NOW() - INTERVAL '%s hours'",
                (hours,)
            )
            return results[0][0] if results else 0
        except Exception as e:
            self.logger.error(f"❌ Failed to get recent vehicles: {e}")
            return 0
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        return {
            "using_supabase": self.using_supabase,
            "connection_available": self.connection_pool is not None,
            "total_vehicles": self.get_vehicle_count(),
            "recent_vehicles_24h": self.get_recent_vehicles(24)
        }
    
    def close_all_connections(self):
        """Close all database connections."""
        if self.connection_pool:
            self.connection_pool.closeall()
        self.logger.info("🔌 All database connections closed")

# Global instance
cloud_db_manager = None

def get_cloud_db_manager() -> CloudDatabaseManager:
    """Get the global cloud database manager instance."""
    global cloud_db_manager
    if cloud_db_manager is None:
        cloud_db_manager = CloudDatabaseManager()
    return cloud_db_manager

def test_cloud_database():
    """Test the cloud database connection."""
    print("🔍 Testing Cloud Database Manager...")
    
    try:
        db = get_cloud_db_manager()
        status = db.get_connection_status()
        
        print(f"✅ Cloud Database Status:")
        print(f"   Using Supabase: {status['using_supabase']}")
        print(f"   Connection Available: {status['connection_available']}")
        print(f"   Total Vehicles: {status['total_vehicles']:,}")
        print(f"   Recent Vehicles (24h): {status['recent_vehicles_24h']:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cloud database test failed: {e}")
        return False

if __name__ == "__main__":
    test_cloud_database()
'''
    
    with open('cloud_database_manager.py', 'w') as f:
        f.write(manager_code)
    
    print("✅ Created cloud_database_manager.py")
    return True

def main():
    """Main setup function."""
    print("🚀 Setting up Cloud Database Solution")
    print("=" * 50)
    
    # Create environment template
    create_env_template()
    
    # Create cloud database manager
    create_cloud_database_manager()
    
    print("\n📋 Next Steps:")
    print("1. Go to https://supabase.com")
    print("2. Create a new project")
    print("3. Get your project URL and API key")
    print("4. Update .env.cloud with your Supabase credentials")
    print("5. Run: python cloud_database_manager.py")
    print("6. Update your applications to use the cloud database manager")
    
    print("\n✅ Cloud database setup files created!")

if __name__ == "__main__":
    main()