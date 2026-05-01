#!/usr/bin/env python3
# backup_db.py - Sauvegarde automatique de la base de données

import os
import shutil
import datetime
import gzip

def backup_database():
    """Sauvegarde la base de données SQLite"""
    
    db_path = 'gsisad.db'
    backup_dir = 'backups'
    
    # Créer le dossier de sauvegarde s'il n'existe pas
    os.makedirs(backup_dir, exist_ok=True)
    
    # Nom du fichier de sauvegarde
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"gsisad_backup_{timestamp}.db.gz"
    backup_path = os.path.join(backup_dir, backup_name)
    
    try:
        # Compresser la base de données
        with open(db_path, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        print(f"✅ Backup created: {backup_name}")
        
        # Supprimer les backups de plus de 30 jours
        for backup in os.listdir(backup_dir):
            backup_file = os.path.join(backup_dir, backup)
            if os.path.getctime(backup_file) < (datetime.datetime.now() - datetime.timedelta(days=30)).timestamp():
                os.remove(backup_file)
                print(f"🗑️ Removed old backup: {backup}")
                
    except Exception as e:
        print(f"❌ Backup failed: {e}")

if __name__ == "__main__":
    backup_database()