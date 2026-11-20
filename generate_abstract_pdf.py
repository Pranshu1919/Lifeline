"""
Generate Academic Research Paper Abstract PDF for LifeLine Project
Adheres strictly to academic formatting guidelines:
- Word count <= 250 words (exact: 184 words)
- Unreferenced (no citations or footnotes)
- No mathematical expressions
- No first-person sentence structure (objective third-person/passive)
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

def generate_abstract_pdf():
    # Target paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dirs = [
        os.path.join(base_dir, "documents"),
        os.path.join(base_dir, "document"),
        base_dir
    ]
    
    for d in output_dirs[:2]:
        os.makedirs(d, exist_ok=True)
        
    pdf_filenames = [
        os.path.join(d, "LifeLine_Research_Paper_Abstract.pdf") for d in output_dirs
    ]

    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'PaperTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'PaperSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=14
    )

    authors_style = ParagraphStyle(
        'Authors',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#334155'),
        spaceAfter=4
    )

    affiliation_style = ParagraphStyle(
        'Affiliation',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=14
    )

    abstract_heading_style = ParagraphStyle(
        'AbstractHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=8
    )

    abstract_body_style = ParagraphStyle(
        'AbstractBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=14.5,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#1e293b'),
        firstLineIndent=0,
        spaceAfter=10
    )

    keywords_style = ParagraphStyle(
        'Keywords',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        leading=13.5,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#334155'),
        spaceAfter=16
    )

    meta_badge_style = ParagraphStyle(
        'MetaBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#0369a1')
    )

    abstract_text = (
        "<b><i>Abstract</i>— Rapid and equitable emergency response during catastrophic disasters "
        "is frequently impeded by delays in manual triage, noisy multi-modal distress data, "
        "and suboptimal logistical resource allocation. This study presents LifeLine, an "
        "end-to-end multi-modal emergency response framework designed to bridge citizen "
        "distress communications with coordinated disaster authority operations. The framework "
        "couples fine-tuned ensemble natural language processing trained on humanitarian crisis data, "
        "dual lightweight convolutional vision networks, and mixed-integer linear programming "
        "optimization. Unstructured citizen reports undergo automated multi-task linguistic triage "
        "to categorize urgency and humanitarian needs, while visual media is authenticated against "
        "synthetic artifacts and graded for structural damage severity. Resource allocation is "
        "subsequently formalized as a constrained optimization problem solved to global mathematical "
        "optimality using station-to-incident geospatial distance matrices. Empirical evaluations "
        "demonstrate an 84.05 percent classification accuracy with an F1-score of 0.8361 and "
        "sub-four-millisecond latency for humanitarian text triage. Visual authenticity filtering "
        "achieves 79.86 percent accuracy, while the optimization model resolves multi-station dispatch "
        "configurations within eight milliseconds. By integrating automated multi-modal verification "
        "with mathematical dispatch optimization, the proposed architecture substantially mitigates "
        "human triage bottlenecks, curtails rescue latency, and ensures data-driven emergency logistical "
        "coordination during mass-casualty events.</b>"
    )

    keywords_text = (
        "<b><i>Keywords</i>—</b> Multi-Modal Machine Learning, Crisis Informatics, "
        "Disaster Response Systems, Natural Language Processing, Computer Vision, "
        "Mixed-Integer Linear Programming, Emergency Logistics."
    )

    # Calculate exact word count of abstract text alone (excluding tags)
    clean_text = abstract_text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "").replace("—", " ").replace("Abstract", "")
    words = [w for w in clean_text.split() if w.strip()]
    word_count = len(words)

    # Build PDF elements
    story = []
    
    # Header rule
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1e40af'), spaceAfter=14))
    
    # Paper Title
    story.append(Paragraph("LifeLine: An Automated Multi-Modal AI Framework for Real-Time Disaster Triage and Geospatial Resource Dispatch", title_style))
    story.append(Paragraph("A Multi-Modal Crisis Informatics and Emergency Logistics Architecture", subtitle_style))
    
    # Author Block
    authors_text = "<b>Vijay Katiyar</b> (2300270130205) &nbsp;&nbsp;|&nbsp;&nbsp; <b>Priyanshu Kushwaha</b> (2300270130136) &nbsp;&nbsp;|&nbsp;&nbsp; <b>Pranshu</b> (2300270130129)"
    story.append(Paragraph(authors_text, authors_style))
    
    guide_text = "Project Guide: <b>Dr. Sunil Kumar</b>, Professor"
    story.append(Paragraph(guide_text, authors_style))
    
    affiliation_text = "Department of Computer Science & Engineering<br/>Ajay Kumar Garg Engineering College, Ghaziabad, Uttar Pradesh, India"
    story.append(Paragraph(affiliation_text, affiliation_style))
    
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#cbd5e1'), spaceBefore=4, spaceAfter=14))
    
    # Abstract Section
    story.append(Paragraph("Abstract", abstract_heading_style))
    story.append(Paragraph(abstract_text, abstract_body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(keywords_text, keywords_style))
    
    # Divider
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#e2e8f0'), spaceBefore=8, spaceAfter=12))
    
    # Compliance Verification Box
    box_data = [
        [Paragraph(f"<b>Manuscript Guidelines Compliance Verification</b><br/>"
                   f"• <b>Word Count:</b> {word_count} words (Limit: &le; 250 words) &nbsp;&nbsp;|&nbsp;&nbsp; "
                   f"• <b>References / Citations:</b> None (Unreferenced) &nbsp;&nbsp;|&nbsp;&nbsp; "
                   f"• <b>Perspective:</b> Third-Person Only (No first-person terms) &nbsp;&nbsp;|&nbsp;&nbsp; "
                   f"• <b>Mathematical Expressions:</b> None", meta_badge_style)]
    ]
    meta_table = Table(box_data, colWidths=[480])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f9ff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bae6fd')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(meta_table)

    # Build first PDF and copy to other locations
    doc = SimpleDocTemplate(
        pdf_filenames[0],
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=48,
        bottomMargin=48
    )
    doc.build(story)
    print(f"Generated: {pdf_filenames[0]} (Word Count: {word_count})")
    
    import shutil
    for path in pdf_filenames[1:]:
        shutil.copyfile(pdf_filenames[0], path)
        print(f"Copied: {path}")

if __name__ == "__main__":
    generate_abstract_pdf()
