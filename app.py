from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import db, User, HealthMetrics
from ml_models import HealthAnalytics
import numpy as np
import pandas as pd
from datetime import datetime
import os
import plotly
import plotly.graph_objs as go
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gsisad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialiser l'IA
health_ai = HealthAnalytics()

# ============ DÉCORATEUR ADMIN ============
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# ============ FONCTIONS UTILITAIRES ============
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
        return 'high'
    elif bmi > 25 or stress_level > 5:
        return 'medium'
    return 'low'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============ ROUTES ============
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            if user.is_active:
                login_user(user)
                return redirect(url_for('dashboard' if user.role == 'user' else 'admin_dashboard'))
            else:
                flash('Compte désactivé', 'error')
        else:
            flash('Email ou mot de passe incorrect', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email déjà utilisé', 'error')
        else:
            user = User(
                username=request.form['username'],
                email=request.form['email'],
                password_hash=generate_password_hash(request.form['password']),
                role='user'
            )
            db.session.add(user)
            db.session.commit()
            flash('Inscription réussie !', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    metrics = HealthMetrics.query.filter_by(user_id=current_user.id).order_by(HealthMetrics.recorded_at.desc()).first()
    return render_template('dashboard.html', metrics=metrics)

@app.route('/health-form', methods=['GET', 'POST'])
@login_required
def health_form():
    if request.method == 'POST':
        height_m = float(request.form['height']) / 100
        weight = float(request.form['weight'])
        bmi = weight / (height_m ** 2)
        
        if request.form['gender'] == 'male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * float(request.form['height'])) - (5.677 * float(request.form['age']))
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * float(request.form['height'])) - (4.330 * float(request.form['age']))
        
        health_score = calculate_health_score(bmi, float(request.form['sleep_hours']), int(request.form['stress_level']))
        risk_level = determine_risk_level(bmi, int(request.form['stress_level']))
        
        current_user.age = int(request.form['age'])
        current_user.gender = request.form['gender']
        current_user.weight = weight
        current_user.height = float(request.form['height'])
        current_user.activity_level = request.form['activity_level']
        current_user.sleep_hours = float(request.form['sleep_hours'])
        current_user.stress_level = int(request.form['stress_level'])
        current_user.systolic_bp = int(request.form['systolic_bp'])
        current_user.diastolic_bp = int(request.form['diastolic_bp'])
        
        metrics = HealthMetrics(
            user_id=current_user.id,
            bmi=bmi,
            bmr=bmr,
            health_score=health_score,
            risk_level=risk_level
        )
        db.session.add(metrics)
        db.session.commit()
        
        flash('Bilan santé enregistré !', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('health_form.html')

@app.route('/user/settings')
@login_required
def user_settings():
    return render_template('user_settings.html')

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Dashboard administrateur avec analyses EC2"""
    
    # Statistiques globales
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    avg_health_score = db.session.query(db.func.avg(HealthMetrics.health_score)).scalar() or 0
    
    # Récupérer tous les utilisateurs avec données complètes
    users_with_data = User.query.filter(
        User.weight.isnot(None),
        User.height.isnot(None),
        User.age.isnot(None),
        User.sleep_hours.isnot(None),
        User.stress_level.isnot(None)
    ).all()
    
    graphs = []
    
    # Vérifier si on a assez de données
    if len(users_with_data) >= 5:
        
        # 1. RÉGRESSION LINÉAIRE SIMPLE (IMC vs Poids)
        bmi_values = []
        weights = []
        for u in users_with_data:
            if u.weight and u.height:
                bmi = u.weight / ((u.height/100) ** 2)
                bmi_values.append(bmi)
                weights.append(u.weight)
        
        if len(bmi_values) >= 5:
            from sklearn.linear_model import LinearRegression
            import numpy as np
            
            X = np.array(bmi_values).reshape(-1, 1)
            y = np.array(weights)
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Prédictions
            bmi_range = np.linspace(min(bmi_values), max(bmi_values), 50).reshape(-1, 1)
            weights_pred = model.predict(bmi_range)
            
            import plotly.graph_objs as go
            
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=bmi_values, 
                y=weights, 
                mode='markers', 
                name='Données réelles',
                marker=dict(color='#84CC16', size=10)
            ))
            fig1.add_trace(go.Scatter(
                x=bmi_range.flatten(), 
                y=weights_pred, 
                mode='lines', 
                name='Régression',
                line=dict(color='#7C3AED', width=3)
            ))
            fig1.update_layout(
                title='Régression simple: IMC vs Poids',
                xaxis_title='IMC (kg/m²)',
                yaxis_title='Poids (kg)',
                template='plotly_white',
                height=400
            )
            graphs.append({
                'id': 'graph1',
                'json': fig1.to_json(),
                'title': '📈 Régression Linéaire Simple'
            })
        
        # 2. RÉGRESSION MULTIPLE (Âge vs Tension)
        ages = []
        systolic_bp = []
        for u in users_with_data:
            if u.age and u.systolic_bp:
                ages.append(u.age)
                systolic_bp.append(u.systolic_bp)
        
        if len(ages) >= 5:
            import plotly.graph_objs as go
            
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=ages, 
                y=systolic_bp, 
                mode='markers+lines', 
                name='Tension systolique',
                marker=dict(color='#FB7185', size=8),
                line=dict(color='#FB7185', width=2)
            ))
            fig2.update_layout(
                title='Tension artérielle vs Âge',
                xaxis_title='Âge (ans)',
                yaxis_title='Pression systolique (mmHg)',
                template='plotly_white',
                height=400
            )
            graphs.append({
                'id': 'graph2',
                'json': fig2.to_json(),
                'title': '📊 Régression Multiple'
            })
        
        # 3. PCA - Analyse en Composantes Principales
        if len(users_with_data) >= 10:
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
            import numpy as np
            
            features = []
            for u in users_with_data:
                if u.age and u.weight and u.height and u.sleep_hours and u.stress_level:
                    bmi = u.weight / ((u.height/100) ** 2)
                    features.append([u.age, bmi, u.sleep_hours, u.stress_level])
            
            if len(features) >= 5:
                X = np.array(features)
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                pca = PCA(n_components=2)
                X_pca = pca.fit_transform(X_scaled)
                
                import plotly.graph_objs as go
                
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(
                    x=X_pca[:, 0], 
                    y=X_pca[:, 1], 
                    mode='markers',
                    name='Utilisateurs',
                    marker=dict(size=12, color=X_pca[:, 0], colorscale='Viridis', showscale=True),
                    text=[f"User {i+1}" for i in range(len(X_pca))],
                    hoverinfo='text+x+y'
                ))
                fig3.update_layout(
                    title=f'PCA - Réduction dimensionnelle',
                    xaxis_title=f'Composante 1 ({pca.explained_variance_ratio_[0]*100:.1f}%)',
                    yaxis_title=f'Composante 2 ({pca.explained_variance_ratio_[1]*100:.1f}%)',
                    template='plotly_white',
                    height=400
                )
                graphs.append({
                    'id': 'graph3',
                    'json': fig3.to_json(),
                    'title': '🎯 Analyse PCA'
                })
        
        # 4. CLASSIFICATION KNN
        if len(users_with_data) >= 15:
            from sklearn.neighbors import KNeighborsClassifier
            from sklearn.model_selection import train_test_split
            import numpy as np
            
            X_class = []
            y_class = []
            for u in users_with_data:
                if u.age and u.weight and u.height and u.sleep_hours and u.stress_level:
                    bmi = u.weight / ((u.height/100) ** 2)
                    X_class.append([u.age, bmi, u.sleep_hours, u.stress_level])
                    if bmi > 30 or u.stress_level > 8:
                        y_class.append(2)  # Haut risque
                    elif bmi > 25 or u.stress_level > 5:
                        y_class.append(1)  # Risque moyen
                    else:
                        y_class.append(0)  # Risque faible
            
            if len(X_class) >= 10:
                X_train, X_test, y_train, y_test = train_test_split(X_class, y_class, test_size=0.3, random_state=42)
                
                knn = KNeighborsClassifier(n_neighbors=5)
                knn.fit(X_train, y_train)
                knn_accuracy = knn.score(X_test, y_test)
                
                import plotly.graph_objs as go
                
                fig4 = go.Figure()
                fig4.add_trace(go.Bar(
                    x=['KNN'],
                    y=[knn_accuracy * 100],
                    marker_color=['#84CC16'],
                    text=[f'{knn_accuracy*100:.1f}%'],
                    textposition='auto',
                ))
                fig4.update_layout(
                    title='Classification KNN - Précision du modèle',
                    yaxis_title='Précision (%)',
                    yaxis_range=[0, 100],
                    template='plotly_white',
                    height=400
                )
                graphs.append({
                    'id': 'graph4',
                    'json': fig4.to_json(),
                    'title': '🤖 Classification KNN'
                })
        
        # 5. CLUSTERING K-MEANS
        if len(users_with_data) >= 10:
            from sklearn.cluster import KMeans
            import numpy as np
            
            cluster_data = []
            for u in users_with_data:
                if u.weight and u.height and u.stress_level:
                    bmi = u.weight / ((u.height/100) ** 2)
                    cluster_data.append([bmi, u.stress_level])
            
            if len(cluster_data) >= 5:
                X = np.array(cluster_data)
                kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(X)
                
                import plotly.graph_objs as go
                
                colors = ['#84CC16', '#7C3AED', '#FB7185']
                fig5 = go.Figure()
                
                for i in range(3):
                    mask = clusters == i
                    fig5.add_trace(go.Scatter(
                        x=X[mask, 0],
                        y=X[mask, 1],
                        mode='markers',
                        name=f'Cluster {i+1}',
                        marker=dict(size=10, color=colors[i])
                    ))
                
                fig5.update_layout(
                    title='K-Means Clustering - Profils santé',
                    xaxis_title='IMC (kg/m²)',
                    yaxis_title='Niveau de stress (1-10)',
                    template='plotly_white',
                    height=400
                )
                graphs.append({
                    'id': 'graph5',
                    'json': fig5.to_json(),
                    'title': '🔮 Clustering K-Means'
                })
    
    # Compter combien de graphiques ont été générés
    graphs_count = len(graphs)
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         avg_health_score=avg_health_score,
                         graphs=graphs,
                         graphs_count=graphs_count,
                         users_count=len(users_with_data))
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/toggle-user/<int:user_id>')
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:
        user.is_active = not user.is_active
        db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/settings')
@login_required
@admin_required
def admin_settings():
    return render_template('admin_settings.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)