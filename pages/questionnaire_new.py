import streamlit as st
import pandas as pd
import json
import os
from typing import Dict, List
from datetime import datetime
from auth import require_auth

# Configuration de la page
st.set_page_config(page_title="Questionnaire Marketing", layout="wide")

# Vérifier l'authentification
require_auth()

# Création des dossiers nécessaires
os.makedirs("database/responses", exist_ok=True)

def load_questions():
    """Charge les questions depuis le fichier JSON"""
    try:
        with open("database/responses/questions.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_response(response_data):
    """Sauvegarde une réponse dans l'historique"""
    history_file = "database/responses/responses_history.json"
    
    # Charger l'historique existant
    if os.path.exists(history_file):
        with open(history_file, "r", encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    
    # Ajouter la nouvelle réponse
    history.append(response_data)
    
    # Sauvegarder l'historique mis à jour
    with open(history_file, "w", encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def calculate_progress():
    """Calcule la progression du questionnaire"""
    if not st.session_state.get('responses'):
        return 0
    total_questions = sum(len(group['questions']) for group in st.session_state.questions)
    answered_questions = len(st.session_state.responses)
    return int((answered_questions / total_questions) * 100)

def display_summary():
    """Affiche le résumé des réponses avec un style amélioré"""
    st.markdown("""
    <style>
    .summary-container {
        padding: 2rem;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin: 2rem 0;
    }
    .response-table {
        width: 100%;
        margin: 2rem 0;
    }
    .comment-section {
        margin-top: 2rem;
        padding: 1rem;
        border-left: 4px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

    # En-tête du résumé
    st.markdown("<div class='summary-container'>", unsafe_allow_html=True)
    st.markdown("## 📊 Résumé du Questionnaire")
    st.markdown(f"**Client:** {st.session_state.responses[0]['client_name']}")
    st.markdown(f"**Date:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Tableau des réponses par groupe
    for group in st.session_state.questions:
        st.markdown(f"### {group['title']}")
        
        # Filtrer les réponses pour ce groupe
        group_responses = [r for r in st.session_state.responses if r['group'] == group['key']]
        
        # Créer le DataFrame pour ce groupe
        data = []
        for response in group_responses:
            data.append({
                'Question': response['question'],
                'Réponse': response['response'],
                'Commentaire': response['comment'] if response['comment'] else ''
            })
        
        df = pd.DataFrame(data)
        
        # Afficher le tableau avec un style personnalisé
        st.dataframe(
            df,
            column_config={
                "Question": st.column_config.TextColumn("Question", width=500),
                "Réponse": st.column_config.TextColumn(
                    "Réponse",
                    width=100,
                    help="Oui/Non"
                ),
                "Commentaire": st.column_config.TextColumn(
                    "Commentaire",
                    width=300,
                    help="Commentaire additionnel"
                )
            },
            hide_index=True
        )
        st.markdown("---")

    # Section des commentaires
    comments_exist = any(r['comment'] for r in st.session_state.responses)
    if comments_exist:
        st.markdown("## 💬 Commentaires Détaillés")
        for group in st.session_state.questions:
            comments_in_group = [r for r in st.session_state.responses 
                               if r['group'] == group['key'] and r['comment']]
            if comments_in_group:
                st.markdown(f"### {group['title']}")
                for response in comments_in_group:
                    with st.container():
                        st.markdown("""
                        <div style='
                            background-color: #f8f9fa;
                            padding: 1rem;
                            border-radius: 5px;
                            margin: 0.5rem 0;
                            border-left: 4px solid #007bff;
                        '>
                        """, unsafe_allow_html=True)
                        st.markdown(f"**Question:** {response['question']}")
                        st.markdown(f"**Réponse:** {response['response']}")
                        st.markdown(f"**Commentaire:** _{response['comment']}_")
                        st.markdown("</div>", unsafe_allow_html=True)

# Interface principale
st.title("📝 Questionnaire Marketing")

# Charger les questions
questions = load_questions()
if not questions:
    st.warning("⚠️ Aucune question n'est configurée. Veuillez contacter l'administrateur.")
    st.stop()

# Initialiser les variables de session
if 'questions' not in st.session_state:
    st.session_state.questions = questions
if 'current_group' not in st.session_state:
    st.session_state.current_group = 0
if 'responses' not in st.session_state:
    st.session_state.responses = []
if 'show_comment' not in st.session_state:
    st.session_state.show_comment = {}

# Interface pour le nom du client
if 'questionnaire_completed' not in st.session_state:
    st.subheader("📋 Information Client")
    client_name = st.text_input("Nom du client *", key="client_name", help="Nom du client")

    if not client_name:
        st.warning("⚠️ Veuillez entrer le nom du client pour commencer le questionnaire.")
        st.stop()

    # Afficher la progression
    progress = calculate_progress()
    st.progress(progress)
    st.markdown(f"**Progression : {progress}%**")

    # Afficher le groupe de questions actuel
    current_group = st.session_state.questions[st.session_state.current_group]
    st.subheader(f"📝 {current_group['title']}")
    st.markdown(current_group['description'])

    # Afficher les questions du groupe
    for i, question in enumerate(current_group['questions']):
        st.markdown(f"**Q{i+1}. {question['text']}**")
        
        # Créer une clé unique pour la question
        question_key = f"{current_group['key']}_{i}"
        
        # Afficher les options de réponse
        col1, col2 = st.columns([3, 1])
        
        with col1:
            response = st.radio(
                "Votre réponse:",
                ["Oui", "Non"],
                key=f"response_{question_key}",
                horizontal=True
            )
        
        with col2:
            # Bouton pour afficher/masquer le commentaire
            if st.button("💬 Ajouter un commentaire", key=f"btn_{question_key}"):
                st.session_state.show_comment[question_key] = not st.session_state.show_comment.get(question_key, False)
        
        # Afficher le champ de commentaire si le bouton est cliqué
        comment = ""
        if st.session_state.show_comment.get(question_key, False):
            comment = st.text_area(
                "Votre commentaire:",
                key=f"comment_{question_key}",
                help="Ajoutez un commentaire pour expliquer votre réponse"
            )
        
        # Sauvegarder la réponse
        response_data = {
            "date": datetime.now().isoformat(),
            "username": st.session_state.username,
            "client_name": client_name,
            "group": current_group['key'],
            "group_title": current_group['title'],
            "question": question['text'],
            "response": response,
            "comment": comment
        }
        
        # Mettre à jour les réponses en session
        # Vérifier si la réponse existe déjà
        existing_response = next(
            (i for i, r in enumerate(st.session_state.responses) 
             if r['group'] == current_group['key'] and r['question'] == question['text']),
            None
        )
        
        if existing_response is not None:
            st.session_state.responses[existing_response] = response_data
        else:
            st.session_state.responses.append(response_data)
        
        st.markdown("---")

    # Navigation entre les groupes
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.current_group > 0:
            if st.button("⬅️ Groupe précédent"):
                st.session_state.current_group -= 1
                st.rerun()

    with col2:
        if st.session_state.current_group < len(st.session_state.questions) - 1:
            if st.button("Groupe suivant ➡️"):
                st.session_state.current_group += 1
                st.rerun()
        else:
            # Vérifier que toutes les questions ont une réponse
            total_questions = sum(len(group['questions']) for group in st.session_state.questions)
            if len(st.session_state.responses) == total_questions:
                if st.button("✅ Terminer le questionnaire"):
                    # Sauvegarder toutes les réponses
                    for response in st.session_state.responses:
                        save_response(response)
                    st.session_state.questionnaire_completed = True
                    st.rerun()
            else:
                st.warning("⚠️ Veuillez répondre à toutes les questions avant de terminer.")

else:
    # Afficher le résumé
    st.success("🎉 Questionnaire complété avec succès!")
    st.balloons()
    
    # Afficher le résumé détaillé
    display_summary()
    
    # Bouton pour recommencer
    if st.button("🔄 Commencer un nouveau questionnaire"):
        for key in ['responses', 'current_group', 'show_comment', 'questionnaire_completed']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun() 