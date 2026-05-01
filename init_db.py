#!/usr/bin/env python3
"""
Script d'initialisation de la base de données et création des comptes
"""

import os
import sys
import random

# Ajouter le chemin actuel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importer après avoir ajouté le chemin
from models import db, User, HealthMetrics
from werkzeug.security import generate_password_hash

def init_database():
    """Initialiser la base de données avec des comptes de test"""
    
    # Créer l'application Flask
    from flask import Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gsisad.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print("🚀 Initialisation de la base de données...")
        
        # Créer les tables
        db.create_all()
        print("✅ Tables créées")
        
        # Vérifier si déjà des données
        existing_users = User.query.count()
        if existing_users > 0:
            print(f"⚠️ {existing_users} utilisateurs existent déjà. Suppression des anciennes données...")
            db.session.query(HealthMetrics).delete()
            db.session.query(User).delete()
            db.session.commit()
            print("✅ Anciennes données supprimées")
        
        # Fonction pour calculer le score santé
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
        
        # 1. Créer le compte ADMIN
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
            height=175,
            activity_level="moderate",
            sleep_hours=7,
            stress_level=3,
            systolic_bp=120,
            diastolic_bp=80
        )
        db.session.add(admin)
        print("  ✅ admin@gsisad.com / admin123")
        
        # 2. Créer les comptes USER de test
        print("\n👤 Création des comptes utilisateurs...")
        
        test_users = [
            {
                "username": "sportif", "email": "sportif@test.com", "password": "test123",
                "age": 28, "gender": "male", "weight": 70, "height": 180,
                "sleep": 8, "stress": 2, "activity": "active", "bp_sys": 115, "bp_dia": 75
            },
            {
                "username": "sedentaire", "email": "sedentaire@test.com", "password": "test123",
                "age": 45, "gender": "male", "weight": 85, "height": 170,
                "sleep": 6, "stress": 6, "activity": "sedentary", "bp_sys": 130, "bp_dia": 85
            },
            {
                "username": "stresse", "email": "stresse@test.com", "password": "test123",
                "age": 32, "gender": "female", "weight": 78, "height": 172,
                "sleep": 5, "stress": 9, "activity": "light", "bp_sys": 145, "bp_dia": 90
            },
            {
                "username": "senior", "email": "senior@test.com", "password": "test123",
                "age": 65, "gender": "male", "weight": 72, "height": 168,
                "sleep": 7, "stress": 4, "activity": "light", "bp_sys": 135, "bp_dia": 82
            },
            {
                "username": "jeune", "email": "jeune@test.com", "password": "test123",
                "age": 22, "gender": "female", "weight": 60, "height": 165,
                "sleep": 7.5, "stress": 3, "activity": "moderate", "bp_sys": 110, "bp_dia": 70
            },
            {
                "username": "obese", "email": "obese@test.com", "password": "test123",
                "age": 40, "gender": "male", "weight": 110, "height": 175,
                "sleep": 6, "stress": 7, "activity": "sedentary", "bp_sys": 150, "bp_dia": 95
            },
            {
                "username": "cadre", "email": "cadre@test.com", "password": "test123",
                "age": 38, "gender": "male", "weight": 82, "height": 180,
                "sleep": 5.5, "stress": 8, "activity": "moderate", "bp_sys": 140, "bp_dia": 88
            },
            {
                "username": "retraite", "email": "retraite@test.com", "password": "test123",
                "age": 70, "gender": "female", "weight": 65, "height": 162,
                "sleep": 8, "stress": 2, "activity": "light", "bp_sys": 125, "bp_dia": 78
            },
            {
                "username": "etudiant", "email": "etudiant@test.com", "password": "test123",
                "age": 20, "gender": "male", "weight": 68, "height": 175,
                "sleep": 6.5, "stress": 5, "activity": "moderate", "bp_sys": 118, "bp_dia": 72
            },
            {
                "username": "maman", "email": "maman@test.com", "password": "test123",
                "age": 35, "gender": "female", "weight": 68, "height": 165,
                "sleep": 6, "stress": 6, "activity": "moderate", "bp_sys": 122, "bp_dia": 80
            }
        ]
        
        users_created = []
        for user_data in test_users:
            # Calculer IMC
            bmi = user_data["weight"] / ((user_data["height"]/100) ** 2)
            
            # Calculer BMR
            if user_data["gender"] == "male":
                bmr = 88.362 + (13.397 * user_data["weight"]) + (4.799 * user_data["height"]) - (5.677 * user_data["age"])
            else:
                bmr = 447.593 + (9.247 * user_data["weight"]) + (3.098 * user_data["height"]) - (4.330 * user_data["age"])
            
            # Score santé
            health_score = calculate_health_score(bmi, user_data["sleep"], user_data["stress"])
            
            # Niveau de risque
            if bmi > 30 or user_data["stress"] > 8:
                risk = "high"
            elif bmi > 25 or user_data["stress"] > 5:
                risk = "medium"
            else:
                risk = "low"
            
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=generate_password_hash(user_data["password"]),
                role="user",
                is_active=True,
                age=user_data["age"],
                gender=user_data["gender"],
                weight=user_data["weight"],
                height=user_data["height"],
                activity_level=user_data["activity"],
                sleep_hours=user_data["sleep"],
                stress_level=user_data["stress"],
                systolic_bp=user_data["bp_sys"],
                diastolic_bp=user_data["bp_dia"]
            )
            db.session.add(user)
            db.session.flush()
            
            # Ajouter les métriques santé
            metrics = HealthMetrics(
                user_id=user.id,
                bmi=bmi,
                bmr=bmr,
                health_score=health_score,
                risk_level=risk
            )
            db.session.add(metrics)
            users_created.append(user_data)
            print(f"  ✅ {user_data['username']} - IMC: {bmi:.1f} - Score: {health_score}")
        
        # Valider tout
        db.session.commit()
        
        # Afficher le résumé
        print("\n" + "="*60)
        print("🎉 INITIALISATION TERMINÉE AVEC SUCCÈS !")
        print("="*60)
        
        print("\n👑 COMPTE ADMINISTRATEUR:")
        print("   📧 admin@gsisad.com")
        print("   🔑 admin123")
        print("   🔗 http://localhost:5000/admin/dashboard")
        
        print("\n👤 COMPTES UTILISATEURS (test123 pour tous):")
        for user in users_created[:5]:
            print(f"   📧 {user['email']} - {user['username']}")
        print(f"   ... et {len(users_created) - 5} autres")
        
        print("\n📊 STATISTIQUES:")
        print(f"   👥 Total utilisateurs: {User.query.count()}")
        print(f"   👑 Admins: {User.query.filter_by(role='admin').count()}")
        print(f"   👤 Users: {User.query.filter_by(role='user').count()}")
        print(f"   📈 Métriques santé: {HealthMetrics.query.count()}")
        
        print("\n" + "="*60)
        print("💡 Pour lancer l'application:")
        print("   python app.py")
        print("="*60)

if __name__ == "__main__":
    init_database()