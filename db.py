import os
from datetime import datetime, date
import json
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def get_db_url():
    """Builds MySQL connection URL from .env file with intelligent database detection."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    dbname = os.getenv("DB_NAME", "smart_agriculture")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}"

# Create resilient SQLAlchemy engine with connection pool ping
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        url = get_db_url()
        try:
            _engine = create_engine(
                url,
                pool_recycle=280,
                pool_pre_ping=True,
                connect_args={"charset": "utf8mb4"}
            )
            # Test connection
            with _engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
        except Exception:
            # Fallback check if smart_agri_db exists instead of smart_agriculture
            user = os.getenv("DB_USER", "root")
            password = os.getenv("DB_PASSWORD", "")
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "3306")
            alt_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/smart_agri_db"
            try:
                _engine = create_engine(
                    alt_url,
                    pool_recycle=280,
                    pool_pre_ping=True,
                    connect_args={"charset": "utf8mb4"}
                )
                with _engine.connect() as conn:
                    conn.execute(text("SELECT 1;"))
            except Exception:
                # Revert to base url and let error be handled cleanly in UI
                _engine = create_engine(url, pool_recycle=280, pool_pre_ping=True)
    return _engine


# ------------------------------------------------------------------------------
# 1. PLOTS & FIELD MAP OPERATIONS
# ------------------------------------------------------------------------------
def get_plots():
    """Retrieves all plots with their display names, latest telemetry, and soil baseline."""
    engine = get_engine()
    query = """
    SELECT 
        p.id, p.name, p.crop_type, p.variety, p.area_hectares, 
        p.soil_type, p.planting_date, p.expected_harvest_date, 
        p.growth_stage, p.target_moisture_min, p.target_moisture_max, 
        p.pump_status, p.last_irrigated_at, p.created_at
    FROM plots p
    ORDER BY p.id ASC;
    """
    with engine.connect() as conn:
        df_plots = pd.read_sql(text(query), conn)

    plots_list = []
    for _, row in df_plots.iterrows():
        p_id = int(row['id'])
        name = str(row['name'])
        crop_type = str(row['crop_type'])
        
        # Format Plot Name - Crop Name
        plot_prefix = name.split(' - ')[0].strip() if ' - ' in name else name
        display_title = f"{plot_prefix} - {crop_type}"
        zone_name = name.split(' - ', 1)[1].strip() if ' - ' in name else name

        # Latest Telemetry
        tel = get_latest_telemetry(p_id)

        # Latest Soil Baseline
        soil = get_latest_soil_test(p_id)

        # Moisture status calculation
        status = "NO_DATA"
        current_moisture = None
        if tel:
            current_moisture = float(tel['soil_moisture'])
            min_m = float(row['target_moisture_min'])
            max_m = float(row['target_moisture_max'])
            if current_moisture < min_m - 5.0:
                status = "CRITICAL_DRY"
            elif current_moisture < min_m:
                status = "LOW_ALERT"
            elif current_moisture > max_m:
                status = "SATURATED"
            else:
                status = "OPTIMAL"

        plot_data = {
            'id': p_id,
            'name': name,
            'display_title': display_title,
            'zone_name': zone_name,
            'crop_type': crop_type,
            'variety': str(row['variety']),
            'area_hectares': float(row['area_hectares']),
            'soil_type': str(row['soil_type']),
            'planting_date': str(row['planting_date']),
            'expected_harvest_date': str(row['expected_harvest_date']) if pd.notnull(row['expected_harvest_date']) else None,
            'growth_stage': str(row['growth_stage']),
            'target_moisture_min': float(row['target_moisture_min']),
            'target_moisture_max': float(row['target_moisture_max']),
            'pump_status': str(row['pump_status']),
            'last_irrigated_at': str(row['last_irrigated_at']) if pd.notnull(row['last_irrigated_at']) else None,
            'latest_telemetry': tel,
            'latest_soil_test': soil,
            'moisture_health_status': status,
            'current_moisture': current_moisture
        }
        plots_list.append(plot_data)

    return plots_list


def get_latest_telemetry(plot_id: int):
    """Returns dictionary of latest telemetry reading for a plot."""
    engine = get_engine()
    q = """
    SELECT recorded_at, soil_moisture, soil_temperature, ambient_temperature, 
           humidity, solar_radiation, et0, battery_level, pump_event_triggered
    FROM telemetry_readings
    WHERE plot_id = :plot_id
    ORDER BY recorded_at DESC
    LIMIT 1;
    """
    with engine.connect() as conn:
        res = conn.execute(text(q), {"plot_id": plot_id}).fetchone()
        if res:
            return {
                'recorded_at': str(res[0]),
                'soil_moisture': float(res[1]),
                'soil_temperature': float(res[2]),
                'ambient_temperature': float(res[3]),
                'humidity': float(res[4]),
                'solar_radiation': float(res[5]),
                'et0': float(res[6]),
                'battery_level': float(res[7]) if res[7] is not None else 100.0,
                'pump_event_triggered': bool(res[8])
            }
    return None


def get_latest_soil_test(plot_id: int):
    """Returns dictionary of latest soil test baseline for a plot."""
    engine = get_engine()
    q = """
    SELECT id, test_date, ph_level, nitrogen_ppm, phosphorus_ppm, potassium_ppm,
           organic_matter_percent, electrical_conductivity, recommendations
    FROM soil_tests
    WHERE plot_id = :plot_id
    ORDER BY test_date DESC, id DESC
    LIMIT 1;
    """
    with engine.connect() as conn:
        res = conn.execute(text(q), {"plot_id": plot_id}).fetchone()
        if res:
            return {
                'id': int(res[0]),
                'test_date': str(res[1]),
                'ph_level': float(res[2]),
                'nitrogen_ppm': float(res[3]),
                'phosphorus_ppm': float(res[4]),
                'potassium_ppm': float(res[5]),
                'organic_matter_percent': float(res[6]),
                'electrical_conductivity': float(res[7]),
                'recommendations': str(res[8]) if res[8] else ""
            }
    return None


def update_pump_status(plot_id: int, new_status: str):
    """Updates pump status in MySQL and records activity if commanded ON."""
    engine = get_engine()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = date.today().strftime("%Y-%m-%d")

    with engine.begin() as conn:
        if new_status == 'ON':
            conn.execute(
                text("UPDATE plots SET pump_status = :status, last_irrigated_at = :now WHERE id = :id"),
                {"status": new_status, "now": now_str, "id": plot_id}
            )
            # Log field activity
            conn.execute(
                text("""
                INSERT INTO field_activities (plot_id, activity_type, activity_date, input_name, quantity, unit, cost, operator_name, notes)
                VALUES (:plot_id, 'Irrigation', :act_date, 'Smart Drip System Activation', 25.0, 'cubic meters', 12.50, 'Smart Pump Controller', 'Pump commanded to ON state.')
                """),
                {"plot_id": plot_id, "act_date": today_str}
            )
        else:
            conn.execute(
                text("UPDATE plots SET pump_status = :status WHERE id = :id"),
                {"status": new_status, "id": plot_id}
            )


def create_plot(name: str, crop_type: str, variety: str, area_ha: float, 
                soil_type: str, planting_date: str, harvest_date: str, growth_stage: str,
                min_m: float, max_m: float, ph: float, n_ppm: float, p_ppm: float, 
                k_ppm: float, ec: float, om: float):
    """Registers a new plot and inserts initial soil baseline + baseline telemetry."""
    engine = get_engine()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = date.today().strftime("%Y-%m-%d")

    with engine.begin() as conn:
        # Insert Plot
        res = conn.execute(
            text("""
            INSERT INTO plots (name, crop_type, variety, area_hectares, soil_type, planting_date, expected_harvest_date, growth_stage, target_moisture_min, target_moisture_max, pump_status)
            VALUES (:name, :crop, :variety, :area, :soil, :planting, :harvest, :stage, :min_m, :max_m, 'AUTO')
            """),
            {
                "name": name, "crop": crop_type, "variety": variety or "Standard",
                "area": area_ha, "soil": soil_type, "planting": planting_date,
                "harvest": harvest_date or None, "stage": growth_stage,
                "min_m": min_m, "max_m": max_m
            }
        )
        plot_id = res.lastrowid

        # Insert Soil Test Baseline
        conn.execute(
            text("""
            INSERT INTO soil_tests (plot_id, test_date, ph_level, nitrogen_ppm, phosphorus_ppm, potassium_ppm, organic_matter_percent, electrical_conductivity, lab_name, recommendations)
            VALUES (:plot_id, :test_date, :ph, :n, :p, :k, :om, :ec, 'Laboratory Baseline', 'Initial baseline test created during field onboarding.')
            """),
            {
                "plot_id": plot_id, "test_date": today_str,
                "ph": ph, "n": n_ppm, "p": p_ppm, "k": k_ppm,
                "om": om, "ec": ec
            }
        )

        # Insert Initial Baseline Telemetry
        conn.execute(
            text("""
            INSERT INTO telemetry_readings (plot_id, recorded_at, soil_moisture, soil_temperature, ambient_temperature, humidity, solar_radiation, et0, battery_level, pump_event_triggered)
            VALUES (:plot_id, :now, 45.0, 21.5, 24.0, 60.0, 450.0, 3.5, 100.0, 0)
            """),
            {"plot_id": plot_id, "now": now_str}
        )

    return plot_id


def delete_plot(plot_id: int):
    """
    Cascading delete of plot and all child records across:
    telemetry_readings, soil_tests, field_activities, financial_records, ai_consultations.
    """
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM telemetry_readings WHERE plot_id = :id"), {"id": plot_id})
        conn.execute(text("DELETE FROM soil_tests WHERE plot_id = :id"), {"id": plot_id})
        conn.execute(text("DELETE FROM field_activities WHERE plot_id = :id"), {"id": plot_id})
        conn.execute(text("DELETE FROM financial_records WHERE plot_id = :id"), {"id": plot_id})
        conn.execute(text("DELETE FROM ai_consultations WHERE plot_id = :id"), {"id": plot_id})
        conn.execute(text("DELETE FROM plots WHERE id = :id"), {"id": plot_id})


# ------------------------------------------------------------------------------
# 2. TELEMETRY TIMESERIES
# ------------------------------------------------------------------------------
def get_telemetry_series(plot_id: int, limit: int = 24):
    """Retrieves timeseries dataframe formatted for charts."""
    engine = get_engine()
    query = """
    SELECT recorded_at, soil_moisture, soil_temperature, ambient_temperature, 
           humidity, solar_radiation, et0
    FROM telemetry_readings
    WHERE plot_id = :plot_id
    ORDER BY recorded_at DESC
    LIMIT :limit;
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params={"plot_id": plot_id, "limit": limit})

    if not df.empty:
        df['recorded_at'] = pd.to_datetime(df['recorded_at'])
        df = df.sort_values('recorded_at')
        df['Time'] = df['recorded_at'].dt.strftime('%H:%M')
    return df


