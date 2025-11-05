#!/usr/bin/env python3
"""
Script to ensure reminders and meetings tables exist in the database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from sqlalchemy import text, inspect

def ensure_tables():
    """Ensure reminders and meetings tables exist"""
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print("Checking for reminders and meetings tables...")
        
        # Check reminders table
        if 'reminders' not in existing_tables:
            print("Creating reminders table...")
            try:
                with db.engine.begin() as conn:
                    conn.execute(text("""
                        CREATE TABLE reminders (
                            id INT PRIMARY KEY IDENTITY(1,1),
                            user_id INT NOT NULL,
                            task_id INT NULL,
                            title NVARCHAR(200) NOT NULL,
                            description NVARCHAR(MAX) NULL,
                            reminder_date DATETIME NOT NULL,
                            reminder_type NVARCHAR(50) DEFAULT 'custom',
                            days_before INT NULL,
                            time_based DATETIME NULL,
                            is_sent BIT DEFAULT 0,
                            created_at DATETIME DEFAULT GETUTCDATE(),
                            FOREIGN KEY (user_id) REFERENCES users(id),
                            FOREIGN KEY (task_id) REFERENCES tasks(id)
                        );
                    """))
                print("✓ reminders table created")
            except Exception as e:
                print(f"Error creating reminders table: {e}")
        else:
            print("✓ reminders table exists")
        
        # Check meetings table
        if 'meetings' not in existing_tables:
            print("Creating meetings table...")
            try:
                with db.engine.begin() as conn:
                    conn.execute(text("""
                        CREATE TABLE meetings (
                            id INT PRIMARY KEY IDENTITY(1,1),
                            title NVARCHAR(200) NOT NULL,
                            description NVARCHAR(MAX) NULL,
                            start_time DATETIME NOT NULL,
                            end_time DATETIME NOT NULL,
                            location NVARCHAR(255) NULL,
                            created_by INT NOT NULL,
                            project_id INT NULL,
                            created_at DATETIME DEFAULT GETUTCDATE(),
                            updated_at DATETIME DEFAULT GETUTCDATE(),
                            FOREIGN KEY (created_by) REFERENCES users(id),
                            FOREIGN KEY (project_id) REFERENCES projects(id)
                        );
                    """))
                print("✓ meetings table created")
            except Exception as e:
                print(f"Error creating meetings table: {e}")
        else:
            print("✓ meetings table exists")
        
        # Check meeting_invitations table
        if 'meeting_invitations' not in existing_tables:
            print("Creating meeting_invitations table...")
            try:
                with db.engine.begin() as conn:
                    conn.execute(text("""
                        CREATE TABLE meeting_invitations (
                            id INT PRIMARY KEY IDENTITY(1,1),
                            meeting_id INT NOT NULL,
                            user_id INT NOT NULL,
                            status NVARCHAR(20) DEFAULT 'pending',
                            rejection_reason NVARCHAR(MAX) NULL,
                            responded_at DATETIME NULL,
                            created_at DATETIME DEFAULT GETUTCDATE(),
                            FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                            FOREIGN KEY (user_id) REFERENCES users(id)
                        );
                    """))
                print("✓ meeting_invitations table created")
            except Exception as e:
                print(f"Error creating meeting_invitations table: {e}")
        else:
            print("✓ meeting_invitations table exists")
        
        print("\nAll tables verified!")

if __name__ == '__main__':
    ensure_tables()

