import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import os, sys, shutil

sys.stdout.reconfigure(encoding='utf-8')

LOGO_PATH = r"c:\Users\Vijay\LifeLine\akgec_logo.png"

def setup_page(doc):
    section = doc.sections[0]
    section.page_width = Inches(8.27)   # A4
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(1.25)
    section.right_margin = Inches(0.9)

    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(11.5)
    font.color.rgb = RGBColor(0, 0, 0)

def add_header(doc):
    if os.path.exists(LOGO_PATH):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(0)
        p_logo.paragraph_format.space_after = Pt(2)
        run_img = p_logo.add_run()
        run_img.add_picture(LOGO_PATH, width=Inches(0.95))
        
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(0)
    p_inst.paragraph_format.space_after = Pt(4)
    p_inst.paragraph_format.line_spacing = 1.1
    
    r_coll = p_inst.add_run("AJAY KUMAR GARG ENGINEERING COLLEGE, GHAZIABAD\n")
    r_coll.font.name = 'Times New Roman'
    r_coll.font.size = Pt(12)
    r_coll.font.bold = True
    
    r_dept = p_inst.add_run("Department of Information Technology\n")
    r_dept.font.name = 'Times New Roman'
    r_dept.font.size = Pt(11)
    r_dept.font.bold = True
    
    r_univ = p_inst.add_run("(Affiliated to Dr. A.P.J. Abdul Kalam Technical University, Lucknow)\n")
    r_univ.font.name = 'Times New Roman'
    r_univ.font.size = Pt(9.5)
    r_univ.font.italic = True
    
    # Divider line
    p_line = doc.add_paragraph()
    p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_line.paragraph_format.space_before = Pt(0)
    p_line.paragraph_format.space_after = Pt(8)
    r_line = p_line.add_run("―" * 52)
    r_line.font.name = 'Times New Roman'
    r_line.font.size = Pt(9.5)
    r_line.font.color.rgb = RGBColor(140, 140, 140)