# ------------------------------------------------------------------------------
# 3. FIELD ACTIVITIES & CHEMICAL INPUT LOGS
# ------------------------------------------------------------------------------
def get_activities_df(plot_id: int = None, activity_type: str = None):
    """
    Retrieves activities dataframe with columns:
    Date, Field/Crop, Activity Type, Input, Quantity, Cost, Agronomic Notes.
    (Excludes Operator column as required).
    """
    engine = get_engine()
    query = """
    SELECT 
        fa.activity_date AS `Date`,
        CONCAT(SUBSTRING_INDEX(p.name, ' - ', 1), ' - ', p.crop_type) AS `Field/Crop`,
        fa.activity_type AS `Activity Type`,
        fa.input_name AS `Input`,
        CONCAT(fa.quantity, ' ', fa.unit) AS `Quantity`,
        fa.cost AS `Cost ($)`,
        COALESCE(fa.notes, '—') AS `Agronomic Notes`
    FROM field_activities fa
    JOIN plots p ON fa.plot_id = p.id
    WHERE 1=1
    """
    params = {}
    if plot_id:
        query += " AND fa.plot_id = :plot_id"
        params["plot_id"] = plot_id
    if activity_type and activity_type != "All":
        query += " AND fa.activity_type = :act_type"
        params["act_type"] = activity_type

    query += " ORDER BY fa.activity_date DESC, fa.id DESC LIMIT 150;"

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params=params)

    return df


