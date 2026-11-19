-- ==============================================================================
-- SMART AGRICULTURE IOT & AI DECISION SUPPORT SYSTEM
-- Realistic Farm Seed Data Script
-- Target: 3 Farm Plots, Lab Soil Tests, Telemetry Timeseries, Activities, Financials & AI History
-- ==============================================================================

USE smart_agriculture;

-- Clear previous data
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE ai_consultations;
TRUNCATE TABLE financial_records;
TRUNCATE TABLE field_activities;
TRUNCATE TABLE telemetry_readings;
TRUNCATE TABLE soil_tests;
TRUNCATE TABLE plots;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------------------------
-- 1. INSERT PLOTS
-- ------------------------------------------------------------------------------
INSERT INTO plots (id, name, crop_type, variety, area_hectares, soil_type, planting_date, expected_harvest_date, growth_stage, target_moisture_min, target_moisture_max, pump_status, last_irrigated_at)
VALUES
(
    1, 
    'Plot A - North Field', 
    'Winter Wheat', 
    'Faisalabad-08 / Triticum aestivum', 
    2.50, 
    'Sandy Loam', 
    DATE_SUB(CURRENT_DATE, INTERVAL 45 DAY), 
    DATE_ADD(CURRENT_DATE, INTERVAL 75 DAY), 
    'Vegetative', 
    35.00, 
    65.00, 
    'AUTO', 
    DATE_SUB(NOW(), INTERVAL 14 HOUR)
),
(
    2, 
    'Plot B - Greenhouse Zone 2', 
    'Roma Tomatoes', 
    'Determinate F1 Hybrid', 
    1.20, 
    'Clay Loam', 
    DATE_SUB(CURRENT_DATE, INTERVAL 60 DAY), 
    DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY), 
    'Flowering', 
    45.00, 
    75.00, 
    'ON', 
    DATE_SUB(NOW(), INTERVAL 2 HOUR)
),
(
    3, 
    'Plot C - Southern Terrace', 
    'Sweet Corn', 
    'Pioneer 30Y87 Hybrid (Maize)', 
    3.40, 
    'Silt Loam', 
    DATE_SUB(CURRENT_DATE, INTERVAL 80 DAY), 
    DATE_ADD(CURRENT_DATE, INTERVAL 25 DAY), 
    'Maturation', 
    30.00, 
    60.00, 
    'OFF', 
    DATE_SUB(NOW(), INTERVAL 36 HOUR)
);

-- ------------------------------------------------------------------------------
-- 2. INSERT SOIL TEST BASELINES (Distinct Agronomic Scenarios)
-- ------------------------------------------------------------------------------
INSERT INTO soil_tests (plot_id, test_date, ph_level, nitrogen_ppm, phosphorus_ppm, potassium_ppm, organic_matter_percent, electrical_conductivity, moisture_retention_capacity, lab_name, recommendations)
VALUES
(
    1,
    DATE_SUB(CURRENT_DATE, INTERVAL 50 DAY),
    6.80,
    32.00,
    18.00,
    195.00,
    1.80,
    0.85,
    38.00,
    'National Agricultural Research Center (NARC)',
    'Nitrogen-deficient sandy loam (N=32 ppm is below the 50-80 ppm target). Prone to nitrogen leaching. Apply top-dressing of Granular Urea (46% N) at 60 kg/ha in split applications prior to dawn irrigation.'
),
(
    2,
    DATE_SUB(CURRENT_DATE, INTERVAL 65 DAY),
    6.50,
    56.00,
    24.00,
    210.00,
    3.20,
    1.45,
    48.50,
    'Agri-Tech Soil Analytics Lab',
    'Elevated greenhouse salinity alert (EC=1.45 dS/m exceeds 1.30 dS/m threshold). Potassium is also elevated (210 ppm). Execute fresh water leaching fraction (15% excess) to flush root-zone salts and pause fertilizer salts.'
),
(
    3,
    DATE_SUB(CURRENT_DATE, INTERVAL 85 DAY),
    7.20,
    48.00,
    11.00,
    185.00,
    2.40,
    1.05,
    34.00,
    'Valley Soil Testing Services',
    'Phosphorus-deficient silt loam (P=11 ppm is below the 15-25 ppm target). At pH 7.2, phosphorus fixation occurs. Apply banded Di-Ammonium Phosphate (DAP 18-46-0) at 75 kg/ha targeted near the root zone.'
);

