import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from io import BytesIO
from datetime import datetime
import matplotlib
matplotlib.use('Agg')

def create_header_footer(canvas, doc):
    """Ajoute l'en-tête et le pied de page sur chaque page"""
    width, height = A4
    
    # En-tête
    canvas.saveState()
    canvas.setFillColor(colors.navy)
    canvas.rect(0, height - 2.5*cm, width, 2.5*cm, fill=True)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(1*cm, height - 1.7*cm, "Rapport d'Analyse Marketing")
    canvas.drawString(width - 5*cm, height - 1.7*cm, datetime.now().strftime("%d/%m/%Y"))
    
    # Pied de page
    canvas.setFillColor(colors.navy)
    canvas.rect(0, 0, width, 1.5*cm, fill=True)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(1*cm, 0.7*cm, f"Page {doc.page}")
    canvas.drawString(width - 7*cm, 0.7*cm, "Rapport généré automatiquement")
    canvas.restoreState()

def create_pie_chart(responses, title):
    """Crée un graphique circulaire des réponses"""
    yes_count = sum(1 for v in responses.values() if v == "Oui")
    no_count = sum(1 for v in responses.values() if v == "Non")
    
    plt.figure(figsize=(8, 6))
    plt.pie([yes_count, no_count], 
            labels=['Oui', 'Non'],
            colors=['#2ecc71', '#e74c3c'],
            autopct='%1.1f%%',
            startangle=90)
    plt.title(title, pad=20, fontsize=12)
    
    img_data = BytesIO()
    plt.savefig(img_data, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    img_data.seek(0)
    return Image(img_data, width=4*inch, height=3*inch)

def create_bar_chart(data, title):
    """Crée un graphique en barres des coefficients moyens par groupe"""
    plt.figure(figsize=(10, 5))
    bars = plt.bar(data.keys(), data.values(), color='#3498db')
    plt.title(title, pad=20, fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Coefficient moyen')
    
    # Ajouter les valeurs sur les barres
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom')
    
    img_data = BytesIO()
    plt.savefig(img_data, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    img_data.seek(0)
    return Image(img_data, width=6*inch, height=3*inch)

def create_summary_table(results):
    """Crée un tableau récapitulatif des réponses"""
    table_data = [['Groupe', 'Question', 'Réponse', 'Coefficient']]
    for result in results:
        table_data.append([
            result['Groupe'],
            result['Question'],
            result['Réponse'],
            str(result['Coefficient'])
        ])
    
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    table = Table(table_data, repeatRows=1)
    table.setStyle(table_style)
    return table

def generate_beautiful_pdf(responses, results, filename="Rapport_Marketing.pdf"):
    """Génère un rapport PDF décoratif et professionnel"""
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=3*cm,
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.navy,
        alignment=1
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.navy,
        spaceBefore=20,
        spaceAfter=10
    ))
    
    # Contenu
    story = []
    
    # Page de titre
    story.append(Paragraph("Rapport d'Analyse Marketing", styles['CustomTitle']))
    story.append(Spacer(1, 20))
    
    # Introduction
    story.append(Paragraph("Analyse des Réponses", styles['SectionTitle']))
    story.append(Paragraph(
        f"Date de génération : {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))
    
    # Graphique circulaire des réponses
    story.append(Paragraph("Distribution des Réponses", styles['SectionTitle']))
    story.append(create_pie_chart(responses, "Répartition des Réponses Oui/Non"))
    story.append(Spacer(1, 20))
    
    # Graphique des coefficients moyens par groupe
    story.append(Paragraph("Analyse par Groupe", styles['SectionTitle']))
    group_coeffs = {}
    for result in results:
        group = result['Groupe']
        if group not in group_coeffs:
            group_coeffs[group] = []
        group_coeffs[group].append(result['Coefficient'])
    
    avg_coeffs = {group: np.mean(coeffs) for group, coeffs in group_coeffs.items()}
    story.append(create_bar_chart(avg_coeffs, "Coefficients Moyens par Groupe"))
    story.append(PageBreak())
    
    # Tableau détaillé des réponses
    story.append(Paragraph("Détail des Réponses", styles['SectionTitle']))
    story.append(Spacer(1, 10))
    story.append(create_summary_table(results))
    
    # Génération du PDF
    doc.build(story, onFirstPage=create_header_footer, onLaterPages=create_header_footer)
    return filename 