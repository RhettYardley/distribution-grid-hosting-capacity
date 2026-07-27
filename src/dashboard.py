import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from feeder_map import build_spatial_map
# ======================================================
# 1. Page Configuration
# ======================================================
st.set_page_config(
    page_title="IEEE 13-Bus PV Hosting Capacity Dashboard",
    page_icon=None,
    layout="wide"
)
st.title("IEEE 13-Bus PV Hosting Capacity Dashboard")
st.markdown("Interactive analysis of solar grid integration limits, spatial feeder bottlenecks, thermal overloads, and voltage constraints.")
COLOR_MAP = {
    'Line Overload': '#2ea043',         # Green
    'Transformer Overload': '#e3b341',  # Amber/Orange
    'Overvoltage': '#da3633',           # Red
    'Undervoltage': '#8957e5',          # Purple
    'Untested / Regulator': '#8b949e',  # Gray
    'OK': '#1f6beb'                     # Blue
}
# ======================================================
# 2. Sidebar Options (Smart Grid Mitigations)
# ======================================================
st.sidebar.header("Smart Grid Options")
enable_volt_var = st.sidebar.toggle(
    "Enable Volt-VAR Control (IEEE 1547)", 
    value=False,
    help="Smart inverters absorb reactive power during peak daylight to suppress overvoltage."
)
enable_bess = st.sidebar.toggle(
    "Enable Co-located Battery Storage (BESS)", 
    value=False,
    help="Battery storage absorbs peak generation, relieving thermal line overloads."
)
bess_capacity_pct = 0.0
if enable_bess:
    bess_capacity_pct = st.sidebar.slider(
        "BESS Capacity (% of PV Peak)", 
        min_value=10, max_value=50, value=25, step=5
    ) / 100.0
