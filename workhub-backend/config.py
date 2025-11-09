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
    # Priority: DB_HOST env var > CLOUD_SQL_CONNECTION_NAME > localhost
    # Note: pymssql doesn't support Unix sockets, so we always use TCP/IP
    # ENFORCEMENT: Application MUST use private IP (10.119.176.3) in production
    explicit_db_host = os.environ.get('DB_HOST')
    
    # Check if we're in production (Cloud Run environment)
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('GCP_PROJECT') is not None
    
    if explicit_db_host:
        # STRICT ENFORCEMENT: Block public IP usage in production
        if explicit_db_host == '34.31.203.11':
            if is_production:
                # In production, fail fast if public IP is detected
                import sys
                error_msg = (
                    "ERROR: Public IP (34.31.203.11) detected in production environment!\n"
                    "This will cause SLOW performance and security issues.\n"
                    "Application MUST use private IP (10.119.176.3) in production.\n"
                    "Please update DB_HOST environment variable to 10.119.176.3"
                )
                print(error_msg, file=sys.stderr)
                raise ValueError("Public IP cannot be used in production. Use private IP (10.119.176.3)")
            else:
                # In development, automatically switch to private IP with warning
                DB_HOST = '10.119.176.3'
                import warnings
                import sys
                warnings.warn("DB_HOST was set to public IP (34.31.203.11). Automatically using private IP (10.119.176.3) for better performance and security.", 
                            UserWarning)
                print("WARNING: DB_HOST was set to public IP. Switched to private IP (10.119.176.3) for optimal performance.", file=sys.stderr)
        else:
            # Use explicit DB_HOST
            DB_HOST = explicit_db_host
            
            # Validate private IP in production
            if is_production and DB_HOST not in ['10.119.176.3', 'localhost', '127.0.0.1', 'database', 'host.docker.internal']:
                import sys
                print(f"WARNING: Using DB_HOST={DB_HOST} in production. Ensure this is the private IP for optimal performance.", file=sys.stderr)
            
            # Log the DB_HOST being used for debugging
            if DB_HOST not in ['localhost', '127.0.0.1', 'database', 'host.docker.internal']:
                import sys
                if DB_HOST == '10.119.176.3':
                    print(f"[INFO] Using PRIVATE IP: {DB_HOST} (Optimal for production)", file=sys.stderr)
                else:
                    print(f"[INFO] Using DB_HOST: {DB_HOST}", file=sys.stderr)
        DB_PORT = os.environ.get('DB_PORT', '1433')
    elif CLOUD_SQL_CONNECTION_NAME:
        # Fallback: if CLOUD_SQL_CONNECTION_NAME is set but DB_HOST is not,
        # we can't use Unix socket with pymssql, so this is an error
        # For now, default to localhost (this shouldn't happen in production)
        DB_HOST = os.environ.get('DB_HOST', 'localhost')
        DB_PORT = os.environ.get('DB_PORT', '1433')
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
        # pymssql only supports TCP/IP connections, not Unix sockets
        # Always use TCP/IP connection format
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