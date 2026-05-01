#!/usr/bin/env python3
"""
Script simplifié pour créer 50 utilisateurs
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Ajouter le chemin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, User, HealthMetrics
from werkzeug.security import generate_password_hash

# Créer l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gsisad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def calculate_health_score(bmi, sleep_hours, stress_level):
    score = 100
    if bmi < 18.5 or bmi > 25:
        score -= 20
    if bmi > 30:
        score -= 40
    if sleep_hours < 6 or sleep_hours > 9:
        score -= 15
    score -= stress_level * 2
    return max(0, min(100, score))

def determine_risk_level(bmi, stress_level):
    if bmi > 30 or stress_level > 8:
        return "high"
    elif bmi > 25 or stress_level > 5:
        return "medium"
    return "low"

with app.app_context():
    print("="*60)
    print("🚀 CRÉATION DE LA BASE DE DONNÉES")
    print("="*60)
    
    # Créer toutes les tables
    db.create_all()
    print("✅ Tables créées")
    
    # Supprimer les anciens utilisateurs (sauf admin)
    print("\n🗑️ Nettoyage...")
    db.session.query(HealthMetrics).delete()
    User.query.filter(User.role != 'admin').delete()
    db.session.commit()
    
    # Créer l'admin s'il n'existe pas
    admin = User.query.filter_by(email='admin@gsisad.com').first()
    if not admin:
        print("\n👑 Création du compte ADMIN...")
        admin = User(
            username="admin",
            email="admin@gsisad.com",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            is_active=True,
            age=35,
            gender="male",
            weight=75,
            height=175
        )
        db.session.add(admin)
        db.session.commit()
        print("  ✅ admin@gsisad.com / admin123")
    
    # Créer 50 utilisateurs
    print("\n👥 Création de 50 utilisateurs...")
    
    users_data = [
        # [age, gender, weight, height, sleep, stress, activity]
        [28, "male", 70, 180, 8, 2, "active", "sportif"],
        [45, "male", 85, 170, 6, 6, "sedentary", "surpoids"],
        [32, "female", 78, 172, 5, 9, "light", "obese"],
        [65, "male", 72, 168, 7, 4, "light", "senior"],
        [22, "female", 60, 165, 7.5, 3, "moderate", "jeune"],
        [40, "male", 110, 175, 6, 7, "sedentary", "obese"],
        [38, "male", 82, 180, 5.5, 8, "moderate", "surpoids"],
        [70, "female", 65, 162, 8, 2, "light", "senior"],
        [20, "male", 68, 175, 6.5, 5, "moderate", "jeune"],
        [35, "female", 68, 165, 6, 6, "moderate", "normal"],
        [30, "male", 75, 178, 7, 4, "active", "sportif"],
        [50, "female", 80, 160, 6, 7, "light", "surpoids"],
        [55, "male", 90, 172, 5, 8, "sedentary", "obese"],
        [25, "female", 58, 170, 8, 3, "active", "sportif"],
        [42, "male", 88, 176, 6, 6, "moderate", "surpoids"],
        [33, "female", 72, 168, 7, 5, "moderate", "normal"],
        [58, "male", 95, 174, 5, 7, "sedentary", "obese"],
        [27, "female", 62, 172, 7.5, 4, "active", "sportif"],
        [48, "male", 82, 170, 6.5, 6, "light", "normal"],
        [62, "female", 75, 158, 7, 5, "light", "senior"],
        [29, "male", 73, 182, 8, 3, "active", "sportif"],
        [44, "female", 85, 165, 6, 7, "sedentary", "surpoids"],
        [36, "male", 78, 175, 7, 5, "moderate", "normal"],
        [52, "female", 88, 162, 5.5, 8, "light", "obese"],
        [31, "male", 72, 178, 7.5, 4, "active", "sportif"],
        [47, "female", 92, 168, 6, 7, "sedentary", "obese"],
        [41, "male", 80, 176, 6.5, 6, "moderate", "normal"],
        [26, "female", 65, 170, 8, 3, "active", "sportif"],
        [53, "male", 98, 172, 5, 8, "sedentary", "obese"],
        [34, "female", 75, 166, 7, 5, "moderate", "normal"],
        [39, "male", 85, 174, 6, 6, "light", "surpoids"],
        [49, "female", 82, 164, 6.5, 6, "light", "normal"],
        [59, "male", 92, 170, 5.5, 7, "sedentary", "obese"],
        [23, "female", 63, 172, 8, 3, "active", "sportif"],
        [46, "male", 88, 175, 6, 7, "light", "surpoids"],
        [37, "female", 78, 168, 7, 5, "moderate", "normal"],
        [61, "male", 85, 172, 6.5, 6, "light", "senior"],
        [24, "female", 61, 170, 8, 3, "active", "sportif"],
        [54, "male", 95, 174, 5, 8, "sedentary", "obese"],
        [43, "female", 80, 166, 6.5, 6, "moderate", "normal"],
        [35, "male", 77, 178, 7, 4, "active", "sportif"],
        [51, "female", 86, 164, 6, 7, "light", "surpoids"],
        [57, "male", 93, 171, 5.5, 8, "sedentary", "obese"],
        [21, "female", 59, 168, 8, 3, "active", "jeune"],
        [44, "male", 84, 176, 6, 6, "moderate", "normal"],
        [33, "female", 73, 167, 7, 5, "active", "sportif"],
        [56, "male", 97, 173, 5, 8, "sedentary", "obese"],
        [29, "female", 67, 171, 7.5, 4, "moderate", "normal"],
        [48, "male", 89, 169, 6, 7, "light", "surpoids"],
        [64, "female", 78, 160, 7, 5, "light", "senior"],
    ]
    
    created = 0
    for i, data in enumerate(users_data):
        age, gender, weight, height, sleep, stress, activity, profile = data
        
        # Calculer IMC
        bmi = weight / ((height/100) ** 2)
        
        # Calculer BMR
        if gender == "male":
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
        # Score santé
        health_score = calculate_health_score(bmi, sleep, stress)
        
        # Risque
        risk_level = determine_risk_level(bmi, stress)
        
        # Pression artérielle
        if bmi > 30 or stress > 7:
            systolic = random.randint(130, 160)
            diastolic = random.randint(85, 100)
        elif bmi > 25 or stress > 5:
            systolic = random.randint(120, 140)
            diastolic = random.randint(80, 90)
        else:
            systolic = random.randint(100, 120)
            diastolic = random.randint(60, 80)
        
        username = f"user_{i+1}"
        email = f"user{i+1}@example.com"
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash("password123"),
            role="user",
            is_active=True,
            age=age,
            gender=gender,
            weight=weight,
            height=height,
            activity_level=activity,
            sleep_hours=sleep,
            stress_level=stress,
            systolic_bp=systolic,
            diastolic_bp=diastolic,
            medical_history=f"Patient {profile}"
        )
        db.session.add(user)
        db.session.flush()
        
        metrics = HealthMetrics(
            user_id=user.id,
            bmi=bmi,
            bmr=bmr,
            health_score=health_score,
            risk_level=risk_level
        )
        db.session.add(metrics)
        created += 1
        
        if (i + 1) % 10 == 0:
            print(f"  📊 {i+1}/50 utilisateurs créés...")
    
    db.session.commit()
    
    print(f"\n✅ {created} utilisateurs créés avec succès !")
    print("\n" + "="*60)
    print("📊 STATISTIQUES")
    print("="*60)
    print(f"👥 Total utilisateurs: {User.query.count()}")
    print(f"👑 Admins: {User.query.filter_by(role='admin').count()}")
    print(f"👤 Utilisateurs: {User.query.filter_by(role='user').count()}")
    print(f"📈 Métriques santé: {HealthMetrics.query.count()}")
    
    print("\n🔑 IDENTIFIANTS DE CONNEXION:")
    print("  👑 Admin: admin@gsisad.com / admin123")
    print("  👤 Users: user1@example.com, user2@example.com, ... / password123")
    print("  📝 Exemple: user1@example.com / password123")
    
    print("\n💡 Pour lancer l'application:")
    print("  python app.py")
    print("="*60)