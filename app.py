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


# ============ ANALYSE PERSONNELLE UTILISATEUR ============

@app.route('/user-analysis')
@login_required
def user_analysis():
    """Page d'analyse personnelle pour l'utilisateur"""
    return render_template('user_analysis.html')

@app.route('/api/user-analysis/<string:analysis_type>')
@login_required
def api_user_analysis(analysis_type):
    """API pour les analyses personnelles de l'utilisateur"""
    
    # Récupérer les métriques de l'utilisateur
    metrics = HealthMetrics.query.filter_by(user_id=current_user.id).order_by(HealthMetrics.recorded_at).all()
    
    if len(metrics) < 3:
        return jsonify({'error': 'Données insuffisantes. Ajoutez au moins 3 bilans santé.'})
    
    # Préparer les données
    dates = [m.recorded_at.strftime('%Y-%m-%d') for m in metrics]
    bmi_values = [m.bmi for m in metrics]
    health_scores = [m.health_score for m in metrics]
    
    # Calculer l'IMC cible (poids idéal)
    weights = [current_user.weight] if current_user.weight else [70]
    
    if analysis_type == 'regression_simple':
        # Régression IMC vs Score Santé
        from sklearn.linear_model import LinearRegression
        import numpy as np
        
        X = np.array(bmi_values).reshape(-1, 1)
        y = np.array(health_scores)
        
        if len(X) >= 2:
            model = LinearRegression()
            model.fit(X, y)
            
            bmi_range = np.linspace(min(bmi_values), max(bmi_values), 50).reshape(-1, 1)
            scores_pred = model.predict(bmi_range)
            
            # Calculer corrélation
            correlation = np.corrcoef(bmi_values, health_scores)[0, 1]
            
            return jsonify({
                'type': 'regression_simple',
                'title': 'Régression: IMC vs Score de Santé',
                'x': bmi_values,
                'y': health_scores,
                'x_label': 'IMC (kg/m²)',
                'y_label': 'Score de Santé (/100)',
                'prediction_line': {
                    'x': bmi_range.flatten().tolist(),
                    'y': scores_pred.tolist()
                },
                'correlation': round(correlation, 3),
                'equation': f"Score = {model.coef_[0]:.2f} × IMC + {model.intercept_:.2f}",
                'interpretation': f"Votre analyse montre une corrélation de {abs(correlation):.2f}. " + 
                                 ("Une augmentation de l'IMC diminue votre score santé." if correlation < 0 else "IMC et score santé augmentent ensemble."),
                'csv_data': generate_csv_data([('Date', dates), ('IMC', bmi_values), ('Score Santé', health_scores)])
            })
    
    elif analysis_type == 'regression_multiple':
        # Régression multiple: tension artérielle
        import numpy as np
        from sklearn.linear_model import LinearRegression
        
        # Utiliser les données de l'utilisateur
        X_multiple = []
        y_tension = []
        
        for m in metrics:
            if current_user.age and current_user.sleep_hours and current_user.stress_level:
                X_multiple.append([
                    current_user.age,
                    m.bmi,
                    current_user.sleep_hours or 7,
                    current_user.stress_level or 5
                ])
                y_tension.append(current_user.systolic_bp or 120)
        
        if len(X_multiple) >= 2:
            model = LinearRegression()
            model.fit(X_multiple, y_tension)
            r2 = model.score(X_multiple, y_tension)
            
            # Prédictions
            y_pred = model.predict(X_multiple)
            
            return jsonify({
                'type': 'regression_multiple',
                'title': 'Régression Multiple: Facteurs influençant la tension',
                'x': list(range(len(y_tension))),
                'y_actual': y_tension,
                'y_predicted': y_pred.tolist(),
                'y_name': 'Tension artérielle',
                'x_label': 'Mesures dans le temps',
                'y_label': 'Pression systolique (mmHg)',
                'r2': round(r2, 3),
                'variables': 'Âge, IMC, Sommeil, Stress',
                'interpretation': f"Votre modèle explique {r2*100:.1f}% des variations de tension. " +
                                 f"Les facteurs les plus influents sont l'IMC et le stress.",
                'csv_data': generate_csv_data([('Mesure', range(len(y_tension))), ('Tension Réelle', y_tension), ('Tension Prédite', y_pred)])
            })
    
    elif analysis_type == 'pca':
        # PCA sur les données personnelles
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        import numpy as np
        
        features = []
        for m in metrics:
            features.append([m.bmi, m.health_score, m.bmr])
        
        if len(features) >= 3:
            X = np.array(features)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            return jsonify({
                'type': 'pca',
                'title': 'PCA - Visualisation 2D de vos données',
                'pca_x': X_pca[:, 0].tolist(),
                'pca_y': X_pca[:, 1].tolist(),
                'labels': [f"Mesure {i+1}" for i in range(len(X_pca))],
                'x_label': f'Première composante ({pca.explained_variance_ratio_[0]*100:.1f}%)',
                'y_label': f'Deuxième composante ({pca.explained_variance_ratio_[1]*100:.1f}%)',
                'variance_explained': f"{sum(pca.explained_variance_ratio_)*100:.1f}%",
                'components': 2,
                'interpretation': f"La PCA capture {sum(pca.explained_variance_ratio_)*100:.1f}% de la variance de vos données. " +
                                 "Les points proches indiquent des bilans santé similaires."
            })
    
    elif analysis_type == 'classification':
        # Classification supervisée (KNN vs Random Forest)
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        import numpy as np
        
        # Simuler des données de classification basées sur l'historique
        X_class = []
        y_class = []
        
        for m in metrics:
            X_class.append([m.bmi, m.health_score])
            if m.risk_level == 'high':
                y_class.append(2)
            elif m.risk_level == 'medium':
                y_class.append(1)
            else:
                y_class.append(0)
        
        if len(set(y_class)) >= 2 and len(X_class) >= 4:
            X_train, X_test, y_train, y_test = train_test_split(X_class, y_class, test_size=0.3, random_state=42)
            
            knn = KNeighborsClassifier(n_neighbors=3)
            knn.fit(X_train, y_train)
            knn_acc = knn.score(X_test, y_test) * 100
            
            rf = RandomForestClassifier(n_estimators=50, random_state=42)
            rf.fit(X_train, y_train)
            rf_acc = rf.score(X_test, y_test) * 100
            
            return jsonify({
                'type': 'classification',
                'title': 'Classification - Prédiction du niveau de risque',
                'models': [
                    {'name': 'KNN', 'accuracy': knn_acc},
                    {'name': 'Random Forest', 'accuracy': rf_acc}
                ],
                'knn_accuracy': round(knn_acc, 1),
                'rf_accuracy': round(rf_acc, 1),
                'interpretation': f"KNN: {knn_acc:.1f}% de précision, Random Forest: {rf_acc:.1f}%. " +
                                 f"Le modèle {'Random Forest' if rf_acc > knn_acc else 'KNN'} est plus performant pour vos données."
            })
    
    elif analysis_type == 'clustering':
        # Clustering K-Means
        from sklearn.cluster import KMeans
        import numpy as np
        
        cluster_data = [[m.bmi, m.health_score] for m in metrics]
        
        if len(cluster_data) >= 3:
            X = np.array(cluster_data)
            n_clusters = min(3, len(X))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X)
            
            return jsonify({
                'type': 'clustering',
                'title': 'Clustering - Regroupement de vos bilans santé',
                'points': cluster_data,
                'cluster_labels': clusters.tolist(),
                'clusters': n_clusters,
                'num_clusters': n_clusters,
                'inertia': round(kmeans.inertia_, 2),
                'x_label': 'IMC (kg/m²)',
                'y_label': 'Score de Santé (/100)',
                'interpretation': f"Vos {len(cluster_data)} bilans santé sont regroupés en {n_clusters} clusters. " +
                                 "Chaque cluster représente un profil santé différent dans le temps."
            })
    
    return jsonify({'error': 'Analyse non disponible pour le moment'})

def generate_csv_data(columns):
    """Génère du CSV à partir des données"""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([col[0] for col in columns])
    
    # Trouver la longueur maximale
    max_len = max(len(col[1]) for col in columns)
    
    for i in range(max_len):
        row = []
        for col in columns:
            if i < len(col[1]):
                row.append(col[1][i])
            else:
                row.append('')
        writer.writerow(row)
    
    return output.getvalue()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)