def create_activity(plot_id: int, act_type: str, act_date: str, input_name: str, 
                    quantity: float, unit: str, cost: float, notes: str):
    """Logs a new field activity and synchronizes an expense into financial_records."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO field_activities (plot_id, activity_type, activity_date, input_name, quantity, unit, cost, operator_name, notes)
            VALUES (:plot_id, :act_type, :act_date, :input_name, :quantity, :unit, :cost, 'Farm Technician', :notes)
            """),
            {
                "plot_id": plot_id, "act_type": act_type, "act_date": act_date,
                "input_name": input_name, "quantity": quantity, "unit": unit,
                "cost": cost, "notes": notes
            }
        )

        if cost > 0:
            category_mapping = {
                'Fertilization': 'Fertilizer & Nutrients',
                'Pesticide Application': 'Pesticides & Chemicals',
                'Irrigation': 'Irrigation & Utilities',
                'Soil Tillage': 'Machinery & Fuel',
                'Weed Control': 'Pesticides & Chemicals',
                'Pruning': 'Labor',
                'Harvesting': 'Harvest & Storage'
            }
            category = category_mapping.get(act_type, 'Labor')
            conn.execute(
                text("""
                INSERT INTO financial_records (plot_id, record_type, category, amount, record_date, description)
                VALUES (:plot_id, 'EXPENSE', :category, :amount, :rec_date, :desc)
                """),
                {
                    "plot_id": plot_id, "category": category, "amount": cost,
                    "rec_date": act_date,
                    "desc": f"Auto-logged from {act_type}: {input_name} ({quantity} {unit})"
                }
            )


