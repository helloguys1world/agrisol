-- ==============================================================================
-- SMART AGRICULTURE IOT & AI DECISION SUPPORT SYSTEM
-- Database Schema: MySQL 8.0+ Compatible
-- Academic Project Presentation
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS smart_agriculture
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE smart_agriculture;

-- Disable foreign key checks during schema rebuild
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS ai_consultations;
DROP TABLE IF EXISTS financial_records;
DROP TABLE IF EXISTS field_activities;
DROP TABLE IF EXISTS telemetry_readings;
DROP TABLE IF EXISTS soil_tests;
DROP TABLE IF EXISTS plots;

SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------------------------
-- 1. PLOTS TABLE
-- Represents individual farm zones, fields, or greenhouse compartments.
-- ------------------------------------------------------------------------------
CREATE TABLE plots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    crop_type VARCHAR(100) NOT NULL,
    variety VARCHAR(100) DEFAULT 'Standard',
    area_hectares DECIMAL(6, 2) NOT NULL,
    soil_type VARCHAR(60) NOT NULL,
    planting_date DATE NOT NULL,
    expected_harvest_date DATE NULL,
    growth_stage ENUM('Germination', 'Vegetative', 'Flowering', 'Fruiting', 'Maturation', 'Harvest Ready') NOT NULL DEFAULT 'Vegetative',
    target_moisture_min DECIMAL(5, 2) NOT NULL DEFAULT 30.00 COMMENT 'Lower soil moisture threshold (%)',
    target_moisture_max DECIMAL(5, 2) NOT NULL DEFAULT 65.00 COMMENT 'Upper soil moisture threshold (%)',
    pump_status ENUM('OFF', 'ON', 'AUTO') NOT NULL DEFAULT 'AUTO' COMMENT 'Smart irrigation pump status',
    last_irrigated_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_plots_growth_stage (growth_stage),
    INDEX idx_plots_crop (crop_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 2. SOIL_TESTS TABLE
-- Chemical and physical laboratory baseline analyses for agronomic management.
-- ------------------------------------------------------------------------------
CREATE TABLE soil_tests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT NOT NULL,
    test_date DATE NOT NULL,
    ph_level DECIMAL(4, 2) NOT NULL COMMENT 'Soil pH (optimal 6.0 - 7.5)',
    nitrogen_ppm DECIMAL(6, 2) NOT NULL COMMENT 'Available Nitrogen (mg/kg)',
    phosphorus_ppm DECIMAL(6, 2) NOT NULL COMMENT 'Available Phosphorus (mg/kg)',
    potassium_ppm DECIMAL(6, 2) NOT NULL COMMENT 'Exchangeable Potassium (mg/kg)',
    organic_matter_percent DECIMAL(4, 2) NOT NULL COMMENT 'Soil Organic Matter (%)',
    electrical_conductivity DECIMAL(5, 2) NOT NULL COMMENT 'EC (dS/m) - Soil Salinity indicator',
    moisture_retention_capacity DECIMAL(5, 2) NULL COMMENT 'Field Capacity (%)',
    lab_name VARCHAR(120) DEFAULT 'Agronomy Diagnostic Labs',
    recommendations TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_soil_tests_plot FOREIGN KEY (plot_id) 
        REFERENCES plots(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_soil_tests_date (test_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 3. TELEMETRY_READINGS TABLE
-- High-frequency IoT sensor telemetry (Microclimate & Root-zone sensors).
-- ------------------------------------------------------------------------------
CREATE TABLE telemetry_readings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT NOT NULL,
    recorded_at DATETIME NOT NULL,
    soil_moisture DECIMAL(5, 2) NOT NULL COMMENT 'Volumetric Water Content (%)',
    soil_temperature DECIMAL(5, 2) NOT NULL COMMENT 'Root-zone temperature (°C)',
    ambient_temperature DECIMAL(5, 2) NOT NULL COMMENT 'Air temperature (°C)',
    humidity DECIMAL(5, 2) NOT NULL COMMENT 'Relative Humidity (%)',
    solar_radiation DECIMAL(6, 2) NOT NULL COMMENT 'Solar Irradiance (W/m²)',
    et0 DECIMAL(5, 2) NOT NULL COMMENT 'Penman-Monteith Reference Evapotranspiration (mm/day)',
    battery_level DECIMAL(5, 2) DEFAULT 100.00 COMMENT 'Sensor Node Battery Percentage (%)',
    pump_event_triggered TINYINT(1) DEFAULT 0 COMMENT '1 if reading triggered automatic irrigation',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_telemetry_plot FOREIGN KEY (plot_id) 
        REFERENCES plots(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_telemetry_plot_time (plot_id, recorded_at DESC),
    INDEX idx_telemetry_time (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 4. FIELD_ACTIVITIES TABLE
-- Comprehensive agronomic input tracking: fertilizers, pesticides, irrigation, labor.
-- ------------------------------------------------------------------------------
CREATE TABLE field_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT NOT NULL,
    activity_type ENUM('Irrigation', 'Fertilization', 'Pesticide Application', 'Weed Control', 'Soil Tillage', 'Pruning', 'Harvesting') NOT NULL,
    activity_date DATE NOT NULL,
    input_name VARCHAR(150) NOT NULL COMMENT 'E.g., Urea (46-0-0), Neem Biopesticide, Drip Water',
    quantity DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(30) NOT NULL COMMENT 'kg, liters, cubic meters, hours',
    cost DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT 'Cost in USD/PKR/Currency',
    operator_name VARCHAR(100) NOT NULL,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_activities_plot FOREIGN KEY (plot_id) 
        REFERENCES plots(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_activities_date (activity_date),
    INDEX idx_activities_type (activity_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 5. FINANCIAL_RECORDS TABLE
-- Production cost accounting, crop yield sales revenue, and profit projections.
-- ------------------------------------------------------------------------------
CREATE TABLE financial_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT NOT NULL,
    record_type ENUM('EXPENSE', 'REVENUE', 'PROJECTION') NOT NULL,
    category ENUM('Seeds & Seedlings', 'Fertilizer & Nutrients', 'Pesticides & Chemicals', 'Irrigation & Utilities', 'Machinery & Fuel', 'Labor', 'Harvest & Storage', 'Crop Sales', 'Projected Yield Revenue') NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    record_date DATE NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_financials_plot FOREIGN KEY (plot_id) 
        REFERENCES plots(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_financials_type (record_type),
    INDEX idx_financials_date (record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 6. AI_CONSULTATIONS TABLE
-- Groq LLaMA-3.3-70b-versatile consultation records for agronomic diagnosis.
-- ------------------------------------------------------------------------------
CREATE TABLE ai_consultations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT NULL,
    query_type ENUM('DISEASE_DIAGNOSIS', 'IRRIGATION_ADVICE', 'NUTRIENT_DEFICIENCY', 'YIELD_PREDICTION', 'GENERAL') NOT NULL DEFAULT 'GENERAL',
    user_prompt TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    model_used VARCHAR(80) DEFAULT 'llama-3.3-70b-versatile',
    actionable_recommendations JSON NULL COMMENT 'Extracted key action points in JSON array',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ai_plot FOREIGN KEY (plot_id) 
        REFERENCES plots(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_ai_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