def add_doc_title(doc, title_text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(10)
    run = p.add_run(title_text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.font.bold = True
    return p

def add_body_p(doc, text, space_after=6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11)
    return p

def add_bullet_p(doc, text, bold_prefix=""):
    p = doc.add_paragraph(style='List Bullet')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.2
    p.paragraph_format.space_after = Pt(4)
    if bold_prefix:
        r_b = p.add_run(bold_prefix)
        r_b.font.name = 'Times New Roman'
        r_b.font.size = Pt(10.5)
        r_b.font.bold = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(10.5)
    return p

# =============================================================
# 1. DECLARATION DOCUMENT (1 Page)
# =============================================================
def generate_declaration():
    doc = Document()
    setup_page(doc)
    add_header(doc)
    add_doc_title(doc, "CANDIDATE'S DECLARATION")
    
    add_body_p(
        doc,
        "We, the undersigned students of the Department of Information Technology, Ajay Kumar Garg Engineering College, "
        "Ghaziabad, declare that the project synopsis titled “Smart Disaster Response and Resource Allocation System (LifeLine)” "
        "is an authentic record of our own research and engineering work carried out under the supervision and guidance of "
        "Dr. Sunil Kumar, Professor, Department of Information Technology.",
        space_after=6
    )
    
    add_body_p(
        doc,
        "We affirm that the proposed software architecture, mathematical optimization models (SciPy MILP), multimodal AI pipelines "
        "(TF-IDF NLP triage and PyTorch MobileNetV3 classifiers), and database schemas have not been plagiarized from any other project, "
        "thesis, or report submitted elsewhere. All prior literature, benchmark datasets (CrisisMMD v2.0), and open-source libraries "
        "have been scrupulously credited in standard IEEE reference format [1]–[17].",
        space_after=6
    )
    
    p_pledge_title = doc.add_paragraph()
    p_pledge_title.paragraph_format.space_before = Pt(4)
    p_pledge_title.paragraph_format.space_after = Pt(2)
    r_pt = p_pledge_title.add_run("Academic Integrity & Responsible AI Usage Pledge:")
    r_pt.font.name = 'Times New Roman'
    r_pt.font.size = Pt(11)
    r_pt.font.bold = True
    
    add_bullet_p(
        doc,
        "Ethical Tool Use: Generative AI tools were utilized strictly for technical grammar refinement and document formatting in accordance with academic integrity guidelines.",
        "• "
    )
    add_bullet_p(
        doc,
        "Intellectual Ownership: The system architecture, optimization formulations, database models, and codebase represent our genuine conceptual and engineering effort.",
        "• "
    )
    add_bullet_p(
        doc,
        "Development Commitment: The performance benchmarks and response-time targets described herein are active development goals for the academic session 2026–27.",
        "• "
    )

    p_date = doc.add_paragraph()
    p_date.paragraph_format.space_before = Pt(8)
    p_date.paragraph_format.space_after = Pt(2)
    r_dt = p_date.add_run("Date: September 16, 2026\t\t\t\t\t\tPlace: Ghaziabad")
    r_dt.font.name = 'Times New Roman'
    r_dt.font.size = Pt(10)
    r_dt.font.bold = True

    sig_table = doc.add_table(rows=2, cols=3)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    students = [
        ("Vijay Katiyar", "Roll No. 2300270130205\nB.Tech IT, 7th Sem"),
        ("Priyanshu Kushwaha", "Roll No. 2300270130136\nB.Tech IT, 7th Sem"),
        ("Pranshu", "Roll No. 2300270130129\nB.Tech IT, 7th Sem")
    ]
    
    for i in range(3):
        cell = sig_table.rows[0].cells[i]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(24)
        r = p.add_run("_____________________\n(Signature)")
        r.font.name = 'Times New Roman'
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(120, 120, 120)
        
    for i, (name, details) in enumerate(students):
        cell = sig_table.rows[1].cells[i]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.line_spacing = 1.1
        r_n = p.add_run(name + "\n")
        r_n.font.name = 'Times New Roman'
        r_n.font.size = Pt(10.5)
        r_n.font.bold = True
        r_d = p.add_run(details)
        r_d.font.name = 'Times New Roman'
        r_d.font.size = Pt(9.5)
        
    save_and_copy(doc, "Declaration.docx")

# =============================================================
# 2. CERTIFICATE DOCUMENT (1 Page)
# =============================================================
def generate_certificate():
    doc = Document()
    setup_page(doc)
    add_header(doc)
    add_doc_title(doc, "CERTIFICATE OF SUPERVISION")
    
    add_body_p(
        doc,
        "This is to certify that the project synopsis titled “Smart Disaster Response and Resource Allocation System (LifeLine)” "
        "has been prepared and submitted by the following students of the Department of Information Technology, Ajay Kumar Garg "
        "Engineering College, Ghaziabad, under my direct supervision and academic mentorship:",
        space_after=6
    )
    
    # Table of students
    st_table = doc.add_table(rows=4, cols=4)
    st_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["S. No.", "Name of Candidate", "University Roll No.", "Branch & Year"]
    
    for idx, h in enumerate(headers):
        cell = st_table.rows[0].cells[idx]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10)
        r.font.bold = True
        
    st_data = [
        ("1", "Vijay Katiyar", "2300270130205", "B.Tech IT - 4th Year"),
        ("2", "Priyanshu Kushwaha", "2300270130136", "B.Tech IT - 4th Year"),
        ("3", "Pranshu", "2300270130129", "B.Tech IT - 4th Year")
    ]
    
    for r_idx, row in enumerate(st_data):
        for c_idx, val in enumerate(row):
            cell = st_table.rows[r_idx+1].cells[c_idx]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(9.5)
            if c_idx == 1:
                r.font.bold = True

    add_body_p(
        doc,
        "To the best of my knowledge and belief, this work represents an authentic record of their own study, system design, "
        "and implementation planning. The technical proposals, machine learning formulations, and optimization workflows presented "
        "herein have not been submitted elsewhere for the award of any other academic degree or diploma.",
        space_after=6
    )
    
    add_body_p(
        doc,
        "This project synopsis is approved for submission in partial fulfillment of the requirements for the award of the degree "
        "of Bachelor of Technology in Information Technology from Dr. A.P.J. Abdul Kalam Technical University, Lucknow, for the "
        "academic session 2026–27.",
        space_after=8
    )

    auth_table = doc.add_table(rows=2, cols=3)
    auth_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    for i in range(3):
        cell = auth_table.rows[0].cells[i]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(28)
        r = p.add_run("_____________________\n(Signature)")
        r.font.name = 'Times New Roman'
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(120, 120, 120)

    authorities = [
        ("Dr. Sunil Kumar", "Project Guide & Professor\nDepartment of IT, AKGEC"),
        ("Dr. Aditya Pratap Singh", "Project Coordinator\nDepartment of IT, AKGEC"),
        ("Prof. (Dr.) Rahul Sharma", "Head of Department (HoD)\nDepartment of IT, AKGEC")
    ]

    for i, (name, role) in enumerate(authorities):
        cell = auth_table.rows[1].cells[i]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.line_spacing = 1.1
        r_n = p.add_run(name + "\n")
        r_n.font.name = 'Times New Roman'
        r_n.font.size = Pt(10.5)
        r_n.font.bold = True
        r_r = p.add_run(role)
        r_r.font.name = 'Times New Roman'
        r_r.font.size = Pt(9.5)

    save_and_copy(doc, "Certificate.docx")

# =============================================================
# 3. ACKNOWLEDGEMENT DOCUMENT (1 Page)
# =============================================================
def generate_acknowledgement():
    doc = Document()
    setup_page(doc)
    add_header(doc)
    add_doc_title(doc, "ACKNOWLEDGEMENT")
    
    add_body_p(
        doc,
        "The completion of this project synopsis for “Smart Disaster Response and Resource Allocation System (LifeLine)” marks "
        "an important milestone in our academic curriculum, and we wish to express our deep sense of gratitude to all those who "
        "guided, supported, and encouraged us throughout its preparation.",
        space_after=6
    )
    
    add_body_p(
        doc,
        "First and foremost, we express our profound gratitude and heartfelt thanks to our project supervisor, Dr. Sunil Kumar, "
        "Professor in the Department of Information Technology. His rigorous academic guidance, constructive critique of our "
        "multimodal machine learning and mathematical optimization formulations, and emphasis on practical operational feasibility "
        "were invaluable in shaping this work. His continuous encouragement and prompt reviews of early drafts helped us develop "
        "a cohesive, life-saving software architecture.",
        space_after=6
    )
    
    add_body_p(
        doc,
        "We convey our sincere thanks to Prof. (Dr.) Rahul Sharma, Head of Department (IT), for providing institutional facilities, "
        "computing laboratories, and an inspiring academic environment. We also extend our earnest appreciation to Dr. Aditya Pratap Singh, "
        "Project Coordinator, for his systematic organization of project milestones and valuable administrative support.",
        space_after=6
    )
    
    add_body_p(
        doc,
        "Our sincere thanks are also due to the faculty members and technical staff of the Department of Information Technology, "
        "Ajay Kumar Garg Engineering College, for their constructive suggestions and server configuration insights.",
        space_after=6
    )

    add_body_p(
        doc,
        "Finally, we express our warmest appreciation to our parents, family members, and classmates for their enduring patience, "
        "moral support, and continuous motivation throughout this endeavor.",
        space_after=8
    )
    
    p_sig = doc.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_sig.paragraph_format.space_before = Pt(18)
    p_sig.paragraph_format.line_spacing = 1.15
    
    r_sig = p_sig.add_run(
        "Vijay Katiyar (2300270130205)\n"
        "Priyanshu Kushwaha (2300270130136)\n"
        "Pranshu (2300270130129)\n\n"
        "B.Tech (Information Technology)\n"
        "Ajay Kumar Garg Engineering College, Ghaziabad"
    )
    r_sig.font.name = 'Times New Roman'
    r_sig.font.size = Pt(10.5)
    r_sig.font.bold = True

    save_and_copy(doc, "Acknowledgement.docx")

def save_and_copy(doc, filename):
    local_path = os.path.join(r"c:\Users\Vijay\LifeLine", filename)
    docs_path = os.path.join(r"C:\Users\Vijay\LifeLine_Documents", filename)
    
    doc.save(local_path)
    print(f"SUCCESS: Saved {local_path}")
    
    try:
        shutil.copy2(local_path, docs_path)
        print(f"SUCCESS: Copied to {docs_path}")
    except Exception as e:
        print(f"Error copying to {docs_path}: {e}")

if __name__ == '__main__':
    generate_declaration()
    generate_certificate()
    generate_acknowledgement()
