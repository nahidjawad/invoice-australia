import os
from werkzeug.middleware.proxy_fix import ProxyFix  # Added for production reverse proxy support

# Set OAuth environment variables for development before any other imports
if os.environ.get('FLASK_ENV') == 'development' or not os.environ.get('FLASK_ENV'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

from flask import Flask, render_template
from datetime import datetime

from config import config
from extensions import init_extensions, db
from flask_migrate import Migrate
from models import User, Invoice
from routes import main, invoice, stripe_bp
from auth import auth
from user import user 
from company import company_bp  # <-- Add this import

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    init_extensions(app)  # This calls db.init_app(app) and mail.init_app(app)
    migrate = Migrate(app, db)  # Only once, after db is initialized

    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(invoice, url_prefix='/invoice')
    app.register_blueprint(stripe_bp, url_prefix='/stripe')
    app.register_blueprint(user) 
    app.register_blueprint(company_bp)  # <-- Register the company blueprint
    
    # Context processors
    @app.context_processor
    def inject_globals():
        """Inject global variables into templates"""
        from utils import SessionManager
        user = SessionManager.get_current_user()
        return {
            "current_user": user,
            "year": datetime.now().year,
            "is_premium": user.get("is_premium") if user else False,
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    return app

# Create the application instance
app = create_app()

# Apply ProxyFix only in production to handle reverse proxy headers (e.g., X-Forwarded-Proto, X-Forwarded-Host)
if os.environ.get('FLASK_ENV') == 'production':
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG', False)) 