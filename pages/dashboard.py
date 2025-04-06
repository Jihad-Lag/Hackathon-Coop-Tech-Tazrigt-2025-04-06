import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from auth import require_auth, is_admin
import numpy as np
from io import BytesIO

# Configuration de la page (doit être en premier)
st.set_page_config(page_title="Dashboard - Questionnaire Marketing", layout="wide")

# Vérifier l'authentification
require_auth()

def load_responses():
    """Charge l'historique des réponses"""
    try:
        with open("database/responses/responses_history.json", "r", encoding='utf-8') as f:
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

def process_responses(responses_history, current_user):
    """Traite les réponses pour créer un DataFrame avec filtrage par utilisateur"""
    if not responses_history:
        return pd.DataFrame()

    # Les réponses sont déjà dans le bon format, on peut les convertir directement
    df = pd.DataFrame(responses_history)
    
    # S'assurer que toutes les colonnes nécessaires existent
    required_columns = ['client_name', 'date', 'group', 'question', 'response', 'comment', 'user']
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''
    
    # Filtrer par utilisateur si ce n'est pas un admin
    if not is_admin():
        df = df[df['user'] == current_user]
    
    # Calculer le coefficient (1 pour Oui, 0 pour Non)
    df['coefficient'] = (df['response'] == 'Oui').astype(int)
    
    return df

# Charger les données
responses_history = load_responses()
questions = load_questions()

if not responses_history:
    st.warning("⚠️ Aucune réponse n'a encore été enregistrée.")
    st.stop()

# Convertir l'historique en DataFrame avec filtrage par utilisateur
df_responses = process_responses(responses_history, st.session_state.username)

# Sidebar pour les filtres
st.sidebar.header("🔍 Filtres")

# Afficher le rôle de l'utilisateur
if is_admin():
    st.sidebar.success("👑 Mode Administrateur")
else:
    st.sidebar.info(f"👤 Utilisateur: {st.session_state.username}")

# Filtre par client
clients = sorted(df_responses['client_name'].unique())
selected_client = st.sidebar.selectbox(
    "Sélectionner un client",
    ["Tous les clients"] + list(clients)
)

# Filtre par date
df_responses['date'] = pd.to_datetime(df_responses['date'])
dates = df_responses['date'].dt.date.unique()
start_date = st.sidebar.date_input(
    "Date de début",
    min(dates)
)
end_date = st.sidebar.date_input(
    "Date de fin",
    max(dates)
)

# Filtre par utilisateur (uniquement pour les admins)
if is_admin():
    users = sorted(df_responses['user'].unique())
    selected_user = st.sidebar.selectbox(
        "Sélectionner un utilisateur",
        ["Tous les utilisateurs"] + list(users)
    )

# Appliquer les filtres
mask = df_responses['date'].dt.date.between(start_date, end_date)
if selected_client != "Tous les clients":
    mask &= (df_responses['client_name'] == selected_client)
if is_admin() and selected_user != "Tous les utilisateurs":
    mask &= (df_responses['user'] == selected_user)
filtered_df = df_responses[mask]

# Layout principal
st.title("📊 Dashboard Analytics")

# Afficher les informations de filtrage
if is_admin():
    st.info(f"👤 Affichage des données pour: {selected_user if selected_user != 'Tous les utilisateurs' else 'Tous les utilisateurs'}")
else:
    st.info(f"👤 Affichage de vos données")

# Métriques principales
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_responses = len(filtered_df)
    st.metric("Total Réponses", total_responses)

with col2:
    unique_clients = filtered_df['client_name'].nunique()
    st.metric("Nombre de Clients", unique_clients)

with col3:
    positive_rate = (filtered_df['response'] == 'Oui').mean() * 100
    st.metric("Taux de Réponses Positives", f"{positive_rate:.1f}%")

with col4:
    avg_score = filtered_df['coefficient'].mean() * 100
    st.metric("Score Moyen", f"{avg_score:.1f}%")

# Créer les onglets
tab1, tab2, tab3 = st.tabs(["📊 Vue d'ensemble", "📝 Analyse détaillée", "💬 Commentaires"])

