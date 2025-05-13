import os
import logging
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)

# Set the secret key from environment variables
app.secret_key = os.environ.get("SESSION_SECRET", "sophia_secret_key")

# Configure database (PostgreSQL or SQLite fallback)
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # If PostgreSQL URL is available, use it
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # Fallback to SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sophia_chat.db"
    logger.warning("DATABASE_URL not found, falling back to SQLite")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page"
login_manager.login_message_category = "info"

# Initialize the app with the SQLAlchemy extension
db.init_app(app)

# Import views after app is created to avoid circular imports
from views import *

# Create database tables
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    import models
    from models import User
    
    # Create all tables in the database
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        logger.info("Creating admin user")
        admin = User(
            id='admin',
            username='admin',
            email='admin@example.com',
            is_admin=True,
            messages_left_today=9999,  # unlimited
            is_premium=True
        )
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
    
    logger.debug("Database tables created")

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(user_id)

# Set up scheduler for daily tasks
scheduler = BackgroundScheduler()

# Function to reset daily message limits
def reset_daily_message_limits():
    logger.info("Resetting daily message limits")
    with app.app_context():
        from models import User
        users = User.query.filter(User.is_premium == False).all()
        for user in users:
            user.messages_left_today = 50
            user.last_reset = datetime.utcnow()
        db.session.commit()
        logger.info(f"Reset message limits for {len(users)} users")

# Function to post scheduled content
def post_scheduled_content():
    logger.info("Posting scheduled content")
    with app.app_context():
        from models import SophiaContent
        
        # Get content scheduled for today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        content_to_post = SophiaContent.query.filter(
            SophiaContent.is_posted == False,
            SophiaContent.scheduled_time >= today,
            SophiaContent.scheduled_time < tomorrow
        ).all()
        
        for content in content_to_post:
            # In a real implementation, this would post to social media
            logger.info(f"Posting content {content.id} to {content.platform}")
            content.is_posted = True
            content.posted_time = datetime.utcnow()
            
        db.session.commit()
        logger.info(f"Posted {len(content_to_post)} items")

# Schedule jobs
scheduler.add_job(reset_daily_message_limits, 'cron', hour=0, minute=0)
scheduler.add_job(post_scheduled_content, 'cron', hour=9, minute=0)

# Start the scheduler
scheduler.start()
