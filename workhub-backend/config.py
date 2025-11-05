import os
from dotenv import load_dotenv
from urllib.parse import quote_plus as urlquote

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-jwt-secret-key'
    
    # Database (supports mysql or mssql)
    DB_DIALECT = os.environ.get('DB_DIALECT', 'mssql')
    DB_NAME = os.environ.get('DB_NAME', 'workhub')
    DB_USER = os.environ.get('DB_USER', 'wrkhb')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'WB123Pass')
    
    # Cloud SQL connection support (for GCP Cloud Run)
    CLOUD_SQL_CONNECTION_NAME = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
    
    # Determine DB_HOST based on environment
    if CLOUD_SQL_CONNECTION_NAME:
        # When running on Cloud Run, connect via Unix socket
        DB_HOST = f'/cloudsql/{CLOUD_SQL_CONNECTION_NAME}'
        DB_PORT = None  # Not used for Unix socket connections
    else:
        # Local or Docker environment
        DB_HOST = os.environ.get('DB_HOST', 'localhost')
        DB_PORT = os.environ.get('DB_PORT', '1433')

    # Fallback: if using SA and password not provided via DB_PASSWORD, use SA_PASSWORD
    if (DB_USER or '').lower() == 'sa' and (not DB_PASSWORD or DB_PASSWORD == 'WB123Pass'):
        sa_pwd = os.environ.get('SA_PASSWORD')
        if sa_pwd:
            DB_PASSWORD = sa_pwd

    # URL-encode credentials to avoid breaking the URI when they contain special characters (e.g., '@', ':', '!')
    encoded_user = urlquote(DB_USER) if DB_USER is not None else ''
    encoded_password = urlquote(DB_PASSWORD) if DB_PASSWORD is not None else ''

    if DB_DIALECT == 'mssql':
        # Use pymssql for MS SQL Server
        if CLOUD_SQL_CONNECTION_NAME:
            # Cloud SQL connection via Unix socket
            SQLALCHEMY_DATABASE_URI = (
                f"mssql+pymssql://{encoded_user}:{encoded_password}@{DB_HOST}/{DB_NAME}"
            )
        else:
            # Standard TCP connection
            SQLALCHEMY_DATABASE_URI = (
                f"mssql+pymssql://{encoded_user}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            )
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{encoded_user}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    
    # Mail Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = str(os.environ.get('MAIL_USE_TLS', 'True')).lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # App Configuration
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')