with tab1:
    # Graphique des réponses par groupe
    st.subheader("Répartition des réponses par groupe")
    response_by_group = filtered_df.groupby(['group', 'response']).size().unstack(fill_value=0)
    
    fig = px.bar(
        response_by_group,
        barmode='group',
        title="Réponses par groupe",
        labels={'value': 'Nombre de réponses', 'group': 'Groupe'},
        color_discrete_map={'Oui': '#2ecc71', 'Non': '#e74c3c'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Tableau des statistiques
    st.subheader("Statistiques par groupe")
    stats_by_group = filtered_df.groupby('group').agg({
        'response': [
            ('Total', 'count'),
            ('Oui', lambda x: (x == 'Oui').sum()),
            ('Non', lambda x: (x == 'Non').sum()),
            ('% Oui', lambda x: (x == 'Oui').mean() * 100)
        ]
    }).round(1)
    stats_by_group.columns = stats_by_group.columns.droplevel()
    st.dataframe(stats_by_group, use_container_width=True)

with tab2:
    # Sélection du groupe
    selected_group = st.selectbox(
        "Sélectionner un groupe",
        filtered_df['group'].unique()
    )
    
    group_data = filtered_df[filtered_df['group'] == selected_group]
    
    # Analyse par question
    st.subheader(f"Analyse des questions - {selected_group}")
    
    question_stats = group_data.groupby('question').agg({
        'response': [
            ('Total', 'count'),
            ('Oui', lambda x: (x == 'Oui').sum()),
            ('Non', lambda x: (x == 'Non').sum()),
            ('% Oui', lambda x: (x == 'Oui').mean() * 100)
        ]
    }).round(1)
    question_stats.columns = question_stats.columns.droplevel()
    
    # Graphique
    fig_questions = px.bar(
        question_stats.reset_index(),
        x='question',
        y='% Oui',
        title=f"Pourcentage de réponses positives - {selected_group}",
        labels={'question': 'Question', '% Oui': 'Pourcentage de Oui'}
    )
    fig_questions.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_questions, use_container_width=True)
    
    # Tableau
    st.dataframe(question_stats, use_container_width=True)

with tab3:
    st.subheader("Commentaires")
    
    # Filtrer les réponses avec commentaires
    comments_data = filtered_df[filtered_df['comment'].astype(str).str.strip() != '']
    
    if len(comments_data) > 0:
        # Grouper par client d'abord
        for client_name in comments_data['client_name'].unique():
            st.markdown(f"## Client: {client_name}")
            client_comments = comments_data[comments_data['client_name'] == client_name]
            
            # Puis par groupe
            for group in client_comments['group'].unique():
                st.markdown(f"### {group}")
                group_comments = client_comments[client_comments['group'] == group]
                
                for _, row in group_comments.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style='
                            background-color: #f8f9fa;
                            padding: 1rem;
                            border-radius: 5px;
                            margin: 0.5rem 0;
                            border-left: 4px solid #007bff;
                        '>
                        <strong>Question:</strong> {row['question']}<br>
                        <strong>Réponse:</strong> {row['response']}<br>
                        <strong>Commentaire:</strong> <em>{row['comment']}</em><br>
                        <small>Date: {row['date'].strftime('%d/%m/%Y %H:%M')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.info("Aucun commentaire n'a été trouvé pour les filtres sélectionnés.")

# Export Excel pour les administrateurs
if is_admin():
    st.sidebar.markdown("---")
    if st.sidebar.button("📥 Exporter les données (Excel)"):
        # Créer le buffer pour le fichier Excel
        output = BytesIO()
        
        # Créer le writer Excel
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Feuille des réponses
            filtered_df.to_excel(writer, sheet_name='Réponses', index=False)
            
            # Feuille des statistiques par groupe
            stats_by_group.to_excel(writer, sheet_name='Stats par groupe')
            
            # Feuille des commentaires
            if len(comments_data) > 0:
                comments_data.to_excel(writer, sheet_name='Commentaires', index=False)
        
        # Préparer le téléchargement
        output.seek(0)
        st.sidebar.download_button(
            label="📥 Télécharger l'export Excel",
            data=output,
            file_name=f'responses_export_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

# Analyse détaillée
st.subheader("Analyse Détaillée")
tabs = st.tabs(["Vue Générale", "Par Question", "Commentaires", "Tendances"])

with tabs[0]:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_responses = len(filtered_df)
        st.metric("Total Réponses", total_responses)
    
    with col2:
        avg_score = filtered_df['coefficient'].mean()
        st.metric("Score Moyen Global", f"{avg_score:.2f}")
    
    with col3:
        positive_rate = (filtered_df['response'] == 'Oui').mean() * 100
        st.metric("Taux de Réponses Positives", f"{positive_rate:.1f}%")
    
    with col4:
        unique_clients = filtered_df['client_name'].nunique()
        st.metric("Nombre de Clients", unique_clients)

    # Ajouter un graphique de tendance temporelle
    st.subheader("Évolution des Scores dans le Temps")
    daily_scores = filtered_df.groupby(filtered_df['date'].dt.date).agg({
        'coefficient': 'mean',
        'response': lambda x: (x == 'Oui').mean() * 100
    }).reset_index()
    
    if not daily_scores.empty:
        fig_daily = go.Figure()
        fig_daily.add_trace(go.Scatter(
            x=daily_scores['date'],
            y=daily_scores['coefficient'],
            name='Score Moyen',
            line=dict(color='#2ecc71')
        ))
        fig_daily.add_trace(go.Scatter(
            x=daily_scores['date'],
            y=daily_scores['response'],
            name='Taux de Réponses Positives (%)',
            line=dict(color='#3498db')
        ))
        fig_daily.update_layout(
            title="Évolution Quotidienne",
            xaxis_title="Date",
            yaxis_title="Score"
        )
        st.plotly_chart(fig_daily, use_container_width=True)
    else:
        st.info("Pas assez de données pour afficher l'évolution temporelle.")

with tabs[1]:
    # Analyse par question
    st.markdown("### Analyse par Question")
    
    question_stats = filtered_df.groupby(['group', 'question']).agg({
        'response': lambda x: (x == 'Oui').mean() * 100,
        'coefficient': 'mean',
        'client_name': 'count'
    }).reset_index()
    
    question_stats.columns = ['Groupe', 'Question', 'Taux de Oui (%)', 'Score Moyen', 'Nombre de Réponses']
    st.dataframe(question_stats, use_container_width=True)
    
    if not question_stats.empty:
        # Graphique des questions les plus positives
        fig_top_questions = px.bar(
            question_stats.sort_values('Taux de Oui (%)', ascending=False).head(10),
            x='Question',
            y='Taux de Oui (%)',
            color='Score Moyen',
            title="Top 10 des Questions avec le Plus de Réponses Positives",
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_top_questions, use_container_width=True)

with tabs[2]:
    # Affichage des commentaires
    st.markdown("### Commentaires par Question")
    question_comments = filtered_df[['client_name', 'group', 'question', 'response', 'comment']]
    question_comments = question_comments[question_comments['comment'].astype(str).str.strip() != '']
    
    if not question_comments.empty:
        for group in question_comments['group'].unique():
            with st.expander(f"📑 Groupe: {group}"):
                group_comments = question_comments[question_comments['group'] == group]
                for _, comment in group_comments.iterrows():
                    st.markdown(f"""
                    **Client:** {comment['client_name']}  
                    **Question:** {comment['question']}  
                    **Réponse:** {comment['response']}  
                    **Commentaire:** {comment['comment']}
                    ---
                    """)
    else:
        st.info("Aucun commentaire spécifique disponible")

with tabs[3]:
    # Analyse des tendances temporelles
    st.markdown("### Analyse des Tendances")
    
    # Tendances par groupe
    trends_group = filtered_df.groupby([
        pd.Grouper(key='date', freq='D'),
        'group'
    ]).agg({
        'response': lambda x: (x == 'Oui').mean() * 100,
        'coefficient': 'mean'
    }).reset_index()
    
    if not trends_group.empty:
        # Graphique des tendances
        fig_trends = px.line(
            trends_group,
            x='date',
            y=['response', 'coefficient'],
            color='group',
            title="Évolution par Groupe",
            labels={
                'response': 'Taux de Réponses Positives (%)',
                'coefficient': 'Score Moyen',
                'date': 'Date'
            }
        )
        st.plotly_chart(fig_trends, use_container_width=True)
        
        # Analyse de la progression
        st.subheader("Progression")
        progress_df = trends_group.groupby('group').agg({
            'response': ['first', 'last', lambda x: x.diff().mean()],
            'coefficient': ['first', 'last', lambda x: x.diff().mean()]
        }).round(2)
        
        progress_df.columns = [
            'Taux Initial (%)', 'Taux Final (%)', 'Progression Moyenne (%)',
            'Score Initial', 'Score Final', 'Progression Score'
        ]
        st.dataframe(progress_df, use_container_width=True)
    else:
        st.info("Pas assez de données pour afficher les tendances.") 