-- ------------------------------------------------------------------------------
-- 3. INSERT REALISTIC TELEMETRY READINGS (Hourly timeseries for past 24 hours)
-- ------------------------------------------------------------------------------
-- Plot 1: Wheat Field (Dipping from 44% down to 36%, approaching min threshold)
INSERT INTO telemetry_readings (plot_id, recorded_at, soil_moisture, soil_temperature, ambient_temperature, humidity, solar_radiation, et0, battery_level, pump_event_triggered)
VALUES
(1, DATE_SUB(NOW(), INTERVAL 24 HOUR), 46.2, 18.2, 19.5, 68.0, 50.0, 1.20, 98.0, 0),
(1, DATE_SUB(NOW(), INTERVAL 21 HOUR), 45.4, 17.5, 18.0, 74.0, 0.0, 0.60, 98.0, 0),
(1, DATE_SUB(NOW(), INTERVAL 18 HOUR), 44.8, 16.8, 16.5, 80.0, 0.0, 0.40, 97.5, 0),
(1, DATE_SUB(NOW(), INTERVAL 15 HOUR), 44.1, 16.2, 17.2, 78.0, 180.0, 1.80, 97.0, 0),
(1, DATE_SUB(NOW(), INTERVAL 12 HOUR), 42.6, 19.4, 23.8, 55.0, 680.0, 4.10, 97.0, 0),
(1, DATE_SUB(NOW(), INTERVAL 9 HOUR),  40.8, 22.1, 27.4, 46.0, 840.0, 5.20, 96.5, 0),
(1, DATE_SUB(NOW(), INTERVAL 6 HOUR),  38.9, 23.0, 26.5, 48.0, 590.0, 4.30, 96.0, 0),
(1, DATE_SUB(NOW(), INTERVAL 3 HOUR),  37.4, 21.2, 23.1, 58.0, 220.0, 2.50, 95.5, 0),
(1, DATE_SUB(NOW(), INTERVAL 1 HOUR),  36.2, 19.8, 21.0, 64.0, 45.0, 1.10, 95.0, 0);

-- Plot 2: Greenhouse Tomatoes (High precision moisture control, maintained ~54-58%)
INSERT INTO telemetry_readings (plot_id, recorded_at, soil_moisture, soil_temperature, ambient_temperature, humidity, solar_radiation, et0, battery_level, pump_event_triggered)
VALUES
(2, DATE_SUB(NOW(), INTERVAL 24 HOUR), 52.0, 20.1, 22.0, 62.0, 80.0, 1.50, 99.0, 0),
(2, DATE_SUB(NOW(), INTERVAL 21 HOUR), 50.8, 19.5, 20.5, 68.0, 0.0, 0.80, 99.0, 0),
(2, DATE_SUB(NOW(), INTERVAL 18 HOUR), 49.5, 19.0, 19.8, 72.0, 0.0, 0.50, 98.5, 0),
(2, DATE_SUB(NOW(), INTERVAL 15 HOUR), 48.2, 18.8, 21.0, 70.0, 210.0, 2.00, 98.0, 0),
(2, DATE_SUB(NOW(), INTERVAL 12 HOUR), 46.5, 22.0, 25.5, 58.0, 710.0, 4.30, 98.0, 0),
(2, DATE_SUB(NOW(), INTERVAL 9 HOUR),  44.9, 24.2, 28.2, 52.0, 870.0, 5.50, 97.5, 1), -- Irrigation triggered here
(2, DATE_SUB(NOW(), INTERVAL 6 HOUR),  58.5, 22.8, 26.8, 59.0, 620.0, 4.20, 97.0, 0), -- Moisture replenished
(2, DATE_SUB(NOW(), INTERVAL 3 HOUR),  56.8, 21.5, 24.0, 65.0, 240.0, 2.30, 97.0, 0),
(2, DATE_SUB(NOW(), INTERVAL 1 HOUR),  55.4, 20.6, 22.4, 69.0, 50.0, 1.20, 96.5, 0);

