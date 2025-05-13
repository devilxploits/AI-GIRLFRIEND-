from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """
    User model to track chat users and their message counts
    """
    id = db.Column(db.String(36), primary_key=True)  # UUID as string
    username = db.Column(db.String(64), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)
    
    # Messaging stats
    message_count = db.Column(db.Integer, default=0)
    messages_left_today = db.Column(db.Integer, default=50)  # Reset daily
    telegram_id = db.Column(db.String(50), unique=True, nullable=True)
    instagram_id = db.Column(db.String(50), unique=True, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_reset = db.Column(db.DateTime, default=datetime.utcnow)  # For daily reset
    
    # Relationships
    messages = db.relationship('Message', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
    
    def reset_daily_messages(self):
        """Reset the daily message limit to 50"""
        self.messages_left_today = 50
        self.last_reset = datetime.utcnow()
        return self.messages_left_today

class Message(db.Model):
    """
    Message model to store chat history
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)  # True if from user, False if from Sophia
    language = db.Column(db.String(10))  # Language code detected in the message
    platform = db.Column(db.String(20), default="web")  # web, telegram, instagram
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    has_audio = db.Column(db.Boolean, default=False)  # Whether this message has an audio reply
    audio_path = db.Column(db.String(255), nullable=True)  # Path to audio file for voice messages

class SophiaContent(db.Model):
    """
    Model to store Sophia's content for social media posts
    """
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20))  # image, video, reel
    file_path = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.Text, nullable=True)
    is_posted = db.Column(db.Boolean, default=False)
    platform = db.Column(db.String(20), default="all")  # instagram, telegram, all
    scheduled_time = db.Column(db.DateTime, nullable=True)
    posted_time = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
