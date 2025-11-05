"""
Run the chat messages migration to add edit/delete fields
"""
import sys
from sqlalchemy import text
from app import app
from models import db

def run_migration():
    """Add new columns to chat_messages table"""
    with app.app_context():
        try:
            # Read and execute the migration SQL
            with open('migrations/add_chat_message_fields.sql', 'r') as f:
                sql_content = f.read()
            
            # Split by semicolons and execute each statement
            statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
            
            for statement in statements:
                if statement:
                    print(f"Executing: {statement[:100]}...")
                    db.session.execute(text(statement))
            
            db.session.commit()
            print("✅ Migration completed successfully!")
            print("   - Added updated_at column")
            print("   - Added is_edited column")
            print("   - Added is_deleted column")
            print("   - Added deleted_for_sender column")
            print("   - Added deleted_for_recipient column")
            
            # Verify columns were added
            result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='chat_messages'"))
            columns = [row[0] for row in result]
            print(f"\nChat_messages columns: {columns}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            sys.exit(1)

if __name__ == '__main__':
    run_migration()

