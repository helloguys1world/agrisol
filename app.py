import os
from flask import Flask, jsonify
from config import Config
from models import db
from routes.api import api_bp
from routes.views import views_bp

# Try importing flask_cors, or fallback to native CORS headers
try:
    from flask_cors import CORS
    has_flask_cors = True
except ImportError:
    has_flask_cors = False

def create_app(config_class=Config):
    """Application factory for Smart Agriculture Decision Support System."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable Cross-Origin Resource Sharing
    if has_flask_cors:
        CORS(app)
    else:
        @app.after_request
        def add_cors_headers(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
            return response

    # Initialize SQLAlchemy ORM
    db.init_app(app)

    # Register modular blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    # Health check route
    @app.route('/api/health')
    def health_check():
        db_status = "connected"
        try:
            # Simple query to verify database connection
            db.session.execute(db.text("SELECT 1"))
        except Exception as e:
            db_status = f"unreachable ({str(e)})"

        return jsonify({
            'status': 'online',
            'system': 'Smart Agriculture Decision Support System',
            'version': '1.0.0',
            'database': db_status,
            'groq_configured': bool(app.config.get('GROQ_API_KEY'))
        }), 200

    # Custom Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'success': False, 'error': 'Endpoint or resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    # CLI Command to initialize database tables directly from models
    @app.cli.command("init-db")
    def init_db():
        """Create database tables from SQLAlchemy models."""
        with app.app_context():
            db.create_all()
            sync_distinct_soil_baselines()
            print("Successfully verified/created database tables and synchronized soil baselines.")

    # One-time startup baseline synchronizer
    @app.before_request
    def ensure_baselines_synced():
        if not getattr(app, '_baselines_synced', False):
            sync_distinct_soil_baselines()
            app._baselines_synced = True

    return app


def sync_distinct_soil_baselines():
    """
    Ensures default plots 1, 2, 3 have distinct, realistic agronomic soil test baselines:
    - Plot A: pH 6.8, N 32 (deficient), P 18, K 195, EC 0.85
    - Plot B: pH 6.5, N 56, P 24, K 210, EC 1.45 (salinity alert)
    - Plot C: pH 7.2, N 48, P 11 (deficient), K 185, EC 1.05
    """
    try:
        from datetime import date
        from models import Plot, SoilTest

        distinct_baselines = {
            1: {
                'crop_type': 'Winter Wheat',
                'ph_level': 6.80,
                'nitrogen_ppm': 32.00,
                'phosphorus_ppm': 18.00,
                'potassium_ppm': 195.00,
                'electrical_conductivity': 0.85,
                'organic_matter_percent': 1.80,
                'recommendations': 'Nitrogen-deficient sandy loam (N=32 ppm is below 50-80 target). Top-dress with Urea (46% N) at 60 kg/ha before next irrigation.'
            },
            2: {
                'crop_type': 'Roma Tomatoes',
                'ph_level': 6.50,
                'nitrogen_ppm': 56.00,
                'phosphorus_ppm': 24.00,
                'potassium_ppm': 210.00,
                'electrical_conductivity': 1.45,
                'organic_matter_percent': 3.20,
                'recommendations': 'Elevated greenhouse salinity alert (EC=1.45 dS/m exceeds 1.30 threshold). High potassium (210 ppm). Execute fresh water leaching fraction (15% excess) to flush root-zone salts and pause fertilizer salts.'
            },
            3: {
                'crop_type': 'Sweet Corn',
                'ph_level': 7.20,
                'nitrogen_ppm': 48.00,
                'phosphorus_ppm': 11.00,
                'potassium_ppm': 185.00,
                'electrical_conductivity': 1.05,
                'organic_matter_percent': 2.40,
                'recommendations': 'Phosphorus-deficient silt loam (P=11 ppm is below 15-25 target). Fixation risk at pH 7.2. Apply banded DAP (18-46-0) at 75 kg/ha targeted near root zone.'
            }
        }

        for plot_id, vals in distinct_baselines.items():
            plot = Plot.query.get(plot_id)
            if plot:
                if plot_id == 3 and plot.crop_type != 'Sweet Corn':
                    plot.crop_type = 'Sweet Corn'

                soil = plot.latest_soil_test
                if soil:
                    soil.ph_level = vals['ph_level']
                    soil.nitrogen_ppm = vals['nitrogen_ppm']
                    soil.phosphorus_ppm = vals['phosphorus_ppm']
                    soil.potassium_ppm = vals['potassium_ppm']
                    soil.electrical_conductivity = vals['electrical_conductivity']
                    soil.organic_matter_percent = vals['organic_matter_percent']
                    soil.recommendations = vals['recommendations']
                else:
                    new_soil = SoilTest(
                        plot_id=plot.id,
                        test_date=date.today(),
                        ph_level=vals['ph_level'],
                        nitrogen_ppm=vals['nitrogen_ppm'],
                        phosphorus_ppm=vals['phosphorus_ppm'],
                        potassium_ppm=vals['potassium_ppm'],
                        electrical_conductivity=vals['electrical_conductivity'],
                        organic_matter_percent=vals['organic_matter_percent'],
                        recommendations=vals['recommendations']
                    )
                    db.session.add(new_soil)

        db.session.commit()
    except Exception:
        db.session.rollback()

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print("=" * 70)
    print("  SMART AGRICULTURE DECISION SUPPORT SYSTEM")
    print(f"  Running locally at: http://127.0.0.1:{port}")
    print("  Database Target: MySQL (smart_agriculture)")
    print("=" * 70)
    app.run(host='0.0.0.0', port=port, debug=True)
