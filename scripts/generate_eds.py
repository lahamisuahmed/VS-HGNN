import os
import io
import json
import urllib.request
import subprocess
import zipfile
import tarfile
import pandas as pd
import numpy as np

def run_eds():
    print("=== Starting Exploratory Data Summary (EDS / EOS) Analysis via Online Links ===")
    
    # 1. SmartBugs Wild Dataset (Online Tar stream)
    sb_url = "https://raw.githubusercontent.com/smartbugs/smartbugs-wild/master/contracts.csv.tar.gz"
    print(f"Fetching SmartBugs Wild metadata stream from {sb_url}...")
    req_sb = urllib.request.Request(sb_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req_sb) as resp:
        compressed_sb = resp.read()
    
    with tarfile.open(fileobj=io.BytesIO(compressed_sb), mode="r:gz") as tar:
        member = tar.getmembers()[0]
        f = tar.extractfile(member)
        df_sb = pd.read_csv(f)
        
    print(f"SmartBugs Wild Metadata Loaded successfully! Total Rows: {len(df_sb)}")
    
    # SmartBugs Wild Statistics
    df_sb['nb_transaction'] = pd.to_numeric(df_sb['nb_transaction'], errors='coerce').fillna(0)
    df_sb['balance'] = pd.to_numeric(df_sb['balance'], errors='coerce').fillna(0)
    
    sb_stats = {
        "total_rows": int(len(df_sb)),
        "unique_addresses": int(df_sb['address'].nunique()),
        "total_transactions": int(df_sb['nb_transaction'].sum()),
        "mean_transactions": float(df_sb['nb_transaction'].mean()),
        "median_transactions": float(df_sb['nb_transaction'].median()),
        "max_transactions": int(df_sb['nb_transaction'].max()),
        "zero_balance_contracts": int((df_sb['balance'] == 0).sum()),
        "non_zero_balance_contracts": int((df_sb['balance'] > 0).sum()),
        "max_balance_wei": str(df_sb['balance'].max()),
        "compiler_versions_count": int(df_sb['compiler_version'].nunique()),
        "top_compiler_versions": df_sb['compiler_version'].value_counts().head(10).to_dict()
    }
    
    # 2. DIVE Dataset (Online Zenodo zip stream via curl & GitHub raw links)
    dive_sc_url = "https://raw.githubusercontent.com/DIVE4Data/DIVE/main/RawData/SC_Addresses/SC_Addresses.csv"
    print(f"Fetching DIVE SC Addresses from {dive_sc_url}...")
    df_dive_addresses = pd.read_csv(dive_sc_url)
    
    dive_opcodes_url = "https://raw.githubusercontent.com/DIVE4Data/DIVE/main/Scripts/FeatureExtraction/EVM_Opcodes/EVM_Opcodes_20240921_002520.csv"
    print(f"Fetching DIVE EVM Opcodes reference from {dive_opcodes_url}...")
    df_dive_opcodes = pd.read_csv(dive_opcodes_url)
    
    # Fetch DIVE Labels via Zenodo stream using curl
    zenodo_labels_url = "https://zenodo.org/api/records/18519253/files/DIVE_Labels.zip/content"
    print(f"Fetching DIVE Labels stream from Zenodo ({zenodo_labels_url})...")
    res = subprocess.run(["curl", "-s", "-L", zenodo_labels_url], capture_output=True, check=True)
    dive_zip_bytes = res.stdout
        
    with zipfile.ZipFile(io.BytesIO(dive_zip_bytes)) as z:
        df_dive_labels = pd.read_csv(z.open("Labels/DIVE_Labels.csv"))
        df_dive_tools = pd.read_csv(z.open("Labels/Tool_Results.csv"))
        
    print(f"DIVE Labels Loaded successfully! Labeled Contracts: {len(df_dive_labels)}")
    
    vuln_cols = ['Reentrancy', 'Access Control', 'Arithmetic', 'Unchecked Return Values', 'DoS', 'Bad Randomness', 'Front Running', 'Time manipulation']
    vuln_counts = df_dive_labels[vuln_cols].sum().to_dict()
    
    # Calculate vulnerability counts per contract (single vs multi vs clean)
    df_dive_labels['vuln_count'] = df_dive_labels[vuln_cols].sum(axis=1)
    clean_contracts = int((df_dive_labels['vuln_count'] == 0).sum())
    single_vuln_contracts = int((df_dive_labels['vuln_count'] == 1).sum())
    multi_vuln_contracts = int((df_dive_labels['vuln_count'] > 1).sum())
    
    dive_stats = {
        "total_addresses_sc": int(len(df_dive_addresses)),
        "total_labeled_contracts": int(len(df_dive_labels)),
        "evm_opcodes_count": int(len(df_dive_opcodes)),
        "vulnerability_counts": vuln_counts,
        "clean_contracts": clean_contracts,
        "single_vuln_contracts": single_vuln_contracts,
        "multi_vuln_contracts": multi_vuln_contracts,
        "tools_evaluated": ["MAIAN", "Mythril", "Semgrep", "Slither", "Solhint", "VeriSmart"]
    }
    
    summary = {
        "smartbugs_wild": sb_stats,
        "dive": dive_stats
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/eds_stats.json", "w") as out:
        json.dump(summary, out, indent=2)
        
    print("=== EDS Analysis Completed Successfully! Summary saved to data/eds_stats.json ===")
    return summary

if __name__ == "__main__":
    run_eds()
