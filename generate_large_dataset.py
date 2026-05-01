#!/usr/bin/env python3
"""
Génération de 50 utilisateurs avec données complètes pour les analyses EC2
Version corrigée - gestion des doublons
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

# Prénoms et noms pour générer des utilisateurs réalistes
FIRST_NAMES = [
    "Jean", "Marie", "Pierre", "Sophie", "Thomas", "Julie", "Nicolas", "Camille",
    "Lucas", "Emma", "Hugo", "Lea", "Louis", "Chloe", "Maxime", "Pauline",
    "Antoine", "Sarah", "Alexandre", "Laura", "David", "Manon", "Romain", "Alice",
    "Julien", "Oceane", "Kevin", "Marine", "Jeremy", "Elodie", "Florian", "Morgane",
    "Benoit", "Clara", "Vincent", "Julie", "Philippe", "Celine", "Michel", "Isabelle"
]

LAST_NAMES = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand",
    "Leroy", "Moreau", "Simon", "Laurent", "Michel", "Garcia", "David", "Bertrand",
    "Roux", "Vincent", "Fournier", "Morel", "Girard", "Andre", "Lefevre", "Mercier"
]

ACTIVITY_LEVELS = ["sedentary", "light", "moderate", "active", "very_active"]
GENDERS = ["male", "female"]

# Ensemble pour suivre les usernames déjà utilisés
used_usernames = set()

def calculate_health_score(bmi, sleep_hours, stress_level):
    """Calcul du score santé sur 100"""
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
    """Détermination du niveau de risque"""
    if bmi > 30 or stress_level > 8:
        return "high"
    elif bmi > 25 or stress_level > 5:
        return "medium"
    return "low"

def generate_unique_username(first_name, last_name, index):
    """Génère un nom d'utilisateur unique"""
    base = f"{first_name.lower()}.{last_name.lower()}"
    username = base
    counter = 1
    while username in used_usernames:
        username = f"{base}{counter}"
        counter += 1
    used_usernames.add(username)
    return username