-- Plot 3: Corn Field (Dry conditions, moisture dropped to 31.5% near critical limit)
INSERT INTO telemetry_readings (plot_id, recorded_at, soil_moisture, soil_temperature, ambient_temperature, humidity, solar_radiation, et0, battery_level, pump_event_triggered)
VALUES
(3, DATE_SUB(NOW(), INTERVAL 24 HOUR), 38.5, 21.0, 24.0, 52.0, 90.0, 1.80, 94.0, 0),
(3, DATE_SUB(NOW(), INTERVAL 21 HOUR), 37.8, 20.2, 22.1, 58.0, 0.0, 0.90, 94.0, 0),
(3, DATE_SUB(NOW(), INTERVAL 18 HOUR), 37.0, 19.5, 21.0, 62.0, 0.0, 0.60, 93.5, 0),
(3, DATE_SUB(NOW(), INTERVAL 15 HOUR), 36.1, 19.8, 23.5, 57.0, 260.0, 2.40, 93.0, 0),
(3, DATE_SUB(NOW(), INTERVAL 12 HOUR), 34.4, 23.5, 29.8, 41.0, 890.0, 5.80, 93.0, 0),
(3, DATE_SUB(NOW(), INTERVAL 9 HOUR),  32.8, 26.0, 33.2, 35.0, 950.0, 6.70, 92.5, 0),
(3, DATE_SUB(NOW(), INTERVAL 6 HOUR),  31.9, 25.4, 31.5, 38.0, 680.0, 5.10, 92.0, 0),
(3, DATE_SUB(NOW(), INTERVAL 3 HOUR),  31.5, 23.8, 27.2, 47.0, 290.0, 3.10, 91.5, 0),
(3, DATE_SUB(NOW(), INTERVAL 1 HOUR),  31.2, 22.1, 25.0, 53.0, 60.0, 1.50, 91.0, 0);

-- ------------------------------------------------------------------------------
-- 4. INSERT FIELD ACTIVITIES & CHEMICAL INPUTS
-- ------------------------------------------------------------------------------
INSERT INTO field_activities (plot_id, activity_type, activity_date, input_name, quantity, unit, cost, operator_name, notes)
VALUES
(
    1, 
    'Fertilization', 
    DATE_SUB(CURRENT_DATE, INTERVAL 20 DAY), 
    'Urea (Granular 46% N)', 
    125.00, 
    'kg', 
    75.00, 
    'Tariq Mehmood', 
    'First broadcast application during active crown root development.'
),
(
    1, 
    'Irrigation', 
    DATE_SUB(CURRENT_DATE, INTERVAL 5 DAY), 
    'Groundwater Tube-well canal mix', 
    180.00, 
    'cubic meters', 
    45.00, 
    'Ali Raza', 
    'Flooding irrigation for 4 hours. Checked soil penetration at 20cm depth.'
),
(
    2, 
    'Pesticide Application', 
    DATE_SUB(CURRENT_DATE, INTERVAL 8 DAY), 
    'Organic Neem Oil & Bacillus thuringiensis', 
    3.50, 
    'liters', 
    32.00, 
    'Dr. Sara Khan', 
    'Preventative spray targeting tomato fruit worm and whitefly nymphs.'
),
(
    2, 
    'Fertilization', 
    DATE_SUB(CURRENT_DATE, INTERVAL 12 DAY), 
    'Soluble NPK 10-52-10 (High Phosphorus)', 
    25.00, 
    'kg', 
    60.00, 
    'Dr. Sara Khan', 
    'Drip fertigation to stimulate flower bud set and vigorous root growth.'
),
(
    2, 
    'Pruning', 
    DATE_SUB(CURRENT_DATE, INTERVAL 3 DAY), 
    'Suckering & Trellising labor', 
    16.00, 
    'hours', 
    55.00, 
    'Greenhouse Crew A', 
    'Removed lateral suckers up to first cluster to enhance air circulation and reduce disease risk.'
),
(
    3, 
    'Weed Control', 
    DATE_SUB(CURRENT_DATE, INTERVAL 40 DAY), 
    'Selective Pre-emergence Herbicide (Atrazine 50% SC)', 
    4.00, 
    'liters', 
    48.00, 
    'Hamza Farooq', 
    'Sprayed uniformly across 3.4 hectares after planting.'
),
(
    3, 
    'Fertilization', 
    DATE_SUB(CURRENT_DATE, INTERVAL 25 DAY), 
    'Di-Ammonium Phosphate (DAP 18-46-0)', 
    150.00, 
    'kg', 
    140.00, 
    'Hamza Farooq', 
    'Side dressing applied before ear formation stage.'
);

