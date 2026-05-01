import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import joblib

class HealthAnalytics:
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
    
    def linear_regression_simple(self, X, y):
        """Simple linear regression"""
        model = LinearRegression()
        model.fit(X, y)
        return model
    
    def linear_regression_multiple(self, X, y):
        """Multiple linear regression"""
        model = LinearRegression()
        model.fit(X, y)
        return model
    
    def random_forest_classifier(self, X, y):
        """Random Forest pour classification de risque"""
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        return model
    
    def knn_classifier(self, X, y, n_neighbors=5):
        """KNN pour classification profil santé"""
        model = KNeighborsClassifier(n_neighbors=n_neighbors)
        model.fit(X, y)
        return model
    
    def svm_classifier(self, X, y):
        """SVM pour classification"""
        model = SVC(kernel='rbf', probability=True, random_state=42)
        model.fit(X, y)
        return model
    
    def pca_analysis(self, X, n_components=2):
        """PCA pour réduction dimensionnelle"""
        X_scaled = self.scaler.fit_transform(X)
        pca = PCA(n_components=n_components)
        X_pca = pca.fit_transform(X_scaled)
        return X_pca, pca
    
    def kmeans_clustering(self, X, n_clusters=3):
        """K-Means pour clustering profils"""
        X_scaled = self.scaler.fit_transform(X)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X_scaled)
        return clusters, kmeans