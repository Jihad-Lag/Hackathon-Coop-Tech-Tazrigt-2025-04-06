import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import plotly.express as px
from auth import is_logged_in, require_auth, is_admin
import shutil

# Configuration de la page
st.set_page_config(
    page_title="Questionnaire ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Création des dossiers nécessaires
os.makedirs("database/backups", exist_ok=True)
os.makedirs("database/responses", exist_ok=True)
os.makedirs("database/users", exist_ok=True)
os.makedirs("exports", exist_ok=True)

def load_responses(file_path="database/responses/responses_history.json"):
    """Charge les réponses depuis un fichier"""
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_questions():
    """Charge les questions"""
    try:
        with open("database/responses/questions.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_backup_files():
    """Récupère la liste des fichiers de backup"""
    backup_dir = "database/backups"
    return [f for f in os.listdir(backup_dir) if f.endswith('.json')]

def compare_responses(current_data, backup_data):
    """Compare les données actuelles avec un backup"""
    current_df = pd.DataFrame(current_data)
    backup_df = pd.DataFrame(backup_data)
    
    # Comparaison des statistiques
    stats = {
        'Total réponses': {
            'Actuel': len(current_df),
            'Backup': len(backup_df),
            'Différence': len(current_df) - len(backup_df)
        },
        'Clients uniques': {
            'Actuel': current_df['client_name'].nunique(),
            'Backup': backup_df['client_name'].nunique(),
            'Différence': current_df['client_name'].nunique() - backup_df['client_name'].nunique()
        }
    }
    
    return stats

# Vérifier si l'utilisateur est connecté
if not is_logged_in():
    st.warning("Veuillez vous connecter pour accéder à l'application.")
    st.stop()

# Afficher le titre principal
st.title("📊 Questionnaire Marketing")

# Afficher les informations de l'utilisateur
st.sidebar.markdown(f"### 👤 Utilisateur: {st.session_state.username}")
if st.session_state.get('role') == 'admin':
    st.sidebar.info("🔑 Statut: Administrateur")

# Chargement des données
current_responses = load_responses()
questions = load_questions()

# Filtres dans la sidebar
st.sidebar.markdown("### 🔍 Filtres")

# Récupérer tous les groupes uniques
all_groups = []
if questions:
    all_groups = list(set(q['group'] for q in questions))

selected_groups = st.sidebar.multiselect(
    "Filtrer par groupe",
    options=all_groups,
    default=all_groups
)

# Contenu principal
st.markdown("""
### 🎯 Bienvenue dans l'application de Questionnaire Marketing

Cette application vous permet de :
- Répondre à des questionnaires marketing
- Visualiser les résultats et analyses
- Gérer les sauvegardes (admin)
- Configurer les questions (admin)
""")

# Statistiques rapides
if current_responses:
    # Filtrer les réponses par groupe si nécessaire
    filtered_responses = [
        r for r in current_responses 
        if r.get('group') in selected_groups
    ] if selected_groups else current_responses
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_responses = len(filtered_responses)
        st.metric("Total des réponses", total_responses)
    
    with col2:
        if filtered_responses:
            last_response = datetime.fromisoformat(filtered_responses[-1]['date'])
            days_since = (datetime.now() - last_response).days
            st.metric("Dernière réponse", f"Il y a {days_since} jours")
    
    with col3:
        unique_clients = len(set(r['client_name'] for r in filtered_responses))
        st.metric("Clients uniques", unique_clients)

    # Graphique des réponses dans le temps
    if filtered_responses:
        df_responses = pd.DataFrame(filtered_responses)
        df_responses['date'] = pd.to_datetime(df_responses['date']).dt.date
        
        df_daily = df_responses.groupby(['date', 'group']).size().reset_index(name='count')
        
        fig = px.line(
            df_daily,
            x='date',
            y='count',
            color='group',
            title="Évolution des réponses dans le temps par groupe",
            labels={'count': 'Nombre de réponses', 'date': 'Date', 'group': 'Groupe'}
        )
        st.plotly_chart(fig, use_container_width=True)

# Système de comparaison des backups (admin uniquement)
if is_admin():
    st.subheader("📊 Comparaison des Backups")
    
    backup_files = get_backup_files()
    if backup_files:
        selected_backup = st.selectbox(
            "Sélectionner un backup à comparer",
            options=backup_files,
            format_func=lambda x: f"Backup du {x.split('_')[1].split('.')[0]}"
        )
        
        if selected_backup:
            backup_path = os.path.join("database/backups", selected_backup)
            backup_responses = load_responses(backup_path)
            
            if backup_responses:
                stats = compare_responses(current_responses, backup_responses)
                
                st.markdown("#### Comparaison des statistiques")
                for metric, values in stats.items():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"{metric} (Actuel)", values['Actuel'])
                    with col2:
                        st.metric(f"{metric} (Backup)", values['Backup'])
                    with col3:
                        st.metric("Différence", values['Différence'])
                
                if st.button("🔄 Restaurer ce backup"):
                    # Créer un backup des données actuelles avant la restauration
                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_filename = f"backup_{current_time}.json"
                    shutil.copy2(
                        "database/responses/responses_history.json",
                        f"database/backups/{backup_filename}"
                    )
                    
                    # Restaurer le backup sélectionné
                    shutil.copy2(backup_path, "database/responses/responses_history.json")
                    st.success("✅ Backup restauré avec succès ! La page va se recharger...")
                    st.rerun()
    else:
        st.info("Aucun backup disponible pour la comparaison.")

# Actions rapides
st.subheader("⚡ Actions Rapides")

col1, col2 = st.columns(2)

with col1:
    if st.button("📝 Nouveau Questionnaire"):
        st.switch_page("pages/questionnaire.py")

with col2:
    if st.button("📊 Voir le Dashboard"):
        st.switch_page("pages/dashboard.py")

# Section admin
if st.session_state.get('role') == 'admin':
    st.subheader("🔧 Administration")
    
    admin_col1, admin_col2 = st.columns(2)
    
    with admin_col1:
        if st.button("🔄 Gérer les Backups"):
            st.switch_page("pages/backup_restore.py")
    
    with admin_col2:
        if st.button("👥 Gérer les Utilisateurs"):
            st.switch_page("pages/settings.py") 