import os
import subprocess
import tarfile
import pandas as pd

DATA_DIR = os.path.join(os.getcwd(), "data")
SB_WILD_REPO = "https://github.com/smartbugs/smartbugs-wild.git"
DIVE_REPO = "https://github.com/DIVE4Data/DIVE.git"

def fetch_repos():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 1. Fetch SmartBugs Wild repo if not present
    sb_wild_path = os.path.join(DATA_DIR, "smartbugs-wild")
    if not os.path.exists(sb_wild_path):
        print("Cloning SmartBugs Wild repository...")
        subprocess.run(["git", "clone", "--depth", "1", SB_WILD_REPO, sb_wild_path], check=True)
    else:
        print("SmartBugs Wild repository already exists.")
        
    # Extract contracts.csv.tar.gz if present
    tar_path = os.path.join(sb_wild_path, "contracts.csv.tar.gz")
    csv_out_path = os.path.join(DATA_DIR, "smartbugs_wild_contracts.csv")
    if os.path.exists(tar_path) and not os.path.exists(csv_out_path):
        print("Extracting SmartBugs Wild contracts.csv.tar.gz...")
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=DATA_DIR)
            extracted_file = os.path.join(DATA_DIR, "contracts.csv")
            if os.path.exists(extracted_file):
                os.rename(extracted_file, csv_out_path)
        print(f"Extracted to {csv_out_path}")

    # 2. Fetch DIVE repo if not present
    dive_path = os.path.join(DATA_DIR, "DIVE")
    if not os.path.exists(dive_path):
        print("Cloning DIVE repository...")
        subprocess.run(["git", "clone", "--depth", "1", DIVE_REPO, dive_path], check=True)
    else:
        print("DIVE repository already exists.")

if __name__ == "__main__":
    fetch_repos()
