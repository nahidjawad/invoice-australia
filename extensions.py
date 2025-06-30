import os

# Set OAuth environment variables before importing Flask-Dance
if os.environ.get('FLASK_ENV') == 'development' or not os.environ.get('FLASK_ENV'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_dance.contrib.google import make_google_blueprint

# Initialize extensions
db = SQLAlchemy()
mail = Mail()

def init_extensions(app):
    """Initialize all Flask extensions"""
    db.init_app(app)
    mail.init_app(app)
    
    # Initialize Google OAuth blueprint
    google_bp = make_google_blueprint(
        client_id=app.config.get("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_OAUTH_CLIENT_SECRET"),
        scope=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ],
        redirect_to="auth.google_login_complete",
    )
    app.register_blueprint(google_bp, url_prefix="/login") 