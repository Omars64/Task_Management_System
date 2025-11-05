"""Add password reset fields to existing database"""

import pymssql
from datetime import datetime

# Database connection settings
DB_HOST = 'database'
DB_PORT = 1433
DB_NAME = 'workhub'
DB_USER = 'sa'
DB_PASSWORD = 'YourStrong!Passw0rd'

def add_password_reset_fields():
    try:
        print("Connecting to database...")
        conn = pymssql.connect(
            server=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        print("Adding password reset fields to users table...")
        
        # Check if columns already exist before adding
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'reset_token')
            BEGIN
                ALTER TABLE users ADD reset_token NVARCHAR(255) NULL;
            END
        """)
        
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'reset_token_expires')
            BEGIN
                ALTER TABLE users ADD reset_token_expires DATETIME NULL;
            END
        """)
        
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'force_password_change')
            BEGIN
                ALTER TABLE users ADD force_password_change BIT DEFAULT 0;
            END
        """)
        
        conn.commit()
        print("✓ Password reset fields added successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    add_password_reset_fields()

