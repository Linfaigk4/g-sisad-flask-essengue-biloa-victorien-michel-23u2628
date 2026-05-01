from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profil santé
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    activity_level = db.Column(db.String(20), nullable=True)
    sleep_hours = db.Column(db.Float, nullable=True)
    stress_level = db.Column(db.Integer, nullable=True)
    systolic_bp = db.Column(db.Integer, nullable=True)
    diastolic_bp = db.Column(db.Integer, nullable=True)
    medical_history = db.Column(db.Text, nullable=True)
    
    health_metrics = db.relationship('HealthMetrics', backref='user', lazy=True)

class HealthMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bmi = db.Column(db.Float)
    bmr = db.Column(db.Float)
    health_score = db.Column(db.Integer)
    risk_level = db.Column(db.String(20))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)