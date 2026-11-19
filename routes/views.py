from flask import Blueprint, render_template
from models import Plot, FieldActivity, FinancialRecord, AIConsultation

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def dashboard_view():
    """Main Dashboard with IoT telemetry, field grid, and pump controls."""
    plots = Plot.query.all()
    return render_template('dashboard.html', plots=plots, active_page='dashboard')

@views_bp.route('/logs')
def logs_view():
    """Field activity logs, chemical inputs, fertilizers, and operations."""
    plots = Plot.query.all()
    activities = FieldActivity.query.order_by(FieldActivity.activity_date.desc(), FieldActivity.id.desc()).limit(100).all()
    return render_template('logs.html', plots=plots, activities=activities, active_page='logs')

@views_bp.route('/advisor')
def advisor_view():
    """Groq LLaMA-3.3-70b AI Agricultural Diagnostic Assistant."""
    plots = Plot.query.all()
    history = AIConsultation.query.order_by(AIConsultation.created_at.desc()).limit(15).all()
    return render_template('ai_advisor.html', plots=plots, history=history, active_page='advisor')

@views_bp.route('/financials')
def financials_view():
    """Yield & Cost Calculator, financial tracking, and ROI analysis."""
    plots = Plot.query.all()
    records = FinancialRecord.query.order_by(FinancialRecord.record_date.desc()).all()
    return render_template('financials.html', plots=plots, records=records, active_page='financials')

@views_bp.route('/fields')
def fields_view():
    """Field setup, crop onboarding, and soil baseline management."""
    plots = Plot.query.all()
    return render_template('fields.html', plots=plots, active_page='fields')
