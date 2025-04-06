import streamlit as st
import json
import os
import shutil
from datetime import datetime
import zipfile
from auth import require_auth
import base64
from io import BytesIO
import pandas as pd

# Configuration de la page (doit être en premier)
st.set_page_config(page_title="Backup & Restore - Questionnaire Marketing", layout="wide")

# Vérifier l'authentification admin
require_auth(role="admin")

# Création des dossiers nécessaires
os.makedirs("database/backups", exist_ok=True)
os.makedirs("database/responses", exist_ok=True)
os.makedirs("database/users", exist_ok=True)

st.title("🔄 Backup & Restore")

def create_backup():
    """Crée une archive ZIP contenant tous les fichiers de données"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.zip"
    backup_path = os.path.join("database/backups", backup_filename)
    
    # Liste des fichiers à sauvegarder
    files_to_backup = [
        "database/responses/questions.json",
        "database/responses/responses_history.json",
        "database/users/users.json"
    ]
    
    # Créer un fichier ZIP
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in files_to_backup:
            if os.path.exists(file):
                zf.write(file, os.path.basename(file))
    
    # Sauvegarder dans l'historique
    history_file = "database/backups/backup_history.json"
    if not os.path.exists(history_file):
        backup_history = []
    else:
        with open(history_file, "r") as f:
            backup_history = json.load(f)
    
    backup_size = os.path.getsize(backup_path)
    backup_history.append({
        "date": datetime.now().isoformat(),
        "filename": backup_filename,
        "size": backup_size,
        "path": backup_path,
        "created_by": st.session_state.username
    })
    
    with open(history_file, "w") as f:
        json.dump(backup_history, f, indent=4)
    
    return backup_path

def restore_backup(backup_path):
    """Restaure les données depuis une archive ZIP"""
    with zipfile.ZipFile(backup_path, 'r') as zip_ref:
        # Créer un dossier temporaire pour la restauration
        temp_dir = "temp_restore"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Extraire les fichiers
        zip_ref.extractall(temp_dir)
        
        # Vérifier et déplacer les fichiers
        restored_files = []
        for file in os.listdir(temp_dir):
            source = os.path.join(temp_dir, file)
            try:
                # Vérifier si le fichier est un JSON valide
                with open(source, 'r', encoding='utf-8') as f:
                    json.load(f)
                
                # Déterminer le dossier de destination
                if file == 'users.json':
                    dest_folder = "database/users"
                else:
                    dest_folder = "database/responses"
                
                # Créer une sauvegarde du fichier existant
                dest_path = os.path.join(dest_folder, file)
                if os.path.exists(dest_path):
                    backup_name = f"{file}.bak"
                    shutil.copy2(dest_path, os.path.join(dest_folder, backup_name))
                
                # Déplacer le fichier
                shutil.move(source, dest_path)
                restored_files.append(file)
            except (json.JSONDecodeError, Exception) as e:
                st.error(f"Erreur lors de la restauration de {file}: {str(e)}")
        
        # Nettoyer le dossier temporaire
        shutil.rmtree(temp_dir)
        
        return restored_files

def get_backup_info(backup_path):
    """Récupère les informations sur le contenu du backup"""
    info = {}
    with zipfile.ZipFile(backup_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            info[file] = {
                'size': zip_ref.getinfo(file).file_size,
                'date': datetime.fromtimestamp(zip_ref.getinfo(file).date_time[0:6]).isoformat()
            }
    return info

# Interface utilisateur
tabs = st.tabs(["Backup", "Restore", "Historique des Backups"])

with tabs[0]:
    st.header("📤 Créer un Backup")
    st.markdown("""
    Cette fonction va créer une archive ZIP contenant :
    - Les questions du questionnaire
    - L'historique des réponses
    - Les données utilisateurs
    
    Le backup sera automatiquement :
    1. Créé dans le dossier database/backups
    2. Enregistré dans l'historique
    3. Téléchargé sur votre ordinateur
    """)
    
    if st.button("🔄 Créer un Nouveau Backup"):
        with st.spinner("Création du backup en cours..."):
            try:
                backup_path = create_backup()
                # Téléchargement automatique
                with open(backup_path, "rb") as f:
                    backup_data = f.read()
                st.success("✅ Backup créé avec succès!")
                
                # Afficher les informations du backup
                backup_info = get_backup_info(backup_path)
                st.json(backup_info)
                
                # Créer le bouton de téléchargement et le cliquer automatiquement
                st.markdown(
                    f"""
                    <script>
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(new Blob([{backup_data}], {{type: 'application/zip'}}));
                        link.download = "{os.path.basename(backup_path)}";
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    </script>
                    """,
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.error(f"Erreur lors de la création du backup : {str(e)}")

with tabs[1]:
    st.header("📥 Restaurer un Backup")
    st.warning("⚠️ La restauration écrasera les données actuelles. Une sauvegarde des fichiers existants sera créée automatiquement.")
    
    # Liste des backups disponibles
    backup_files = []
    backup_dir = "database/backups"
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
    
    if not backup_files:
        st.info("Aucun backup disponible")
    else:
        # Trier les backups par date (le plus récent en premier)
        backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_backup = st.selectbox(
                "Sélectionner un backup à restaurer",
                backup_files,
                format_func=lambda x: f"{x} ({datetime.fromtimestamp(os.path.getmtime(os.path.join(backup_dir, x))).strftime('%Y-%m-%d %H:%M:%S')})"
            )
        
        with col2:
            st.markdown("###")  # Pour aligner le bouton
            if st.button("🔄 Restaurer", type="primary"):
                with st.spinner("Restauration en cours..."):
                    try:
                        backup_path = os.path.join(backup_dir, selected_backup)
                        
                        # Afficher les informations du backup
                        st.info("Contenu du backup :")
                        backup_info = get_backup_info(backup_path)
                        st.json(backup_info)
                        
                        # Restaurer les fichiers
                        restored_files = restore_backup(backup_path)
                        st.success(f"✅ Restauration réussie! Fichiers restaurés : {', '.join(restored_files)}")
                        st.info("ℹ️ Veuillez rafraîchir la page pour voir les changements.")
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la restauration : {str(e)}")

with tabs[2]:
    st.header("📋 Historique des Backups")
    
    history_file = "database/backups/backup_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
        
        if history:
            # Créer un DataFrame pour l'affichage
            history_df = pd.DataFrame(history)
            history_df['date'] = pd.to_datetime(history_df['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
            history_df['size'] = history_df['size'].apply(lambda x: f"{x/1024:.1f} KB")
            
            # Ajouter des statistiques
            st.subheader("📊 Statistiques")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Nombre total de backups", len(history))
            
            with col2:
                avg_size = sum(float(s.replace(" KB", "")) for s in history_df['size']) / len(history)
                st.metric("Taille moyenne", f"{avg_size:.1f} KB")
            
            with col3:
                last_backup = datetime.strptime(history_df['date'].iloc[-1], '%Y-%m-%d %H:%M:%S')
                days_since = (datetime.now() - last_backup).days
                st.metric("Dernier backup", f"Il y a {days_since} jours")
            
            # Afficher l'historique
            st.subheader("📜 Historique Complet")
            st.dataframe(
                history_df[['date', 'filename', 'size', 'created_by']].rename(columns={
                    'date': 'Date',
                    'filename': 'Nom du fichier',
                    'size': 'Taille',
                    'created_by': 'Créé par'
                }),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Aucun historique de backup disponible")
    else:
        st.info("Aucun historique de backup disponible") 