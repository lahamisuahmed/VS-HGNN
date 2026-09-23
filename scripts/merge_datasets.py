import os
import io
import json
import urllib.request
import subprocess
import zipfile
import tarfile
import pandas as pd
import numpy as np

def run_optimized_merge():
    print("=== Starting Optimized Dataset Merge Pipeline ===")
    os.makedirs("data/merged", exist_ok=True)
    
    # -------------------------------------------------------------
    # Step 1: Stream DIVE Ground-Truth Labels & Addresses
    # -------------------------------------------------------------
    print("[1/5] Fetching DIVE contract addresses and labels...")
    dive_sc_url = "https://raw.githubusercontent.com/DIVE4Data/DIVE/main/RawData/SC_Addresses/SC_Addresses.csv"
    df_dive_addr = pd.read_csv(dive_sc_url)
    df_dive_addr['contractID'] = df_dive_addr.index + 1
    df_dive_addr['norm_address'] = df_dive_addr['contractAddress'].astype(str).str.lower().str.strip()
    
    # Fetch Labels via Zenodo API stream using curl
    zenodo_labels_url = "https://zenodo.org/api/records/18519253/files/DIVE_Labels.zip/content"
    res = subprocess.run(["curl", "-s", "-L", zenodo_labels_url], capture_output=True, check=True)
    with zipfile.ZipFile(io.BytesIO(res.stdout)) as z:
        df_dive_labels = pd.read_csv(z.open("Labels/DIVE_Labels.csv"))
        df_dive_tools = pd.read_csv(z.open("Labels/Tool_Results.csv"))
    
    # Merge DIVE addresses with Labels & Tools
    df_dive_full = df_dive_addr.merge(df_dive_labels, on='contractID', how='inner')
    df_dive_full = df_dive_full.merge(df_dive_tools, on='contractID', how='left')
    print(f"       DIVE fully labeled entries: {len(df_dive_full):,}")
    
    # -------------------------------------------------------------
    # Step 2: Stream SmartBugs Wild Metadata
    # -------------------------------------------------------------
    print("[2/5] Streaming SmartBugs Wild metadata...")
    sb_url = "https://raw.githubusercontent.com/smartbugs/smartbugs-wild/master/contracts.csv.tar.gz"
    req_sb = urllib.request.Request(sb_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req_sb) as resp:
        compressed_sb = resp.read()
    with tarfile.open(fileobj=io.BytesIO(compressed_sb), mode="r:gz") as tar:
        df_sb = pd.read_csv(tar.extractfile(tar.getmembers()[0]))
        
    df_sb['norm_address'] = df_sb['address'].astype(str).str.lower().str.strip()
    df_sb['nb_transaction'] = pd.to_numeric(df_sb['nb_transaction'], errors='coerce').fillna(0).astype(np.int64)
    df_sb['balance'] = pd.to_numeric(df_sb['balance'], errors='coerce').fillna(0)
    print(f"       SmartBugs Wild entries: {len(df_sb):,}")
    
    # -------------------------------------------------------------
    # Step 3: High-Performance Hash-Join (Inner Join: Supervised Core)
    # -------------------------------------------------------------
    print("[3/5] Executing optimized Hash-Join for Supervised Benchmark Core...")
    
    # Select columns to merge
    sb_cols = ['norm_address', 'nb_transaction', 'creation_date', 'last_transaction_date', 'compiler_version', 'name', 'balance']
    
    # Inner Join: Exact overlap with verified ground-truth + on-chain runtime
    df_merged_inner = df_dive_full.merge(df_sb[sb_cols], on='norm_address', how='inner')
    df_merged_inner.drop_duplicates(subset=['norm_address'], inplace=True)
    
    # Mark supervision flag
    df_merged_inner['has_ground_truth'] = True
    
    # Save Supervised Benchmark Core
    supervised_path = "data/merged/vs_hgnn_supervised_benchmark.csv"
    df_merged_inner.to_csv(supervised_path, index=False)
    print(f"       Supervised Benchmark saved to {supervised_path} (Shape: {df_merged_inner.shape})")
    
    # -------------------------------------------------------------
    # Step 4: Semi-Supervised Hybrid Graph Join (Full Universe)
    # -------------------------------------------------------------
    print("[4/5] Constructing Full Semi-Supervised Universe for Heterogeneous GNN...")
    
    # Left join onto SmartBugs Wild: all 972k contracts with ground truth mask
    df_hybrid = df_sb.merge(df_dive_full, on='norm_address', how='left')
    df_hybrid['has_ground_truth'] = ~df_hybrid['contractID'].isna()
    
    # Save statistics and summary profile
    vuln_cols = ['Reentrancy', 'Access Control', 'Arithmetic', 'Unchecked Return Values', 'DoS', 'Bad Randomness', 'Front Running', 'Time manipulation']
    
    overlap_count = len(df_merged_inner)
    vuln_distribution_inner = df_merged_inner[vuln_cols].sum().to_dict()
    
    merge_stats = {
        "dive_total_addresses": len(df_dive_addr),
        "dive_labeled_contracts": len(df_dive_labels),
        "smartbugs_wild_contracts": len(df_sb),
        "exact_address_overlap": overlap_count,
        "overlap_percentage_of_dive": float(overlap_count / len(df_dive_labels) * 100),
        "supervised_benchmark_shape": list(df_merged_inner.shape),
        "vulnerability_counts_in_supervised_benchmark": vuln_distribution_inner,
        "mean_transactions_supervised": float(df_merged_inner['nb_transaction'].mean()),
        "median_transactions_supervised": float(df_merged_inner['nb_transaction'].median()),
        "total_transactions_supervised": int(df_merged_inner['nb_transaction'].sum()),
        "unique_compilers_supervised": int(df_merged_inner['compiler_version'].nunique())
    }
    
    stats_path = "data/merged/merge_summary_stats.json"
    with open(stats_path, "w") as f:
        json.dump(merge_stats, f, indent=2)
        
    print(f"[5/5] Merge complete! Summary statistics written to {stats_path}.")
    print(f"       Overlap Contracts: {overlap_count:,}")
    print(f"       Supervised Total Transactions: {merge_stats['total_transactions_supervised']:,}")
    return merge_stats

if __name__ == "__main__":
    run_optimized_merge()
