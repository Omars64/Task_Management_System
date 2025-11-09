#!/usr/bin/env python3
"""
Database Connection Diagnostic Script
Checks if the application is using public or private IP for database connection
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_db_connection():
    """Check database connection configuration"""
    print("=" * 60)
    print("DATABASE CONNECTION DIAGNOSTIC")
    print("=" * 60)
    
    # Get environment variables
    db_host = os.environ.get('DB_HOST')
    db_port = os.environ.get('DB_PORT', '1433')
    db_name = os.environ.get('DB_NAME', 'workhub')
    cloud_sql_conn = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
    
    print(f"\n[INFO] Current Configuration:")
    print(f"   DB_HOST: {db_host or 'Not set (will use localhost)'}")
    print(f"   DB_PORT: {db_port}")
    print(f"   DB_NAME: {db_name}")
    print(f"   CLOUD_SQL_CONNECTION_NAME: {cloud_sql_conn or 'Not set'}")
    
    # Check if using public IP
    if db_host == '34.31.203.11':
        print(f"\n[WARNING] Using PUBLIC IP (34.31.203.11)")
        print(f"   This will cause SLOW performance!")
        print(f"   Recommendation: Switch to PRIVATE IP (10.119.176.3)")
        return False
    elif db_host == '10.119.176.3':
        print(f"\n[SUCCESS] Using PRIVATE IP (10.119.176.3)")
        print(f"   This provides optimal performance and security")
        return True
    elif db_host in ['localhost', '127.0.0.1', 'database', 'host.docker.internal']:
        print(f"\n[INFO] Using local database ({db_host})")
        print(f"   This is fine for local development")
        return True
    elif db_host:
        print(f"\n[WARNING] Using custom DB_HOST ({db_host})")
        print(f"   Please verify this is the correct IP address")
        return None
    else:
        print(f"\n[WARNING] DB_HOST not set")
        print(f"   Will default to localhost")
        return None
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    result = check_db_connection()
    sys.exit(0 if result else 1)

