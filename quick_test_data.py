"""
Version simplifiée pour tests rapides - 10 utilisateurs uniquement
"""

from app import app, db
from models import User, HealthMetrics
from werkzeug.security import generate_password_hash
import random
from datetime import datetime, timedelta

def quick_generate():
    with app.app_context():
        # Nettoyage
        db.session.query(HealthMetrics).delete()
        db.session.query(User).delete()
        
        # Données de test
        test_users = [
            {"name": "admin", "email": "admin@test.com", "role": "admin", 
             "age": 35, "weight": 75, "height": 175, "sleep": 7, "stress": 3},
            {"name": "sportif", "email": "sportif@test.com", "role": "user",
             "age": 28, "weight": 70, "height": 180, "sleep": 8, "stress": 2},
            {"name": "sedentaire", "email": "sedentaire@test.com", "role": "user",
             "age": 45, "weight": 85, "height": 170, "sleep": 6, "stress": 6},
            {"name": "stresse", "email": "stresse@test.com", "role": "user",
             "age": 32, "weight": 78, "height": 172, "sleep": 5, "stress": 9},
            {"name": "senior", "email": "senior@test.com", "role": "user",
             "age": 65, "weight": 72, "height": 168, "sleep": 7, "stress": 4},
            {"name": "jeune", "email": "jeune@test.com", "role": "user",
             "age": 22, "weight": 65, "height": 178, "sleep": 7, "stress": 5},
            {"name": "obese", "email": "obese@test.com", "role": "user",
             "age": 40, "weight": 110, "height": 175, "sleep": 6, "stress": 7},
            {"name": "femme_active", "email": "femme@test.com", "role": "user",
             "age": 30, "weight": 60, "height": 165, "sleep": 7.5, "stress": 4},
            {"name": "cadre_stresse", "email": "cadre@test.com", "role": "user",
             "age": 38, "weight": 82, "height": 180, "sleep": 5.5, "stress": 8},
            {"name": "retraite", "email": "retraite@test.com", "role": "user",
             "age": 70, "weight": 68, "height": 170, "sleep": 8, "stress": 2}
        ]
        
        users = []
        for data in test_users:
            bmi = data["weight"] / ((data["height"]/100) ** 2)
            if data["gender"] == "male":
                bmr = 88.362 + (13.397 * data["weight"]) + (4.799 * data["height"]) - (5.677 * data["age"])
            else:
                bmr = 447.593 + (9.247 * data["weight"]) + (3.098 * data["height"]) - (4.330 * data["age"])
            
            health_score = 100
            if bmi < 18.5 or bmi > 25: health_score -= 20
            if bmi > 30: health_score -= 40
            if data["sleep"] < 6 or data["sleep"] > 9: health_score -= 15
            health_score -= data["stress"] * 2
            health_score = max(0, min(100, health_score))
            
            if bmi > 30 or data["stress"] > 8:
                risk = "high"
            elif bmi > 25 or data["stress"] > 5:
                risk = "medium"
            else:
                risk = "low"
            
            user = User(
                username=data["name"],
                email=data["email"],
                password_hash=generate_password_hash("test123"),
                role=data["role"],
                is_active=True,
                age=data["age"],
                gender=data.get("gender", "male"),
                weight=data["weight"],
                height=data["height"],
                activity_level=data.get("activity", "moderate"),
                sleep_hours=data["sleep"],
                stress_level=data["stress"],
                systolic_bp=120,
                diastolic_bp=80
            )
            db.session.add(user)
            db.session.flush()
            
            metrics = HealthMetrics(
                user_id=user.id,
                bmi=bmi,
                bmr=bmr,
                health_score=health_score,
                risk_level=risk
            )
            db.session.add(metrics)
            users.append(user)
        
        db.session.commit()
        
        print("10 utilisateurs de test créés !")
        print("\n Identifiants de connexion:")
        print("  Admin: admin@test.com / test123")
        print("  User: sportif@test.com / test123")
        print("  User: stresse@test.com / test123")
        print("\nDashboard admin: http://localhost:5000/admin/dashboard")

if __name__ == "__main__":
    quick_generate()