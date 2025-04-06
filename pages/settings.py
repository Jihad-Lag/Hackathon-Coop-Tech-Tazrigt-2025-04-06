import streamlit as st
import json
import os
from datetime import datetime
from auth import require_auth, hash_password

# Configuration de la page
st.set_page_config(page_title="Paramètres - Questionnaire Marketing", layout="wide")

# Vérification de l'authentification admin
require_auth(role="admin")

# Création du dossier database si nécessaire
os.makedirs("database/users", exist_ok=True)

def load_users():
    """Charge la liste des utilisateurs"""
    users_file = "database/users/users.json"
    if os.path.exists(users_file):
        with open(users_file, "r", encoding='utf-8') as f:
            return json.load(f)
    return {"admin": {"password": hash_password("admin123"), "role": "admin"}}

def save_users(users):
    """Sauvegarde la liste des utilisateurs"""
    users_file = "database/users/users.json"
    with open(users_file, "w", encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

st.title("⚙️ Paramètres")

# Chargement des utilisateurs
users = load_users()

# Interface de gestion des utilisateurs
tabs = st.tabs(["Gestion des Utilisateurs", "Journaux d'Activité"])

with tabs[0]:
    st.header("👥 Gestion des Utilisateurs")
    
    # Affichage des utilisateurs existants
    st.subheader("Utilisateurs Existants")
    
    users_df = []
    for username, data in users.items():
        users_df.append({
            "Nom d'utilisateur": username,
            "Rôle": data["role"],
            "Dernière modification": data.get("last_modified", "N/A")
        })
    
    st.dataframe(users_df, use_container_width=True, hide_index=True)
    
    # Formulaire d'ajout d'utilisateur
    st.subheader("Ajouter un Utilisateur")
    with st.form("add_user"):
        new_username = st.text_input("Nom d'utilisateur")
        new_password = st.text_input("Mot de passe", type="password")
        new_role = st.selectbox("Rôle", ["user", "admin"])
        
        submitted = st.form_submit_button("Ajouter")
        if submitted and new_username and new_password:
            if new_username in users:
                st.error("Ce nom d'utilisateur existe déjà!")
            else:
                users[new_username] = {
                    "password": hash_password(new_password),
                    "role": new_role,
                    "last_modified": datetime.now().isoformat()
                }
                save_users(users)
                st.success(f"Utilisateur {new_username} ajouté avec succès!")
                st.rerun()
    
    # Suppression d'utilisateur
    st.subheader("Supprimer un Utilisateur")
    user_to_delete = st.selectbox("Sélectionner un utilisateur à supprimer",
                                 [u for u in users.keys() if u != "admin"])
    
    if st.button("Supprimer", type="primary"):
        if user_to_delete == "admin":
            st.error("Impossible de supprimer l'utilisateur admin!")
        else:
            del users[user_to_delete]
            save_users(users)
            st.success(f"Utilisateur {user_to_delete} supprimé avec succès!")
            st.rerun()
    
    # Modification du mot de passe
    st.subheader("Modifier le Mot de Passe")
    with st.form("change_password"):
        user_to_modify = st.selectbox("Sélectionner un utilisateur",
                                    list(users.keys()))
        new_password = st.text_input("Nouveau mot de passe", type="password")
        
        if st.form_submit_button("Modifier"):
            users[user_to_modify]["password"] = hash_password(new_password)
            users[user_to_modify]["last_modified"] = datetime.now().isoformat()
            save_users(users)
            st.success(f"Mot de passe modifié pour {user_to_modify}!")

with tabs[1]:
    st.header("📋 Journaux d'Activité")
    st.info("Cette fonctionnalité sera disponible prochainement...") 