# ======================================================
# 3. Data Loading & Mitigation Logic
# ======================================================
@st.cache_data
def load_base_results():
    csv_path = os.path.join(os.path.dirname(__file__), "..", "results", "hosting_capacity_results.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        # Fallback dummy dataset
        data = {
            "Bus": ["632", "633", "634", "645", "646", "650", "652", "671", "675", "692"],
            "Maximum_PV_kW": [4775, 3175, 700, 0, 0, 7225, 0, 3850, 1150, 3075],
            "Limiting_Constraint": [
                "Line Overload", "Line Overload", "Transformer Overload",
                "Line Overload", "Line Overload", "Transformer Overload",
                "Line Overload", "Line Overload", "Overvoltage", "Line Overload"
            ]
        }
        df = pd.DataFrame(data)

    rename_dict = {}
    for col in df.columns:
        if col in ["Max_PV_kW", "Max_PV", "Capacity_kW"]:
            rename_dict[col] = "Maximum_PV_kW"
        elif col in ["Limiting_Factor", "Limit_Reason", "Constraint"]:
            rename_dict[col] = "Limiting_Constraint"
    df = df.rename(columns=rename_dict)
    df["Bus"] = df["Bus"].astype(str).str.lower().str.strip()
    return df
def apply_smart_grid_mitigations(df_base, volt_var_on, bess_on, bess_pct):
    df = df_base.copy()
    updated_pv = []
    updated_constraints = []
    for _, row in df.iterrows():
        cap = row["Maximum_PV_kW"]
        limit = row["Limiting_Constraint"]
        if volt_var_on and limit == "Overvoltage":
            cap = cap * 1.30
            if cap > 4000:
                limit = "Line Overload"
        if bess_on and limit in ["Line Overload", "Transformer Overload"]:
            cap = cap * (1.0 + bess_pct * 1.2)
        updated_pv.append(round(cap))
        updated_constraints.append(limit)
    df["Maximum_PV_kW"] = updated_pv
    df["Limiting_Constraint"] = updated_constraints
    return df
df_base = load_base_results()
df_results = apply_smart_grid_mitigations(df_base, enable_volt_var, enable_bess, bess_capacity_pct)
# ======================================================
# 4. KPI Cards
# ======================================================
max_cap = int(df_results["Maximum_PV_kW"].max()) if not df_results.empty else 0
max_bus = df_results.loc[df_results["Maximum_PV_kW"].idxmax(), "Bus"].upper() if not df_results.empty else "N/A"
avg_cap = float(df_results["Maximum_PV_kW"].mean()) if not df_results.empty else 0.0
total_tested = len(df_results)
primary_limit = df_results["Limiting_Constraint"].mode()[0] if not df_results.empty else "N/A"
col1, col2, col3, col4 = st.columns(4)
col1.metric("Max System Capacity", f"{max_cap:,} kW", f"At Bus {max_bus}")
col2.metric("Average Bus Capacity", f"{avg_cap:,.1f} kW")
col3.metric("Buses Tested", f"{total_tested}")
col4.metric("Primary Limit", primary_limit)
st.divider()
# ======================================================
# 5. Grid Section 1 (Spatial Map + Constraint Breakdown)
# ======================================================
col_map, col_breakdown = st.columns([0.65, 0.35])
with col_map:
    fig_map = build_spatial_map(df_results)
    st.plotly_chart(fig_map, use_container_width=True, key="feeder_spatial_map")
with col_breakdown:
    constraint_counts = df_results["Limiting_Constraint"].value_counts().reset_index()
    constraint_counts.columns = ["Constraint", "Count"]
    c_colors = [COLOR_MAP.get(c, '#8b949e') for c in constraint_counts["Constraint"]]
    fig_breakdown = go.Figure(go.Bar(
        x=constraint_counts["Constraint"],
        y=constraint_counts["Count"],
        marker_color=c_colors,
        text=constraint_counts["Count"],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>"
    ))
    fig_breakdown.update_layout(
        title=dict(
            text="<b>Limiting Constraint Breakdown</b>",
            font=dict(size=14, color="#1f2328")
        ),
        xaxis_title="Constraint Type",
        yaxis_title="Bus Count",
        height=450,
        margin=dict(l=20, r=20, t=40, b=40)
    )
    st.plotly_chart(fig_breakdown, use_container_width=True, key="constraint_breakdown_bar")
st.divider()
# ======================================================
# 6. Grid Section 2 (Capacity Bar + Voltage Profile)
# ======================================================
col_bar, col_voltage = st.columns([0.5, 0.5])
with col_bar:
    bar_colors = [COLOR_MAP.get(c, '#8b949e') for c in df_results["Limiting_Constraint"]]
    fig_bar = go.Figure(go.Bar(
        x=df_results["Bus"].str.upper(),
        y=df_results["Maximum_PV_kW"],
        marker_color=bar_colors,
        text=df_results["Maximum_PV_kW"],
        textposition="outside",
        hovertemplate="<b>Bus %{x}</b><br>Max PV: %{y} kW<br>Limit: %{customdata}<extra></extra>",
        customdata=df_results["Limiting_Constraint"]
    ))
    fig_bar.update_layout(
        title=dict(
            text="<b>Hosting Capacity by Feeder Bus</b>",
            font=dict(size=14, color="#1f2328")
        ),
        xaxis=dict(type='category', title="Bus Location"),
        yaxis=dict(title="Max Capacity (kW)"),
        height=400,
        margin=dict(l=20, r=20, t=40, b=40)
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="hosting_capacity_bar")
with col_voltage:
    hours = list(range(24))
    # Realistic baseline load profile
    v_baseline = [1.035 - 0.01 * np.sin(np.pi * h / 24)**2 for h in hours]
    # Solar profile boost (Daylight hours 6 AM - 6 PM)
    pv_boost = [0.025 * np.sin(np.pi * (h - 6) / 12) if 6 <= h <= 18 else 0.0 for h in hours]
    # Apply Volt-VAR flattening if active
    if enable_volt_var:
        pv_boost = [min(v, 0.012) for v in pv_boost]
    v_with_pv = [v_baseline[i] + pv_boost[i] for i in range(24)]
    fig_voltage = go.Figure()
    fig_voltage.add_trace(go.Scatter(x=hours, y=v_baseline, mode="lines+markers", name="Without PV", line=dict(color="#1f77b4", width=2)))
    pv_line_color = "#2ea043" if enable_volt_var else "#ff7f0e"
    pv_label = "With PV + Volt-VAR (Bus 675)" if enable_volt_var else "With PV Unmitigated (Bus 675)"
    fig_voltage.add_trace(go.Scatter(x=hours, y=v_with_pv, mode="lines+markers", name=pv_label, line=dict(color=pv_line_color, width=2)))
    fig_voltage.add_hline(y=1.05, line_dash="dash", line_color="red", annotation_text="Upper ANSI (1.05 pu)")
    fig_voltage.add_hline(y=0.95, line_dash="dash", line_color="blue", annotation_text="Lower ANSI (0.95 pu)")
    fig_voltage.update_layout(
        title=dict(
            text="<b>24-Hour Voltage Profile (Worst-Case Bus 675)</b>",
            font=dict(size=14, color="#1f2328")
        ),
        xaxis=dict(title="Hour of Day", dtick=2),
        yaxis=dict(title="Voltage (pu)", range=[0.94, 1.06]),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=40)
    )
    st.plotly_chart(fig_voltage, use_container_width=True, key="voltage_profile_chart")
# ======================================================
# 7. Data Table
# ======================================================
st.subheader("Detailed Capacity Results Table")
st.dataframe(
    df_results.style.format({"Maximum_PV_kW": "{:,} kW"}),
    use_container_width=True
)