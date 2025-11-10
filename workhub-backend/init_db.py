"""
Database initialization script
Creates tables and adds sample data
Also ensures SQL Server login and database (when using MSSQL)
"""
import os
import subprocess
from app import create_app
from models import db, User, Task, SystemSettings
from datetime import datetime, timedelta

def ensure_mssql_login_and_db():
    if os.environ.get('DB_DIALECT') != 'mssql':
        return
    host = os.environ.get('DB_HOST', 'mssql')
    port = os.environ.get('DB_PORT', '1433')
    db_name = os.environ.get('DB_NAME', 'workhub')
    db_user = os.environ.get('DB_USER', 'wrkhb')
    db_password = os.environ.get('DB_PASSWORD', 'WB123Pass')
    sa_password = os.environ.get('SA_PASSWORD', 'YourStrong!Passw0rd')

    base = ['/opt/mssql-tools18/bin/sqlcmd', '-S', f'{host},{port}', '-C', '-U', 'SA', '-P', sa_password]

    # Create DB if not exists
    subprocess.call(base + ['-Q', f"IF DB_ID('{db_name}') IS NULL CREATE DATABASE [{db_name}]"])
    # Create login if not exists
    subprocess.call(base + ['-Q', f"IF NOT EXISTS (SELECT name FROM sys.sql_logins WHERE name = '{db_user}') CREATE LOGIN [{db_user}] WITH PASSWORD='{db_password}', CHECK_POLICY=OFF"])
    # Create user in DB and grant roles
    subprocess.call(base + ['-d', db_name, '-Q', f"IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = '{db_user}') CREATE USER [{db_user}] FOR LOGIN [{db_user}]"])
    subprocess.call(base + ['-d', db_name, '-Q', f"EXEC sp_addrolemember 'db_owner', '{db_user}'"])

    # Ensure the login is enabled and unlocked with correct default database
    subprocess.call(base + ['-Q', f"ALTER LOGIN [{db_user}] ENABLE;"])
    subprocess.call(base + ['-Q', f"ALTER LOGIN [{db_user}] WITH PASSWORD='{db_password}' UNLOCK;"])
    subprocess.call(base + ['-Q', f"ALTER LOGIN [{db_user}] WITH DEFAULT_DATABASE=[{db_name}];"])


