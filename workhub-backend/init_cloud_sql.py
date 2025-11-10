#!/usr/bin/env python3
"""
Database initialization script for Cloud SQL
Creates all required tables in the Cloud SQL database
Run this script to initialize the database schema.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from sqlalchemy import text, inspect

def init_database():
    """Initialize database schema - creates all tables"""
    from flask import has_app_context, current_app
    
    # If called from within an app context (e.g., from app.py), use current app
    # Otherwise, create a new app
    if has_app_context():
        app = current_app
        _init_schema(app)
    else:
        app = create_app()
        with app.app_context():
            _init_schema(app)

def _init_schema(app):
    """Internal function to initialize schema - works with or without app context"""
    # Use the provided app context (we're already in one when called from app.py)
    # But ensure we have an app context for database operations
    from flask import has_app_context
    
    if has_app_context():
        # Already in app context, proceed directly
        _do_init()
    else:
        # Not in app context, create one
        with app.app_context():
            _do_init()

def _do_init():
    """Actually perform the initialization - must be called within app context"""
    print("=" * 60)
    print("Initializing Cloud SQL Database Schema")
    print("=" * 60)
    
    # Check existing tables
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()
    print(f"\nExisting tables: {existing_tables}\n")
    
    # Create all tables using SQLAlchemy
    print("Creating tables using SQLAlchemy models...")
    try:
        db.create_all()
        print("✓ SQLAlchemy create_all() completed")
    except Exception as e:
        print(f"⚠ Warning from create_all(): {e}")
        print("Continuing with manual table creation...")
    
    # Manually create tables that might not be created by SQLAlchemy
    # (Some tables are created via migrations in init_db.py)
    print("\nEnsuring all required tables exist...")
    
    tables_to_create = {
            'projects': """
                IF OBJECT_ID('dbo.projects', 'U') IS NULL
                BEGIN
                    CREATE TABLE dbo.projects (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        name NVARCHAR(150) NOT NULL UNIQUE,
                        description NVARCHAR(MAX) NULL,
                        created_at DATETIME NULL,
                        updated_at DATETIME NULL,
                        owner_id INT NULL,
                        FOREIGN KEY (owner_id) REFERENCES users(id)
                    );
                END
            """,
            'sprints': """
                IF OBJECT_ID('dbo.sprints', 'U') IS NULL
                BEGIN
                    CREATE TABLE dbo.sprints (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        project_id INT NOT NULL,
                        name NVARCHAR(150) NOT NULL,
                        goal NVARCHAR(255) NULL,
                        start_date DATETIME NOT NULL,
                        end_date DATETIME NOT NULL,
                        created_at DATETIME NULL,
                        updated_at DATETIME NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                    );
                END
            """,
            'project_members': """
                IF OBJECT_ID('dbo.project_members', 'U') IS NULL
                BEGIN
                    CREATE TABLE dbo.project_members (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        project_id INT NOT NULL,
                        user_id INT NOT NULL,
                        role NVARCHAR(50) NULL,
                        joined_at DATETIME NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(id),
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        CONSTRAINT uq_project_user UNIQUE (project_id, user_id)
                    );
                END
            """,
            'reminders': """
                IF OBJECT_ID('dbo.reminders', 'U') IS NULL
                BEGIN
                    CREATE TABLE dbo.reminders (
                        id INT IDENTITY(1,1) PRIMARY KEY,
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
                END
            """,
            'meetings': """
                IF OBJECT_ID('dbo.meetings', 'U') IS NULL
                BEGIN
                    CREATE TABLE dbo.meetings (
                        id INT IDENTITY(1,1) PRIMARY KEY,
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
                END
            """,
            'meeting_invitations': """
                IF OBJECT_ID('dbo.meeting_invitations', 'U') IS NULL
                BEGIN
                    CREATE TABLE dbo.meeting_invitations (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        meeting_id INT NOT NULL,
                        user_id INT NOT NULL,
                        status NVARCHAR(20) DEFAULT 'pending',
                        rejection_reason NVARCHAR(MAX) NULL,
                        responded_at DATETIME NULL,
                        created_at DATETIME DEFAULT GETUTCDATE(),
                        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    );
                END
            """,
            'chat_conversations': """
                IF OBJECT_ID('dbo.chat_conversations', 'U') IS NULL
                BEGIN
                    CREATE TABLE dbo.chat_conversations (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        user1_id INT NOT NULL,
                        user2_id INT NOT NULL,
                        status NVARCHAR(20) DEFAULT 'pending',
                        requested_by INT NOT NULL,
                        requested_at DATETIME DEFAULT GETUTCDATE(),
                        accepted_at DATETIME NULL,
                        created_at DATETIME DEFAULT GETUTCDATE(),
                        updated_at DATETIME DEFAULT GETUTCDATE(),
                        FOREIGN KEY (user1_id) REFERENCES users(id),
                        FOREIGN KEY (user2_id) REFERENCES users(id),
                        FOREIGN KEY (requested_by) REFERENCES users(id),
                        CONSTRAINT uq_chat_users UNIQUE (user1_id, user2_id)
                    );
                END
            """,
            'chat_messages': """
                IF OBJECT_ID('dbo.chat_messages', 'U') IS NULL
                BEGIN
                    CREATE TABLE dbo.chat_messages (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        conversation_id INT NOT NULL,
                        sender_id INT NOT NULL,
                        recipient_id INT NOT NULL,
                        content NVARCHAR(MAX) NOT NULL,
                        reply_to_id INT NULL,
                        delivery_status NVARCHAR(20) DEFAULT 'sent',
                        is_read BIT DEFAULT 0,
                        read_at DATETIME NULL,
                        created_at DATETIME DEFAULT GETUTCDATE(),
                        updated_at DATETIME NULL,
                        is_edited BIT DEFAULT 0,
                        is_deleted BIT DEFAULT 0,
                        deleted_for_sender BIT DEFAULT 0,
                        deleted_for_recipient BIT DEFAULT 0,
                        FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE,
                        FOREIGN KEY (sender_id) REFERENCES users(id),
                        FOREIGN KEY (recipient_id) REFERENCES users(id),
                        FOREIGN KEY (reply_to_id) REFERENCES chat_messages(id)
                    );
                END
            """,
            'message_reactions': """
                IF OBJECT_ID('dbo.message_reactions', 'U') IS NULL
                BEGIN
                    CREATE TABLE dbo.message_reactions (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        message_id INT NOT NULL,
                        user_id INT NOT NULL,
                        emoji NVARCHAR(MAX) NOT NULL,
                        created_at DATETIME DEFAULT GETUTCDATE(),
                        FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        CONSTRAINT uq_message_user_emoji UNIQUE (message_id, user_id, emoji)
                    );
                END
            """
    }
    
    # Add project_id and sprint_id columns to tasks if they don't exist
    try:
        with db.engine.begin() as conn:
            # Check if project_id column exists
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='tasks' AND COLUMN_NAME='project_id'
            """))
            if result.scalar() == 0:
                print("Adding project_id column to tasks table...")
                conn.execute(text("ALTER TABLE tasks ADD project_id INT NULL"))
                conn.execute(text("ALTER TABLE tasks ADD FOREIGN KEY (project_id) REFERENCES projects(id)"))
                print("✓ Added project_id column")
            else:
                print("✓ project_id column already exists")
            
            # Check if sprint_id column exists
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='tasks' AND COLUMN_NAME='sprint_id'
            """))
            if result.scalar() == 0:
                print("Adding sprint_id column to tasks table...")
                conn.execute(text("ALTER TABLE tasks ADD sprint_id INT NULL"))
                conn.execute(text("ALTER TABLE tasks ADD FOREIGN KEY (sprint_id) REFERENCES sprints(id)"))
                print("✓ Added sprint_id column")
            else:
                print("✓ sprint_id column already exists")
    except Exception as e:
        print(f"⚠ Warning adding task columns: {e}")
    
    # Create tables that don't exist
    for table_name, create_sql in tables_to_create.items():
        try:
            if table_name not in existing_tables:
                print(f"Creating {table_name} table...")
                with db.engine.begin() as conn:
                    conn.execute(text(create_sql))
                print(f"✓ {table_name} table created")
            else:
                print(f"✓ {table_name} table already exists")
        except Exception as e:
            print(f"⚠ Error creating {table_name}: {e}")
    
    # Add related_conversation_id to notifications if it doesn't exist
    try:
        with db.engine.begin() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='notifications' AND COLUMN_NAME='related_conversation_id'
            """))
            if result.scalar() == 0:
                print("Adding related_conversation_id column to notifications table...")
                conn.execute(text("ALTER TABLE notifications ADD related_conversation_id INT NULL"))
                conn.execute(text("ALTER TABLE notifications ADD FOREIGN KEY (related_conversation_id) REFERENCES chat_conversations(id)"))
                print("✓ Added related_conversation_id column")
            else:
                print("✓ related_conversation_id column already exists")
    except Exception as e:
        print(f"⚠ Warning adding notifications column: {e}")
    
    # Ensure all chat_messages columns exist (migration for existing tables)
    print("\nEnsuring all chat_messages columns exist...")
    try:
        with db.engine.begin() as conn:
            # Check and add reply_to_id if missing
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='chat_messages' AND COLUMN_NAME='reply_to_id'
            """))
            if result.scalar() == 0:
                print("Adding reply_to_id column to chat_messages table...")
                conn.execute(text("ALTER TABLE dbo.chat_messages ADD reply_to_id INT NULL"))
                # Add foreign key constraint if it doesn't exist
                try:
                    conn.execute(text("""
                        IF NOT EXISTS (
                            SELECT 1 FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS 
                            WHERE CONSTRAINT_NAME = 'FK_chat_messages_reply_to'
                        )
                        BEGIN
                            ALTER TABLE dbo.chat_messages 
                            ADD CONSTRAINT FK_chat_messages_reply_to 
                            FOREIGN KEY (reply_to_id) REFERENCES chat_messages(id);
                        END
                    """))
                except Exception as fk_error:
                    print(f"⚠ Note: Foreign key may already exist: {fk_error}")
                print("✓ Added reply_to_id column and foreign key")
            else:
                print("✓ reply_to_id column already exists")
            
            # Check and add other missing columns
            missing_columns = [
                ('updated_at', 'DATETIME NULL'),
                ('is_edited', 'BIT NOT NULL DEFAULT(0)'),
                ('is_deleted', 'BIT NOT NULL DEFAULT(0)'),
                ('deleted_for_sender', 'BIT NOT NULL DEFAULT(0)'),
                ('deleted_for_recipient', 'BIT NOT NULL DEFAULT(0)')
            ]
            
            for col_name, col_def in missing_columns:
                result = conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='chat_messages' AND COLUMN_NAME='{col_name}'
                """))
                if result.scalar() == 0:
                    print(f"Adding {col_name} column to chat_messages table...")
                    conn.execute(text(f"ALTER TABLE dbo.chat_messages ADD {col_name} {col_def}"))
                    print(f"✓ Added {col_name} column")
                else:
                    print(f"✓ {col_name} column already exists")
    except Exception as e:
        print(f"⚠ Warning ensuring chat_messages columns: {e}")
    
    # Cleanup any corrupted emoji reactions stored previously
    print("\nCleaning up corrupted emoji reactions (if any)...")
    try:
        with db.engine.begin() as conn:
            # Remove reactions with empty or placeholder emojis
            deleted = conn.execute(text("""
                DELETE FROM dbo.message_reactions 
                WHERE emoji IS NULL 
                   OR LTRIM(RTRIM(CAST(emoji AS NVARCHAR(MAX)))) = '' 
                   OR CAST(emoji AS NVARCHAR(MAX)) = '??'
            """))
            # Note: rowcount may be -1 depending on driver; this is informational
            print("✓ Emoji cleanup executed")
    except Exception as e:
        print(f"⚠ Warning cleaning corrupted emojis: {e}")
    
    # Ensure message_reactions.emoji column is large enough for all emojis
    print("\nEnsuring message_reactions.emoji column size is sufficient...")
    try:
        with db.engine.begin() as conn:
            # Check current column size
            result = conn.execute(text("""
                SELECT CHARACTER_MAXIMUM_LENGTH 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='message_reactions' AND COLUMN_NAME='emoji'
            """))
            current_size = result.scalar()
            # If column exists and is smaller than MAX, alter it
            if current_size is not None and current_size < 1000:
                print(f"Current emoji column size is {current_size}, expanding to NVARCHAR(MAX)...")
                conn.execute(text("ALTER TABLE dbo.message_reactions ALTER COLUMN emoji NVARCHAR(MAX) NOT NULL"))
                print("✓ Expanded emoji column to NVARCHAR(MAX)")
            elif current_size is None:
                print("⚠ message_reactions table or emoji column not found - will be created with correct size")
            else:
                print(f"✓ emoji column already has sufficient size ({current_size})")
    except Exception as e:
        print(f"⚠ Warning ensuring message_reactions.emoji column: {e}")
    
    # Verify all tables exist
    print("\n" + "=" * 60)
    print("Verifying tables...")
    print("=" * 60)
    inspector = inspect(db.engine)
    final_tables = inspector.get_table_names()
    print(f"\nFinal tables in database: {sorted(final_tables)}")
    
    required_tables = [
        'users', 'tasks', 'projects', 'sprints', 'project_members',
        'notifications', 'time_logs', 'comments', 'system_settings',
        'notification_preferences', 'file_attachments', 'reminders',
        'meetings', 'meeting_invitations', 'chat_conversations',
        'chat_messages', 'message_reactions'
    ]
    
    missing_tables = [t for t in required_tables if t not in final_tables]
    if missing_tables:
        print(f"\n⚠ Warning: Missing tables: {missing_tables}")
    else:
        print("\n✓ All required tables exist!")
    
    print("\n" + "=" * 60)
    print("Database initialization complete!")
    print("=" * 60)

if __name__ == '__main__':
    init_database()

