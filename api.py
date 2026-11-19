from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func
from models import db, Plot, SoilTest, TelemetryReading, FieldActivity, FinancialRecord, AIConsultation

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ------------------------------------------------------------------------------
# 1. PLOTS & FIELD MAP ENDPOINTS
# ------------------------------------------------------------------------------
@api_bp.route('/plots', methods=['GET'])
def get_plots():
    """Retrieve all farm plots with their latest telemetry snapshot."""
    try:
        plots = Plot.query.all()
        return jsonify({
            'success': True,
            'count': len(plots),
            'plots': [plot.to_dict(include_latest=True) for plot in plots]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/plots/<int:plot_id>', methods=['GET'])
def get_plot_detail(plot_id):
    """Retrieve detailed plot profile including latest soil baseline."""
    plot = Plot.query.get_or_404(plot_id)
    latest_soil = plot.soil_tests.order_by(SoilTest.test_date.desc()).first()

    return jsonify({
        'success': True,
        'plot': plot.to_dict(include_latest=True),
        'latest_soil_test': latest_soil.to_dict() if latest_soil else None
    }), 200


@api_bp.route('/plots/<int:plot_id>', methods=['DELETE'])
def delete_plot(plot_id):
    """
    Permanently delete a field plot and cascade delete all child records:
    telemetry readings, soil tests, field activities, financial records,
    and AI consultations to avoid orphaned data or foreign-key errors.
    """
    try:
        plot = Plot.query.get_or_404(plot_id)
        plot_name = plot.display_title

        # Explicitly delete child records across all related tables
        TelemetryReading.query.filter_by(plot_id=plot.id).delete()
        SoilTest.query.filter_by(plot_id=plot.id).delete()
        FieldActivity.query.filter_by(plot_id=plot.id).delete()
        FinancialRecord.query.filter_by(plot_id=plot.id).delete()
        AIConsultation.query.filter_by(plot_id=plot.id).delete()

        db.session.delete(plot)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f"Field '{plot_name}' and all associated telemetry, logs, and financial records have been permanently deleted."
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/plots', methods=['POST'])
def create_plot():
    """
    Register a new field plot with crop details and optional soil baseline test.
    """
    data = request.get_json() or {}
    try:
        # Validate required fields
        required_fields = ['name', 'crop_type', 'area_hectares', 'soil_type', 'planting_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f"Field '{field}' is required"}), 400

        planting_date = datetime.strptime(data['planting_date'], '%Y-%m-%d').date()
        expected_harvest = None
        if data.get('expected_harvest_date'):
            expected_harvest = datetime.strptime(data['expected_harvest_date'], '%Y-%m-%d').date()

        new_plot = Plot(
            name=data['name'],
            crop_type=data['crop_type'],
            variety=data.get('variety', 'Standard'),
            area_hectares=float(data['area_hectares']),
            soil_type=data['soil_type'],
            planting_date=planting_date,
            expected_harvest_date=expected_harvest,
            growth_stage=data.get('growth_stage', 'Vegetative'),
            target_moisture_min=float(data.get('target_moisture_min', 30.0)),
            target_moisture_max=float(data.get('target_moisture_max', 65.0)),
            pump_status=data.get('pump_status', 'AUTO')
        )
        db.session.add(new_plot)
        db.session.flush() # Populate new_plot.id

        # Optional initial soil baseline
        if data.get('ph_level') is not None and data.get('nitrogen_ppm') is not None:
            initial_soil = SoilTest(
                plot_id=new_plot.id,
                test_date=date.today(),
                ph_level=float(data['ph_level']),
                nitrogen_ppm=float(data['nitrogen_ppm']),
                phosphorus_ppm=float(data.get('phosphorus_ppm', 20.0)),
                potassium_ppm=float(data.get('potassium_ppm', 180.0)),
                organic_matter_percent=float(data.get('organic_matter_percent', 2.0)),
                electrical_conductivity=float(data.get('electrical_conductivity', 1.2)),
                moisture_retention_capacity=float(data.get('moisture_retention_capacity', 40.0)),
                lab_name=data.get('lab_name', 'Initial Baseline Testing'),
                recommendations=data.get('recommendations', 'Baseline test created during field onboarding.')
            )
            db.session.add(initial_soil)

        # Initial baseline telemetry point so plot renders immediately
        initial_telemetry = TelemetryReading(
            plot_id=new_plot.id,
            recorded_at=datetime.utcnow(),
            soil_moisture=float(data.get('initial_moisture', 45.0)),
            soil_temperature=21.5,
            ambient_temperature=24.0,
            humidity=60.0,
            solar_radiation=450.0,
            et0=3.5,
            battery_level=100.0,
            pump_event_triggered=False
        )
        db.session.add(initial_telemetry)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f"Plot '{new_plot.name}' successfully registered.",
            'plot': new_plot.to_dict(include_latest=True)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/plots/<int:plot_id>/pump', methods=['POST'])
def update_pump_status(plot_id):
    """
    Control smart irrigation pump mode: 'ON', 'OFF', or 'AUTO'.
    """
    plot = Plot.query.get_or_404(plot_id)
    data = request.get_json() or {}
    new_status = data.get('pump_status')

    if new_status not in ['ON', 'OFF', 'AUTO']:
        return jsonify({'success': False, 'error': "Invalid status. Must be 'ON', 'OFF', or 'AUTO'."}), 400

    try:
        plot.pump_status = new_status
        if new_status == 'ON':
            plot.last_irrigated_at = datetime.utcnow()
            # Also log field activity for irrigation
            activity = FieldActivity(
                plot_id=plot.id,
                activity_type='Irrigation',
                activity_date=date.today(),
                input_name='Smart Drip System Activation',
                quantity=25.0,
                unit='cubic meters',
                cost=12.50,
                operator_name='Smart Pump Controller (Automated/Manual)',
                notes=f'Pump commanded to {new_status} state.'
            )
            db.session.add(activity)

        db.session.commit()
        return jsonify({
            'success': True,
            'message': f"Plot #{plot.id} ({plot.name}) pump set to {new_status}.",
            'plot': plot.to_dict(include_latest=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ------------------------------------------------------------------------------
# 2. TELEMETRY & SENSOR TIMESERIES ENDPOINTS
# ------------------------------------------------------------------------------
@api_bp.route('/telemetry/<int:plot_id>', methods=['GET'])
def get_telemetry_series(plot_id):
    """
    Retrieve historical telemetry readings formatted for Chart.js graphs.
    """
    limit = request.args.get('limit', 24, type=int)
    plot = Plot.query.get_or_404(plot_id)

    readings = TelemetryReading.query.filter_by(plot_id=plot_id)\
        .order_by(TelemetryReading.recorded_at.desc())\
        .limit(limit)\
        .all()

    # Reverse to chronological order (oldest to newest) for charts
    readings.reverse()

    timestamps = [r.recorded_at.strftime('%H:%M') for r in readings]
    soil_moisture = [float(r.soil_moisture) for r in readings]
    soil_temp = [float(r.soil_temperature) for r in readings]
    ambient_temp = [float(r.ambient_temperature) for r in readings]
    humidity = [float(r.humidity) for r in readings]
    et0 = [float(r.et0) for r in readings]
    solar_radiation = [float(r.solar_radiation) for r in readings]

    return jsonify({
        'success': True,
        'plot': {
            'id': plot.id,
            'name': plot.name,
            'crop_type': plot.crop_type,
            'target_min': float(plot.target_moisture_min),
            'target_max': float(plot.target_moisture_max)
        },
        'count': len(readings),
        'chart_data': {
            'timestamps': timestamps,
            'soil_moisture': soil_moisture,
            'soil_temp': soil_temp,
            'ambient_temp': ambient_temp,
            'humidity': humidity,
            'et0': et0,
            'solar_radiation': solar_radiation
        },
        'readings': [r.to_dict() for r in readings]
    }), 200


@api_bp.route('/telemetry', methods=['POST'])
def ingest_telemetry():
    """
    Ingest real-time IoT node sensor telemetry and check irrigation thresholds.
    """
    data = request.get_json() or {}
    try:
        plot_id = data.get('plot_id')
        plot = Plot.query.get_or_404(plot_id)

        soil_moisture = float(data.get('soil_moisture', 40.0))
        soil_temp = float(data.get('soil_temperature', 20.0))
        ambient_temp = float(data.get('ambient_temperature', 24.0))
        humidity = float(data.get('humidity', 60.0))
        solar_rad = float(data.get('solar_radiation', 500.0))
        et0 = float(data.get('et0', 3.5))
        battery = float(data.get('battery_level', 99.0))

        # Check automated irrigation logic
        pump_triggered = False
        if plot.pump_status == 'AUTO' and soil_moisture < float(plot.target_moisture_min):
            pump_triggered = True
            plot.last_irrigated_at = datetime.utcnow()

        reading = TelemetryReading(
            plot_id=plot.id,
            recorded_at=datetime.utcnow(),
            soil_moisture=soil_moisture,
            soil_temperature=soil_temp,
            ambient_temperature=ambient_temp,
            humidity=humidity,
            solar_radiation=solar_rad,
            et0=et0,
            battery_level=battery,
            pump_event_triggered=pump_triggered
        )
        db.session.add(reading)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Telemetry reading logged successfully.',
            'pump_event_triggered': pump_triggered,
            'reading': reading.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ------------------------------------------------------------------------------
# 3. FIELD ACTIVITIES & CHEMICAL INPUT LOGS
# ------------------------------------------------------------------------------
@api_bp.route('/activities', methods=['GET'])
def get_activities():
    """Retrieve field activity logs with optional plot filter."""
    plot_id = request.args.get('plot_id', type=int)
    activity_type = request.args.get('type')

    query = FieldActivity.query
    if plot_id:
        query = query.filter_by(plot_id=plot_id)
    if activity_type:
        query = query.filter_by(activity_type=activity_type)

    activities = query.order_by(FieldActivity.activity_date.desc(), FieldActivity.id.desc()).limit(100).all()

    return jsonify({
        'success': True,
        'count': len(activities),
        'activities': [act.to_dict() for act in activities]
    }), 200


@api_bp.route('/activities', methods=['POST'])
def create_activity():
    """
    Log field operation (Fertilizer, Pesticide, Irrigation, Tillage, etc.)
    and automatically record corresponding financial expense.
    """
    data = request.get_json() or {}
    try:
        plot_id = data.get('plot_id')
        plot = Plot.query.get_or_404(plot_id)

        required = ['activity_type', 'activity_date', 'input_name', 'quantity', 'unit', 'operator_name']
        for r in required:
            if not data.get(r):
                return jsonify({'success': False, 'error': f"Field '{r}' is required"}), 400

        act_date = datetime.strptime(data['activity_date'], '%Y-%m-%d').date()
        cost = float(data.get('cost', 0.0))

        activity = FieldActivity(
            plot_id=plot.id,
            activity_type=data['activity_type'],
            activity_date=act_date,
            input_name=data['input_name'],
            quantity=float(data['quantity']),
            unit=data['unit'],
            cost=cost,
            operator_name=data['operator_name'],
            notes=data.get('notes', '')
        )
        db.session.add(activity)

        # Auto-record expense if cost > 0
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
            category = category_mapping.get(data['activity_type'], 'Labor')
            expense = FinancialRecord(
                plot_id=plot.id,
                record_type='EXPENSE',
                category=category,
                amount=cost,
                record_date=act_date,
                description=f"Auto-logged from {data['activity_type']}: {data['input_name']} ({data['quantity']} {data['unit']})"
            )
            db.session.add(expense)

        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Field activity and expense successfully logged.',
            'activity': activity.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ------------------------------------------------------------------------------
# 4. FINANCIALS & YIELD PROFIT CALCULATOR ENDPOINTS
# ------------------------------------------------------------------------------
@api_bp.route('/financials', methods=['GET'])
def get_financials_summary():
    """
    Compute aggregate production cost vs. estimated yield revenue and net margins.
    """
    try:
        plots = Plot.query.all()
        records = FinancialRecord.query.all()

        total_expenses = float(db.session.query(func.coalesce(func.sum(FinancialRecord.amount), 0))\
            .filter(FinancialRecord.record_type == 'EXPENSE').scalar())

        total_realized_revenue = float(db.session.query(func.coalesce(func.sum(FinancialRecord.amount), 0))\
            .filter(FinancialRecord.record_type == 'REVENUE').scalar())

        total_projected_revenue = float(db.session.query(func.coalesce(func.sum(FinancialRecord.amount), 0))\
            .filter(FinancialRecord.record_type == 'PROJECTION').scalar())

        effective_revenue = total_realized_revenue if total_realized_revenue > 0 else total_projected_revenue
        projected_net_profit = effective_revenue - total_expenses
        profit_margin_percent = round((projected_net_profit / effective_revenue * 100), 1) if effective_revenue > 0 else 0.0

        # Expenses broken down by category
        category_breakdown = {}
        cat_queries = db.session.query(FinancialRecord.category, func.sum(FinancialRecord.amount))\
            .filter(FinancialRecord.record_type == 'EXPENSE')\
            .group_by(FinancialRecord.category).all()
        for cat, amt in cat_queries:
            category_breakdown[cat] = float(amt)

        # Plot-by-plot financial comparison
        plot_financials = []
        for p in plots:
            p_exp = float(db.session.query(func.coalesce(func.sum(FinancialRecord.amount), 0))\
                .filter(FinancialRecord.plot_id == p.id, FinancialRecord.record_type == 'EXPENSE').scalar())
            p_proj = float(db.session.query(func.coalesce(func.sum(FinancialRecord.amount), 0))\
                .filter(FinancialRecord.plot_id == p.id, FinancialRecord.record_type.in_(['REVENUE', 'PROJECTION'])).scalar())
            p_profit = p_proj - p_exp
            plot_financials.append({
                'plot_id': p.id,
                'plot_name': p.display_title,
                'zone_name': p.zone_name,
                'crop_type': p.crop_type,
                'area_hectares': float(p.area_hectares),
                'total_expense': p_exp,
                'projected_revenue': p_proj,
                'net_profit': p_profit,
                'cost_per_hectare': round(p_exp / float(p.area_hectares), 2) if float(p.area_hectares) > 0 else 0,
                'profit_per_hectare': round(p_profit / float(p.area_hectares), 2) if float(p.area_hectares) > 0 else 0
            })

        return jsonify({
            'success': True,
            'summary': {
                'total_expenses': total_expenses,
                'total_realized_revenue': total_realized_revenue,
                'total_projected_revenue': total_projected_revenue,
                'effective_revenue': effective_revenue,
                'projected_net_profit': projected_net_profit,
                'profit_margin_percent': profit_margin_percent
            },
            'category_breakdown': category_breakdown,
            'plot_financials': plot_financials,
            'recent_records': [r.to_dict() for r in records[:50]]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/financials', methods=['POST'])
def add_financial_record():
    """Add a manual expense or revenue entry."""
    data = request.get_json() or {}
    try:
        plot_id = data.get('plot_id')
        plot = Plot.query.get_or_404(plot_id)

        rec_date = datetime.strptime(data['record_date'], '%Y-%m-%d').date()

        record = FinancialRecord(
            plot_id=plot.id,
            record_type=data['record_type'],
            category=data['category'],
            amount=float(data['amount']),
            record_date=rec_date,
            description=data['description']
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Financial transaction recorded.',
            'record': record.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ------------------------------------------------------------------------------
# 5. GROQ AI INTEGRATION & ADVISOR ENDPOINTS
# ------------------------------------------------------------------------------
@api_bp.route('/ai/history', methods=['GET'])
def get_ai_history():
    """Retrieve past AI consultations and diagnostic recommendations."""
    consultations = AIConsultation.query.order_by(AIConsultation.created_at.desc()).limit(25).all()
    return jsonify({
        'success': True,
        'count': len(consultations),
        'consultations': [c.to_dict() for c in consultations]
    }), 200


@api_bp.route('/ai/ask', methods=['POST'])
def ask_ai_advisor():
    """
    Process agronomic diagnostic queries via Groq LLaMA-3.3-70b-versatile
    or specialized smart fallback if API key is not yet set.
    """
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    query_type = data.get('query_type', 'GENERAL')
    plot_id = data.get('plot_id')

    if not prompt:
        return jsonify({'success': False, 'error': 'Query prompt is required.'}), 400

    plot = Plot.query.get(plot_id) if plot_id else None
    plot_context = ""
    if plot:
        latest = plot.latest_telemetry
        latest_soil = plot.latest_soil_test
        soil_info = ""
        if latest_soil:
            soil_info = f"""
LABORATORY SOIL BASELINE METRICS:
Soil pH: {latest_soil.ph_level} (Optimal: 6.0 - 7.5)
Available Nitrogen (N): {latest_soil.nitrogen_ppm} ppm (Target: 50 - 80 ppm)
Available Phosphorus (P): {latest_soil.phosphorus_ppm} ppm (Target: 15 - 25 ppm)
Exchangeable Potassium (K): {latest_soil.potassium_ppm} ppm (Target: 120 - 200 ppm)
Electrical Conductivity (EC / Salinity): {latest_soil.electrical_conductivity} dS/m (Warning threshold: > 1.30 dS/m)
Soil Organic Matter: {latest_soil.organic_matter_percent}%
Agronomic Lab Diagnosis: {latest_soil.recommendations}
"""
        plot_context = f"""
FIELD CONTEXT:
Plot Name: {plot.display_title} ({plot.name})
Crop: {plot.crop_type} ({plot.variety})
Growth Stage: {plot.growth_stage}
Soil Type: {plot.soil_type}
Target Moisture: {plot.target_moisture_min}% - {plot.target_moisture_max}%
Latest Sensor Moisture: {latest.soil_moisture if latest else 'N/A'}%
Ambient Temp: {latest.ambient_temperature if latest else 'N/A'}°C
Humidity: {latest.humidity if latest else 'N/A'}%
Reference ET0: {latest.et0 if latest else 'N/A'} mm/day
{soil_info}
"""

    # Import groq service
    try:
        from groq_service import generate_agronomic_advice
        ai_result = generate_agronomic_advice(
            prompt=prompt,
            query_type=query_type,
            plot_context=plot_context,
            api_key=current_app.config.get('GROQ_API_KEY')
        )
    except Exception as e:
        # Fallback response structure
        ai_result = {
            'response': f"### Agronomic Diagnostic Advisory\n\nBased on your observations:\n{prompt}\n\n**Preliminary Recommendation:**\nMaintain balanced soil moisture and monitor symptom progression. Consider laboratory foliar testing if symptoms persist.\n\n*(Note: {str(e)})*",
            'model': 'llama-3.3-70b-versatile',
            'recommendations': [
                "Inspect leaf undersides for fungal spores or mites",
                "Maintain optimal irrigation within crop threshold",
                "Ensure proper field drainage and air circulation"
            ]
        }

    # Save consultation to database
    try:
        consultation = AIConsultation(
            plot_id=plot.id if plot else None,
            query_type=query_type,
            user_prompt=prompt,
            ai_response=ai_result['response'],
            model_used=ai_result.get('model', 'llama-3.3-70b-versatile'),
            actionable_recommendations=ai_result.get('recommendations', [])
        )
        db.session.add(consultation)
        db.session.commit()

        return jsonify({
            'success': True,
            'consultation': consultation.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': True,
            'consultation': {
                'ai_response': ai_result['response'],
                'model_used': ai_result.get('model', 'llama-3.3-70b-versatile'),
                'actionable_recommendations': ai_result.get('recommendations', [])
            },
            'warning': f"Failed to persist consultation to database: {str(e)}"
        }), 200
