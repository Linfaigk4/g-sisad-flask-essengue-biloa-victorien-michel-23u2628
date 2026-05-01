#!/bin/bash
# build.sh - Script de build pour Render

echo "🚀 G-SISAD Build Script Starting..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Node.js dependencies for Tailwind CSS
echo "📦 Installing Node.js dependencies..."
npm install

# Build Tailwind CSS
echo "🎨 Building Tailwind CSS..."
npm run build-css

# Initialize database
echo "🗄️ Initializing database..."
python init_db.py

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p static/css
mkdir -p logs
mkdir -p backups

# Set permissions
echo "🔒 Setting permissions..."
chmod -R 755 static
chmod -R 755 templates

echo "✅ Build completed successfully!"