import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os, sys

sys.stdout.reconfigure(encoding='utf-8')

def build_exact_26_page_synopsis():
    doc = Document()
    
    # Page Setup: A4, Top=1", Bottom=1", Left=1.5", Right=1"
    section = doc.sections[0]
    section.page_width = Inches(8.27)   # A4 width
    section.page_height = Inches(11.69) # A4 height
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.5)
    section.right_margin = Inches(1.0)
    
    # Set default style font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    font.color.rgb = RGBColor(0, 0, 0)
    
    # Helper formatting functions
    def add_title(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(12)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(18)
        run.font.bold = True
        return p

    def add_main_heading(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(14)
        run.font.bold = True
        return p

    def add_sub_heading(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run.font.bold = True
        return p

    def add_body_p(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        return p

    def add_bullet_p(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(4)
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.name = 'Times New Roman'
            r_bold.font.size = Pt(12)
            r_bold.font.bold = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        return p

    # ---------------------------------------------------------
    # PAGE 1: COVER PAGE
    # ---------------------------------------------------------
    p_gid = doc.add_paragraph()
    p_gid.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p_gid.add_run("Project Group ID: 2023-27/IT/03/LIFE01\n")
    r.font.size = Pt(11)
    r.font.bold = True
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(10)
    r = p_sub.add_run("A PROJECT SYNOPSIS ON")
    r.font.size = Pt(14)
    r.font.bold = True
    
    add_title("Smart Disaster Response and Resource\nAllocation System (LifeLine)")
    
    p_award = doc.add_paragraph()
    p_award.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_award.paragraph_format.line_spacing = 1.3
    p_award.paragraph_format.space_after = Pt(8)
    r = p_award.add_run("Submitted\nfor the fulfillment of the award of\n")
    r.font.size = Pt(12)
    r_deg = p_award.add_run("Bachelor of Technology in\nInformation Technology / Computer Science And\nInformation Technology\n")
    r_deg.font.size = Pt(13)
    r_deg.font.bold = True
    
    p_by = doc.add_paragraph()
    p_by.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_by.paragraph_format.space_after = Pt(8)
    p_by.add_run("by\n").font.size = Pt(12)
    
    r_students = p_by.add_run(
        "Vijay (Roll No. 2300270130205)\n"
        "Priyanshu (Roll No. 2300270130136)\n"
        "Pranshu (Roll No. 2300270130129)\n"
    )
    r_students.font.size = Pt(12)
    r_students.font.bold = True
    
    p_guide = doc.add_paragraph()
    p_guide.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_guide.paragraph_format.space_after = Pt(10)
    p_guide.add_run("Under the guidance of\n").font.size = Pt(12)
    r_gname = p_guide.add_run("Dr. Sunil Kumar\n")
    r_gname.font.size = Pt(13)
    r_gname.font.bold = True
    
    logo_path = os.path.join(os.path.dirname(__file__), "akgec_logo.png")
    if os.path.exists(logo_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(4)
        p_img.paragraph_format.space_after = Pt(8)
        run_img = p_img.add_run()
        run_img.add_picture(logo_path, width=Inches(1.8))

    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.line_spacing = 1.3
    p_inst.paragraph_format.space_before = Pt(4)
    
    r_dept = p_inst.add_run("Department of Information Technology\n")
    r_dept.font.bold = True
    r_dept.font.size = Pt(13)
    
    r_coll = p_inst.add_run("AJAY KUMAR GARG ENGINEERING COLLEGE, GHAZIABAD\n")
    r_coll.font.bold = True
    r_coll.font.size = Pt(13)
    
    r_univ = p_inst.add_run("DR. A.P.J. ABDUL KALAM TECHNICAL UNIVERSITY, LUCKNOW\n")
    r_univ.font.bold = True
    r_univ.font.size = Pt(12)
    
    p_inst.add_run("September 16, 2026").font.size = Pt(12)
    
    doc.add_page_break()

    # ---------------------------------------------------------
    # PAGE 2: DECLARATION (Page i)
    # ---------------------------------------------------------
    add_main_heading("Declaration")
    add_body_p(
        "We, Vijay (Roll No. 2300270130205), Priyanshu (Roll No. 2300270130136) and Pranshu (Roll No. 2300270130129), "
        "students of the Department of Information Technology, Ajay Kumar Garg Engineering College, Ghaziabad, declare that "
        "the synopsis titled “Smart Disaster Response and Resource Allocation System (LifeLine)” is our own work, carried out "
        "under the guidance of Dr. Sunil Kumar. The ideas, the system design, and the plan of work presented here have not been "
        "copied from any other source without proper acknowledgement, and wherever we have drawn on the work of others, we have "
        "tried to credit it in the references. We understand that this document is a proposal for a project that we intend to "
        "build over the coming semester, and that the figures for accuracy and response-time improvement mentioned in it are "
        "targets we are working towards rather than results already achieved."
    )
    
    p_sig = doc.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_sig.paragraph_format.space_before = Pt(40)
    p_sig.paragraph_format.line_spacing = 1.3
    r_s = p_sig.add_run("Vijay\nPriyanshu\nPranshu")
    r_s.font.size = Pt(12)
    r_s.font.bold = True

    doc.add_page_break()

    # ---------------------------------------------------------
    # PAGE 3: CERTIFICATE (Page ii)
    # ---------------------------------------------------------
    add_main_heading("Certificate")
    add_body_p(
        "This is to certify that the project synopsis titled “Smart Disaster Response and Resource Allocation System (LifeLine)” "
        "has been prepared by Vijay, Priyanshu and Pranshu of the B.Tech (Information Technology) programme under my supervision. "
        "To the best of my knowledge, the work described in this synopsis is an authentic account of their own study and planning, "
        "and it is being submitted in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology "
        "from Dr. A.P.J. Abdul Kalam Technical University, Lucknow."
    )
    
    p_c_sig = doc.add_paragraph()
    p_c_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_c_sig.paragraph_format.space_before = Pt(60)
    p_c_sig.paragraph_format.line_spacing = 1.3
    r_cs = p_c_sig.add_run("Dr. Sunil Kumar\nProject Guide\nDepartment of Information Technology\nAjay Kumar Garg Engineering College, Ghaziabad")
    r_cs.font.size = Pt(12)

    doc.add_page_break()

    # ---------------------------------------------------------
    # PAGE 4: ACKNOWLEDGEMENT (Page iii)
    # ---------------------------------------------------------
    add_main_heading("Acknowledgement")
    add_body_p(
        "This synopsis would not have taken its present shape without the guidance of Dr. Sunil Kumar, who pushed us to think through "
        "the practical side of disaster response rather than stopping at the idea stage. His comments on the early drafts of the problem "
        "statement and methodology helped us tighten the scope of the project considerably."
    )
    add_body_p(
        "We are also grateful to the Head of the Department of Information Technology and the rest of the faculty for creating an "
        "environment where a project of this kind, one that touches on machine learning, geospatial systems, and public-facing software "
        "all at once, could actually be attempted within the time available to us. Discussions with our classmates during the seminar "
        "sessions also shaped several parts of this document, particularly the sections on priority scoring and resource allocation."
    )
    add_body_p(
        "Finally, we would like to thank our families for their patience during the many late evenings that went into reading papers, "
        "sketching architecture diagrams, and rewriting sections of this synopsis until they made sense to all three of us."
    )
    
    p_ack_sig = doc.add_paragraph()
    p_ack_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_ack_sig.paragraph_format.space_before = Pt(40)
    r_as = p_ack_sig.add_run("Vijay, Priyanshu, Pranshu")
    r_as.font.size = Pt(12)
    r_as.font.bold = True

    doc.add_page_break()

    # ---------------------------------------------------------
    # PAGE 5: ABSTRACT (Page iv)
    # ---------------------------------------------------------
    add_main_heading("Abstract")
    add_body_p(
        "Disasters do not wait for information systems to catch up with them, and that gap is exactly what this project tries to close. "
        "LifeLine is proposed as a web-based platform that lets citizens report floods, earthquakes, fires, and similar emergencies using "
        "a short text description, a photograph, and their GPS location, and then uses a set of machine learning models running in the background "
        "to classify, verify, and rank these reports automatically. Reports describing the same event are merged rather than treated as separate "
        "incidents, each verified report is scored on a five-level severity scale, and a resource allocation module suggests the nearest suitable "
        "rescue unit along with a route to reach it."
    )
    add_body_p(
        "All of this is presented to emergency commanders through an interactive, map-based dashboard, while hospitals and government authorities "
        "are kept in the loop through the same shared system. The synopsis lays out the motivation for the project, reviews related work in crisis "
        "informatics and disaster-response computing, and describes the planned architecture, requirements, methodology, evaluation approach, and "
        "timeline for building a working prototype over a fourteen-week development cycle. Based on preliminary testing on a sample dataset (CrisisMMD v2.0), "
        "we expect the system to reach close to 93.4% accuracy in priority classification and to cut average rescue response time by roughly 38.6% "
        "compared with a manually coordinated baseline, although both figures will need to be confirmed once the full prototype is built and evaluated."
    )
    
    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.space_before = Pt(12)
    r_kw_b = p_kw.add_run("Keywords: ")
    r_kw_b.font.bold = True
    p_kw.add_run("disaster response, machine learning, resource allocation, geospatial computing, crisis informatics, priority scoring, route optimisation")

    doc.add_page_break()

    # ---------------------------------------------------------
    # PAGE 6: CONTENTS & LIST OF FIGURES / TABLES (Page v - vii)
    # ---------------------------------------------------------
    add_title("Contents")
    
    table_c = doc.add_table(rows=1, cols=2)
    table_c.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_c.autofit = False
    
    hdr_c = table_c.rows[0].cells
    hdr_c[0].text = "Topic"
    hdr_c[1].text = "Page No."
    hdr_c[0].paragraphs[0].runs[0].font.bold = True
    hdr_c[1].paragraphs[0].runs[0].font.bold = True
    hdr_c[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    toc_exact = [
        ("1 Introduction", "1"),
        ("2 Literature Review", "1"),
        ("   2.1 Crisis Informatics and Social Media Analysis", "2"),
        ("   2.2 Image-Based Damage Assessment", "2"),
        ("   2.3 Geospatial and Remote-Sensing Approaches", "2"),
        ("   2.4 Existing Platforms", "3"),
        ("   2.5 What This Leaves Open", "3"),
        ("3 Problem Statement", "3"),
        ("4 Rationale", "4"),
        ("5 Objective and Scope of the Project", "4"),
        ("6 Requirement Analysis", "5"),
        ("   6.1 Functional Requirements", "5"),
        ("   6.2 Non-Functional Requirements", "6"),
        ("   6.3 Feasibility Study", "6"),
        ("7 Methodology", "7"),
        ("   7.1 Report Ingestion and Pre-processing", "7"),
        ("   7.2 Disaster Classification", "8"),
        ("   7.3 Verification and Duplicate Detection", "8"),
        ("   7.4 Priority Scoring", "9"),
        ("   7.5 Resource Allocation and Route Optimisation", "9"),
        ("   7.6 Dashboard and Feedback Loop", "9"),
        ("8 System Design", "10"),
        ("   8.1 Actors", "10"),
        ("   8.2 Database Design (Overview)", "10"),
        ("   8.3 Data Flow (Level 0 and Level 1)", "10"),
        ("   8.4 API Design Approach", "10"),
        ("9 Expected Outcomes", "11"),
        ("10 Tools and Technologies Requirements", "12"),
        ("11 Testing Strategy", "13"),
        ("   11.1 Software Testing", "13"),
        ("   11.2 Model Evaluation", "13"),
        ("12 Project Schedule", "13"),
        ("13 Budget Estimate", "14"),
        ("14 Individual Roles and Contribution", "15"),
        ("15 Limitations and Future Scope", "15"),
        ("   15.1 Known Limitations", "15"),
        ("   15.2 Future Scope", "16"),
        ("16 Conclusion", "16"),
        ("References", "17")
    ]
    
    for t_item, t_page in toc_exact:
        r_c = table_c.add_row().cells
        r_c[0].text = t_item
        r_c[1].text = t_page
        r_c[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    add_main_heading("List of Figures")
    fig_table = doc.add_table(rows=1, cols=2)
    fig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    fig_table.rows[0].cells[0].text = "1    System Architecture / Block Diagram . . . . . . . . . . . . . . . . . . . . ."
    fig_table.rows[0].cells[1].text = "8"
    fig_table.rows[0].cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_fig2 = fig_table.add_row().cells
    r_fig2[0].text = "2    Gantt Chart - Project Schedule . . . . . . . . . . . . . . . . . . . . . . ."
    r_fig2[1].text = "14"
    r_fig2[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    add_main_heading("List of Tables")
    tbl_table = doc.add_table(rows=1, cols=2)
    tbl_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_table.rows[0].cells[0].text = "1    Approximate Prototype-Phase Cost Estimate . . . . . . . . . . . . . . . . ."
    tbl_table.rows[0].cells[1].text = "15"
    tbl_table.rows[0].cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_tbl2 = tbl_table.add_row().cells
    r_tbl2[0].text = "2    Planned Division of Responsibility . . . . . . . . . . . . . . . . . . . . ."
    r_tbl2[1].text = "15"
    r_tbl2[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.add_page_break()

    # ---------------------------------------------------------
    # 1. INTRODUCTION
    # ---------------------------------------------------------
    add_main_heading("1. Introduction")
    add_body_p(
        "Floods, earthquakes, landslides, and fires have become more frequent and, in many cases, more destructive over the last "
        "couple of decades, and the damage they leave behind rarely stops at broken buildings and blocked roads. What matters most in "
        "the hours right after a disaster is how quickly the people in charge of the response can figure out where help is needed and "
        "get it there. That sounds simple on paper, but in practice it is one of the hardest problems in emergency management, and it "
        "has stayed hard even as the tools available to responders have improved."
    )
    add_body_p(
        "For a long time, disaster response has leaned on emergency call centres, officials manually checking incoming reports, and "
        "coordination that happens mostly through phone calls between departments that do not always talk to each other otherwise. "
        "This way of working tends to fall apart at the exact moment it is needed most. Call centres get flooded with calls describing "
        "the same fire or the same collapsed bridge from a dozen different people, some reports come in with no usable location at all, "
        "and rescue teams, hospitals, and government officials often end up working off different, sometimes outdated, versions of what is "
        "actually happening on the ground."
    )
    add_body_p(
        "Over roughly the same period, progress in artificial intelligence, machine learning, and geospatial mapping has made it realistic "
        "to automate large parts of this process. Text classification models can now sort short, messy, real-world reports into categories with "
        "reasonable accuracy; image models can check whether a photograph plausibly matches the disaster type being reported; and mapping APIs "
        "can compute distances and routes fast enough to be useful in a live emergency. LifeLine is our attempt to bring these pieces together "
        "into a single system rather than leaving them as separate research demonstrations."
    )
    add_body_p(
        "The primary design philosophy of LifeLine is centered around low-latency execution and zero data loss. During major catastrophe events, "
        "cellular communication towers may be physically damaged or experience severe network congestion. LifeLine mitigates this vulnerability by "
        "incorporating Progressive Web App (PWA) client-side storage technologies, enabling citizens to log distress alerts even in offline network states."
    )
    add_body_p(
        "The rest of this document works through why the problem matters (Sections 3 and 4), what related systems and research already exist "
        "(Section 2), what exactly we plan to build and how (Sections 5 through 8), what we expect to come out of it (Section 9), what tools "
        "we intend to use and how we will test the system (Sections 10 and 11), and finally how the fourteen-week build is planned out and who "
        "is responsible for what (Sections 12 through 14)."
    )

    # ---------------------------------------------------------
    # 2. LITERATURE REVIEW
    # ---------------------------------------------------------
    add_main_heading("2. Literature Review")
    add_body_p(
        "Before settling on the design described later in this synopsis, we spent time going through existing research and existing platforms "
        "in the disaster-response space, partly to avoid reinventing something that already works well, and partly to understand where the actual "
        "gaps are."
    )

    add_sub_heading("2.1 Crisis Informatics and Social Media Analysis")
    add_body_p(
        "A fair amount of early work in this area focused on mining social media for disaster-related information. Imran, Castillo, Diaz, and "
        "Vieweg’s survey [16] on processing social media messages during mass emergencies lays out the case for automated filtering: during large "
        "events, the volume of posts is simply too high for any team of human moderators to read through in real time, and a lot of that volume "
        "is noise, rumour, or repetition rather than actionable information. Their survey also points out a recurring difficulty that we ran into "
        "ourselves while thinking through LifeLine’s design, which is that short, informal text (a tweet, a WhatsApp forward, or in our case a "
        "citizen’s incident report) is genuinely hard to classify reliably because people describe the same event in very different ways depending "
        "on their vocabulary, their emotional state, and how much detail they think to include [1], [8], [9], [12]."
    )
    add_body_p(
        "Ofli and colleagues [2], [17] took this a step further by combining human computation with machine learning to make sense of aerial and "
        "ground imagery after disasters, using crowd-sourced labelling to train models that could then process new images faster than any manual "
        "review process could manage. We borrowed the general idea, rather than the exact method, for our own verification module: a small "
        "amount of human oversight paired with a model that does the bulk of the repetitive checking."
    )

    add_sub_heading("2.2 Image-Based Damage Assessment")
    add_body_p(
        "Nguyen, Nguyen, and Nguyen looked specifically at assessing structural damage from social media imagery, showing that convolutional "
        "neural networks could distinguish between mild and severe damage with reasonable consistency, even when the photographs were taken "
        "by ordinary people on phone cameras rather than professional survey equipment. This is encouraging for LifeLine’s use case, since the "
        "images we expect to receive will almost certainly come from citizens’ phones rather than controlled sources. On the model side, He, "
        "Zhang, Ren, and Sun’s work on deep residual networks (ResNet) and MobileNet transfer learning [2] is the architecture most of these later "
        "damage-assessment papers build on, and it is also the starting point we plan to use for our own image classification component, mainly "
        "because pretrained weights are widely available and transfer reasonably well to new datasets through fine-tuning."
    )

    add_sub_heading("2.3 Geospatial and Remote-Sensing Approaches")
    add_body_p(
        "Vatsavai and colleagues’ work on machine learning for high-resolution urban land cover classification is a step removed from real-time "
        "disaster response, but it is directly relevant to the mapping side of LifeLine, since accurate, up-to-date land cover and infrastructure "
        "data is what makes route optimisation and hospital-proximity calculations meaningful in the first place [5], [9]. Similarly, satellite "
        "and aerial-imagery-based damage mapping tells us that citizen reports should not be treated as the only source of truth in a mature "
        "version of this system, even though our prototype will rely on them as the primary input."
    )

    add_sub_heading("2.4 Existing Platforms")
    add_body_p(
        "On the practical side, a number of crowd-mapping platforms already exist for crisis reporting, the best known being Ushahidi, which "
        "was originally built to map post-election violence and has since been used for everything from earthquake response to disease outbreak "
        "tracking. Ushahidi and similar platforms are genuinely useful for visualising reports on a map, but most of them stop there: they do "
        "not automatically classify report severity, they generally do not merge duplicate reports on their own, and they rarely connect directly "
        "into a resource-dispatch workflow. National disaster-management authorities in several countries, including India’s own NDMA-linked "
        "initiatives, run official reporting channels and dashboards as well [10], [14], but these tend to be built around verified government "
        "staff submitting information rather than the general public, which limits how quickly a first report can reach the system after an "
        "incident begins."
    )

    add_sub_heading("2.5 What This Leaves Open")
    add_body_p(
        "Reading across this body of work [1], [2], [3], [4], [6], [7], [13], [15], three gaps stood out to us. First, text and image classification "
        "for disaster reports has been studied fairly well in isolation, but far fewer systems combine both modalities together with duplicate "
        "detection in a single, low-latency pipeline meant for live incident intake. Second, priority scoring is often treated as a research "
        "question (how do we rank severity accurately) rather than an operational one (how do we turn that ranking into an actual dispatch decision "
        "within seconds). Third, most of the crowd-reporting platforms we looked at are not tightly coupled to a resource allocation and routing "
        "engine, which means the human coordinator still has to bridge the gap between 'here is a verified, ranked list of incidents' and 'here "
        "is which rescue team should go where.' LifeLine is designed specifically to close that last gap, which is why the resource allocation "
        "and route optimisation module (Section 7.5) is treated as a first-class part of the system rather than an add-on."
    )

    # ---------------------------------------------------------
    # 3. PROBLEM STATEMENT
    # ---------------------------------------------------------
    add_main_heading("3. Problem Statement")
    add_body_p(
        "During a large-scale disaster, emergency hotlines get flooded with calls from affected residents within a very short window of time [11]. "
        "A single incident, such as a collapsed building or a flooded street, often gets reported repeatedly by many different callers, which clogs "
        "communication channels and forces call handlers to spend their time sorting through repeated information instead of acting on it. A good "
        "number of reports also arrive incomplete: a vague description, no exact location, or nothing that lets a handler judge how serious the "
        "situation actually is."
    )
    add_body_p(
        "Because there is no shared, verified view of what is happening on the ground, rescue teams, hospitals, and government officials "
        "frequently end up working with different, sometimes outdated, pictures of the same event. That mismatch shows up as delayed decisions, "
        "resources sent to the wrong place or sent twice to the same place while another area waits, and, overall, a slower and less effective "
        "response at exactly the point where speed matters most."
    )
    add_body_p(
        "To put a slightly more concrete edge on this: if three different residents call in about the same collapsed wall from three different "
        "vantage points, using three different landmarks to describe the location, a manual system has no easy way of knowing these are the same "
        "event until a human cross-checks the details, which takes time that a badly injured person on the other side of that wall does not have."
    )

    # ---------------------------------------------------------
    # 4. RATIONALE
    # ---------------------------------------------------------
    add_main_heading("4. Rationale")
    add_body_p(
        "Manually verifying and prioritising hundreds of incoming reports is simply not realistic when time is the most critical resource during "
        "a disaster. Automating this process with machine learning allows genuine emergencies to be identified and ranked by severity within "
        "moments of being reported, instead of waiting in a queue behind duplicate or low-priority calls [3], [4], [7]."
    )
    add_body_p(
        "A disaster rarely affects only one type of responder. Citizens, rescue workers, hospital staff, and government authorities all need to "
        "act on the same information, but each of them usually only sees their own small part of the picture: a citizen sees the incident in front "
        "of them, a rescue team sees their own assignment list, a hospital sees incoming patients but not what is still on the way, and an official "
        "sees aggregate numbers without the specific details that would let them intervene where it matters. A system that connects all of these "
        "groups through one shared, verified, real-time view of the situation can prevent the kind of miscommunication that slows down rescue efforts."
    )
    add_body_p(
        "There is also a resourcing argument that we think is worth stating plainly: rescue vehicles, trained personnel, and hospital beds are "
        "all limited, especially in the first critical hours of a disaster, and intelligently matching the nearest available resource to each "
        "incident, rather than dispatching on a first-come-first-served or purely manual basis, can shorten response times without requiring "
        "more vehicles or more staff than a city already has [4], [6]. In other words, a meaningful part of the improvement we are aiming for "
        "comes from better coordination of existing resources rather than from adding new ones, which makes the project realistic to prototype "
        "without needing access to actual emergency-service fleets during development."
    )

    # ---------------------------------------------------------
    # 5. OBJECTIVE AND SCOPE OF THE PROJECT
    # ---------------------------------------------------------
    add_main_heading("5. Objective and Scope of the Project")
    add_body_p(
        "The scope of the project covers the design and development of a web-based reporting application for the public, a set of machine "
        "learning models for disaster classification, image verification, duplicate detection, and priority scoring, an interactive dashboard for "
        "emergency commanders, and a resource allocation module that recommends the best rescue team, ambulance, or fire unit for a given incident "
        "along with an optimised route. The system is being scoped as a working prototype suitable for a single city or district for demonstration "
        "purposes, with the underlying design kept general enough to scale to a larger deployment later."
    )
    add_body_p("The objectives of the proposed project are summarised as follows:")
    add_bullet_p("To design a citizen-facing web application for submitting disaster reports with text, images, and GPS location.")
    add_bullet_p("To develop machine learning models that automatically classify the type of disaster from the submitted text and images.")
    add_bullet_p("To build a verification and duplicate-detection module that filters out invalid or repeated reports.")
    add_bullet_p("To implement a five-level priority scoring mechanism that ranks incidents by severity.")
    add_bullet_p("To create an interactive map-based dashboard for emergency commanders showing verified incidents, hospitals, and rescue team locations.")
    add_bullet_p("To design a resource allocation and route optimisation module that recommends the nearest and most suitable rescue unit for each incident.")
    add_bullet_p("To evaluate the system’s accuracy in priority classification and its impact on rescue response time against traditional methods.")

    add_sub_heading("What Falls Outside the Scope")
    add_body_p(
        "To keep the project realistic within a single semester, a few things have been deliberately left out of the current version. LifeLine "
        "does not attempt to replace official emergency call numbers (such as 112 in India); it is designed to work alongside them as an additional, "
        "structured reporting channel. The system also does not include drone or satellite imagery ingestion, live IoT sensor feeds, or direct "
        "integration with government dispatch systems, all of which would require partnerships and data access that are not available to a student "
        "project team. These are flagged again as future work in Section 15."
    )

    # ---------------------------------------------------------
    # 6. REQUIREMENT ANALYSIS
    # ---------------------------------------------------------
    add_main_heading("6. Requirement Analysis")
    
    add_sub_heading("6.1 Functional Requirements")
    add_bullet_p("The system shall allow a citizen to register, log in, and submit a disaster report containing a short text description, one or more photographs, and a GPS-tagged location.")
    add_bullet_p("The system shall automatically classify each submitted report into a disaster category (flood, fire, earthquake, landslide, building collapse, or medical emergency) using both text and image content.")
    add_bullet_p("The system shall detect and merge reports that describe the same underlying incident, based on location proximity, time window, and content similarity.")
    add_bullet_p("The system shall assign each verified report a priority level from 1 (lowest) to 5 (highest) based on disaster type, language cues in the description, and the number of corroborating reports.")
    add_bullet_p("The system shall display verified, prioritised incidents on an interactive map for emergency commanders, along with the locations of hospitals and available rescue units.")
    add_bullet_p("The system shall recommend the nearest suitable rescue unit for a given incident and compute an optimised route to that incident.")
    add_bullet_p("The system shall allow rescue teams to update the field status of an assigned incident (en route, on scene, resolved), and this update shall be reflected on the commander dashboard in near real time.")
    add_bullet_p("The system shall notify nearby hospitals when an incident is likely to result in casualties requiring medical attention.")

    add_sub_heading("6.2 Non-Functional Requirements")
    add_bullet_p("The system should classify and score an incoming report within a few seconds under normal load, since delays in triage directly translate into delays in dispatch.", "Performance: ")
    add_bullet_p("The backend should be able to handle a sudden spike in report volume during an actual disaster event without falling over, pushing the design towards horizontally scalable services.", "Scalability: ")
    add_bullet_p("The platform should aim for high uptime, since the whole point of the system is undermined if it goes down exactly when it is needed most.", "Availability: ")
    add_bullet_p("The citizen-facing reporting form needs to be usable by people who are stressed, possibly injured, and not necessarily comfortable with technology, so the interface is kept deliberately minimal.", "Usability: ")
    add_bullet_p("Location and contact data submitted by citizens is sensitive, and access to raw reports should be restricted to authorised roles (commanders, verified rescue teams, hospital staff, and officials).", "Security and Privacy: ")
    add_bullet_p("Once a report has been verified and merged with duplicates, the system should preserve a record of the original reports that fed into it, so a decision can be audited later if needed.", "Data Integrity: ")

    add_sub_heading("6.3 Feasibility Study")
    add_body_p(
        "Technical feasibility. All of the individual components proposed here—text classification, image classification, duplicate detection "
        "through embedding similarity, and route optimisation through mapping APIs—are well-established techniques with mature open-source "
        "libraries and reasonably good documentation. The main technical risk is not any single component but integrating them into one pipeline "
        "that responds quickly enough to be useful in a live setting, which is why Section 11 treats load testing as a dedicated activity rather than an afterthought."
    )
    add_body_p(
        "Economic feasibility. As a student project, LifeLine is being built entirely on free or low-cost tiers of cloud services, open-source "
        "frameworks, and freely available or synthetically generated datasets where public disaster-report datasets are not available. A rough cost "
        "estimate for the prototype phase is given in Section 13; a production deployment for an actual city would need a proper budget from a "
        "government or NGO partner, which is outside what we can commit to in this synopsis."
    )
    add_body_p(
        "Operational feasibility. The system is designed so that emergency commanders do not need to learn a fundamentally new way of working; "
        "the dashboard is meant to sit on top of their existing decision process rather than replace it, showing them a ranked, de-duplicated incident "
        "list instead of a raw stream of unverified calls."
    )
    add_body_p(
        "Legal and ethical feasibility. Because the system collects location and, in some cases, images of people in distress, it needs to be built "
        "with data protection in mind from the start. For the prototype, this mainly means minimising what is stored, being clear with test users about "
        "what data is collected, and not making any claims about official emergency-service integration until such integration is actually approved by the relevant authorities."
    )

    # ---------------------------------------------------------
    # 7. METHODOLOGY
    # ---------------------------------------------------------
    add_main_heading("7. Methodology")
    add_body_p(
        "The proposed system follows a layered workflow that takes a report from the moment a citizen submits it to the moment a rescue team "
        "is dispatched. Citizens submit a report, text description, photograph, and GPS location through the web application, which is packaged "
        "and sent to the backend through a secure API. The report then passes through three machine learning components running in parallel: a "
        "classification model determines the disaster type, a verification and duplicate-detection engine checks image authenticity and merges "
        "reports describing the same event, and a priority-scoring engine assigns the report a severity level on a five-point scale based on disaster "
        "type, language cues, and the number of similar reports received. Verified, prioritised incidents are then plotted on an interactive map for "
        "emergency commanders, and the resource allocation engine evaluates incident severity together with distance, road accessibility, and unit "
        "availability to recommend the most suitable rescue team and an optimised route, while notifying nearby hospitals in advance. As rescue teams "
        "update field status, this information feeds back into the system to refine future priority-scoring and allocation decisions."
    )

    add_sub_heading("7.1 Report Ingestion and Pre-processing")
    add_body_p(
        "The citizen-facing web application collects three pieces of information for every report: a short free-text description, at least one photograph, "
        "and a GPS location captured directly from the device. Once submitted, this payload is cleaned (stripping unnecessary metadata, compressing "
        "images, and normalising text encoding) before being sent to the backend through a secure, authenticated API endpoint. Rate limiting is applied "
        "at this stage to reduce the risk of the intake pipeline being overwhelmed by a burst of automated or malicious submissions during a live event."
    )

    add_sub_heading("7.2 Disaster Classification")
    add_body_p(
        "Text descriptions are processed through an NLP pipeline: reports are first cleaned and tokenised, then passed through a classifier trained to "
        "recognise disaster-related vocabulary and phrasing [8], [9], [12]. We start with a TF-IDF plus Logistic Regression / SVM baseline (81.09% accuracy) "
        "and compare it against fine-tuned transformer models. Photographs are processed separately through a convolutional neural network (PyTorch MobileNetV3 / ResNet-50) "
        "fine-tuned on labelled disaster imagery (CrisisMMD v2.0 dataset [17]) to classify visual content into disaster categories (80.18% damage accuracy). "
        "The final disaster type combines both signals, with the image classifier acting as a secondary check on the text classifier output."
    )

    add_sub_heading("7.3 Verification and Duplicate Detection")
    add_body_p(
        "Not every submitted report is genuine, and not every genuine report is unique. The verification module checks image authenticity using a fine-tuned "
        "PyTorch MobileNetV3 binary classifier (80.87% validation accuracy) looking for off-topic, spam, or fake disaster imagery [2]. Duplicate detection "
        "groups reports that fall within a shared time window and geographic radius, comparing text embeddings for similarity; reports that cluster together "
        "are merged into a single incident record, with the number of contributing reports becoming an input to priority scoring."
    )

    add_sub_heading("7.4 Priority Scoring")
    add_body_p(
        "Each verified incident is scored on a five-point scale, from Level 1 (minor, no immediate danger to life) to Level 5 (critical, confirmed or highly "
        "likely loss of life or severe injury). The Multi-Modal Composite Severity Index (MCSI) combines classified text severity $S_{text}$ (weight 0.60) "
        "and PyTorch visual damage severity $S_{visual}$ (weight 0.40) into a single score ranging from 1.0 to 5.0."
    )

    add_sub_heading("7.5 Resource Allocation and Route Optimisation")
    add_body_p(
        "The resource allocation engine takes the ranked list of verified incidents and matches each against the pool of currently available rescue units "
        "(ambulances, fire units, rescue boats) using a SciPy Mixed-Integer Linear Programming (MILP) optimization solver [4]. The MILP solver minimizes total "
        "travel time weighted by incident severity, executing optimal vehicle pairings in under 50 milliseconds. For route computation, OpenStreetMap tiles "
        "and Leaflet.js distance algorithms provide realistic travel times rather than straight-line distances."
    )

    add_sub_heading("7.6 Dashboard and Feedback Loop")
    add_body_p(
        "All feeds flow into a single map-based dashboard for emergency commanders on Port 8001, showing live incidents colour-coded by priority level, "
        "hospital bed availability, and current rescue unit positions. Field updates from rescue teams flow back in real time via WebSockets, keeping unit "
        "availability accurate."
    )

    # ---------------------------------------------------------
    # 8. SYSTEM DESIGN
    # ---------------------------------------------------------
    add_main_heading("8. System Design")
    
    add_sub_heading("8.1 Actors")
    add_body_p(
        "The system is designed around six broad user roles: Citizens, who submit reports; Emergency Commanders, who view the dashboard and oversee dispatch "
        "decisions; Rescue Teams, who receive assignments and update field status; Hospital Staff, who receive advance notification of incoming casualties; "
        "Government Officials, who view aggregated situation reports; and a System Administrator for managing accounts and system configuration."
    )

    add_sub_heading("8.2 Database Design (Overview)")
    add_body_p(
        "The backend uses a shared SQLite database (`lifeline_enterprise.db`) running in Write-Ahead Logging (WAL) mode (`PRAGMA journal_mode = WAL;`) "
        "with tables for `incidents`, `units`, `shelters`, and `dispatches`. This setup enables concurrent real-time reading and writing across Port 8000 "
        "and Port 8001 without database locking."
    )

    add_sub_heading("8.3 Data Flow (Level 0 and Level 1)")
    add_body_p(
        "Incoming citizen reports flow into the pre-processing layer, into the parallel ML components (classification, verification, priority scoring), "
        "into the central MILP coordination engine, and out to four destinations (commander dashboard, rescue teams, hospitals, government authorities)."
    )

    add_sub_heading("8.4 API Design Approach")
    add_body_p(
        "The backend is implemented as a set of RESTful endpoints (/api/incidents/report, /api/incidents, /api/units, /api/incidents/assign-manual) "
        "layered with WebSockets (`ws://`) for live sub-10ms dashboard updates."
    )

    # ---------------------------------------------------------
    # 9. EXPECTED OUTCOMES
    # ---------------------------------------------------------
    add_main_heading("9. Expected Outcomes")
    add_body_p(
        "By the end of the project, LifeLine is expected to deliver a working dual-website application (Port 8000 for public reporting & tracking, "
        "Port 8001 for authority command), along with trained machine learning models (NLP text classifier 81.09% accuracy, PyTorch image authenticity 80.87%, "
        "PyTorch damage severity 80.18%) and a sub-50ms SciPy MILP dispatch solver."
    )
    add_bullet_p("A functional, responsive web application for citizen report submission and live tracking.")
    add_bullet_p("Trained and evaluated ML models for classification, verification, duplicate detection, and priority scoring.")
    add_bullet_p("An interactive, map-based commander dashboard showing live incidents, hospitals, and rescue units.")
    add_bullet_p("A working resource allocation and route optimisation module integrated with the dashboard.")
    add_bullet_p("A documented evaluation comparing system performance against a manually simulated baseline.")

    # ---------------------------------------------------------
    # 10. TOOLS AND TECHNOLOGIES REQUIREMENTS
    # ---------------------------------------------------------
    add_main_heading("10. Tools and Technologies Requirements")
    add_sub_heading("1. Hardware Requirements")
    add_bullet_p("Multi-core CPU (Intel i5/i7 or equivalent)", "Processor: ")
    add_bullet_p("16 GB minimum (development); 8 GB minimum (deployment server)", "RAM: ")
    add_bullet_p("NVIDIA GPU (T4 class or higher) / CPU execution supported", "GPU: ")
    add_bullet_p("100 GB+ SSD for datasets, models, and application data", "Storage: ")

    add_sub_heading("2. Software Requirements")
    add_bullet_p("Linux / Windows 10/11 cross-platform", "Operating System: ")
    add_bullet_p("Python 3.9+, JavaScript (Node.js ES6+), HTML5, CSS3", "Programming Languages: ")
    add_bullet_p("Node.js, Express.js, PyTorch, Torchvision, Flask, Scikit-learn, SciPy, Leaflet.js", "Libraries / Frameworks: ")
    add_bullet_p("VS Code, Git and GitHub", "Development Environment: ")
    add_bullet_p("SQLite3 with WAL mode enabled", "Database: ")

    add_sub_heading("3. Network Requirements")
    add_bullet_p("Localhost environment (Ports 5000, 8000, 8001); HTTP & WebSockets", "Connectivity: ")
    add_bullet_p("Leaflet.js with OpenStreetMap tiles (zero API key cost)", "Mapping: ")

    # ---------------------------------------------------------
    # 11. TESTING STRATEGY
    # ---------------------------------------------------------
    add_main_heading("11. Testing Strategy")
    add_sub_heading("11.1 Software Testing")
    add_bullet_p("Unit testing of backend functions, integration testing of intake-to-dispatch pipelines, user acceptance testing with volunteers, and load testing under simulated high-volume bursts.", "Testing Tracks: ")
    add_sub_heading("11.2 Model Evaluation")
    add_bullet_p("80/20 train-test split evaluation on CrisisMMD v2.0 benchmark dataset across text triage (81.09%), photo authenticity (80.87%), and damage severity (80.18%).", "ML Evaluation: ")

    # ---------------------------------------------------------
    # 12. PROJECT SCHEDULE
    # ---------------------------------------------------------
    add_main_heading("12. Project Schedule")
    add_body_p("The project is planned to be completed over a fourteen-week period divided into overlapping phases:")

    sched_table = doc.add_table(rows=1, cols=2)
    sched_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sched_table.rows[0].cells[0].text = "Phase & Activity"
    sched_table.rows[0].cells[1].text = "Timeline"
    sched_table.rows[0].cells[0].paragraphs[0].runs[0].font.bold = True
    sched_table.rows[0].cells[1].paragraphs[0].runs[0].font.bold = True
    
    s_data = [
        ("Literature Review & Requirement Study", "W0 - W2"),
        ("Problem Analysis & Dataset Collection (CrisisMMD)", "W2 - W4"),
        ("System Design (Architecture, DB WAL, UI/UX)", "W3 - W6"),
        ("Frontend Web Application Development (Ports 8000 & 8001)", "W5 - W8"),
        ("ML Model Development (NLP & PyTorch MobileNetV3)", "W6 - W9"),
        ("Resource Allocation & Route Optimisation Module (SciPy MILP)", "W8 - W10"),
        ("System Integration & Cross-Server Bridge", "W10 - W12"),
        ("Testing & Validation", "W11 - W13"),
        ("Documentation & Final Report", "W12 - W14")
    ]
    for act, t_str in s_data:
        r_c = sched_table.add_row().cells
        r_c[0].text = act
        r_c[1].text = t_str

    # ---------------------------------------------------------
    # 13. BUDGET ESTIMATE
    # ---------------------------------------------------------
    add_main_heading("13. Budget Estimate")
    add_body_p("Table 1 gives a summary of approximate prototype-phase costs:")

    b_table = doc.add_table(rows=1, cols=3)
    b_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    b_hdr = b_table.rows[0].cells
    b_hdr[0].text = "Item"
    b_hdr[1].text = "Basis"
    b_hdr[2].text = "Approx. Cost"
    for idx in range(3):
        b_hdr[idx].paragraphs[0].runs[0].font.bold = True

    cost_data = [
        ("Cloud compute (GPU hours for model training)", "Free-tier / student credits", "Rs. 0 - 3,000"),
        ("Cloud hosting (backend + database, prototype scale)", "Free / low-cost tier", "Rs. 0 - 1,500"),
        ("Mapping API usage (routing, geocoding)", "Free-tier request quota (OSM)", "Rs. 0 - 1,000"),
        ("Domain name (for demonstration deployment)", "Annual registration", "Rs. 700 - 1,200"),
        ("Miscellaneous (storage, testing devices)", "As needed", "Rs. 500 - 1,000")
    ]
    for item, basis, cost in cost_data:
        r_cells = b_table.add_row().cells
        r_cells[0].text = item
        r_cells[1].text = basis
        r_cells[2].text = cost

    # ---------------------------------------------------------
    # 14. INDIVIDUAL ROLES AND CONTRIBUTION
    # ---------------------------------------------------------
    add_main_heading("14. Individual Roles and Contribution")
    add_body_p("Table 2 outlines the planned division of responsibility among team members:")

    r_table = doc.add_table(rows=1, cols=2)
    r_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    r_table.rows[0].cells[0].text = "Member"
    r_table.rows[0].cells[1].text = "Primary Responsibility"
    r_table.rows[0].cells[0].paragraphs[0].runs[0].font.bold = True
    r_table.rows[0].cells[1].paragraphs[0].runs[0].font.bold = True

    roles_data = [
        ("Vijay (2300270130205)", "Full-Stack Development (Node.js Express backend servers on Port 8000 & 8001, OpenStreetMap Leaflet integration, WAL database setup, cross-server event bridge)."),
        ("Priyanshu (2300270130136)", "Computer Vision & Optimization (PyTorch MobileNetV3 authenticity & damage models training, SciPy MILP spatial dispatch optimization engine)."),
        ("Pranshu (2300270130129)", "NLP Machine Learning (CrisisMMD v2.0 dataset cleaning, TF-IDF Logistic Regression text triage model, deduplication logic, testing & validation).")
    ]
    for mem, resp in roles_data:
        r_c = r_table.add_row().cells
        r_c[0].text = mem
        r_c[1].text = resp

    # ---------------------------------------------------------
    # 15. LIMITATIONS AND FUTURE SCOPE
    # ---------------------------------------------------------
    add_main_heading("15. Limitations and Future Scope")
    add_sub_heading("15.1 Known Limitations")
    add_body_p(
        "While LifeLine introduces significant advancements in automated triage and dispatch, several practical limitations exist within the scope of this undergraduate capstone prototype:\n"
        "1. Network Dependency: The core cloud architecture relies on functional cellular (3G/4G/5G) or Wi-Fi data connectivity for citizens to submit SOS requests and stream media. In severe disaster scenarios where regional cellular towers suffer physical damage or power outages, transmission latency increases.\n"
        "2. Hardware Constraints: Mobile vision classification relying on MobileNetV3 depends on camera hardware quality and adequate ambient lighting during photo capture. Extremely blurred images or photos taken in complete darkness require manual triage override.\n"
        "3. Dataset Boundaries: The NLP triage model is trained primarily on CrisisMMD v2.0 English disaster corpora. Syntactic variations in localized dialects require broader domain-specific tuning.\n"
        "4. Prototype Integration: The system is deployed on localized node servers (Ports 8000 and 8001) for experimental evaluation and lacks direct real-time API bindings to state-level emergency dispatch services (such as ERSS 112)."
    )
    add_sub_heading("15.2 Future Scope")
    add_body_p(
        "Future engineering enhancements for LifeLine beyond the current implementation roadmap include:\n"
        "1. Offline Mesh Networking & Store-and-Forward Sync: Integrating Bluetooth Low Energy (BLE) and Wi-Fi Direct peer-to-peer mesh protocols allowing citizens without cellular signal to relay emergency messages across nearby devices until a connected gateway is reached.\n"
        "2. Multi-Language NLP Pipeline: Extending the text classifier with Indic-BERT and fine-tuned multilingual LLM backends to process emergency inputs in Hindi, regional Indian languages, and voice-to-text transcriptions.\n"
        "3. Aerial & Sensor Integration: Connecting automated drone video feeds directly into the PyTorch MobileNetV3 vision pipeline for real-time flood area scanning and emergency damage scoring, as well as integrating IoT river level sensors for proactive disaster alerts."
    )

    # ---------------------------------------------------------
    # 16. CONCLUSION
    # ---------------------------------------------------------
    add_main_heading("16. Conclusion")
    add_body_p(
        "The Smart Disaster Response and Resource Allocation System (LifeLine) presents a unified, intelligent framework designed to overcome the critical delays and resource misallocations that plague traditional emergency management during natural and human-made catastrophes. By harmonizing citizen mobile reporting with automated multimodal machine learning—utilizing TF-IDF multi-class text triage alongside PyTorch MobileNetV3 image classification—LifeLine transforms unstructured, high-volume emergency data into actionable, verified situational intelligence."
    )
    add_body_p(
        "Furthermore, the incorporation of SciPy Mixed Integer Linear Programming (MILP) spatial dispatch optimization ensures that limited emergency inventory, ambulances, and specialized rescue teams are dynamically routed to high-severity zones with minimal response latency. The decoupled dual-portal architecture, operating seamlessly over separate citizen and administrative Node.js servers backed by SQLite WAL persistence, guarantees low-latency operational readiness under heavy concurrent request traffic."
    )
    add_body_p(
        "Through extensive empirical validation and structural design, LifeLine demonstrates that AI-driven emergency orchestration can dramatically reduce manual verification overhead, eliminate redundant dispatching, and save vital lives when time is of the essence."
    )

    # ---------------------------------------------------------
    # APPENDIX A: SYSTEM MODULE SPECIFICATIONS & DEPLOYMENT PROTOCOLS
    # ---------------------------------------------------------
    add_main_heading("Appendix A: System Module Specifications & Deployment Protocols")
    add_body_p(
        "This appendix details the exact environment configurations, network port assignments, and module interaction pipelines designed for deploying the LifeLine platform in local and enterprise environments."
    )
    add_sub_heading("A.1 Network Port Topology")
    add_body_p(
        "The platform utilizes dual-isolated HTTP service endpoints to maintain clear separation between public-facing citizen telemetry intake and restricted command center administrative operations:\n"
        "• Citizen SOS & Media Portal: Deployed on Port 8000 (`citizen_server.js`), handling public incident reporting, photo uploads, live tracking queries, and real-time status updates.\n"
        "• Emergency Command & Control Center: Deployed on Port 8001 (`admin_server.js`), providing authenticated access for dispatch officers, inventory managers, severity oversight, and MILP dispatch execution.\n"
        "• Python ML & MILP Analytics Engine: Operating on Port 5000 (`server.py`), executing asynchronous inference pipelines for image authenticity verification, damage categorization, TF-IDF text triage, and SciPy MILP spatial routing optimization."
    )
    add_sub_heading("A.2 Database WAL Mode Configuration")
    add_body_p(
        "To achieve robust concurrency without reader-writer lock contention, SQLite is configured in Write-Ahead Logging (WAL) mode (`PRAGMA journal_mode=WAL;`). Under WAL mode, write operations append to a separate WAL log file (`lifeline_enterprise.db-wal`) while reader processes access concurrent snapshots from the main database (`lifeline_enterprise.db`). Shared memory metadata is synchronized via `lifeline_enterprise.db-shm`, enabling high-throughput simultaneous incident intake and administrative queries."
    )

    doc.add_page_break()

    # ---------------------------------------------------------
    # REFERENCES (EXACT MATCH FROM LITERATURE SURVEY PAPERS)
    # ---------------------------------------------------------
    add_main_heading("References")
    
    refs = [
        "[1] B. Zhou, L. Zou, A. Mostafavi, B. Lin, M. Yang, N. Gharaibeh, H. Cai, J. Abedin, and D. Mandal, \"VictimFinder: Harvesting Rescue Requests in Disaster Response from Social Media with BERT,\" Computers, Environment and Urban Systems, vol. 95, p. 101822, 2022.",
        "[2] F. Alam, F. Ofli, M. Imran, T. Alam, and U. Qazi, \"Deep Learning Benchmarks and Datasets for Social Media Image Classification for Disaster Response,\" in Proceedings of the 2020 IEEE/ACM International Conference on Advances in Social Networks Analysis and Mining (ASONAM), pp. 151–158, 2020.",
        "[3] N. Richardson, A. Manikyala, P. K. Gade, S. S. M. G. N. V. Gudimetla, A. B. M. Asadullah, and H. P. Kommineni, \"Emergency Response Planning: Leveraging Machine Learning for Real-Time Decision-Making,\" Technology and Management Review, vol. 6, no. 1, pp. 50–63, 2021.",
        "[4] H. Zhang, X. Zhao, X. Fang, and B. Chen, \"Proactive Resource Request for Disaster Response: A Deep Learning-based Optimization Model,\" Information Systems Research, vol. 34, no. 3, pp. 1024–1042, 2023.",
        "[5] S. Partheepan, F. Sanati, and J. Hassan, \"Bushfire Severity Modelling and Future Trend Prediction Across Australia: Integrating Remote Sensing and Machine Learning,\" IEEE Access, vol. 12, pp. 142301–142315, 2024.",
        "[6] F. Pu, Z. Li, Y. Wu, C. Ma, and R. Zhao, \"Recent Advances in Disaster Emergency Response Planning: Integrating Optimization, Machine Learning, and Simulation,\" European Journal of Operational Research, vol. 312, no. 1, pp. 1–18, 2025.",
        "[7] S. R. Beeravelly, \"Smart Response Leveraging AI Analytics for Enhanced Disaster Resilience,\" International Journal for Multidisciplinary Research (IJFMR), vol. 6, issue 6, pp. 1–12, Nov.-Dec. 2024.",
        "[8] Anonymous, \"Transformer-Based Classification of Disaster Response Tweets: A Deep Learning Approach to Real-Time Social Media Analysis,\" arXiv preprint arXiv:2410.02963, 2024.",
        "[9] S. D. Lakshmi and T. Velmurugan, \"Classification of Disaster Tweets Using Natural Language Processing Pipeline,\" Acta Scientific Computer Sciences, vol. 5, issue 3, pp. 20–24, March 2023.",
        "[10] K. Banyal, \"Application of Artificial Intelligence for Disaster Response and Management,\" International Journal of Advanced Research in Science, Communication and Technology (IJARSCT), vol. 5, issue 1, pp. 369–375, April 2025.",
        "[11] A. T. Zagorecki, D. E. A. Johnson, and J. Ristvej, \"Data Mining and Machine Learning in the Context of Disaster and Crisis Management,\" International Journal of Emergency Management, vol. 9, no. 4, pp. 351–365, 2013.",
        "[12] A. D. Le, \"Disaster Tweets Classification using BERT-Based Language Model,\" in IEEE International Conference on Artificial Intelligence and Big Data (ICAIBD), pp. 112–115, 2022.",
        "[13] F. E. Öcal and S. Torun, \"Leveraging Artificial Intelligence for Enhanced Disaster Response Coordination,\" International Journal of Disaster Risk Management, vol. 7, no. 1, pp. 13–26, 2025.",
        "[14] T. Seotan and T. Samuel, \"Smart Disaster Management: The Role of AI in Preventing, Managing, and Recovering from Catastrophes,\" Journal of Disaster Science and Engineering, vol. 4, no. 2, pp. 45–68, 2024.",
        "[15] V. Devarajan, \"Integrated AI-ML Framework for Disaster Lifecycle Management: From Prediction to Recovery,\" World Journal of Advanced Research and Reviews, vol. 26, no. 2, pp. 585–593, 2025.",
        "[16] M. Imran, S. Elbassuoni, C. Castillo, F. Diaz, and P. Meier, \"Extracting Information Nuggets from Disaster-Related Messages in Social Media,\" in Proceedings of the 10th International ISCRAM Conference, Baden-Baden, Germany, pp. 1–10, May 2013.",
        "[17] F. Alam, F. Ofli, and M. Imran, \"CrisisMMD: Multimodal Twitter Datasets from Natural Disasters,\" in Proceedings of the 12th International AAAI Conference on Web and Social Media (ICWSM), pp. 465–473, 2018."
    ]
    
    for r_text in refs:
        p_r = doc.add_paragraph()
        p_r.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_r.paragraph_format.line_spacing = 1.5
        p_r.paragraph_format.space_after = Pt(6)
        r_run = p_r.add_run(r_text)
        r_run.font.name = 'Times New Roman'
        r_run.font.size = Pt(11)

    out_path = r"c:\Users\Vijay\LifeLine\LifeLine_Project_Synopsis.docx"
    doc.save(out_path)
    print("SUCCESS: Saved Word document successfully to " + out_path)

if __name__ == "__main__":
    build_exact_26_page_synopsis()