def generate_user(index):
    """Génère un utilisateur fictif"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    username = generate_unique_username(first_name, last_name, index)
    email = f"{username}@example.com"
    
    # Âge (18-80 ans)
    age = random.randint(18, 80)
    
    # Taille (150-190 cm)
    height = random.uniform(150, 190)
    
    # IMC cible selon le profil
    profile_type = random.choice(["sportif", "normal", "surpoids", "obese", "senior", "jeune"])
    
    if profile_type == "sportif":
        target_bmi = random.uniform(18.5, 22)
        activity = random.choice(["active", "very_active"])
        sleep = random.uniform(7, 9)
        stress = random.randint(1, 3)
    elif profile_type == "normal":
        target_bmi = random.uniform(22, 25)
        activity = random.choice(["moderate", "active"])
        sleep = random.uniform(6.5, 8)
        stress = random.randint(3, 5)
    elif profile_type == "surpoids":
        target_bmi = random.uniform(25, 30)
        activity = random.choice(["light", "sedentary"])
        sleep = random.uniform(5.5, 7)
        stress = random.randint(5, 7)
    elif profile_type == "obese":
        target_bmi = random.uniform(30, 40)
        activity = "sedentary"
        sleep = random.uniform(4, 6)
        stress = random.randint(6, 9)
    elif profile_type == "senior":
        target_bmi = random.uniform(23, 28)
        activity = random.choice(["light", "sedentary"])
        sleep = random.uniform(6, 8)
        stress = random.randint(2, 5)
        age = random.randint(60, 80)
    else:  # jeune
        target_bmi = random.uniform(19, 24)
        activity = random.choice(["moderate", "active"])
        sleep = random.uniform(7, 9)
        stress = random.randint(3, 7)
        age = random.randint(18, 30)
    
    # Poids basé sur IMC cible
    weight = target_bmi * ((height/100) ** 2)
    weight = max(45, min(150, weight))
    
    # Genre
    gender = random.choice(GENDERS)
    
    # Pression artérielle
    if target_bmi > 30 or stress > 7:
        systolic_bp = random.randint(130, 160)
        diastolic_bp = random.randint(85, 100)
    elif target_bmi > 25 or stress > 5:
        systolic_bp = random.randint(120, 140)
        diastolic_bp = random.randint(80, 90)
    else:
        systolic_bp = random.randint(100, 120)
        diastolic_bp = random.randint(60, 80)
    
    # Date d'inscription (année écoulée)
    created_at = datetime.now() - timedelta(days=random.randint(1, 365))
    
    # Calculer l'IMC réel
    bmi = weight / ((height/100) ** 2)
    
    # Calculer BMR
    if gender == "male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    # Score santé
    health_score = calculate_health_score(bmi, sleep, stress)
    
    # Niveau de risque
    risk_level = determine_risk_level(bmi, stress)
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash("password123"),
        role="user",
        is_active=True,
        created_at=created_at,
        age=age,
        gender=gender,
        weight=weight,
        height=height,
        activity_level=activity,
        sleep_hours=sleep,
        stress_level=stress,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        medical_history=f"Patient {profile_type} - Suivi régulier"
    )
    
    metrics = HealthMetrics(
        user_id=0,  # ID temporaire, sera mis à jour après l'ajout
        bmi=bmi,
        bmr=bmr,
        health_score=health_score,
        risk_level=risk_level,
        recorded_at=created_at
    )
    
    return user, metrics, profile_type

def generate_large_dataset():
    """Génère 50 utilisateurs avec données"""
    
    with app.app_context():
        print("="*60)
        print("🚀 GÉNÉRATION DE 50 UTILISATEURS AVEC DONNÉES COMPLÈTES")
        print("="*60)
        
        # Supprimer les anciennes données (sauf admin)
        print("\n🗑️ Nettoyage des anciennes données...")
        
        # Sauvegarder l'admin s'il existe
        admin_user = User.query.filter_by(role='admin').first()
        
        # Supprimer toutes les métriques
        db.session.query(HealthMetrics).delete()
        
        # Supprimer tous les utilisateurs non-admin
        if admin_user:
            User.query.filter(User.role != 'admin').delete()
        else:
            User.query.delete()
        
        db.session.commit()
        print("✅ Anciennes données supprimées")
        
        # Créer ou conserver l'admin
        if not admin_user:
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
            db.session.flush()
            print("  ✅ admin@gsisad.com / admin123")
        
        # Réinitialiser les usernames utilisés
        global used_usernames
        used_usernames.clear()
        
        # Ajouter l'admin à la liste des usernames utilisés
        used_usernames.add("admin")
        
        # Générer 50 utilisateurs
        print("\n👥 Génération des 50 utilisateurs...")
        users_data = []
        profile_counts = {"sportif": 0, "normal": 0, "surpoids": 0, "obese": 0, "senior": 0, "jeune": 0}
        all_users = []
        
        for i in range(50):
            user, metrics, profile_type = generate_user(i)
            all_users.append((user, metrics))
            profile_counts[profile_type] += 1
            
            # Afficher la progression
            if (i + 1) % 10 == 0:
                print(f"  📊 {i+1}/50 utilisateurs créés...")
        
        # Ajouter tous les utilisateurs en une fois
        for user, metrics in all_users:
            db.session.add(user)
        
        db.session.flush()
        
        # Ajouter les métriques
        for user, metrics in all_users:
            metrics.user_id = user.id
            db.session.add(metrics)
        
        db.session.commit()
        
        # Statistiques
        print("\n" + "="*60)
        print("📊 STATISTIQUES DES DONNÉES GÉNÉRÉES")
        print("="*60)
        
        total_users = User.query.count()
        print(f"\n👥 Total utilisateurs: {total_users}")
        print(f"👑 Admins: {User.query.filter_by(role='admin').count()}")
        print(f"👤 Utilisateurs standards: {User.query.filter_by(role='user').count()}")
        print(f"📈 Métriques santé: {HealthMetrics.query.count()}")
        
        print("\n📋 Répartition par profil:")
        for profile, count in profile_counts.items():
            emoji = {
                "sportif": "🏃", "normal": "✅", "surpoids": "⚠️", 
                "obese": "🔴", "senior": "👴", "jeune": "🧒"
            }
            print(f"  {emoji.get(profile, '•')} {profile.capitalize()}: {count} utilisateurs")
        
        # Statistiques avancées
        from sqlalchemy import func
        
        avg_age = db.session.query(func.avg(User.age)).scalar()
        avg_bmi = db.session.query(func.avg(HealthMetrics.bmi)).scalar()
        avg_score = db.session.query(func.avg(HealthMetrics.health_score)).scalar()
        avg_stress = db.session.query(func.avg(User.stress_level)).scalar()
        
        print("\n📊 Moyennes globales:")
        print(f"  📏 Âge moyen: {avg_age:.0f} ans")
        print(f"  ⚖️ IMC moyen: {avg_bmi:.1f}")
        print(f"  💚 Score santé moyen: {avg_score:.0f}/100")
        print(f"  😰 Stress moyen: {avg_stress:.1f}/10")
        
        # Répartition des risques
        risk_distribution = db.session.query(
            HealthMetrics.risk_level, 
            func.count(HealthMetrics.id)
        ).group_by(HealthMetrics.risk_level).all()
        
        print("\n⚠️ Niveaux de risque:")
        for risk, count in risk_distribution:
            emoji = "🟢" if risk == "low" else "🟡" if risk == "medium" else "🔴"
            print(f"  {emoji} {risk.upper()}: {count} utilisateurs")
        
        # Afficher quelques exemples
        print("\n👤 Exemples d'utilisateurs créés:")
        sample_users = User.query.filter_by(role='user').limit(5).all()
        for user in sample_users:
            metrics = HealthMetrics.query.filter_by(user_id=user.id).first()
            if metrics:
                print(f"  • {user.username} ({user.age} ans) - IMC: {metrics.bmi:.1f} - Score: {metrics.health_score}")
        
        # Vérifier si on a assez de données
        user_count = User.query.filter_by(role='user').count()
        if user_count >= 30:
            print("\n🎉 PARFAIT ! Vous avez assez de données pour les analyses EC2 !")
            print(f"   {user_count} utilisateurs disponibles → Tous les graphiques s'afficheront")
        else:
            print(f"\n⚠️ Attention: Seulement {user_count}/50 utilisateurs créés")
        
        print("\n" + "="*60)
        print("🎉 GÉNÉRATION TERMINÉE AVEC SUCCÈS !")
        print("="*60)
        
        print("\n🔑 IDENTIFIANTS DE CONNEXION:")
        print("  👑 Admin: admin@gsisad.com / admin123")
        print("  👤 Users: [username]@example.com / password123")
        
        # Afficher quelques identifiants de test
        print("\n📝 Exemples d'identifiants utilisateur:")
        sample_users = User.query.filter_by(role='user').limit(3).all()
        for user in sample_users:
            print(f"  📧 {user.email} / password123")
        
        print("\n💡 Pour lancer l'application:")
        print("  python app.py")
        print("\n📊 Dashboard admin: http://localhost:5000/admin/dashboard")
        print("="*60)

if __name__ == "__main__":
    generate_large_dataset()