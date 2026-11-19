# AgriSense AI: Precision Agricultural Decision Support System
### Academic Capstone Project Presentation & System Documentation

![Frontend](https://img.shields.io/badge/Frontend-Streamlit%20Pure%20Python-2D5A27)
![Database](https://img.shields.io/badge/Database-MySQL%208.0-8FBC8F)
![AI Engine](https://img.shields.io/badge/AI%20Engine-Groq%20LLaMA--3.3--70b--versatile-F59E0B)
![Styling](https://img.shields.io/badge/UI%20Theme-Forest%20Green%20%26%20Cream-2D5A27)

---

## 1. Executive Abstract & System Overview

**AgriSense AI** is a full-stack, cloud-ready **Precision Agriculture Decision Support System (DSS)**. It bridges the gap between IoT root-zone telemetry, microclimate evapotranspiration physics, double-entry crop accounting, and state-of-the-art Generative AI. 

The platform integrates:
- **Continuous IoT Telemetry Ingestion**: Monitors volumetric soil water content ($\% \text{ VWC}$), root-zone temperature, ambient temperature, relative humidity, solar irradiance ($\text{W/m}^2$), and FAO-56 Penman-Monteith reference evapotranspiration ($\text{ET}_0$).
- **Autonomous Irrigation Control**: Closed-loop pump automation comparing real-time moisture against custom agronomic thresholds (`target_moisture_min` and `target_moisture_max`).
- **High-Speed Diagnostic Inference**: Powered by the **Groq LPU Inference Engine** running **LLaMA-3.3-70b-versatile**, providing zero-latency clinical plant pathology diagnoses, disease treatment protocols, and smart irrigation schedules.
- **Agricultural Economics & Yield Simulation**: Tracks operational production inputs (fertilizers, biopesticides, tillage, irrigation electricity, labor) and models harvest yield scenarios to calculate net profit margins and return on investment (ROI).

---

## 2. System Architecture

```
                    +------------------------------------------+
                    |           IoT Field Sensor Nodes         |
                    | (Moisture, Temp, Humidity, Solar, ET0)   |
                    +--------------------+---------------------+
                                         |
                                         v HTTP / JSON API
                    +------------------------------------------+
                    |             Flask REST API               |
                    |   (Blueprints: /api and Page Views)      |
                    +--------------------+---------------------+
                                         |
                 +-----------------------+-----------------------+
                 |                                               |
                 v                                               v
+---------------------------------+             +----------------------------------+
|      SQLAlchemy 2.0 ORM         |             |      Groq Cloud LPU Service      |
|  (Connection Pool & Models)     |             |    (LLaMA-3.3-70b-versatile)     |
+----------------+----------------+             +----------------+-----------------+
                 |                                               |
                 v                                               v
+---------------------------------+             +----------------------------------+
|        MySQL 8.0 Database       |             |   Clinical Agronomic Diagnosis   |
| (6 Relational Normalized Tables)|             |   Action Items & Prescription    |
+---------------------------------+             +----------------------------------+
                 |                                               |
                 +-----------------------+-----------------------+
                                         |
                                         v
                    +------------------------------------------+
                    |        Tailwind CSS + Jinja2 UI          |
                    |    (Forest Green & Soft Cream Theme)     |
                    +------------------------------------------+
```

---

## 3. Tech Stack & Engineering Rationale

| Layer | Technology | Architectural Rationale for University Presentation |
| :--- | :--- | :--- |
| **Backend** | Python 3.10+ / **Flask 3.x** | Clean, explicit separation of concerns, lightweight footprint, and intuitive code structure that is straightforward to explain during code defense. |
| **ORM** | **Flask-SQLAlchemy 3.x** | Object-Relational Mapping providing type safety, relationships with cascade rules, and seamless database migrations. |
| **Database** | **MySQL 8.0+** | Relational ACID compliance, indexing on timeseries (`plot_id`, `recorded_at`), foreign-key constraints, and JSON column support. |
| **AI Engine** | **Groq API (`llama-3.3-70b-versatile`)** | Industry-leading inference speed via Language Processing Units (LPUs). Provides deep scientific reasoning for pathology and agronomy at near-zero latency. |
| **Frontend** | **Tailwind CSS & Vanilla JS** | Zero heavy build toolchains; pure semantic HTML5/Jinja2 templates with high-performance responsive UI. |
| **Visuals** | **Chart.js 4.x** | Dynamic, interactive multi-axis environmental charts for root-zone moisture depletion curves and diurnal microclimates. |
| **Palette** | **Green & Cream** | Professional, accessible agricultural palette: Forest Green (`#2D5A27`), Sage Green (`#8FBC8F`), Soft Cream (`#FDFBF7`), and Deep Earth (`#1C2819`). |

---

## 4. Database Schema Design

The relational database is normalized into 6 core tables:

1. **`plots`**: Field zones, acreage, crop cultivars, growth stages, moisture thresholds, and pump statuses.
2. **`soil_tests`**: Laboratory chemical baselines ($\text{pH}$, available $\text{N-P-K}$ in ppm, organic matter $\%$, electrical conductivity $\text{EC}$ in $\text{dS/m}$).
3. **`telemetry_readings`**: High-frequency IoT root-zone and microclimate telemetry ($\text{VWC } \%$, soil/air temp, humidity, solar radiation, Penman-Monteith $\text{ET}_0$).
4. **`field_activities`**: Operations log (fertilizers, pesticides, irrigation, labor, pruning, tillage) with input quantities, units, and costs.
5. **`financial_records`**: Double-entry ledger tracking production expenses by category vs. crop sales and harvest revenue projections.
6. **`ai_consultations`**: Historical Groq LLaMA-3.3-70b diagnostic interactions, queries, responses, and parsed action items.

---

## 5. Quick Start & Installation Guide

### Prerequisites
- Python 3.10 or higher
- MySQL Server 8.0+ (running locally or via XAMPP / Docker / Cloud MySQL)

### Step 1: Clone or Open Project Directory
```bash
cd c:\Users\muham\OneDrive\Desktop\project
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Setup MySQL Database & Seed Data
Log into your MySQL client (Terminal, MySQL Workbench, or phpMyAdmin) and run:
```bash
# Execute schema setup
mysql -u root -p < schema.sql

# Populate with realistic agronomic sample data
mysql -u root -p < seed_data.sql
```

*Note: If your MySQL user has no password (common in local XAMPP), simply run:*
```bash
mysql -u root < schema.sql
mysql -u root < seed_data.sql
```

### Step 4: Configure Environment Variables
Open the `.env` file in the project root:
```ini
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=smart-agri-secret-academic-presentation-2026

# MySQL Database Configuration
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
DB_NAME=smart_agriculture
DATABASE_URL=mysql+pymysql://root:@localhost:3306/smart_agriculture

# Groq Cloud API Key (Get a free key at https://console.groq.com/keys)
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

*(Note: If you do not have a Groq key during your presentation, the built-in Academic Fallback Engine will automatically step in with zero crashes).*

### Step 5: Launch the Streamlit Web Application
```bash
streamlit run streamlit_app.py
```
*(Or alternatively: `python -m streamlit run streamlit_app.py`)*

Open your web browser at:
👉 **`http://localhost:8501`**

*(Note: The legacy Flask backend is also preserved and can still be run via `python app.py` at `http://127.0.0.1:5000` if needed).*

---

## 6. Step-by-Step Professor Presentation Script

Follow this structured 5-step walkthrough to give an impressive academic project defense:

### Step 1: The Telemetry Dashboard (`/`)
- **What to show**: The top KPI summary cards (Total Managed Farmland, Average Soil Moisture, Active Irrigation Pumps, Reference $\text{ET}_0$).
- **What to explain**:
  > *"Professor, our system monitors root-zone volumetric water content in real-time alongside microclimate conditions. Notice Plot B (Tomatoes) is at 55.4% moisture in optimal condition, while Plot C (Corn) has dipped to 31.2%, triggering a critical depletion alert."*
- **Interactive Action**: Click **"View Timeseries"** or use the Zone dropdown. Show the 24-hour Chart.js trajectory demonstrating how soil moisture depletes during peak solar irradiance ($800\text{ W/m}^2$) and how the curve responds to the upper and lower threshold boundaries.

### Step 2: Autonomous Pump Matrix & Closed-Loop Control
- **What to show**: The color-coded field cards with pump buttons (`AUTO`, `ON`, `OFF`).
- **What to explain**:
  > *"Each field zone features closed-loop automation. When in AUTO mode, if telemetry detects moisture dropping below `target_moisture_min`, the controller commands irrigation. We can also override this manually."*
- **Interactive Action**: Click the **`ON`** button for Plot A. Point out the instant toast notification and explain that an irrigation activity record and utility expense entry were automatically committed to the database.

### Step 3: Field Operations & Input Logging (`/logs`)
- **What to show**: The filterable agricultural activity ledger.
- **What to explain**:
  > *"Traceability is crucial in modern agronomy. Every chemical formulation, fertilizer grade (such as Urea 46-0-0 or DAP), and biopesticide applied is recorded with application rates, operator names, and costs."*
- **Interactive Action**: Click **"Log Daily Farm Input"**, enter an application (e.g. 50 kg of NPK fertilizer), and submit. Show how it appears immediately in the table.

### Step 4: Groq AI Diagnostic Center (`/advisor`)
- **What to show**: The AI Agronomist interface powered by Groq LLaMA-3.3-70b.
- **What to explain**:
  > *"Instead of generic LLM advice, our system binds live field telemetry into the prompt context. The AI receives the crop variety, growth stage, ambient humidity, temperature, and Penman-Monteith $\text{ET}_0$."*
- **Interactive Action**:
  1. Click the preset chip: **"🍅 Tomato Early Blight"**.
  2. Click **"Run Diagnostic Analysis"**.
  3. Highlight the ultra-fast Groq LPU response time, the scientific pathogen breakdown (*Alternaria solani*), dosage guidelines (Mancozeb 2.5 g/L), and the interactive Action Checklist.

### Step 5: Yield & Financial Profit Calculator (`/financials`)
- **What to show**: The economic sensitivity simulator and cost-per-hectare breakdown.
- **What to explain**:
  > *"Precision farming must be economically viable. Here we compare production expenses across seeds, fertilizers, chemicals, water, and labor against projected harvest revenues."*
- **Interactive Action**: Adjust the **Market Price ($/kg)** or **Expected Yield** in the scenario calculator and show how the Gross Revenue, Net Profit, and ROI update in real-time.

---

## 7. Agronomic Theory & Mathematical Foundations

To impress your professor, be prepared to explain these foundational concepts:

### 1. FAO-56 Penman-Monteith Evapotranspiration ($\text{ET}_0$)
Reference evapotranspiration represents the rate of water loss from an idealized grass reference crop:
$$ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$
Where:
- $R_n$: Net radiation at the crop surface ($\text{MJ/m}^2\text{/day}$)
- $G$: Soil heat flux density ($\text{MJ/m}^2\text{/day}$)
- $T$: Mean daily air temperature at 2 m height ($^\circ\text{C}$)
- $u_2$: Wind speed at 2 m height ($\text{m/s}$)
- $e_s - e_a$: Saturation vapor pressure deficit ($\text{kPa}$)
- $\Delta$: Slope vapor pressure curve ($\text{kPa/}^\circ\text{C}$)
- $\gamma$: Psychrometric constant ($\text{kPa/}^\circ\text{C}$)

### 2. Management Allowable Depletion (MAD)
Irrigation is scheduled when the soil water content depletes to a fraction ($p$) of Total Available Water (TAW):
$$\text{RAW} = p \times \text{TAW} = p \times \frac{(\text{FC} - \text{WP}) \times Z_r}{100}$$
- $\text{FC}$: Field Capacity ($\%$)
- $\text{WP}$: Permanent Wilting Point ($\%$)
- $Z_r$: Effective root-zone depth ($\text{m}$)

---

## 8. Expected Professor Q&A Defense

#### Q1: "Why did you use Groq instead of standard OpenAI or local HuggingFace models?"
> **Answer**: *"Groq utilizes Language Processing Units (LPUs) that achieve deterministic throughput of hundreds of tokens per second. In an IoT decision-support environment, ultra-low latency allows the system to analyze incoming telemetry anomalies and deliver real-time agronomic prescriptions to field managers without UI lag."*

#### Q2: "How does the system mitigate LLM hallucinations in crop disease diagnosis?"
> **Answer**: *"We employ Strict Context Injection (RAG-adjacent pattern). We inject the specific plot parameters (crop cultivar, growth stage, soil moisture %, ambient temperature, and $\text{ET}_0$) directly into the system prompt. Furthermore, the model is strictly constrained to standard agronomic classifications and structured Markdown headers with dosage bounds."*

#### Q3: "How is telemetry persisted and queried efficiently in MySQL?"
> **Answer**: *"We established composite indexes on `(plot_id, recorded_at DESC)`. This enables $O(\log N)$ retrieval of the latest telemetry point for the dashboard map grid and fast range queries for timeseries charts."*

#### Q4: "How does the system connect field inputs with financial records?"
> **Answer**: *"When an operator logs an operation (such as applying fertilizer or running irrigation) in `field_activities`, the backend API automatically computes the monetary cost and logs a corresponding entry in `financial_records` within a single atomic database transaction."*

---

## 9. Academic Project Metadata
- **Project Title**: Smart Agriculture IoT & AI Decision Support System
- **Module**: Final Year / Academic Capstone Presentation
- **Authors**: Senior Full-Stack Development Pair
- **License**: Academic Educational License
