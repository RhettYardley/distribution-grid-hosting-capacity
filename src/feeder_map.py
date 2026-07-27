import plotly.graph_objects as go
# ==================================================
# Color mapping for grid constraints
# ==================================================
COLOR_MAP = {
    'Line Overload': '#2ea043',         # Green
    'Transformer Overload': '#e3b341',  # Amber/Orange
    'Overvoltage': '#da3633',           # Red
    'Undervoltage': '#8957e5',          # Purple
    'Untested / Regulator': '#8b949e',  # Gray
    'OK': '#1f6beb'                     # Blue
}
# ==================================================
# Standard IEEE 13 Node Grid Coordinates (Matching Diagram Layout)
# ==================================================
IEEE13_BUS_COORDS = {
    "650": (4.0, 6.0),
    "rg60": (4.0, 5.0),
    "632": (4.0, 4.0),
    "670": (4.0, 5.5),  # Retained in dict to prevent KeyError on dashboard
    "645": (2.0, 4.0),
    "646": (0.0, 4.0),
    "633": (6.0, 4.0),
    "634": (8.0, 4.0),
    "671": (4.0, 2.0),
    "684": (2.0, 2.0),
    "611": (0.0, 2.0),
    "652": (2.0, 0.0),
    "680": (4.0, 0.0),
    "692": (6.0, 2.0),
    "675": (8.0, 2.0),
}
# ==================================================
# Feeder Topology Connections (Lines & Switches)
# ==================================================
IEEE13_LINES = [
    ("650", "rg60"), ("rg60", "632"), ("632", "645"), ("645", "646"),
    ("632", "633"), ("633", "634"), ("632", "671"),
    ("671", "680"), ("671", "684"), ("684", "611"), ("684", "652"),
    ("671", "692"), ("692", "675")
]
def build_spatial_map(df):
    """
    Builds an interactive Plotly feeder map for the IEEE 13-Bus system.
    """
    results_lookup = {}
    for _, row in df.iterrows():
        bus_key = str(row["Bus"]).lower().strip()
        results_lookup[bus_key] = {
            "Maximum_PV_kW": row["Maximum_PV_kW"],
            "Limiting_Constraint": row["Limiting_Constraint"]
        }
    # ==================================================
    # 1. Edge Traces (Lines)
    # ==================================================
    edge_x, edge_y = [], []
    for bus1, bus2 in IEEE13_LINES:
        if bus1 in IEEE13_BUS_COORDS and bus2 in IEEE13_BUS_COORDS:
            x0, y0 = IEEE13_BUS_COORDS[bus1]
            x1, y1 = IEEE13_BUS_COORDS[bus2]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=3, color='#30363d'),
        hoverinfo='none',
        mode='lines',
        showlegend=False
    )
    # ==================================================
    # 2. Node Traces (Circles)
    # ==================================================
    node_x, node_y, hover_text, node_colors, node_sizes, bus_labels = [], [], [], [], [], []
    for bus_key, (x, y) in IEEE13_BUS_COORDS.items():
        # Exclude rendering bus 670 node on plot if disconnected
        if bus_key == "670":
            continue
        node_x.append(x)
        node_y.append(y)
        bus_labels.append(f"<b>Bus {bus_key.upper()}</b>")
        bus_data = results_lookup.get(bus_key.lower().strip(), None)
        if bus_data:
            max_pv = bus_data["Maximum_PV_kW"]
            limit = bus_data["Limiting_Constraint"]
            color = COLOR_MAP.get(limit, "#8b949e")
            size = max(18, min(36, 18 + (max_pv / 250)))
            hover_str = (
                f"<b>Bus {bus_key.upper()}</b><br>"
                f"Max PV Capacity: <b>{max_pv:,} kW</b><br>"
                f"Limiting Constraint: <b>{limit}</b>"
            )
        else:
            color = COLOR_MAP.get("Untested / Regulator", "#8b949e")
            size = 12
            hover_str = f"<b>Bus {bus_key.upper()}</b><br>Regulator / Substation Node"
        node_colors.append(color)
        node_sizes.append(size)
        hover_text.append(hover_str)
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        hovertext=hover_text,
        marker=dict(
            size=node_sizes, 
            color=node_colors, 
            line=dict(width=2, color="white")
        ),
        showlegend=False,
    )
    # ==================================================
    # 3. Dedicated Text Trace (Offset y + 0.35 for readability)
    # ==================================================
    text_trace = go.Scatter(
        x=node_x,
        y=[y + 0.35 for y in node_y],
        mode="text",
        text=bus_labels,
        textfont=dict(size=11, color="#1f2328", family="Segoe UI, Arial"),
        hoverinfo="none",
        showlegend=False
    )
    fig = go.Figure(data=[edge_trace, node_trace, text_trace])
    fig.update_layout(
        title=dict(
            text="<b>IEEE 13-Node Feeder Topology & Spatial Hosting Capacity</b>",
            font=dict(size=14, color="#1f2328"),
        ),
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=20, r=20, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(
            showgrid=False, 
            zeroline=False, 
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=450,
    )
    return fig