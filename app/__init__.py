from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from app.routes.helper_bot_routes import helper_bot_bp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/MikeAubry02025/email_agent/.env')

db = SQLAlchemy()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.dirname(__file__), "email_agent.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Database connection pooling optimization
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20
    }
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.auth import auth_bp
    from app.routes.main_routes import main_bp
    from app.routes.email_routes import email_bp
    from app.routes.api_routes import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(email_bp, url_prefix='/email')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(helper_bot_bp, url_prefix='/helper_bot')

    # Create tables
    with app.app_context():
        db.create_all()

    return app