import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os

os.makedirs('figures', exist_ok=True)

# -------------------------------------------------------------
# FIGURE 1: System Architecture Diagram
# -------------------------------------------------------------
def create_fig1_architecture():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Title
    ax.text(50, 96, "Figure 1: High-Level System Architecture of LifeLine Platform", 
            ha='center', va='center', fontsize=13, fontweight='bold', family='sans-serif', color='#1A365D')
    
    # Layer 1: Presentation Tier (Portals)
    rect_citizen = patches.FancyBboxPatch((4, 66), 42, 24, boxstyle="round,pad=1.5", 
                                          fc='#EBF8FF', ec='#3182CE', lw=2)
    ax.add_patch(rect_citizen)
    ax.text(25, 86, "Citizen Disaster Portal (Port 8000)", ha='center', va='center', 
            fontsize=10, fontweight='bold', color='#2B6CB0')
    ax.text(25, 78, "• Mobile PWA & Responsive UI (HTML5/Tailwind)\n• Live Media Recording (Camera/Audio)\n• Geolocation (HTML5 GNSS Sensor)\n• Offline Cache & Sync (Service Worker + IndexedDB)\n• Real-Time Rescue Vehicle Tracker (Leaflet GIS)", 
            ha='center', va='center', fontsize=7.5, color='#2D3748')

    rect_admin = patches.FancyBboxPatch((54, 66), 42, 24, boxstyle="round,pad=1.5", 
                                        fc='#FEFCBF', ec='#D69E2E', lw=2)
    ax.add_patch(rect_admin)
    ax.text(75, 86, "Authority Command Center (Port 8001)", ha='center', va='center', 
            fontsize=10, fontweight='bold', color='#B7791F')
    ax.text(75, 78, "• Live Incident Dashboard (Severity Sorting L1-L5)\n• Interactive Leaflet GIS Spatial Heatmap\n• Automated MILP Dispatch Trigger Button\n• Manual Resource & Vehicle Dropdown Override\n• Multi-Agency Hospital & Shelter Live Telemetry", 
            ha='center', va='center', fontsize=7.5, color='#2D3748')

    # Layer 2: API Gateway & Event Synchronization
    rect_bridge = patches.FancyBboxPatch((20, 48), 60, 12, boxstyle="round,pad=1.2", 
                                         fc='#EDF2F7', ec='#4A5568', lw=1.8, ls='--')
    ax.add_patch(rect_bridge)
    ax.text(50, 56, "REST API Gateway & Cross-Server WebSocket Event Bridge", ha='center', va='center', 
            fontsize=9.5, fontweight='bold', color='#2D3748')
    ax.text(50, 51, "Express.js Routing | Real-Time WebSocket Telemetry Broadcast | Cross-Origin Sync", 
            ha='center', va='center', fontsize=7.5, color='#4A5568')

    # Layer 3: Core Analytics & Optimization Engine
    rect_ai = patches.FancyBboxPatch((4, 18), 42, 24, boxstyle="round,pad=1.5", 
                                      fc='#F0FFF4', ec='#38A169', lw=2)
    ax.add_patch(rect_ai)
    ax.text(25, 38, "Python AI & MILP Service (Port 5000)", ha='center', va='center', 
            fontsize=10, fontweight='bold', color='#276749')
    ax.text(25, 29, "• NLP Triage Model (TF-IDF + Logistic Regression)\n• PyTorch MobileNetV3 Authenticity Verification\n• PyTorch MobileNetV3 Visual Damage Scorer\n• Multi-Modal Composite Severity Index (MCSI)\n• SciPy Mixed-Integer Linear Program (MILP) Solver", 
            ha='center', va='center', fontsize=7.5, color='#2D3748')

    # Layer 4: Data Persistence Tier
    rect_db = patches.FancyBboxPatch((54, 18), 42, 24, boxstyle="round,pad=1.5", 
                                     fc='#FAF5FF', ec='#805AD5', lw=2)
    ax.add_patch(rect_db)
    ax.text(75, 38, "Persistence Tier (SQLite WAL Engine)", ha='center', va='center', 
            fontsize=10, fontweight='bold', color='#6B46C1')
    ax.text(75, 29, "• Write-Ahead Logging (WAL) Mode (`lifeline_enterprise.db`)\n• High-Throughput Concurrency (Shared Memory .db-shm)\n• Incidents, Units, Shelters & Dispatches Schema\n• File System Media Storage (`/uploads`)\n• Sub-millisecond Transaction Locks", 
            ha='center', va='center', fontsize=7.5, color='#2D3748')

    # Connective Arrows
    ax.annotate('', xy=(25, 60), xytext=(25, 66), arrowprops=dict(arrowstyle='<->', color='#3182CE', lw=1.5))
    ax.annotate('', xy=(75, 60), xytext=(75, 66), arrowprops=dict(arrowstyle='<->', color='#D69E2E', lw=1.5))
    ax.annotate('', xy=(25, 42), xytext=(25, 48), arrowprops=dict(arrowstyle='<->', color='#38A169', lw=1.5))
    ax.annotate('', xy=(75, 42), xytext=(75, 48), arrowprops=dict(arrowstyle='<->', color='#805AD5', lw=1.5))
    ax.annotate('', xy=(46, 30), xytext=(54, 30), arrowprops=dict(arrowstyle='<->', color='#4A5568', lw=1.5))
    
    plt.tight_layout()
    plt.savefig('figures/fig1_system_architecture.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created fig1_system_architecture.png")

# -------------------------------------------------------------
# FIGURE 2: DFD Level 0 (Context Diagram)
# -------------------------------------------------------------
def create_fig2_dfd_level0():
    fig, ax = plt.subplots(figsize=(9.5, 5.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    ax.text(50, 95, "Figure 2: Data Flow Diagram (DFD Level 0 - Context Diagram)", 
            ha='center', va='center', fontsize=12, fontweight='bold', color='#1A365D')
    
    # Central Process Circle
    circle_center = patches.Circle((50, 50), 16, fc='#EBF8FF', ec='#2B6CB0', lw=2.5)
    ax.add_patch(circle_center)
    ax.text(50, 53, "0.0\nLifeLine Disaster\nResponse System", ha='center', va='center', 
            fontsize=9.5, fontweight='bold', color='#1A365D')
    ax.text(50, 41, "(Dual Web + AI + MILP)", ha='center', va='center', 
            fontsize=7.5, color='#4A5568')

    # Entities (Squares)
    # Citizen
    rect_c = patches.Rectangle((4, 60), 22, 16, fc='#EDF2F7', ec='#4A5568', lw=1.8)
    ax.add_patch(rect_c)
    ax.text(15, 68, "Citizen / Victim\n(Public User)", ha='center', va='center', fontsize=8.5, fontweight='bold')

    # Commander
    rect_cmd = patches.Rectangle((74, 60), 22, 16, fc='#EDF2F7', ec='#4A5568', lw=1.8)
    ax.add_patch(rect_cmd)
    ax.text(85, 68, "Emergency Commander\n(Authority)", ha='center', va='center', fontsize=8.5, fontweight='bold')

    # First Responders
    rect_res = patches.Rectangle((4, 20), 22, 16, fc='#EDF2F7', ec='#4A5568', lw=1.8)
    ax.add_patch(rect_res)
    ax.text(15, 28, "First Responders\n(Ambulance/Rescue)", ha='center', va='center', fontsize=8.5, fontweight='bold')

    # Hospitals / Shelters
    rect_hosp = patches.Rectangle((74, 20), 22, 16, fc='#EDF2F7', ec='#4A5568', lw=1.8)
    ax.add_patch(rect_hosp)
    ax.text(85, 28, "Hospitals & Shelters\n(Care Facilities)", ha='center', va='center', fontsize=8.5, fontweight='bold')

    # Data Flow Arrows & Labels
    # Citizen -> System
    ax.annotate('', xy=(34, 56), xytext=(26, 64), arrowprops=dict(arrowstyle='->', color='#2B6CB0', lw=1.5))
    ax.text(26, 61, "Distress Alert\n(Text, Photo, GPS)", fontsize=7, color='#2B6CB0', ha='right')

    # System -> Citizen
    ax.annotate('', xy=(26, 70), xytext=(36, 62), arrowprops=dict(arrowstyle='->', color='#2B6CB0', lw=1.5))
    ax.text(31, 71, "Live Tracking Status\n& ETA Updates", fontsize=7, color='#2B6CB0', ha='left')

    # System -> Commander
    ax.annotate('', xy=(74, 70), xytext=(64, 62), arrowprops=dict(arrowstyle='->', color='#D69E2E', lw=1.5))
    ax.text(68, 71, "Verified Severity Map\n& Triage Alerts (L1-L5)", fontsize=7, color='#B7791F', ha='right')

    # Commander -> System
    ax.annotate('', xy=(66, 56), xytext=(74, 64), arrowprops=dict(arrowstyle='->', color='#D69E2E', lw=1.5))
    ax.text(73, 58, "MILP Run / Manual\nResource Override", fontsize=7, color='#B7791F', ha='left')

    # System -> Responders
    ax.annotate('', xy=(26, 30), xytext=(36, 42), arrowprops=dict(arrowstyle='->', color='#38A169', lw=1.5))
    ax.text(28, 38, "Automated Dispatch Orders\n& Waypoint Navigation", fontsize=7, color='#276749', ha='right')

    # System <-> Hospitals
    ax.annotate('', xy=(64, 42), xytext=(74, 30), arrowprops=dict(arrowstyle='<->', color='#805AD5', lw=1.5))
    ax.text(72, 38, "Bed Availability &\nCasualty Inflow Alert", fontsize=7, color='#6B46C1', ha='left')

    plt.tight_layout()
    plt.savefig('figures/fig2_dfd_level0.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created fig2_dfd_level0.png")

# -------------------------------------------------------------
# FIGURE 3: DFD Level 1 (Process Decomposition)
# -------------------------------------------------------------
def create_fig3_dfd_level1():
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    ax.text(50, 96, "Figure 3: Data Flow Diagram (DFD Level 1 - Detailed Functional Pipeline)", 
            ha='center', va='center', fontsize=12, fontweight='bold', color='#1A365D')
    
    processes = [
        (10, 68, "1.0\nIntake &\nValidation", '#EBF8FF', '#3182CE'),
        (35, 68, "2.0\nMulti-Modal\nAI Triage", '#F0FFF4', '#38A169'),
        (65, 68, "3.0\nComposite\nScoring (MCSI)", '#FEFCBF', '#D69E2E'),
        (65, 24, "4.0\nSciPy MILP\nOptimization", '#FAF5FF', '#805AD5'),
        (25, 24, "5.0\nGIS Mapping &\nLive Tracking", '#EDF2F7', '#4A5568'),
    ]
    
    for px, py, text, fc, ec in processes:
        rect = patches.FancyBboxPatch((px, py), 18, 16, boxstyle="round,pad=1", fc=fc, ec=ec, lw=1.8)
        ax.add_patch(rect)
        ax.text(px+9, py+8, text, ha='center', va='center', fontsize=8.5, fontweight='bold')
    
    # Data Store D1: SQLite Database
    rect_ds = patches.Rectangle((40, 46), 20, 10, fc='#FFF5F5', ec='#E53E3E', lw=1.8)
    ax.add_patch(rect_ds)
    ax.text(50, 51, "D1: SQLite WAL DB\n(Incidents, Units, Dispatches)", ha='center', va='center', 
            fontsize=7.5, fontweight='bold', color='#C53030')

    # Flow lines
    # 1.0 -> 2.0
    ax.annotate('', xy=(35, 76), xytext=(28, 76), arrowprops=dict(arrowstyle='->', color='#4A5568', lw=1.5))
    ax.text(31.5, 78, "Cleaned Payload", fontsize=6.5, ha='center')
    
    # 2.0 -> 3.0
    ax.annotate('', xy=(65, 76), xytext=(53, 76), arrowprops=dict(arrowstyle='->', color='#4A5568', lw=1.5))
    ax.text(59, 78, "NLP & Vision Vectors", fontsize=6.5, ha='center')

    # 3.0 -> D1
    ax.annotate('', xy=(50, 56), xytext=(65, 68), arrowprops=dict(arrowstyle='->', color='#4A5568', lw=1.5))
    ax.text(61, 60, "Write Incident (L1-L5)", fontsize=6.5, ha='center')

    # D1 -> 4.0
    ax.annotate('', xy=(67, 40), xytext=(58, 46), arrowprops=dict(arrowstyle='->', color='#4A5568', lw=1.5))
    ax.text(66, 44, "Active Incidents & Units", fontsize=6.5, ha='center')

    # 4.0 -> D1
    ax.annotate('', xy=(54, 46), xytext=(65, 36), arrowprops=dict(arrowstyle='->', color='#805AD5', lw=1.5))
    ax.text(54, 38, "Write Dispatches", fontsize=6.5, ha='center')

    # 4.0 -> 5.0
    ax.annotate('', xy=(43, 32), xytext=(65, 32), arrowprops=dict(arrowstyle='->', color='#4A5568', lw=1.5))
    ax.text(54, 34, "Optimal Assignment Vectors", fontsize=6.5, ha='center')

    # 5.0 -> External User
    ax.text(12, 32, "Citizen GPS &\nCommander Map", fontsize=7.5, fontweight='bold', color='#2B6CB0', ha='center')
    ax.annotate('', xy=(18, 32), xytext=(25, 32), arrowprops=dict(arrowstyle='<-', color='#2B6CB0', lw=1.5))

    plt.tight_layout()
    plt.savefig('figures/fig3_dfd_level1.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created fig3_dfd_level1.png")

# -------------------------------------------------------------
# FIGURE 4: AI Pipeline Flowchart
# -------------------------------------------------------------
def create_fig4_ai_pipeline():
    fig, ax = plt.subplots(figsize=(9, 6.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    ax.text(50, 96, "Figure 4: Multi-Modal AI & Computer Vision Triage Pipeline", 
            ha='center', va='center', fontsize=12, fontweight='bold', color='#1A365D')
    
    # Input
    rect_in = patches.FancyBboxPatch((30, 84), 40, 8, boxstyle="round,pad=0.8", fc='#EDF2F7', ec='#4A5568', lw=1.5)
    ax.add_patch(rect_in)
    ax.text(50, 88, "Emergency Report (Text + Photo/Video + GPS)", ha='center', va='center', fontsize=8.5, fontweight='bold')

    # Split into NLP and Vision
    # Left Branch: NLP
    rect_nlp = patches.FancyBboxPatch((6, 56), 40, 20, boxstyle="round,pad=1", fc='#EBF8FF', ec='#3182CE', lw=1.8)
    ax.add_patch(rect_nlp)
    ax.text(26, 71, "NLP Text Triage Branch", ha='center', va='center', fontsize=9, fontweight='bold', color='#2B6CB0')
    ax.text(26, 62, "1. Tokenization & Clean N-Grams\n2. TF-IDF Feature Vectorizer\n3. Logistic Regression Classifier\nOutput: 8 Disaster Classes + S_NLP (0-1)", 
            ha='center', va='center', fontsize=7.5, color='#2D3748')

    # Right Branch: Vision
    rect_vis = patches.FancyBboxPatch((54, 56), 40, 20, boxstyle="round,pad=1", fc='#F0FFF4', ec='#38A169', lw=1.8)
    ax.add_patch(rect_vis)
    ax.text(74, 71, "PyTorch Vision Branch", ha='center', va='center', fontsize=9, fontweight='bold', color='#276749')
    ax.text(74, 62, "1. Resize & Normalize Image (224x224)\n2. MobileNetV3 Authenticity Filter\n3. MobileNetV3 Damage Classification\nOutput: S_Vision (0-1: None/Mild/Severe)", 
            ha='center', va='center', fontsize=7.5, color='#2D3748')

    # Merge into MCSI Formula
    rect_mcsi = patches.FancyBboxPatch((20, 26), 60, 18, boxstyle="round,pad=1.2", fc='#FEFCBF', ec='#D69E2E', lw=2)
    ax.add_patch(rect_mcsi)
    ax.text(50, 39, "Multi-Modal Composite Severity Index (MCSI)", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#B7791F')
    ax.text(50, 31, r"$MCSI = 0.45 \cdot S_{NLP} + 0.40 \cdot S_{Vision} + 0.15 \cdot N_{Corroboration}$" + "\nDynamic Normalization to Priority Scale [1 to 5]", 
            ha='center', va='center', fontsize=8, color='#744210')

    # Final Output Box
    rect_out = patches.FancyBboxPatch((28, 4), 44, 12, boxstyle="round,pad=0.8", fc='#FAF5FF', ec='#805AD5', lw=1.8)
    ax.add_patch(rect_out)
    ax.text(50, 10, "Priority Dispatch Classification\nLevel 1 (Low) → Level 5 (Critical Mass-Casualty)", 
            ha='center', va='center', fontsize=8.5, fontweight='bold', color='#6B46C1')

    # Connecting arrows
    ax.annotate('', xy=(26, 76), xytext=(40, 84), arrowprops=dict(arrowstyle='->', color='#3182CE', lw=1.5))
    ax.annotate('', xy=(74, 76), xytext=(60, 84), arrowprops=dict(arrowstyle='->', color='#38A169', lw=1.5))
    ax.annotate('', xy=(38, 44), xytext=(26, 56), arrowprops=dict(arrowstyle='->', color='#3182CE', lw=1.5))
    ax.annotate('', xy=(62, 44), xytext=(74, 56), arrowprops=dict(arrowstyle='->', color='#38A169', lw=1.5))
    ax.annotate('', xy=(50, 16), xytext=(50, 26), arrowprops=dict(arrowstyle='->', color='#D69E2E', lw=1.8))

    plt.tight_layout()
    plt.savefig('figures/fig4_ai_pipeline_flowchart.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created fig4_ai_pipeline_flowchart.png")

# -------------------------------------------------------------
# FIGURE 5: SciPy MILP Resource Allocation Flowchart
# -------------------------------------------------------------
def create_fig5_milp_flowchart():
    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    ax.text(50, 96, "Figure 5: SciPy Mixed-Integer Linear Programming (MILP) Dispatch Solver Flowchart", 
            ha='center', va='center', fontsize=11.5, fontweight='bold', color='#1A365D')
    
    steps = [
        (25, 80, 50, 10, "1. Query Active Unassigned Incidents Sorted by Severity (L5 → L1)", '#EDF2F7', '#4A5568'),
        (25, 64, 50, 10, "2. Query Available Rescue Fleet & Hospital Capacities in Range", '#EBF8FF', '#3182CE'),
        (20, 48, 60, 10, "3. Construct Haversine Distance & Response Time Cost Matrix C_ij", '#F0FFF4', '#38A169'),
        (15, 28, 70, 14, "4. Formulate Optimization Objective: Minimize Total Response Cost\nSubject to: Unit Capacity, One Unit per Critical Incident, Hospital Bed Bounds", '#FEFCBF', '#D69E2E'),
        (20, 8, 60, 12, "5. Execute SciPy milp(c, integrality=1, constraints=A_ub)\nDispatch Response Vehicles & Stream Live GPS Trajectory to Victims", '#FAF5FF', '#805AD5'),
    ]
    
    for px, py, w, h, txt, fc, ec in steps:
        rect = patches.FancyBboxPatch((px, py), w, h, boxstyle="round,pad=1", fc=fc, ec=ec, lw=1.6)
        ax.add_patch(rect)
        ax.text(50, py+h/2, txt, ha='center', va='center', fontsize=7.8, fontweight='bold', color='#2D3748')

    for y_start, y_end in [(80, 74), (64, 58), (48, 42), (28, 20)]:
        ax.annotate('', xy=(50, y_end), xytext=(50, y_start), arrowprops=dict(arrowstyle='->', color='#2B6CB0', lw=1.8))

    plt.tight_layout()
    plt.savefig('figures/fig5_milp_flowchart.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created fig5_milp_flowchart.png")

# -------------------------------------------------------------
# FIGURE 6: PWA Offline Queue & Sync Flowchart
# -------------------------------------------------------------
def create_fig6_pwa_offline():
    fig, ax = plt.subplots(figsize=(9.5, 6), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    ax.text(50, 96, "Figure 6: Progressive Web App (PWA) Offline Queueing & Background Synchronization Flowchart", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#1A365D')

    # Step 1: User SOS Submission
    rect_start = patches.FancyBboxPatch((30, 82), 40, 8, boxstyle="round,pad=0.8", fc='#EDF2F7', ec='#4A5568', lw=1.5)
    ax.add_patch(rect_start)
    ax.text(50, 86, "Citizen Submits SOS with Media & GPS", ha='center', va='center', fontsize=8, fontweight='bold')

    # Step 2: Decision Diamond
    diamond = patches.Polygon([[50, 76], [68, 66], [50, 56], [32, 66]], fc='#FEFCBF', ec='#D69E2E', lw=1.8)
    ax.add_patch(diamond)
    ax.text(50, 66, "Internet Active?\n(navigator.onLine)", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#744210')

    # Yes Branch: Online HTTP POST
    rect_on = patches.FancyBboxPatch((72, 42), 24, 14, boxstyle="round,pad=1", fc='#F0FFF4', ec='#38A169', lw=1.8)
    ax.add_patch(rect_on)
    ax.text(84, 49, "Direct HTTP POST\nto Port 8000 API\n(Real-Time Ingestion)", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#276749')

    # No Branch: Offline IndexedDB
    rect_off = patches.FancyBboxPatch((4, 42), 28, 14, boxstyle="round,pad=1", fc='#FFF5F5', ec='#E53E3E', lw=1.8)
    ax.add_patch(rect_off)
    ax.text(18, 49, "Service Worker Intercepts\nStore Blob into IndexedDB\n'pending_sos' Object Store", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#9B2C2C')

    # Wait for Online Event
    rect_wait = patches.FancyBboxPatch((4, 16), 28, 14, boxstyle="round,pad=1", fc='#FAF5FF', ec='#805AD5', lw=1.8)
    ax.add_patch(rect_wait)
    ax.text(18, 23, "Window listens for\n'online' network event\n& PWA Background Sync", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#6B46C1')

    # Flush Queue & Sync
    rect_sync = patches.FancyBboxPatch((46, 16), 34, 14, boxstyle="round,pad=1", fc='#EBF8FF', ec='#3182CE', lw=1.8)
    ax.add_patch(rect_sync)
    ax.text(63, 23, "Read & Dequeue IndexedDB Records\nMultipart POST to `/api/report`\nClear Local Queue & Confirm SOS", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#2B6CB0')

    # Connectors
    ax.annotate('', xy=(50, 76), xytext=(50, 82), arrowprops=dict(arrowstyle='->', color='#4A5568', lw=1.5))
    ax.annotate('Yes', xy=(72, 52), xytext=(68, 66), arrowprops=dict(arrowstyle='->', color='#38A169', lw=1.5), fontsize=8, fontweight='bold', color='#38A169')
    ax.annotate('No', xy=(18, 56), xytext=(32, 66), arrowprops=dict(arrowstyle='->', color='#E53E3E', lw=1.5), fontsize=8, fontweight='bold', color='#E53E3E')
    ax.annotate('', xy=(18, 30), xytext=(18, 42), arrowprops=dict(arrowstyle='->', color='#9B2C2C', lw=1.5))
    ax.annotate('', xy=(46, 23), xytext=(32, 23), arrowprops=dict(arrowstyle='->', color='#805AD5', lw=1.5))
    ax.annotate('', xy=(84, 30), xytext=(84, 42), arrowprops=dict(arrowstyle='->', color='#38A169', lw=1.5))
    ax.annotate('', xy=(80, 23), xytext=(84, 23), arrowprops=dict(arrowstyle='->', color='#38A169', lw=1.5))

    plt.tight_layout()
    plt.savefig('figures/fig6_pwa_offline.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created fig6_pwa_offline.png")

# -------------------------------------------------------------
# FIGURE 7: 17-Week Gantt Chart
# -------------------------------------------------------------
def create_fig7_gantt():
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    
    phases = [
        "Phase 8: Integration & Final Evaluation",
        "Phase 7: PWA Offline Sync & GIS Routing",
        "Phase 6: Dual Frontend Portals (8000/8001)",
        "Phase 5: Node.js WAL Backend & Event Bridge",
        "Phase 4: SciPy MILP Dispatch Engine",
        "Phase 3: NLP & PyTorch Vision Training",
        "Phase 2: Dataset Acquisition & Cleaning",
        "Phase 1: Literature Review & Problem Definition"
    ]
    
    starts = [15, 13, 11, 9, 7, 4, 2, 0]
    durations = [2, 2, 2, 2, 2, 3, 2, 2]
    colors = ['#805AD5', '#3182CE', '#38A169', '#D69E2E', '#E53E3E', '#DD6B20', '#319795', '#4A5568']
    
    y_pos = np.arange(len(phases))
    
    bars = ax.barh(y_pos, durations, left=starts, height=0.55, align='center', color=colors, edgecolor='#2D3748', lw=1)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(phases, fontsize=8.5, fontweight='bold', color='#1A202C')
    ax.set_xlabel("Project Timeline (Weeks 1 to 17)", fontsize=9.5, fontweight='bold', color='#1A365D')
    ax.set_xlim(0, 18)
    ax.set_xticks(range(0, 19, 2))
    ax.set_xticklabels([f"W{i}" if i>0 else "Start" for i in range(0, 19, 2)], fontsize=8)
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    
    for bar, start, dur in zip(bars, starts, durations):
        ax.text(start + dur/2, bar.get_y() + bar.get_height()/2, f"W{start+1}-W{start+dur}", 
                ha='center', va='center', color='white', fontsize=7.5, fontweight='bold')
        
    ax.set_title("Figure 7: 17-Week Project Execution Timeline & Milestone Gantt Chart", 
                 fontsize=11.5, fontweight='bold', color='#1A365D', pad=12)
    
    plt.tight_layout()
    plt.savefig('figures/fig7_gantt_chart.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created fig7_gantt_chart.png")

if __name__ == '__main__':
    create_fig1_architecture()
    create_fig2_dfd_level0()
    create_fig3_dfd_level1()
    create_fig4_ai_pipeline()
    create_fig5_milp_flowchart()
    create_fig6_pwa_offline()
    create_fig7_gantt()
