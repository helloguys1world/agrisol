from datetime import datetime, date
import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Plot(db.Model):
    """Farm zone, greenhouse bay, or outdoor field plot."""
    __tablename__ = 'plots'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    crop_type = db.Column(db.String(100), nullable=False)
    variety = db.Column(db.String(100), default='Standard')
    area_hectares = db.Column(db.Numeric(6, 2), nullable=False)
    soil_type = db.Column(db.String(60), nullable=False)
    planting_date = db.Column(db.Date, nullable=False)
    expected_harvest_date = db.Column(db.Date, nullable=True)
    growth_stage = db.Column(db.Enum('Germination', 'Vegetative', 'Flowering', 'Fruiting', 'Maturation', 'Harvest Ready', name='growth_stage_enum'), default='Vegetative', nullable=False)
    target_moisture_min = db.Column(db.Numeric(5, 2), nullable=False, default=30.00)
    target_moisture_max = db.Column(db.Numeric(5, 2), nullable=False, default=65.00)
    pump_status = db.Column(db.Enum('OFF', 'ON', 'AUTO', name='pump_status_enum'), default='AUTO', nullable=False)
    last_irrigated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    soil_tests = db.relationship('SoilTest', backref='plot', cascade='all, delete-orphan', lazy='dynamic')
    telemetry_readings = db.relationship('TelemetryReading', backref='plot', cascade='all, delete-orphan', lazy='dynamic', order_by='TelemetryReading.recorded_at.desc()')
    field_activities = db.relationship('FieldActivity', backref='plot', cascade='all, delete-orphan', lazy='dynamic', order_by='FieldActivity.activity_date.desc()')
    financial_records = db.relationship('FinancialRecord', backref='plot', cascade='all, delete-orphan', lazy='dynamic', order_by='FinancialRecord.record_date.desc()')
    ai_consultations = db.relationship('AIConsultation', backref='plot', cascade='all, delete-orphan', lazy='dynamic', order_by='AIConsultation.created_at.desc()')

    @property
    def latest_telemetry(self):
        """Returns the most recent telemetry reading for this plot."""
        return self.telemetry_readings.first()

    @property
    def latest_soil_test(self):
        """Returns the most recent soil test baseline for this plot."""
        return self.soil_tests.order_by(SoilTest.test_date.desc()).first()

    @property
    def display_title(self):
        """
        Formats header as 'Plot Name - Crop Name' (e.g., 'Plot A - Winter Wheat').
        Extracts plot prefix (e.g., 'Plot A') from compound names like 'Plot A - North Field'.
        """
        if ' - ' in self.name:
            plot_prefix = self.name.split(' - ')[0].strip()
        else:
            plot_prefix = self.name
        return f"{plot_prefix} - {self.crop_type}"

    @property
    def zone_name(self):
        """Extracts field zone portion from name if present (e.g. 'North Field')."""
        if ' - ' in self.name:
            return self.name.split(' - ', 1)[1].strip()
        return self.name

    @property
    def days_since_planting(self):
        """Days elapsed since planting date."""
        if self.planting_date:
            return (date.today() - self.planting_date).days
        return 0

    @property
    def moisture_health_status(self):
        """
        Determines agronomic health status based on current soil moisture vs thresholds.
        Returns: 'OPTIMAL', 'LOW_ALERT', 'CRITICAL_DRY', 'SATURATED', or 'NO_DATA'
        """
        latest = self.latest_telemetry
        if not latest:
            return 'NO_DATA'
        
        current_moisture = float(latest.soil_moisture)
        min_moisture = float(self.target_moisture_min)
        max_moisture = float(self.target_moisture_max)

        if current_moisture < min_moisture - 5.0:
            return 'CRITICAL_DRY'
        elif current_moisture < min_moisture:
            return 'LOW_ALERT'
        elif current_moisture > max_moisture:
            return 'SATURATED'
        else:
            return 'OPTIMAL'

    def to_dict(self, include_latest=True):
        """Convert Plot model to dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'display_title': self.display_title,
            'zone_name': self.zone_name,
            'crop_type': self.crop_type,
            'variety': self.variety,
            'area_hectares': float(self.area_hectares) if self.area_hectares else 0.0,
            'soil_type': self.soil_type,
            'planting_date': self.planting_date.isoformat() if self.planting_date else None,
            'expected_harvest_date': self.expected_harvest_date.isoformat() if self.expected_harvest_date else None,
            'days_since_planting': self.days_since_planting,
            'growth_stage': self.growth_stage,
            'target_moisture_min': float(self.target_moisture_min),
            'target_moisture_max': float(self.target_moisture_max),
            'pump_status': self.pump_status,
            'last_irrigated_at': self.last_irrigated_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_irrigated_at else None,
            'moisture_health_status': self.moisture_health_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

        if include_latest:
            latest = self.latest_telemetry
            data['latest_telemetry'] = latest.to_dict() if latest else None
            soil = self.latest_soil_test
            data['latest_soil_test'] = soil.to_dict() if soil else None

        return data


class SoilTest(db.Model):
    """Laboratory soil baseline chemistry analysis."""
    __tablename__ = 'soil_tests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plot_id = db.Column(db.Integer, db.ForeignKey('plots.id', ondelete='CASCADE'), nullable=False)
    test_date = db.Column(db.Date, nullable=False)
    ph_level = db.Column(db.Numeric(4, 2), nullable=False)
    nitrogen_ppm = db.Column(db.Numeric(6, 2), nullable=False)
    phosphorus_ppm = db.Column(db.Numeric(6, 2), nullable=False)
    potassium_ppm = db.Column(db.Numeric(6, 2), nullable=False)
    organic_matter_percent = db.Column(db.Numeric(4, 2), nullable=False)
    electrical_conductivity = db.Column(db.Numeric(5, 2), nullable=False)
    moisture_retention_capacity = db.Column(db.Numeric(5, 2), nullable=True)
    lab_name = db.Column(db.String(120), default='Agronomy Diagnostic Labs')
    recommendations = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'plot_id': self.plot_id,
            'test_date': self.test_date.isoformat() if self.test_date else None,
            'ph_level': float(self.ph_level),
            'nitrogen_ppm': float(self.nitrogen_ppm),
            'phosphorus_ppm': float(self.phosphorus_ppm),
            'potassium_ppm': float(self.potassium_ppm),
            'organic_matter_percent': float(self.organic_matter_percent),
            'electrical_conductivity': float(self.electrical_conductivity),
            'moisture_retention_capacity': float(self.moisture_retention_capacity) if self.moisture_retention_capacity else None,
            'lab_name': self.lab_name,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TelemetryReading(db.Model):
    """IoT microclimate and root-zone sensor telemetry."""
    __tablename__ = 'telemetry_readings'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    plot_id = db.Column(db.Integer, db.ForeignKey('plots.id', ondelete='CASCADE'), nullable=False)
    recorded_at = db.Column(db.DateTime, nullable=False)
    soil_moisture = db.Column(db.Numeric(5, 2), nullable=False)
    soil_temperature = db.Column(db.Numeric(5, 2), nullable=False)
    ambient_temperature = db.Column(db.Numeric(5, 2), nullable=False)
    humidity = db.Column(db.Numeric(5, 2), nullable=False)
    solar_radiation = db.Column(db.Numeric(6, 2), nullable=False)
    et0 = db.Column(db.Numeric(5, 2), nullable=False)
    battery_level = db.Column(db.Numeric(5, 2), default=100.00)
    pump_event_triggered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'plot_id': self.plot_id,
            'recorded_at': self.recorded_at.strftime('%Y-%m-%d %H:%M:%S') if self.recorded_at else None,
            'soil_moisture': float(self.soil_moisture),
            'soil_temperature': float(self.soil_temperature),
            'ambient_temperature': float(self.ambient_temperature),
            'humidity': float(self.humidity),
            'solar_radiation': float(self.solar_radiation),
            'et0': float(self.et0),
            'battery_level': float(self.battery_level) if self.battery_level is not None else 100.0,
            'pump_event_triggered': bool(self.pump_event_triggered)
        }


class FieldActivity(db.Model):
    """Agricultural operations log: irrigation, fertilizers, chemicals, labor."""
    __tablename__ = 'field_activities'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plot_id = db.Column(db.Integer, db.ForeignKey('plots.id', ondelete='CASCADE'), nullable=False)
    activity_type = db.Column(
        db.Enum('Irrigation', 'Fertilization', 'Pesticide Application', 'Weed Control', 'Soil Tillage', 'Pruning', 'Harvesting', name='activity_type_enum'),
        nullable=False
    )
    activity_date = db.Column(db.Date, nullable=False)
    input_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(30), nullable=False)
    cost = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    operator_name = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'plot_id': self.plot_id,
            'plot_name': self.plot.display_title if self.plot else f"Plot #{self.plot_id}",
            'activity_type': self.activity_type,
            'activity_date': self.activity_date.isoformat() if self.activity_date else None,
            'input_name': self.input_name,
            'quantity': float(self.quantity),
            'unit': self.unit,
            'cost': float(self.cost),
            'operator_name': self.operator_name,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class FinancialRecord(db.Model):
    """Production expense tracking, crop revenues, and yield projections."""
    __tablename__ = 'financial_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plot_id = db.Column(db.Integer, db.ForeignKey('plots.id', ondelete='CASCADE'), nullable=False)
    record_type = db.Column(db.Enum('EXPENSE', 'REVENUE', 'PROJECTION', name='record_type_enum'), nullable=False)
    category = db.Column(
        db.Enum('Seeds & Seedlings', 'Fertilizer & Nutrients', 'Pesticides & Chemicals', 'Irrigation & Utilities', 'Machinery & Fuel', 'Labor', 'Harvest & Storage', 'Crop Sales', 'Projected Yield Revenue', name='category_enum'),
        nullable=False
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'plot_id': self.plot_id,
            'plot_name': self.plot.display_title if self.plot else f"Plot #{self.plot_id}",
            'record_type': self.record_type,
            'category': self.category,
            'amount': float(self.amount),
            'record_date': self.record_date.isoformat() if self.record_date else None,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class AIConsultation(db.Model):
    """Groq LLaMA-3.3-70b-versatile consultation record."""
    __tablename__ = 'ai_consultations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plot_id = db.Column(db.Integer, db.ForeignKey('plots.id', ondelete='SET NULL'), nullable=True)
    query_type = db.Column(
        db.Enum('DISEASE_DIAGNOSIS', 'IRRIGATION_ADVICE', 'NUTRIENT_DEFICIENCY', 'YIELD_PREDICTION', 'GENERAL', name='query_type_enum'),
        default='GENERAL', nullable=False
    )
    user_prompt = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    model_used = db.Column(db.String(80), default='llama-3.3-70b-versatile')
    actionable_recommendations = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        # Parse JSON recommendations if stored as string or array
        recs = self.actionable_recommendations
        if isinstance(recs, str):
            try:
                recs = json.loads(recs)
            except Exception:
                recs = [recs]
        return {
            'id': self.id,
            'plot_id': self.plot_id,
            'plot_name': self.plot.name if self.plot else 'Farm-wide / General',
            'query_type': self.query_type,
            'user_prompt': self.user_prompt,
            'ai_response': self.ai_response,
            'model_used': self.model_used,
            'actionable_recommendations': recs or [],
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }
