import os
import pandas as pd
import opendssdirect as dss
# ==================================================
# Configure IEEE 1547 Volt-VAR Smart Inverter Control
# ==================================================
def enable_volt_var_control():
    """Configures IEEE 1547 Volt-VAR smart inverter curve in OpenDSS."""
    dss.Text.Command("New XYCurve.vv_curve npts=4 xarray=[0.95, 0.99, 1.01, 1.05] yarray=[1.0, 0.0, 0.0, -1.0]")
    dss.Text.Command(
        "New InvControl.VoltVarCtrl "
        "mode=VOLTVAR "
        "vvc_curve1=vv_curve "
        "EventLog=yes "
        "deltaQ_factor=0.2"
    )
# ==================================================
# Add Battery Energy Storage System (BESS)
# ==================================================  
def add_bess_to_bus(bus_name, kw_capacity):
    """Adds co-located battery storage to absorb peak solar generation."""
    dss.Text.Command(
        f"New Storage.BESS_{bus_name} "
        f"bus1={bus_name} "
        f"phases=3 "
        f"kv=4.16 "
        f"kWrated={kw_capacity} "
        f"kWhrated={kw_capacity * 4} "
        f"state=CHARGING "
        f"%charge=100"
    )
# ==================================================
# Check Voltage Constraint Violations
# ==================================================
def check_voltage_violations(v_min=0.95, v_max=1.05):
    """Checks if any node violates ANSI C84.1 voltage limits."""
    v_pu = dss.Circuit.AllBusMagPu()
    for v in v_pu:
        if v > 0 and (v < v_min or v > v_max):
            return True
    return False
# ==================================================
# Check Thermal Constraint Violations
# ==================================================
def check_thermal_violations():
    """Checks if any line or transformer exceeds 100% rated capacity."""
    for i in range(dss.Lines.First()):
        currents = dss.CktElement.CurrentsMagAng()
        rating = dss.Lines.NormalAmps()
        if rating > 0 and max(currents[:6]) > rating:
            return True
    return False
# ==================================================
# Run PV Hosting Capacity Analysis
# ==================================================
def run_hosting_capacity_study(enable_vv=False, enable_bess=False, bess_ratio=0.25):
    """
    Iterates PV capacity per bus until thermal or voltage limits break.
    """
    master_file = os.path.join(os.path.dirname(__file__), "..", "dss_models", "IEEE13NodeMaster.dss")
    buses_to_test = ["632", "633", "634", "645", "646", "652", "671", "675", "692"]
    results = []
    for bus in buses_to_test:
        dss.Text.Command("Clear")
        dss.Text.Command(f"Compile ({master_file})")
        if enable_vv:
            enable_volt_var_control()
        pv_kw = 0
        step_kw = 50
        limiting_constraint = "OK"
        while pv_kw < 10000:
            pv_kw += step_kw
            # Update PV generator
            dss.Text.Command(f"New PVSystem.PV_{bus} bus1={bus} phases=3 kv=4.16 kVA={pv_kw} Pmpp={pv_kw} pf=1.0")
            if enable_bess:
                add_bess_to_bus(bus, kw_capacity=pv_kw * bess_ratio)
            dss.Solution.Solve()
            if check_voltage_violations():
                limiting_constraint = "Overvoltage"
                pv_kw -= step_kw
                break
            elif check_thermal_violations():
                limiting_constraint = "Line Overload"
                pv_kw -= step_kw
                break
        results.append({
            "Bus": bus,
            "Maximum_PV_kW": pv_kw,
            "Limiting_Constraint": limiting_constraint
        })
    df_results = pd.DataFrame(results)
    return df_results
# ==================================================
# Execute Simulation and Save Results
# ==================================================
if __name__ == "__main__":
    df = run_hosting_capacity_study(enable_vv=True, enable_bess=True)
    out_path = os.path.join(os.path.dirname(__file__), "..", "results", "hosting_capacity_results.csv")
    df.to_csv(out_path, index=False)
    print(f"Simulation complete. Saved results to {out_path}")