-- ------------------------------------------------------------------------------
-- 5. INSERT FINANCIAL RECORDS (Cost of Production vs Revenues / Projections)
-- ------------------------------------------------------------------------------
INSERT INTO financial_records (plot_id, record_type, category, amount, record_date, description)
VALUES
-- Plot 1: Wheat Expenses & Projected Revenue
(1, 'EXPENSE', 'Seeds & Seedlings', 110.00, DATE_SUB(CURRENT_DATE, INTERVAL 45 DAY), 'Certified Faisalabad-08 seed bags (125 kg)'),
(1, 'EXPENSE', 'Machinery & Fuel', 85.00, DATE_SUB(CURRENT_DATE, INTERVAL 44 DAY), 'Laser land leveling & seed drill tractor rental'),
(1, 'EXPENSE', 'Fertilizer & Nutrients', 75.00, DATE_SUB(CURRENT_DATE, INTERVAL 20 DAY), 'Urea top dressing (125 kg)'),
(1, 'EXPENSE', 'Irrigation & Utilities', 45.00, DATE_SUB(CURRENT_DATE, INTERVAL 5 DAY), 'Electric tube-well pumping energy fee'),
(1, 'PROJECTION', 'Projected Yield Revenue', 1850.00, DATE_ADD(CURRENT_DATE, INTERVAL 75 DAY), 'Projected wheat harvest: 95 maunds (3,800 kg) @ $0.48/kg'),

-- Plot 2: Tomatoes Expenses & Projected Revenue
(2, 'EXPENSE', 'Seeds & Seedlings', 95.00, DATE_SUB(CURRENT_DATE, INTERVAL 60 DAY), 'Certified F1 Roma hybrid nursery seedlings'),
(2, 'EXPENSE', 'Fertilizer & Nutrients', 140.00, DATE_SUB(CURRENT_DATE, INTERVAL 12 DAY), 'NPK water-soluble fertigation salts'),
(2, 'EXPENSE', 'Pesticides & Chemicals', 32.00, DATE_SUB(CURRENT_DATE, INTERVAL 8 DAY), 'Neem oil biopesticide treatment'),
(2, 'EXPENSE', 'Labor', 120.00, DATE_SUB(CURRENT_DATE, INTERVAL 3 DAY), 'Trellising, pruning and greenhouse climate monitoring'),
(2, 'PROJECTION', 'Projected Yield Revenue', 3200.00, DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY), 'Projected fresh market tomato yield: 6,400 kg @ $0.50/kg'),

-- Plot 3: Corn Expenses & Actual / Projected
(3, 'EXPENSE', 'Seeds & Seedlings', 180.00, DATE_SUB(CURRENT_DATE, INTERVAL 80 DAY), 'Pioneer 30Y87 hybrid maize seed cartons'),
(3, 'EXPENSE', 'Machinery & Fuel', 130.00, DATE_SUB(CURRENT_DATE, INTERVAL 78 DAY), 'Deep disc plowing, rotavator and ridging'),
(3, 'EXPENSE', 'Pesticides & Chemicals', 48.00, DATE_SUB(CURRENT_DATE, INTERVAL 40 DAY), 'Pre-emergence herbicide'),
(3, 'EXPENSE', 'Fertilizer & Nutrients', 140.00, DATE_SUB(CURRENT_DATE, INTERVAL 25 DAY), 'DAP fertilizer side-dressing'),
(3, 'EXPENSE', 'Irrigation & Utilities', 90.00, DATE_SUB(CURRENT_DATE, INTERVAL 15 DAY), 'Canal water cess and auxiliary diesel pump fuel'),
(3, 'PROJECTION', 'Projected Yield Revenue', 2900.00, DATE_ADD(CURRENT_DATE, INTERVAL 25 DAY), 'Estimated grain yield: 18,000 kg @ $0.16/kg');

