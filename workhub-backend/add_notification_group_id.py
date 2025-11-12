"""Add related_group_id column to notifications table"""

from app import create_app
from models import db
from sqlalchemy import text

def add_notification_group_id():
    """Add related_group_id column to notifications table if it doesn't exist"""
    app = create_app()
    with app.app_context():
        try:
            print("Checking for related_group_id column in notifications table...")
            with db.engine.begin() as conn:
                # Check if column exists
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='notifications' AND COLUMN_NAME='related_group_id'
                """))
                
                if result.scalar() == 0:
                    print("Adding related_group_id column to notifications table...")
                    # Add the column
                    conn.execute(text("""
                        ALTER TABLE dbo.notifications ADD related_group_id INT NULL;
                    """))
                    # Add foreign key constraint
                    conn.execute(text("""
                        ALTER TABLE dbo.notifications 
                        ADD FOREIGN KEY (related_group_id) REFERENCES chat_groups(id);
                    """))
                    print("✓ Added related_group_id column and foreign key successfully!")
                else:
                    print("✓ related_group_id column already exists")
                    
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(add_notification_group_id())

