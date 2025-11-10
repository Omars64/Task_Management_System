"""
Comprehensive migration script to ensure ALL chat_messages columns exist
This script checks and adds any missing columns required by the ChatMessage model
"""
from app import create_app
from models import db
from sqlalchemy import text


def ensure_all_chat_columns():
    """Ensure all columns exist in chat_messages table (SQL Server compatible)"""
    app = create_app()
    with app.app_context():
        with db.engine.begin() as conn:
            print("=" * 60)
            print("Checking and adding missing columns to chat_messages table...")
            print("=" * 60)
            
            # List of all required columns with their SQL Server definitions
            required_columns = [
                {
                    'name': 'reply_to_id',
                    'definition': 'INT NULL',
                    'description': 'Foreign key to chat_messages.id for reply functionality'
                },
                {
                    'name': 'updated_at',
                    'definition': 'DATETIME NULL',
                    'description': 'Timestamp when message was last edited'
                },
                {
                    'name': 'is_edited',
                    'definition': 'BIT NOT NULL DEFAULT(0)',
                    'description': 'Flag indicating if message was edited'
                },
                {
                    'name': 'is_deleted',
                    'definition': 'BIT NOT NULL DEFAULT(0)',
                    'description': 'Flag indicating if message was deleted for everyone'
                },
                {
                    'name': 'deleted_for_sender',
                    'definition': 'BIT NOT NULL DEFAULT(0)',
                    'description': 'Flag indicating if message was deleted for sender'
                },
                {
                    'name': 'deleted_for_recipient',
                    'definition': 'BIT NOT NULL DEFAULT(0)',
                    'description': 'Flag indicating if message was deleted for recipient'
                }
            ]
            
            added_count = 0
            existing_count = 0
            
            for col in required_columns:
                # Check if column exists
                check_query = text(f"""
                    IF NOT EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='chat_messages' AND COLUMN_NAME='{col['name']}'
                    )
                    BEGIN 
                        ALTER TABLE dbo.chat_messages ADD {col['name']} {col['definition']};
                        SELECT 1 AS added;
                    END
                    ELSE
                    BEGIN
                        SELECT 0 AS added;
                    END
                """)
                
                try:
                    result = conn.execute(check_query)
                    row = result.fetchone()
                    if row and row[0] == 1:
                        print(f"✅ Added column: {col['name']} ({col['description']})")
                        added_count += 1
                    else:
                        print(f"✓ Column already exists: {col['name']}")
                        existing_count += 1
                except Exception as e:
                    print(f"⚠️  Error checking/adding column {col['name']}: {e}")
            
            # Add foreign key for reply_to_id if it doesn't exist
            if added_count > 0 or existing_count > 0:
                try:
                    # Check if foreign key exists
                    fk_check = text("""
                        IF NOT EXISTS (
                            SELECT 1 FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS 
                            WHERE CONSTRAINT_NAME = 'FK_chat_messages_reply_to'
                        )
                        BEGIN
                            ALTER TABLE dbo.chat_messages 
                            ADD CONSTRAINT FK_chat_messages_reply_to 
                            FOREIGN KEY (reply_to_id) REFERENCES chat_messages(id);
                        END
                    """)
                    conn.execute(fk_check)
                    print("✅ Foreign key constraint for reply_to_id ensured")
                except Exception as e:
                    # Foreign key might already exist or column might not exist yet
                    if 'reply_to_id' in str(e).lower() or 'column' in str(e).lower():
                        print(f"⚠️  Note: Could not add foreign key for reply_to_id (may already exist): {e}")
                    else:
                        print(f"⚠️  Error adding foreign key: {e}")
            
            # Ensure content column is Unicode (for emojis)
            try:
                content_check = text("""
                    IF EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='chat_messages' 
                        AND COLUMN_NAME='content' AND DATA_TYPE <> 'nvarchar'
                    )
                    BEGIN 
                        ALTER TABLE dbo.chat_messages ALTER COLUMN content NVARCHAR(MAX) NOT NULL;
                        SELECT 1 AS updated;
                    END
                    ELSE
                    BEGIN
                        SELECT 0 AS updated;
                    END
                """)
                result = conn.execute(content_check)
                row = result.fetchone()
                if row and row[0] == 1:
                    print("✅ Updated content column to NVARCHAR(MAX) for emoji support")
                else:
                    print("✓ Content column already Unicode (NVARCHAR)")
            except Exception as e:
                print(f"⚠️  Note: Content column check: {e}")
            
            print("=" * 60)
            print(f"Migration Summary:")
            print(f"  - Columns added: {added_count}")
            print(f"  - Columns already existing: {existing_count}")
            print(f"  - Total required columns: {len(required_columns)}")
            print("=" * 60)
            
            if added_count > 0:
                print("\n✅ Migration completed successfully!")
                print("   All required columns are now present in chat_messages table.")
            else:
                print("\n✅ All columns already exist - no migration needed!")
            
            # Verify all columns exist
            verify_query = text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='chat_messages'
                ORDER BY ORDINAL_POSITION
            """)
            result = conn.execute(verify_query)
            columns = result.fetchall()
            
            print(f"\n📋 Current chat_messages table structure ({len(columns)} columns):")
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"   - {col[0]}: {col[1]} {nullable}{default}")


if __name__ == "__main__":
    ensure_all_chat_columns()

