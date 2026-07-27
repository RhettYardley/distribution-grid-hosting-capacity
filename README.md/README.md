# IEEE 13-Bus PV Hosting Capacity & Analytics Dashboard

An interactive power distribution grid analytical application built with **Python**, **Streamlit**, **OpenDSS**, and **Plotly**. 

This platform models the benchmark **IEEE 13-Node Test Feeder** to evaluate Photovoltaic (PV) integration limits, identify grid bottlenecks (overvoltage and line thermal overload), and explore the impact of Volt-VAR control and battery storage on PV hosting capacity. **IEEE 1547 Smart Inverter Volt-VAR control** and **Co-located Battery Energy Storage Systems (BESS)**.

---

## Key Features

* **Spatial Grid & Voltage Visualization:** Interactive map displaying feeder topology, node connection statuses, and per-unit (p.u.) voltage headrooms.
* **Iterative Hosting Capacity Engine:** Dynamic OpenDSS power flow calculations to determine maximum allowable PV capacity before violating ANSI C84.1 voltage limits (1.05 p.u.) or conductor thermal ampacities.
* **Smart Inverter Control (IEEE 1547):** Simulate reactive power absorption/injection (Volt-VAR curves) to alleviate high voltage conditions caused by peak reverse power flow.
* **Co-Located BESS Shaving:** Integrate energy storage resources during peak solar hours to shave generation spikes and expand feeder headroom.
* **24-Hour Time-Series Analytics:** Plot diurnal load profiles alongside solar irradiance curves to inspect duck-curve phenomena and peak net-load timing.

---

## Repository Structure

```text
├── circuits/           # IEEE 13-bus OpenDSS feeder definitions (.dss files)
├── data/               # 24-hour normalized load demand & solar irradiance profile CSVs
├── figures/            # Exported visual charts and network diagrams
├── results/            # Exported simulation logs and bus hosting capacity metrics
└── src/
    ├── dashboard.py    # Streamlit web UI and interaction logic
    ├── feeder_map.py   # Plotly spatial network topology visualizer
    ├── hosting_capacity.py # OpenDSS power flow simulation & hosting capacity solver
    └── profiles.py     # Time-series profile ingestion engine
├── .gitignore          # Git ignore file for virtual environments and pycache
├── README.md           # Project documentation
└── requirements.txt    # Python dependencies