def init_database():
    # Import here to avoid circular imports
    from sqlalchemy import create_engine, text
    
    # First, create the database if it doesn't exist
    db_dialect = os.environ.get('DB_DIALECT', 'mssql')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '1433')
    db_user = os.environ.get('DB_USER', 'sa')
    db_password = os.environ.get('DB_PASSWORD', 'YourStrong!Passw0rd')
    db_name = os.environ.get('DB_NAME', 'workhub')
    
    if db_dialect == 'mssql':
        master_uri = f"mssql+pymssql://{db_user}:{db_password}@{db_host}:{db_port}/master"
        try:
            master_engine = create_engine(master_uri)
            with master_engine.connect() as conn:
                conn.execute(text("COMMIT"))
                result = conn.execute(text(f"SELECT name FROM sys.databases WHERE name = '{db_name}'"))
                if not result.fetchone():
                    print(f"Creating database '{db_name}'...")
                    conn.execute(text(f"CREATE DATABASE [{db_name}]"))
                    conn.commit()
                    print(f"Database '{db_name}' created successfully!")
                else:
                    print(f"Database '{db_name}' already exists.")
        except Exception as e:
            print(f"Warning: Could not create database: {e}. Continuing anyway...")
    
    app = create_app()
    
    with app.app_context():
        # When using MSSQL container, ensure login and db exist
        try:
            ensure_mssql_login_and_db()
        except Exception as e:
            print(f"Warning: ensure_mssql_login_and_db failed: {e}")

        # Ensure tables exist; create missing tables/columns (idempotent)
        print("Ensuring database tables exist...")
        try:
            db.create_all()
        except Exception as e:
            print(f"create_all warning: {e}")

        # Apply simple migrations for projects/sprints/task FKs if missing
        try:
            from sqlalchemy import text
            with db.engine.begin() as conn:
                # Create projects table if not exists
                conn.execute(text("""
                    IF OBJECT_ID('dbo.projects', 'U') IS NULL
                    BEGIN
                        CREATE TABLE dbo.projects (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            name NVARCHAR(150) NOT NULL UNIQUE,
                            description NVARCHAR(MAX) NULL,
                            created_at DATETIME NULL,
                            updated_at DATETIME NULL,
                            owner_id INT NULL
                        );
                    END
                """))
                # Create sprints table if not exists
                conn.execute(text("""
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
                            updated_at DATETIME NULL
                        );
                    END
                """))
                # Create project_members table if not exists
                conn.execute(text("""
                    IF OBJECT_ID('dbo.project_members', 'U') IS NULL
                    BEGIN
                        CREATE TABLE dbo.project_members (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            project_id INT NOT NULL,
                            user_id INT NOT NULL,
                            role NVARCHAR(50) NULL,
                            joined_at DATETIME NULL,
                            CONSTRAINT uq_project_user UNIQUE (project_id, user_id)
                        );
                    END
                """))
                conn.execute(text("""
                    -- Add columns project_id, sprint_id to tasks if missing (robust checks)
                    -- Try via INFORMATION_SCHEMA under dbo
                    IF NOT EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='tasks' AND COLUMN_NAME='project_id'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM sys.columns c
                        JOIN sys.objects o ON o.object_id = c.object_id
                        WHERE o.name = 'tasks' AND c.name = 'project_id'
                    )
                    BEGIN
                        IF OBJECT_ID('dbo.tasks', 'U') IS NOT NULL
                            ALTER TABLE dbo.tasks ADD project_id INT NULL;
                        ELSE IF OBJECT_ID('tasks', 'U') IS NOT NULL
                            ALTER TABLE tasks ADD project_id INT NULL;
                    END
                """))

                conn.execute(text("""
                    IF NOT EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='tasks' AND COLUMN_NAME='sprint_id'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM sys.columns c
                        JOIN sys.objects o ON o.object_id = c.object_id
                        WHERE o.name = 'tasks' AND c.name = 'sprint_id'
                    )
                    BEGIN
                        IF OBJECT_ID('dbo.tasks', 'U') IS NOT NULL
                            ALTER TABLE dbo.tasks ADD sprint_id INT NULL;
                        ELSE IF OBJECT_ID('tasks', 'U') IS NOT NULL
                            ALTER TABLE tasks ADD sprint_id INT NULL;
                    END
                """))
                
                # Create reminders table if not exists
                conn.execute(text("""
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
                """))
                
                # Create meetings table if not exists
                conn.execute(text("""
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
                """))
                
                # Create meeting_invitations table if not exists
                conn.execute(text("""
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
                """))
                
                # Create chat_conversations table if not exists
                conn.execute(text("""
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
                """))
                
                # Create chat_messages table if not exists (with ALL required columns)
                conn.execute(text("""
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
                """))
                
                # Ensure all columns exist (in case table was created with old schema)
                # This will add any missing columns without error if they already exist
                conn.execute(text("""
                    -- Add reply_to_id if missing
                    IF NOT EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='chat_messages' AND COLUMN_NAME='reply_to_id'
                    )
                    BEGIN 
                        ALTER TABLE dbo.chat_messages ADD reply_to_id INT NULL;
                        ALTER TABLE dbo.chat_messages ADD CONSTRAINT FK_chat_messages_reply_to 
                        FOREIGN KEY (reply_to_id) REFERENCES chat_messages(id);
                    END
                """))
                conn.execute(text("""
                    -- Add updated_at if missing
                    IF NOT EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='chat_messages' AND COLUMN_NAME='updated_at'
                    )
                    BEGIN ALTER TABLE dbo.chat_messages ADD updated_at DATETIME NULL; END
                """))
                conn.execute(text("""
                    -- Add is_edited if missing
                    IF NOT EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='chat_messages' AND COLUMN_NAME='is_edited'
                    )
                    BEGIN ALTER TABLE dbo.chat_messages ADD is_edited BIT NOT NULL DEFAULT(0); END
                """))
                conn.execute(text("""
                    -- Add is_deleted if missing
                    IF NOT EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='chat_messages' AND COLUMN_NAME='is_deleted'
                    )
                    BEGIN ALTER TABLE dbo.chat_messages ADD is_deleted BIT NOT NULL DEFAULT(0); END
                """))
                conn.execute(text("""
                    -- Add deleted_for_sender if missing
                    IF NOT EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='chat_messages' AND COLUMN_NAME='deleted_for_sender'
                    )
                    BEGIN ALTER TABLE dbo.chat_messages ADD deleted_for_sender BIT NOT NULL DEFAULT(0); END
                """))
                conn.execute(text("""
                    -- Add deleted_for_recipient if missing
                    IF NOT EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='chat_messages' AND COLUMN_NAME='deleted_for_recipient'
                    )
                    BEGIN ALTER TABLE dbo.chat_messages ADD deleted_for_recipient BIT NOT NULL DEFAULT(0); END
                """))
                
                # Add related_conversation_id to notifications if not exists
                conn.execute(text("""
                    IF NOT EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='notifications' AND COLUMN_NAME='related_conversation_id'
                    )
                    BEGIN
                        ALTER TABLE dbo.notifications ADD related_conversation_id INT NULL;
                        ALTER TABLE dbo.notifications ADD FOREIGN KEY (related_conversation_id) REFERENCES chat_conversations(id);
                    END
                """))
            print("✓ Applied schema migrations for projects/sprints/reminders/meetings/chat.")
        except Exception as e:
            print(f"Warning: migration steps failed: {e}")
        
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@workhub.com').first()
        
        if not existing_admin:
            # Create default super admin user with strong password
            super_admin = User(
                email='superadmin@workhub.com',
                name='Super Admin',
                role='super_admin',
                email_verified=True,
                signup_status='approved'
            )
            super_admin.set_password('SuperAdmin@123')  # Strong password
            db.session.add(super_admin)
            
            # Create default admin user with strong password
            admin = User(
                email='admin@workhub.com',
                name='Admin User',
                role='admin',
                email_verified=True,
                signup_status='approved'
            )
            admin.set_password('Admin@123456')  # Strong password: 12 chars, uppercase, lowercase, digit, special
            db.session.add(admin)
            
            # Create sample regular users with strong passwords and proper roles
            # Manager user
            user1 = User(
                email='john@workhub.com',
                name='John Doe',
                role='manager',
                email_verified=True,
                signup_status='approved'
            )
            user1.set_password('User@123456')  # Strong password
            db.session.add(user1)
            
            # Developer user
            user2 = User(
                email='jane@workhub.com',
                name='Jane Smith',
                role='developer',
                email_verified=True,
                signup_status='approved'
            )
            user2.set_password('User@123456')  # Strong password
            db.session.add(user2)
            
            # Team Lead user
            user3 = User(
                email='bob@workhub.com',
                name='Bob Johnson',
                role='team_lead',
                email_verified=True,
                signup_status='approved'
            )
            user3.set_password('User@123456')
            db.session.add(user3)
            
            # Viewer user
            user4 = User(
                email='alice@workhub.com',
                name='Alice Williams',
                role='viewer',
                email_verified=True,
                signup_status='approved'
            )
            user4.set_password('User@123456')
            db.session.add(user4)
            
            db.session.commit()
            print("Sample users created!")
            print("Super Admin: superadmin@workhub.com / SuperAdmin@123")
            print("Admin: admin@workhub.com / Admin@123456")
            print("Manager: john@workhub.com / User@123456")
            print("Developer: jane@workhub.com / User@123456")
            print("Team Lead: bob@workhub.com / User@123456")
            print("Viewer: alice@workhub.com / User@123456")
            
            # Create sample tasks
            task1 = Task(
                title='Setup development environment',
                description='Install all necessary tools and dependencies',
                priority='high',
                status='completed',
                assigned_to=user1.id,
                created_by=admin.id,
                due_date=datetime.utcnow() - timedelta(days=2),
                completed_at=datetime.utcnow() - timedelta(days=1)
            )
            
            task2 = Task(
                title='Design database schema',
                description='Create ER diagram and define all tables',
                priority='medium',
                status='in_progress',
                assigned_to=user1.id,
                created_by=admin.id,
                due_date=datetime.utcnow() + timedelta(days=3)
            )
            
            task3 = Task(
                title='Implement authentication',
                description='Add login, registration, and password reset functionality',
                priority='high',
                status='todo',
                assigned_to=user2.id,
                created_by=admin.id,
                due_date=datetime.utcnow() + timedelta(days=5)
            )
            
            task4 = Task(
                title='Create user dashboard',
                description='Design and implement the main user interface',
                priority='medium',
                status='todo',
                assigned_to=user2.id,
                created_by=admin.id,
                due_date=datetime.utcnow() + timedelta(days=7)
            )
            
            db.session.add_all([task1, task2, task3, task4])
            db.session.commit()
            print("Sample tasks created!")
            
            # Create system settings
            settings = SystemSettings(
                site_title='Work Hub',
                default_role='developer',  # Changed from 'user' to 'developer'
                email_notifications_enabled=True,
                default_language='en'
            )
            db.session.add(settings)
            db.session.commit()
            print("System settings initialized!")
        else:
            print("Database already initialized!")

        # Ensure there are some tasks for visibility if table is empty
        try:
            empty = False
            try:
                empty = (Task.query.count() == 0)
            except Exception:
                # Fallback to raw count not selecting new columns
                from sqlalchemy import text as sql_text
                with db.engine.connect() as c:
                    res = c.execute(sql_text("SELECT COUNT(1) AS cnt FROM tasks"))
                    row = res.fetchone()
                    empty = (row[0] == 0)
            if empty:
                print("Seeding sample tasks (table empty)...")
                admin = User.query.filter_by(email='admin@workhub.com').first()
                dev = User.query.filter_by(email='jane@workhub.com').first()
                mgr = User.query.filter_by(email='john@workhub.com').first()
                t1 = Task(title='Sample Task 1', description='This is a seeded sample task.', priority='medium', status='todo', assigned_to=mgr.id if mgr else None, created_by=admin.id if admin else None, due_date=datetime.utcnow()+timedelta(days=5))
                t2 = Task(title='Sample Task 2', description='Second sample task for testing.', priority='high', status='in_progress', assigned_to=dev.id if dev else None, created_by=admin.id if admin else None, due_date=datetime.utcnow()+timedelta(days=3))
                db.session.add_all([t1, t2])
                db.session.commit()
                print("✓ Seeded sample tasks.")
        except Exception as e:
            print(f"Warning: could not seed sample tasks: {e}")

        print("\nDatabase initialization complete!")

if __name__ == '__main__':
    init_database()