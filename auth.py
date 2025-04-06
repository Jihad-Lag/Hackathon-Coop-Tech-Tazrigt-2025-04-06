import streamlit as st
import json
import os
from hashlib import sha256

def init_session_state():
    """Initialise les variables de session"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None

def load_users():
    """Charge les utilisateurs depuis le fichier JSON"""
    try:
        with open("database/users/users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def is_valid_credentials(username: str, password: str) -> bool:
    """Vérifie si les identifiants sont valides"""
    users = load_users()
    return username in users and users[username]["password"] == password

def get_user_role(username: str) -> str:
    """Récupère le rôle de l'utilisateur"""
    users = load_users()
    return users.get(username, {}).get("role", "user")

def login(username: str, password: str) -> bool:
    """Connecte l'utilisateur"""
    if is_valid_credentials(username, password):
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.role = get_user_role(username)
        return True
    return False

def logout():
    """Déconnecte l'utilisateur"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None

def is_logged_in() -> bool:
    """Vérifie si l'utilisateur est connecté"""
    return st.session_state.get('authenticated', False)

def is_admin() -> bool:
    """Vérifie si l'utilisateur est un administrateur"""
    return st.session_state.get('role') == 'admin'

def require_auth(role: str = None):
    """Vérifie l'authentification et le rôle optionnel"""
    init_session_state()
    
    if not is_logged_in():
        st.warning("Veuillez vous connecter pour accéder à cette page.")
        show_login_form()
        st.stop()
    
    if role and st.session_state.role != role:
        st.error("Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        st.stop()

def show_login_form():
    """Affiche le formulaire de connexion"""
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")
        
        if submitted:
            if login(username, password):
                st.success("Connexion réussie!")
                st.rerun()
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect")

def save_users(users):
    """Sauvegarde les utilisateurs dans un fichier JSON"""
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    """Hash le mot de passe avec SHA-256"""
    return sha256(password.encode()).hexdigest()

def is_authenticated():
    """Vérifie si l'utilisateur est authentifié"""
    return st.session_state.get('authenticated', False) 