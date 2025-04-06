import streamlit as st
import json
import os
from typing import Dict
from auth import require_auth

# Configuration de la page (doit être en premier)
st.set_page_config(page_title="Administration - Questionnaire Marketing", layout="wide")

# Vérifier l'authentification admin
require_auth(role="admin")

st.title("✏️ Administration du Questionnaire")

def load_questions() -> Dict:
    """Charge les questions depuis le fichier JSON"""
    if os.path.exists("questions.json"):
        with open("questions.json", "r", encoding='utf-8') as f:
            return json.load(f)
    return {
        "G1": {
            "title": "Communication",
            "questions": {
                "Q1": {"text": "Est-ce que vous faite de la publicité, promotion commerciale...", "default": "Oui", "coef": 1},
                "Q2": {"text": "Avez-vous une politique de communication ?", "default": "Non", "coef": 1}
            }
        }
    }

def save_questions(data: Dict):
    """Sauvegarde les questions dans un fichier JSON"""
    with open("questions.json", "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

questions_data = load_questions()

with st.expander("📁 Gestion des Groupes", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        new_group_name = st.text_input("Nom du nouveau groupe:")
        if st.button("➕ Ajouter Groupe") and new_group_name:
            new_key = f"G{len(questions_data)+1}"
            questions_data[new_key] = {"title": new_group_name, "questions": {}}
            save_questions(questions_data)
            st.rerun()
    
    with col2:
        group_to_delete = st.selectbox(
            "Groupe à supprimer:",
            [f"{k} - {v['title']}" for k, v in questions_data.items()],
            key="delete_group_select"
        )
        if st.button("🗑️ Supprimer Groupe"):
            group_key = group_to_delete.split(" - ")[0]
            del questions_data[group_key]
            save_questions(questions_data)
            st.rerun()

for group_key, group_data in questions_data.items():
    with st.expander(f"{group_key} : {group_data['title']}", expanded=True):
        new_title = st.text_input(
            "Titre:", 
            value=group_data['title'],
            key=f"group_title_{group_key}"
        )
        if new_title != group_data['title']:
            group_data['title'] = new_title
            save_questions(questions_data)

        st.markdown("### Ajouter une Question")
        new_q_col1, new_q_col2 = st.columns([4, 1])
        with new_q_col1:
            new_q_text = st.text_area(
                "Texte de la question:", 
                value="",
                height=100,
                key=f"new_q_text_{group_key}"
            )
        with new_q_col2:
            new_q_coef = st.number_input(
                "Coefficient:", 
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1,
                key=f"new_q_coef_{group_key}"
            )
            new_q_default = st.selectbox(
                "Réponse par défaut:",
                ["Aucun", "Oui", "Non"],
                key=f"new_q_default_{group_key}"
            )
            if st.button("➕ Ajouter", key=f"add_q_{group_key}") and new_q_text:
                q_num = len(group_data['questions']) + 1
                q_key = f"Q{q_num}"
                group_data['questions'][q_key] = {
                    "text": new_q_text,
                    "default": None if new_q_default == "Aucun" else new_q_default,
                    "coef": new_q_coef
                }
                save_questions(questions_data)
                st.rerun()

        st.markdown("### Questions Existantes")
        for q_key in list(group_data['questions'].keys()):
            q_data = group_data['questions'][q_key]
            with st.container(border=True):
                cols = st.columns([5, 1, 1, 1])
                
                with cols[0]:
                    new_text = st.text_area(
                        "Question:", 
                        value=q_data['text'],
                        key=f"q_text_{group_key}_{q_key}",
                        height=100
                    )
                    if new_text != q_data['text']:
                        q_data['text'] = new_text
                        save_questions(questions_data)
                
                with cols[1]:
                    new_default = st.selectbox(
                        "Défaut:", 
                        ["Aucun", "Oui", "Non"], 
                        index=0 if q_data['default'] is None else 1 if q_data['default'] == "Oui" else 2,
                        key=f"q_default_{group_key}_{q_key}"
                    )
                    q_data['default'] = None if new_default == "Aucun" else new_default
                    save_questions(questions_data)
                
                with cols[2]:
                    new_coef = st.number_input(
                        "Coef.", 
                        min_value=0.1,
                        max_value=10.0,
                        value=float(q_data['coef']),
                        step=0.1,
                        key=f"q_coef_{group_key}_{q_key}"
                    )
                    q_data['coef'] = new_coef
                    save_questions(questions_data)
                
                with cols[3]:
                    if st.button("🗑️", key=f"del_{group_key}_{q_key}"):
                        del group_data['questions'][q_key]
                        save_questions(questions_data)
                        st.rerun() 