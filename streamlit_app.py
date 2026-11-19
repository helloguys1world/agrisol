import os
from datetime import date, datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load local modules
import db
from groq_service import generate_agronomic_advice

load_dotenv()

# ==============================================================================
# STREAMLIT PAGE CONFIGURATION & THEME
# ==============================================================================
st.set_page_config(
    page_title="AgriSense AI - Precision Agriculture",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling Tokens (Forest Green #2D5A27 & Soft Cream #FDFBF7)
st.markdown("""
<style>
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        color: #2D5A27;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        color: #4B5548;
        font-weight: 600;
        font-size: 0.85rem;
    }
    /* Card Container */
    .agri-card {
        background-color: #FFFFFF;
        border: 1px solid #E8E1D5;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(28, 40, 25, 0.04);
    }
    /* Status Badges */
    .badge-optimal {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-low {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-critical {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-saturated {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
with st.sidebar:
    st.markdown("## 🌱 AgriSense AI")
    st.caption("Smart Agriculture Decision Support System")
    st.divider()

    nav_selection = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "🗺️ Field Setup",
            "📋 Field Logs",
            "🤖 Groq AI Advisor",
            "💰 Yield & ROI"
        ],
        index=0
    )

    st.divider()
    st.markdown("### 📡 System Telemetry")
    try:
        engine = db.get_engine()
        st.success("🟢 MySQL: Connected")
    except Exception as e:
        st.error(f"🔴 MySQL: Unreachable ({str(e)})")

    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key and not groq_key.startswith("gsk_your_") and len(groq_key) > 20:
        st.success("⚡ Groq LPU: Ready (LLaMA-3.3-70b)")
    else:
        st.info("⚡ Groq: Academic Engine Mode")

    st.caption("Academic Capstone Project Presentation")


# ==============================================================================
# 1. DASHBOARD VIEW
# ==============================================================================
if nav_selection == "📊 Dashboard":
    st.title("🌾 Agricultural Telemetry Dashboard")
    st.caption("Real-time root-zone sensors, microclimate evapotranspiration, and autonomous pump control.")

    plots = db.get_plots()

    if not plots:
        st.warning("No farm plots found in database. Please head to '🗺️ Field Setup' to add a field.")
    else:
        # Top KPI Summary Cards
        total_area = sum(p['area_hectares'] for p in plots)
        active_pumps = sum(1 for p in plots if p['pump_status'] == 'ON')
        
        valid_moistures = [p['current_moisture'] for p in plots if p['current_moisture'] is not None]
        avg_moisture = (sum(valid_moistures) / len(valid_moistures)) if valid_moistures else 0.0

        valid_et0 = [p['latest_telemetry']['et0'] for p in plots if p['latest_telemetry']]
        avg_et0 = (sum(valid_et0) / len(valid_et0)) if valid_et0 else 0.0

        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        kpi_col1.metric("Total Farmland", f"{total_area:.1f} Ha", f"{len(plots)} Monitored Zones")
        kpi_col2.metric("Avg Soil Moisture", f"{avg_moisture:.1f}%", "Root-Zone VWC")
        kpi_col3.metric("Irrigation Pumps", f"{active_pumps} / {len(plots)} Active", "Closed-Loop")
        kpi_col4.metric("Reference ET₀", f"{avg_et0:.2f} mm/day", "FAO-56 Penman-Monteith")

        st.divider()

        # Section: Plot Cards Grid
        st.subheader("Field Zones & Autonomous Pump Matrix")
        st.caption("Color-coded root-zone moisture progress, microclimate gauges, and live pump state controls.")

        # Display plots in 2 columns
        grid_cols = st.columns(min(len(plots), 2))
        for idx, plot in enumerate(plots):
            col = grid_cols[idx % 2]
            with col:
                with st.container(border=True):
                    # Card Header: Plot Name - Crop Name
                    header_col1, header_col2 = st.columns([3, 1])
                    with header_col1:
                        st.markdown(f"### {plot['display_title']}")
                        st.caption(f"**Variety:** {plot['variety']} &bull; **Zone:** {plot['zone_name']}")
                    with header_col2:
                        status = plot['moisture_health_status']
                        if status == 'OPTIMAL':
                            st.markdown('<span class="badge-optimal">OPTIMAL</span>', unsafe_allow_html=True)
                        elif status == 'LOW_ALERT':
                            st.markdown('<span class="badge-low">LOW ALERT</span>', unsafe_allow_html=True)
                        elif status == 'CRITICAL_DRY':
                            st.markdown('<span class="badge-critical">CRITICAL DRY</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="badge-saturated">SATURATED</span>', unsafe_allow_html=True)

                    # Subtext Details
                    st.markdown(f"📏 **Area:** {plot['area_hectares']} Ha &bull; 🏔️ **Soil:** {plot['soil_type']} &bull; ⏱️ **Stage:** {plot['growth_stage']}")

                    # Soil Moisture Meter
                    tel = plot['latest_telemetry']
                    if tel:
                        m_val = float(tel['soil_moisture'])
                        min_m = plot['target_moisture_min']
                        max_m = plot['target_moisture_max']
                        st.markdown(f"**Root-Zone Moisture:** `{m_val:.1f}%` *(Target: {min_m:.0f}% – {max_m:.0f}%)*")
                        progress_normalized = max(0.0, min(1.0, m_val / 100.0))
                        st.progress(progress_normalized)
                    else:
                        st.info("No sensor readings logged for this zone yet.")

                    # Microclimate Telemetry Gauges
                    if tel:
                        g1, g2, g3, g4 = st.columns(4)
                        g1.metric("Soil Temp", f"{tel['soil_temperature']:.1f}°C")
                        g2.metric("Air Temp", f"{tel['ambient_temperature']:.1f}°C")
                        g3.metric("Humidity", f"{tel['humidity']:.0f}%")
                        g4.metric("ET₀ Rate", f"{tel['et0']:.1f} mm")

                    # Soil Baseline N-P-K & EC Metrics Card
                    soil = plot['latest_soil_test']
                    if soil:
                        st.markdown("---")
                        st.markdown("🧪 **Laboratory Soil Baseline Metrics**")
                        s_col1, s_col2, s_col3 = st.columns([1, 2, 1])

                        # pH Box
                        ph = soil['ph_level']
                        ph_color = "#2D5A27" if (6.0 <= ph <= 7.5) else "#D97706"
                        s_col1.markdown(f"""
                        <div style="background-color: #F4EFE6; padding: 10px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 0.75rem; color: #4B5548; font-weight: 600;">pH Level</div>
                            <div style="font-size: 1.25rem; font-weight: 800; color: {ph_color};">{ph:.1f}</div>
                            <div style="font-size: 0.65rem; color: #4B5548;">Target: 6.0–7.5</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Individual N-P-K Color-Coded Box
                        n_val = soil['nitrogen_ppm']
                        p_val = soil['phosphorus_ppm']
                        k_val = soil['potassium_ppm']
                        n_color = "#2D5A27" if (50 <= n_val <= 80) else "#D97706"
                        p_color = "#2D5A27" if (15 <= p_val <= 25) else "#D97706"
                        k_color = "#2D5A27" if (120 <= k_val <= 200) else "#D97706"

                        s_col2.markdown(f"""
                        <div style="background-color: #F4EFE6; padding: 10px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 0.75rem; color: #4B5548; font-weight: 600;">N - P - K (ppm)</div>
                            <div style="font-size: 1.15rem; font-weight: 800; letter-spacing: 1px;">
                                <span style="color: {n_color};" title="Nitrogen">{n_val:.0f}</span>
                                <span style="color: #4B5548; font-weight: 400;"> - </span>
                                <span style="color: {p_color};" title="Phosphorus">{p_val:.0f}</span>
                                <span style="color: #4B5548; font-weight: 400;"> - </span>
                                <span style="color: {k_color};" title="Potassium">{k_val:.0f}</span>
                            </div>
                            <div style="font-size: 0.65rem; color: #4B5548;">Target: 50–80 | 15–25 | 120–200 ppm</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Salinity EC Box
                        ec = soil['electrical_conductivity']
                        ec_color = "#DC2626" if ec > 1.30 else "#2D5A27"
                        ec_label = "Warning >1.30" if ec > 1.30 else "Optimal ≤1.30"
                        s_col3.markdown(f"""
                        <div style="background-color: #F4EFE6; padding: 10px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 0.75rem; color: #4B5548; font-weight: 600;">Salinity EC</div>
                            <div style="font-size: 1.15rem; font-weight: 800; color: {ec_color};">{ec:.2f} <span style="font-size:0.7rem; font-weight: normal;">dS/m</span></div>
                            <div style="font-size: 0.65rem; color: {ec_color}; font-weight: 600;">{ec_label}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Interactive Pump Controls
                    st.markdown("---")
                    p_col1, p_col2 = st.columns([2, 3])
                    with p_col1:
                        st.markdown(f"**🚰 Pump Mode:** `{plot['pump_status']}`")
                        if plot['last_irrigated_at']:
                            st.caption(f"Last Run: {plot['last_irrigated_at'][11:16]}")
                    with p_col2:
                        btn_auto, btn_on, btn_off = st.columns(3)
                        if btn_auto.button("AUTO", key=f"auto_{plot['id']}", use_container_width=True, type="primary" if plot['pump_status'] == 'AUTO' else "secondary"):
                            db.update_pump_status(plot['id'], 'AUTO')
                            st.rerun()
                        if btn_on.button("ON", key=f"on_{plot['id']}", use_container_width=True, type="primary" if plot['pump_status'] == 'ON' else "secondary"):
                            db.update_pump_status(plot['id'], 'ON')
                            st.rerun()
                        if btn_off.button("OFF", key=f"off_{plot['id']}", use_container_width=True, type="primary" if plot['pump_status'] == 'OFF' else "secondary"):
                            db.update_pump_status(plot['id'], 'OFF')
                            st.rerun()

        st.divider()

        # Section: Interactive Timeseries Graphs
        st.subheader("📈 Environmental Telemetry Timeseries")
        chart_plot = st.selectbox(
            "Select Field Zone for Timeseries Analysis:",
            options=plots,
            format_func=lambda p: f"{p['display_title']} ({p['zone_name']})"
        )

        if chart_plot:
            df_tel = db.get_telemetry_series(chart_plot['id'], limit=24)
            if not df_tel.empty:
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.markdown(f"#### Soil Moisture Trajectory (%) &bull; Target: {chart_plot['target_moisture_min']}% – {chart_plot['target_moisture_max']}%")
                    # Prepare chart dataframe with thresholds
                    df_chart_m = df_tel[['Time', 'soil_moisture']].copy().set_index('Time')
                    df_chart_m['Target Min'] = chart_plot['target_moisture_min']
                    df_chart_m['Target Max'] = chart_plot['target_moisture_max']
                    st.line_chart(df_chart_m, color=["#2D5A27", "#E11D48", "#0284C7"])

                with t_col2:
                    st.markdown("#### Microclimate & Reference ET₀ Demand (mm/day)")
                    df_chart_c = df_tel[['Time', 'ambient_temperature', 'humidity', 'et0']].copy().set_index('Time')
                    st.line_chart(df_chart_c, color=["#D97706", "#3B82F6", "#059669"])
            else:
                st.info("No 24-hour historical telemetry found for this zone.")


# ==============================================================================
# 2. FIELD SETUP VIEW (WITH CASCADING DELETE)
# ==============================================================================
elif nav_selection == "🗺️ Field Setup":
    st.title("🗺️ Field Setup & Agronomic Baselines")
    st.caption("Onboard new farm plots, manage crop parameters, and configure laboratory soil baseline chemistry.")

    # Form: Add New Plot
    with st.expander("➕ Register New Farm Plot", expanded=False):
        with st.form("new_plot_form"):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                p_name = st.text_input("Plot Name / Identifier *", placeholder="e.g. Plot D - West Orchard")
                p_crop = st.text_input("Crop Type *", placeholder="e.g. Winter Wheat, Tomato, Maize")
                p_variety = st.text_input("Cultivar / Variety", value="Commercial F1")
                p_area = st.number_input("Area Coverage (Hectares) *", min_value=0.1, value=2.5, step=0.1)
                p_soil = st.selectbox("Soil Texture *", ["Sandy Loam", "Clay Loam", "Silt Loam", "Loamy Sand", "Clay"])

            with f_col2:
                p_planting = st.date_input("Planting Date *", value=date.today())
                p_harvest = st.date_input("Expected Harvest Date", value=None)
                p_stage = st.selectbox("Current Growth Stage", ["Germination", "Vegetative", "Flowering", "Fruiting", "Maturation", "Harvest Ready"], index=1)
                min_moist = st.number_input("Target Moisture Min (%)", value=30.0, step=1.0)
                max_moist = st.number_input("Target Moisture Max (%)", value=65.0, step=1.0)

            st.markdown("#### Laboratory Soil Chemistry Baseline (Optional)")
            s1, s2, s3, s4, s5, s6 = st.columns(6)
            b_ph = s1.number_input("pH Level", value=6.8, step=0.1)
            b_n = s2.number_input("N (ppm)", value=45.0, step=1.0)
            b_p = s3.number_input("P (ppm)", value=20.0, step=1.0)
            b_k = s4.number_input("K (ppm)", value=185.0, step=1.0)
            b_ec = s5.number_input("EC (dS/m)", value=1.05, step=0.05)
            b_om = s6.number_input("Org Matter (%)", value=2.2, step=0.1)

            submit_plot = st.form_submit_button("Register Field Plot", type="primary", use_container_width=True)
            if submit_plot:
                if not p_name.strip() or not p_crop.strip():
                    st.error("Please provide both Plot Name and Crop Type.")
                else:
                    new_id = db.create_plot(
                        name=p_name.strip(),
                        crop_type=p_crop.strip(),
                        variety=p_variety.strip(),
                        area_ha=float(p_area),
                        soil_type=p_soil,
                        planting_date=str(p_planting),
                        harvest_date=str(p_harvest) if p_harvest else None,
                        growth_stage=p_stage,
                        min_m=float(min_moist),
                        max_m=float(max_moist),
                        ph=float(b_ph),
                        n_ppm=float(b_n),
                        p_ppm=float(b_p),
                        k_ppm=float(b_k),
                        ec=float(b_ec),
                        om=float(b_om)
                    )
                    st.success(f"Plot '{p_name}' successfully onboarded with ID #{new_id}!")
                    st.rerun()

    st.divider()

    # Existing Fields List with Cascading Delete
    st.subheader("Registered Field Zones")
    plots = db.get_plots()

    if not plots:
        st.info("No field plots currently registered.")
    else:
        for plot in plots:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.markdown(f"### {plot['display_title']}")
                    st.caption(f"**Zone:** {plot['zone_name']} &bull; **Cultivar:** {plot['variety']}")
                    st.markdown(f"📏 **Area:** {plot['area_hectares']} Ha &bull; 🏔️ **Soil:** {plot['soil_type']}")
                    st.markdown(f"🌱 **Planted:** {plot['planting_date']} &bull; ⏱️ **Stage:** {plot['growth_stage']}")

                with c2:
                    st.markdown("**Soil Baseline Analysis:**")
                    soil = plot['latest_soil_test']
                    if soil:
                        st.markdown(f"- **pH:** `{soil['ph_level']:.1f}`")
                        st.markdown(f"- **N-P-K:** `{soil['nitrogen_ppm']:.0f} - {soil['phosphorus_ppm']:.0f} - {soil['potassium_ppm']:.0f} ppm`")
                        st.markdown(f"- **Salinity EC:** `{soil['electrical_conductivity']:.2f} dS/m`")
                        if soil['recommendations']:
                            st.caption(f"💡 {soil['recommendations']}")
                    else:
                        st.caption("No soil test on file.")

                with c3:
                    st.markdown("**Field Management:**")
                    st.markdown(f"Target Moisture: `{plot['target_moisture_min']}% – {plot['target_moisture_max']}%`")
                    st.markdown(f"Pump Status: `{plot['pump_status']}`")

                    # Cascading Delete Confirmation Box
                    st.markdown("---")
                    del_confirm = st.checkbox(
                        "Confirm cascading deletion",
                        key=f"del_chk_{plot['id']}",
                        help="Deletes this plot and cascades to delete all related telemetry, field logs, financial records, and AI consultations."
                    )
                    if st.button("🗑️ Delete Field Plot", key=f"del_btn_{plot['id']}", type="secondary", disabled=not del_confirm):
                        db.delete_plot(plot['id'])
                        st.success(f"Plot '{plot['display_title']}' and all child records deleted permanently.")
                        st.rerun()


# ==============================================================================
# 3. FIELD LOGS VIEW (NO OPERATOR COLUMN)
# ==============================================================================
elif nav_selection == "📋 Field Logs":
    st.title("📋 Agricultural Input & Operation Logs")
    st.caption("Log daily fertilizer top-dressing, biopesticide sprays, irrigation runs, and field operations.")

    plots = db.get_plots()

    # Form: Add New Activity Log
    with st.expander("➕ Log Daily Farm Input or Activity", expanded=False):
        if not plots:
            st.warning("Please onboard a field plot first before logging inputs.")
        else:
            with st.form("new_log_form"):
                l_col1, l_col2 = st.columns(2)
                with l_col1:
                    sel_plot = st.selectbox(
                        "Target Field Zone *",
                        options=plots,
                        format_func=lambda p: f"{p['display_title']} ({p['zone_name']})"
                    )
                    act_type = st.selectbox(
                        "Activity Type *",
                        ["Fertilization", "Pesticide Application", "Irrigation", "Weed Control", "Pruning", "Soil Tillage", "Harvesting"]
                    )
                    act_date = st.date_input("Date Applied *", value=date.today())

                with l_col2:
                    input_name = st.text_input("Input / Formulation Name *", placeholder="e.g. Granular Urea (46-0-0), DAP, Neem Biopesticide")
                    q_col1, q_col2, q_col3 = st.columns(3)
                    qty = q_col1.number_input("Quantity *", min_value=0.1, value=50.0, step=1.0)
                    unit = q_col2.selectbox("Unit *", ["kg", "liters", "cubic meters", "bags", "hours"])
                    cost = q_col3.number_input("Total Cost ($)", min_value=0.0, value=45.0, step=5.0)

                notes = st.text_area("Agronomic Notes / Observations", placeholder="Application conditions, sprayer pressure, leaf wetness...")
                
                submit_log = st.form_submit_button("Save Log Entry", type="primary", use_container_width=True)
                if submit_log:
                    if not input_name.strip():
                        st.error("Please specify the Input / Formulation Name.")
                    else:
                        db.create_activity(
                            plot_id=sel_plot['id'],
                            act_type=act_type,
                            act_date=str(act_date),
                            input_name=input_name.strip(),
                            quantity=float(qty),
                            unit=unit,
                            cost=float(cost),
                            notes=notes.strip()
                        )
                        st.success(f"Logged {act_type} ({input_name}) for {sel_plot['display_title']}! Auto-synchronized to financials.")
                        st.rerun()

    st.divider()

    # Filter Bar
    st.subheader("Field Operations Ledger")
    f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
    with f_col1:
        plot_filter_options = [{"id": None, "label": "All Field Zones"}] + [{"id": p['id'], "label": p['display_title']} for p in plots]
        selected_plot_filter = st.selectbox(
            "Filter by Zone:",
            options=plot_filter_options,
            format_func=lambda x: x["label"]
        )
    with f_col2:
        selected_type_filter = st.selectbox(
            "Filter by Type:",
            ["All", "Fertilization", "Pesticide Application", "Irrigation", "Weed Control", "Pruning", "Soil Tillage", "Harvesting"]
        )

    # Retrieve DataFrame (Without Operator column)
    df_activities = db.get_activities_df(
        plot_id=selected_plot_filter["id"],
        activity_type=selected_type_filter
    )

    with f_col3:
        st.metric("Total Operations Found", len(df_activities))

    if df_activities.empty:
        st.info("No field operations recorded matching the selected filters.")
    else:
        st.dataframe(
            df_activities,
            use_container_width=True,
            hide_index=True
        )


# ==============================================================================
# 4. GROQ AI ADVISOR VIEW
# ==============================================================================
elif nav_selection == "🤖 Groq AI Advisor":
    st.title("🤖 Groq AI Agronomist & Diagnostic Center")
    st.caption("Powered by Groq Cloud Language Processing Units (LPUs) running LLaMA-3.3-70b-versatile.")

    plots = db.get_plots()

    if not plots:
        st.warning("Please configure at least one field plot in '🗺️ Field Setup'.")
    else:
        # Field Selector & Query Type
        a_col1, a_col2 = st.columns(2)
        with a_col1:
            sel_plot = st.selectbox(
                "Select Field Zone Context *",
                options=plots,
                format_func=lambda p: f"{p['display_title']} ({p['growth_stage']})"
            )
        with a_col2:
            query_type = st.selectbox(
                "Diagnostic Category *",
                [
                    "DISEASE_DIAGNOSIS",
                    "IRRIGATION_ADVICE",
                    "NUTRIENT_DEFICIENCY",
                    "YIELD_PREDICTION",
                    "GENERAL"
                ],
                format_func=lambda x: {
                    "DISEASE_DIAGNOSIS": "🍅 Crop Disease & Pathogen Diagnosis",
                    "IRRIGATION_ADVICE": "💧 Precision Irrigation & ET₀ Advisory",
                    "NUTRIENT_DEFICIENCY": "🧪 Soil & N-P-K Nutrient Deficiency",
                    "YIELD_PREDICTION": "📈 Yield & Harvest Strategy",
                    "GENERAL": "🌾 General Agronomic Guidance"
                }.get(x, x)
            )

        # Show Live Context Being Injected
        tel = sel_plot['latest_telemetry']
        soil = sel_plot['latest_soil_test']
        with st.expander("🔍 Inspect Live Field Telemetry & Soil Baselines Fed to LLM", expanded=False):
            st.markdown(f"**Zone:** `{sel_plot['display_title']}` &bull; **Crop:** `{sel_plot['crop_type']}` (`{sel_plot['variety']}`) &bull; **Soil:** `{sel_plot['soil_type']}`")
            if tel:
                st.markdown(f"- Moisture: `{tel['soil_moisture']}%` *(Opt: {sel_plot['target_moisture_min']}% - {sel_plot['target_moisture_max']}%)*")
                st.markdown(f"- Temperature: Air `{tel['ambient_temperature']}°C` | Soil `{tel['soil_temperature']}°C`")
                st.markdown(f"- Microclimate: Humidity `{tel['humidity']}%` | Reference ET₀ `{tel['et0']} mm/day`")
            if soil:
                st.markdown(f"- Soil Chemistry: pH `{soil['ph_level']}` | N-P-K `{soil['nitrogen_ppm']} - {soil['phosphorus_ppm']} - {soil['potassium_ppm']} ppm` | Salinity EC `{soil['electrical_conductivity']} dS/m`")
                if soil['recommendations']:
                    st.markdown(f"- Lab Baseline Note: *{soil['recommendations']}*")

        # Preset Academic Prompts
        st.markdown("**Quick Preset Academic Inquiries:**")
        chip1, chip2, chip3, chip4 = st.columns(4)
        preset_prompt = ""
        if chip1.button("🍅 Early Blight Diagnosis", use_container_width=True):
            preset_prompt = "Tomato lower leaves exhibit concentric brown target rings with yellow chlorotic margins. Lesions spreading across lower stems."
        if chip2.button("🌾 Wheat Irrigation Timing", use_container_width=True):
            preset_prompt = "Winter wheat soil moisture is dipping to 36.2% approaching min 35% threshold. Ambient temp is 21°C and ET0 is 1.1 mm/day. Should automated pump run at night or at dawn?"
        if chip3.button("🌽 Corn Phosphorus Fixation", use_container_width=True):
            preset_prompt = "Sweet corn lower leaves show purple pigmentation along margins and stunted vigor. Soil test shows available phosphorus at 11 ppm with alkaline pH 7.2."
        if chip4.button("🧂 Salinity Flush Protocol", use_container_width=True):
            preset_prompt = "Greenhouse soil test shows electrical conductivity EC at 1.45 dS/m exceeding the 1.30 threshold. Provide leaching fraction and nutrient adjustments."

        # User Prompt Text Area
        default_val = preset_prompt if preset_prompt else "Describe crop foliage discoloration, lesion patterns, insect pressure, or irrigation question..."
        user_query = st.text_area("Farmer Observations & Symptoms *", value=preset_prompt if preset_prompt else "", placeholder=default_val, height=120)

        if st.button("🚀 Run Agronomic Diagnostic Analysis", type="primary"):
            if not user_query.strip():
                st.error("Please enter a question or symptom description.")
            else:
                with st.spinner("Analyzing microclimate telemetry and generating clinical prescription..."):
                    # Assemble full context string
                    context_str = f"""
FIELD CONTEXT:
Plot Name: {sel_plot['display_title']} ({sel_plot['name']})
Crop: {sel_plot['crop_type']} ({sel_plot['variety']})
Growth Stage: {sel_plot['growth_stage']}
Soil Type: {sel_plot['soil_type']}
Target Moisture Bounds: {sel_plot['target_moisture_min']}% - {sel_plot['target_moisture_max']}%
Latest Sensor Moisture: {tel['soil_moisture'] if tel else 'N/A'}%
Ambient Temp: {tel['ambient_temperature'] if tel else 'N/A'}°C
Humidity: {tel['humidity'] if tel else 'N/A'}%
Reference ET0: {tel['et0'] if tel else 'N/A'} mm/day
"""
                    if soil:
                        context_str += f"""
LABORATORY SOIL BASELINE METRICS:
Soil pH: {soil['ph_level']} (Optimal: 6.0 - 7.5)
Available Nitrogen (N): {soil['nitrogen_ppm']} ppm (Target: 50 - 80 ppm)
Available Phosphorus (P): {soil['phosphorus_ppm']} ppm (Target: 15 - 25 ppm)
Exchangeable Potassium (K): {soil['potassium_ppm']} ppm (Target: 120 - 200 ppm)
Electrical Conductivity (EC / Salinity): {soil['electrical_conductivity']} dS/m (Warning threshold: > 1.30 dS/m)
Soil Organic Matter: {soil['organic_matter_percent']}%
Agronomic Lab Diagnosis: {soil['recommendations']}
"""
                    # Query Groq
                    res = generate_agronomic_advice(
                        prompt=user_query.strip(),
                        query_type=query_type,
                        plot_context=context_str,
                        api_key=os.getenv("GROQ_API_KEY")
                    )

                    # Persist consultation to MySQL
                    db.save_ai_consultation(
                        plot_id=sel_plot['id'],
                        query_type=query_type,
                        prompt=user_query.strip(),
                        response=res['response'],
                        model=res.get('model', 'llama-3.3-70b-versatile'),
                        recs=res.get('recommendations', [])
                    )

                    # Display Response
                    st.success("Prescription generated successfully!")
                    st.markdown(f"**Inference Model:** `{res.get('model', 'llama-3.3-70b-versatile')}`")
                    st.markdown(res['response'])

                    # Action Items Checklist
                    recs = res.get('recommendations', [])
                    if recs:
                        st.markdown("#### ✅ High-Priority Action Checklist")
                        for idx, item in enumerate(recs):
                            st.checkbox(item, key=f"rec_chk_{idx}")

        st.divider()

        # Historical Consultations
        with st.expander("📜 Recent Diagnostic Consultation History", expanded=False):
            df_hist = db.get_ai_history(limit=10)
            if df_hist.empty:
                st.info("No past consultations recorded.")
            else:
                for _, row in df_hist.iterrows():
                    st.markdown(f"**{row['plot_label']}** &bull; `{row['query_type']}` &bull; *{row['created_at']}*")
                    st.caption(f"Q: \"{row['user_prompt']}\"")
                    st.markdown("---")


# ==============================================================================
# 5. YIELD & ROI VIEW
# ==============================================================================
elif nav_selection == "💰 Yield & ROI":
    st.title("💰 Yield Forecast & Production Economics")
    st.caption("Calculate cost of production, evaluate harvest price scenarios, and track farm net profit margins.")

    fin_data = db.get_financials_summary()

    # Financial KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Production Cost", f"${fin_data['total_expenses']:,.2f}", "Seeds, Nutrients, Labor")
    k2.metric("Projected Revenue", f"${fin_data['effective_revenue']:,.2f}", "Estimated Harvest")
    k3.metric("Projected Net Profit", f"${fin_data['net_profit']:,.2f}", f"{fin_data['margin_percent']:.1f}% Net Margin")
    
    plots = db.get_plots()
    total_area = sum(p['area_hectares'] for p in plots)
    avg_cost_ha = (fin_data['total_expenses'] / total_area) if total_area > 0 else 0.0
    k4.metric("Avg Cost / Hectare", f"${avg_cost_ha:,.2f} / Ha", "Input Intensity")

    st.divider()

    # Interactive Yield & Price Scenario Calculator
    st.subheader("🧮 Interactive Harvest Yield & Price Sensitivity Calculator")
    st.caption("Simulate commodity market fluctuations and harvest volumes to project returns.")

    if plots:
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            target_plot = st.selectbox(
                "Target Field Zone",
                options=plots,
                format_func=lambda p: f"{p['display_title']} ({p['area_hectares']} Ha)"
            )
        with sc2:
            default_yield = 6000 if "tomato" in target_plot['crop_type'].lower() else (3800 if "wheat" in target_plot['crop_type'].lower() else 5200)
            sim_yield = st.number_input("Expected Yield (kg / Ha)", value=default_yield, step=100)
        with sc3:
            default_price = 0.50 if "tomato" in target_plot['crop_type'].lower() else (0.48 if "wheat" in target_plot['crop_type'].lower() else 0.25)
            sim_price = st.number_input("Market Selling Price ($ / kg)", value=default_price, step=0.05, format="%.2f")
        with sc4:
            default_cost = 450.0 if "tomato" in target_plot['crop_type'].lower() else (320.0 if "wheat" in target_plot['crop_type'].lower() else 360.0)
            sim_cost = st.number_input("Production Cost ($ / Ha)", value=default_cost, step=20.0)

        # Simulation output
        area = target_plot['area_hectares']
        sim_total_kg = area * sim_yield
        sim_gross_rev = sim_total_kg * sim_price
        sim_total_exp = area * sim_cost
        sim_net = sim_gross_rev - sim_total_exp
        sim_roi = (sim_net / sim_total_exp * 100) if sim_total_exp > 0 else 0.0

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Simulated Harvest", f"{sim_total_kg:,.0f} kg")
        r2.metric("Simulated Gross Revenue", f"${sim_gross_rev:,.2f}")
        r3.metric("Simulated Total Cost", f"${sim_total_exp:,.2f}")
        r4.metric("Projected Net Profit", f"${sim_net:,.2f}", f"{sim_roi:.1f}% ROI")

    st.divider()

    # Economic Performance Table
    st.subheader("Field Zone Economic Performance")
    if not fin_data['plot_financials_df'].empty:
        st.dataframe(
            fin_data['plot_financials_df'],
            use_container_width=True,
            hide_index=True
        )

    # Cost Breakdown by Category
    if not fin_data['category_df'].empty:
        st.subheader("Production Cost Breakdown by Category")
        c_chart, c_table = st.columns([2, 1])
        with c_chart:
            st.bar_chart(
                fin_data['category_df'].set_index('Category'),
                color="#2D5A27"
            )
        with c_table:
            st.dataframe(fin_data['category_df'], hide_index=True, use_container_width=True)

    st.divider()

    # Add Transaction Form & Ledger
    st.subheader("Financial Transactions Ledger")
    with st.expander("➕ Record Financial Transaction", expanded=False):
        if plots:
            with st.form("new_finance_form"):
                fc1, fc2, fc3 = st.columns(3)
                f_plot = fc1.selectbox("Field Zone *", options=plots, format_func=lambda p: p['display_title'])
                f_type = fc2.selectbox("Record Type *", ["EXPENSE", "REVENUE", "PROJECTION"])
                f_cat = fc3.selectbox(
                    "Category *",
                    [
                        "Seeds & Seedlings",
                        "Fertilizer & Nutrients",
                        "Pesticides & Chemicals",
                        "Irrigation & Utilities",
                        "Machinery & Fuel",
                        "Labor",
                        "Harvest & Storage",
                        "Crop Sales",
                        "Projected Yield Revenue"
                    ]
                )
                fc4, fc5 = st.columns(2)
                f_amt = fc4.number_input("Amount ($) *", min_value=1.0, value=150.0, step=10.0)
                f_date = fc5.date_input("Transaction Date *", value=date.today())
                f_desc = st.text_input("Memo / Description *", placeholder="e.g. Certified Seed stock purchase")

                if st.form_submit_button("Save Transaction", type="primary"):
                    if not f_desc.strip():
                        st.error("Please enter a description.")
                    else:
                        db.create_financial_record(
                            plot_id=f_plot['id'],
                            rec_type=f_type,
                            category=f_cat,
                            amount=float(f_amt),
                            rec_date=str(f_date),
                            description=f_desc.strip()
                        )
                        st.success("Financial record logged successfully!")
                        st.rerun()

    if not fin_data['transactions_df'].empty:
        st.dataframe(fin_data['transactions_df'], use_container_width=True, hide_index=True)