-- ------------------------------------------------------------------------------
-- 6. INSERT SAMPLE GROQ AI CONSULTATIONS (Demonstrates LLaMA-3.3-70b-versatile Output)
-- ------------------------------------------------------------------------------
INSERT INTO ai_consultations (plot_id, query_type, user_prompt, ai_response, model_used, actionable_recommendations)
VALUES
(
    2,
    'DISEASE_DIAGNOSIS',
    'Tomato lower leaves are exhibiting concentric brown rings surrounded by a chlorotic yellow halo. The stems show dark elongated lesions. What is the pathogen and how do I treat it immediately?',
    '### Diagnostic Assessment: Early Blight (*Alternaria solani*)

**Pathogen Profile:**
The symptoms described (concentric target-like rings with yellow chlorotic margins on lower foliage) are hallmark diagnostic indicators of Early Blight caused by the fungus *Alternaria solani*. High relative humidity and leaf wetness in Greenhouse Zone 2 provide the ideal microclimate for conidial sporulation.

**Recommended Action Protocol:**
1. **Immediate Cultural Control:** Prune and safely bag all lower leaves showing target spots. Do not compost infected leaves; burn or discard away from the greenhouse.
2. **Irrigation Adjustment:** Restrict overhead watering; ensure drip lines are functioning without splashing soil particles onto lower foliage. Increase greenhouse ventilation to lower humidity below 65%.
3. **Fungicide Treatment:**
   - *Organic / Biological:* Apply Copper Octanoate (Copper Soap) or *Bacillus subtilis* foliar spray at sunset.
   - *Conventional Curative:* Apply Azoxystrobin (250 SC) at 0.8 mL/L or Mancozeb 75% WP at 2.5 g/L with thorough spray coverage on both leaf surfaces.
4. **Re-inspection:** Re-evaluate disease progression within 72 hours.',
    'llama-3.3-70b-versatile',
    JSON_ARRAY(
        'Prune and destroy infected lower foliage immediately',
        'Avoid wetting leaves during irrigation and decrease greenhouse humidity',
        'Apply copper-based or Mancozeb fungicide spray within 24 hours',
        'Re-inspect in 72 hours for lesion stabilization'
    )
),
(
    1,
    'IRRIGATION_ADVICE',
    'Plot A soil moisture is at 36.2%, approaching the minimum threshold of 35%. Ambient temperature is 21°C and ET0 is 1.1 mm/day. Should the automated pump initiate irrigation now or wait until tomorrow morning?',
    '### Smart Irrigation Advisory: Plot A (Winter Wheat)

**Telemetry Analysis:**
- Current Moisture: **36.2%** (Critical Lower Bound: 35.0%)
- Reference Evapotranspiration (ET0): **1.1 mm/day** (Low nocturnal water demand)
- Diurnal Temperature: **19.8°C - 21.0°C**

**Recommendation:**
**Schedule Irrigation for 05:00 AM (Early Dawn).**

**Agronomic Justification:**
While the soil moisture is within 1.2% of the trigger threshold, nighttime evaporative demand is minimal (ET0 0.4 - 0.6 mm/h). Initiating irrigation at night creates prolonged root-zone saturation in sandy loam, predisposing young roots to fungal pathogens (*Pythium root rot*). Irrigating at dawn ensures maximum infiltration efficiency before midday solar irradiance spikes, minimizing evaporation losses by up to 28%.',
    'llama-3.3-70b-versatile',
    JSON_ARRAY(
        'Postpone automated irrigation until 05:00 AM tomorrow',
        'Set irrigation duration to deliver 25 mm depth (approx. 4.5 hours drip pulse)',
        'Monitor moisture recovery to target 60% post-run'
    )
);
