import os
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from app import create_app
from models import db, User


def promote(email: str):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.role = 'super_admin'
            user.email_verified = True
            user.signup_status = 'approved'
            db.session.commit()
            print(f"OK: Promoted {email} to super_admin")
            return
        # Create if not exists
        user = User(
            email=email,
            name=email.split('@')[0],
            role='super_admin',
            email_verified=True,
            signup_status='approved',
        )
        user.set_password(os.environ.get('NEW_SUPERADMIN_PASSWORD', 'SuperAdmin@123'))
        db.session.add(user)
        db.session.commit()
        print(f"OK: Created and promoted {email} to super_admin")


if __name__ == '__main__':
    target_email = os.environ.get('PROMOTE_EMAIL') or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not target_email:
        print('ERROR: provide email via PROMOTE_EMAIL env or argv')
        sys.exit(1)
    promote(target_email)