# ------------------------------------------------------------------------------
# 4. FINANCIALS & ECONOMIC RECORDS
# ------------------------------------------------------------------------------
def get_financials_summary():
    """Computes total expenses, revenue, net profit, and plot breakdown."""
    engine = get_engine()
    with engine.connect() as conn:
        total_exp = conn.execute(text("SELECT COALESCE(SUM(amount), 0) FROM financial_records WHERE record_type = 'EXPENSE'")).scalar() or 0.0
        total_rev = conn.execute(text("SELECT COALESCE(SUM(amount), 0) FROM financial_records WHERE record_type = 'REVENUE'")).scalar() or 0.0
        total_proj = conn.execute(text("SELECT COALESCE(SUM(amount), 0) FROM financial_records WHERE record_type = 'PROJECTION'")).scalar() or 0.0
        
        effective_rev = total_rev if total_rev > 0 else total_proj
        net_profit = effective_rev - total_exp
        margin = round((net_profit / effective_rev * 100), 1) if effective_rev > 0 else 0.0

        # Category Breakdown
        df_cat = pd.read_sql(
            text("SELECT category AS Category, SUM(amount) AS Amount FROM financial_records WHERE record_type = 'EXPENSE' GROUP BY category"),
            conn
        )

        # Plot breakdown
        query_plots = """
        SELECT 
            p.id,
            CONCAT(SUBSTRING_INDEX(p.name, ' - ', 1), ' - ', p.crop_type) AS `Field/Crop`,
            p.area_hectares AS `Area (Ha)`,
            COALESCE((SELECT SUM(amount) FROM financial_records WHERE plot_id = p.id AND record_type = 'EXPENSE'), 0) AS `Total Cost ($)`,
            COALESCE((SELECT SUM(amount) FROM financial_records WHERE plot_id = p.id AND record_type IN ('REVENUE', 'PROJECTION')), 0) AS `Proj. Revenue ($)`
        FROM plots p;
        """
        df_plots = pd.read_sql(text(query_plots), conn)
        df_plots['Cost / Ha ($)'] = (df_plots['Total Cost ($)'] / df_plots['Area (Ha)']).round(2)
        df_plots['Net Profit ($)'] = (df_plots['Proj. Revenue ($)'] - df_plots['Total Cost ($)']).round(2)

        # Transactions
        query_tx = """
        SELECT 
            fr.record_date AS `Date`,
            CONCAT(SUBSTRING_INDEX(p.name, ' - ', 1), ' - ', p.crop_type) AS `Field`,
            fr.record_type AS `Type`,
            fr.category AS `Category`,
            fr.amount AS `Amount ($)`,
            fr.description AS `Description`
        FROM financial_records fr
        JOIN plots p ON fr.plot_id = p.id
        ORDER BY fr.record_date DESC, fr.id DESC
        LIMIT 100;
        """
        df_tx = pd.read_sql(text(query_tx), conn)

    return {
        'total_expenses': float(total_exp),
        'effective_revenue': float(effective_rev),
        'net_profit': float(net_profit),
        'margin_percent': float(margin),
        'category_df': df_cat,
        'plot_financials_df': df_plots,
        'transactions_df': df_tx
    }


def create_financial_record(plot_id: int, rec_type: str, category: str, amount: float, rec_date: str, description: str):
    """Inserts a manual financial record into financial_records."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO financial_records (plot_id, record_type, category, amount, record_date, description)
            VALUES (:plot_id, :rec_type, :category, :amount, :rec_date, :description)
            """),
            {
                "plot_id": plot_id, "rec_type": rec_type, "category": category,
                "amount": amount, "rec_date": rec_date, "description": description
            }
        )


# ------------------------------------------------------------------------------
# 5. GROQ AI CONSULTATIONS
# ------------------------------------------------------------------------------
def save_ai_consultation(plot_id: int, query_type: str, prompt: str, response: str, model: str, recs: list):
    """Saves Groq AI consultation to ai_consultations."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO ai_consultations (plot_id, query_type, user_prompt, ai_response, model_used, actionable_recommendations)
            VALUES (:plot_id, :query_type, :prompt, :response, :model, :recs)
            """),
            {
                "plot_id": plot_id, "query_type": query_type,
                "prompt": prompt, "response": response, "model": model,
                "recs": json.dumps(recs)
            }
        )


def get_ai_history(limit: int = 15):
    """Retrieves recent AI consultations."""
    engine = get_engine()
    query = """
    SELECT 
        c.created_at, c.query_type, c.user_prompt, c.ai_response, c.model_used,
        COALESCE(CONCAT(SUBSTRING_INDEX(p.name, ' - ', 1), ' - ', p.crop_type), 'Farm-Wide') AS plot_label
    FROM ai_consultations c
    LEFT JOIN plots p ON c.plot_id = p.id
    ORDER BY c.created_at DESC, c.id DESC
    LIMIT :limit;
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params={"limit": limit})
    return df
