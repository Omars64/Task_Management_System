"""
Quick database fix for chat_messages table
Run this to add missing columns that are causing the 500 error
"""
import os
import psycopg2
from urllib.parse import urlparse

# Get database URL from environment or use default
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/workhub')

def run_migration():
    """Add missing columns to chat_messages table"""
    try:
        # Parse database URL
        result = urlparse(DATABASE_URL)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port or 5432
        
        print(f"Connecting to database: {database} on {hostname}:{port}")
        
        # Connect to database
        conn = psycopg2.connect(
            database=database,
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        
        cursor = conn.cursor()
        
        print("\n🔧 Adding missing columns to chat_messages table...")
        
        # Add columns one by one
        columns_to_add = [
            ("updated_at", "TIMESTAMP"),
            ("is_edited", "BOOLEAN DEFAULT FALSE"),
            ("is_deleted", "BOOLEAN DEFAULT FALSE"),
            ("deleted_for_sender", "BOOLEAN DEFAULT FALSE"),
            ("deleted_for_recipient", "BOOLEAN DEFAULT FALSE")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                sql = f"ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
                cursor.execute(sql)
                print(f"  ✅ Added column: {col_name}")
            except Exception as e:
                print(f"  ⚠️  Column {col_name}: {e}")
        
        # Update existing rows with default values
        print("\n🔄 Updating existing rows with default values...")
        cursor.execute("""
            UPDATE chat_messages 
            SET 
              is_edited = COALESCE(is_edited, FALSE),
              is_deleted = COALESCE(is_deleted, FALSE),
              deleted_for_sender = COALESCE(deleted_for_sender, FALSE),
              deleted_for_recipient = COALESCE(deleted_for_recipient, FALSE)
            WHERE is_edited IS NULL 
               OR is_deleted IS NULL 
               OR deleted_for_sender IS NULL 
               OR deleted_for_recipient IS NULL;
        """)
        
        # Commit changes
        conn.commit()
        
        # Verify columns exist
        print("\n📋 Verifying columns in chat_messages table:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'chat_messages'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
        
        print("\n✅ Migration completed successfully!")
        print("\n🚀 Now restart your backend server and refresh the chat page.")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check DATABASE_URL environment variable")
        print(f"3. Current URL: {DATABASE_URL}")
        print("4. Verify database credentials")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(run_migration())

