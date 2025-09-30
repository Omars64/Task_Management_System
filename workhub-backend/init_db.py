"""
Database initialization script
Creates tables and adds sample data
"""
from app import create_app
from models import db, User, Task, SystemSettings
from datetime import datetime, timedelta

def init_database():
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate
        print("Creating database tables...")
        db.create_all()
        
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@workhub.com').first()
        
        if not existing_admin:
            # Create default admin user
            admin = User(
                email='admin@workhub.com',
                name='Admin User',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create sample regular users
            user1 = User(
                email='john@workhub.com',
                name='John Doe',
                role='user'
            )
            user1.set_password('user123')
            db.session.add(user1)
            
            user2 = User(
                email='jane@workhub.com',
                name='Jane Smith',
                role='user'
            )
            user2.set_password('user123')
            db.session.add(user2)
            
            db.session.commit()
            print("Sample users created!")
            print("Admin: admin@workhub.com / admin123")
            print("User 1: john@workhub.com / user123")
            print("User 2: jane@workhub.com / user123")
            
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
                default_role='user',
                email_notifications_enabled=True,
                default_language='en'
            )
            db.session.add(settings)
            db.session.commit()
            print("System settings initialized!")
        else:
            print("Database already initialized!")
        
        print("\nDatabase initialization complete!")

if __name__ == '__main__':
    init_database()