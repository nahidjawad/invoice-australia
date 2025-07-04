import os
from dotenv import load_dotenv

load_dotenv()

# Set OAuth environment variables for development
if os.environ.get('FLASK_ENV') == 'development' or not os.environ.get('FLASK_ENV'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/invoices.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')  # Use the same email as username
    
    # OAuth configuration
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    
    # Stripe configuration
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # File upload configuration
    UPLOAD_FOLDER = 'output'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    # Feedback email
    FEEDBACK_RECIPIENT = os.environ.get('FEEDBACK_RECIPIENT', 'invoices.australia@gmail.com')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    # Allow OAuth to work with HTTP in development
    OAUTHLIB_INSECURE_TRANSPORT = '1'
    OAUTHLIB_RELAX_TOKEN_SCOPE = '1'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Ensure HTTPS in production
    OAUTHLIB_INSECURE_TRANSPORT = '0'
    OAUTHLIB_RELAX_TOKEN_SCOPE = '0'
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging configuration
    LOG_LEVEL = 'INFO'
    
    # Database connection pooling for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True
    }

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    # Allow OAuth to work with HTTP in testing
    OAUTHLIB_INSECURE_TRANSPORT = '1'
    OAUTHLIB_RELAX_TOKEN_SCOPE = '1'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 