import os
import pandas as pd
# ==================================================
# Locate Project Directory
# ==================================================
project_path = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
# ==================================================
# Load Residential Load Profile
# ==================================================
def load_profile():
    file_path = os.path.join(
        project_path,
        "data",
        "load_profiles",
        "residential_load.csv"
    )
    return pd.read_csv(
        file_path
    )
# ==================================================
# Load Solar Profile
# ==================================================
def solar_profile():
    file_path = os.path.join(
        project_path,
        "data",
        "solar_profiles",
        "solar_irradiance.csv"
    )
    return pd.read_csv(
        file_path
    )
# ==================================================
# Test When Run Directly
# ==================================================
if __name__ == "__main__":
    load = load_profile()
    solar = solar_profile()
    print("Load Profile")
    print(load)
    print()
    print("Solar Profile")
    print(solar)