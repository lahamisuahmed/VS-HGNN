import os
import json
import torch
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from torch_geometric.data import HeteroData, Data

def construct_vs_hgnn_graph():
    print("=== Starting VS-HGNN Graph Representation Construction ===")
    os.makedirs("data/graph", exist_ok=True)
    
    # ------------------------------------------------------------------
    # Step 1: Load Merged Supervised Benchmark (Step 1 Output)
    # ------------------------------------------------------------------
    benchmark_path = "data/merged/vs_hgnn_supervised_benchmark.csv"
    if not os.path.exists(benchmark_path):
        raise FileNotFoundError(f"Missing {benchmark_path}. Please run Step 1 merge first.")
        
    print(f"[1/6] Loading benchmark dataset from {benchmark_path}...")
    df = pd.read_csv(benchmark_path)
    N = len(df)
    print(f"       Loaded {N:,} contracts with {df.shape[1]} columns.")
    
    # ------------------------------------------------------------------
    # Step 2: Feature Engineering & Preprocessing for Contract Nodes
    # ------------------------------------------------------------------
    print("[2/6] Engineering multi-modal node feature vectors...")
    
    # A. Runtime features: log-scaled transaction count, log-scaled balance, and life-span
    df['log_tx'] = np.log10(pd.to_numeric(df['nb_transaction'], errors='coerce').fillna(0) + 1.0)
    df['log_balance'] = np.log10(pd.to_numeric(df['balance'], errors='coerce').fillna(0) + 1.0)
    
    # Estimate lifecycle duration in days
    c_date = pd.to_datetime(df['creation_date'], errors='coerce')
    l_date = pd.to_datetime(df['last_transaction_date'], errors='coerce')
    lifecycle_days = (l_date - c_date).dt.total_seconds() / (24 * 3600)
    df['lifecycle_days'] = lifecycle_days.fillna(0).clip(lower=0)
    
    runtime_cols = ['log_tx', 'log_balance', 'lifecycle_days']
    scaler = StandardScaler()
    X_runtime = scaler.fit_transform(df[runtime_cols])
    
    # B. Static Tool Priors (48 columns: MAIAN, Mythril, Semgrep, Slither, Solhint, VeriSmart)
    tool_cols = [c for c in df.columns if any(t in c for t in ['MAIAN', 'Mythril', 'Semgrep', 'Slither', 'Solhint', 'VeriSmart'])]
    df[tool_cols] = df[tool_cols].fillna(0).astype(np.float32)
    X_tools = df[tool_cols].values
    
    # C. Compiler Version Categorical Embedding (Frequency / One-Hot top 20)
    top_compilers = df['compiler_version'].value_counts().head(20).index.tolist()
    compiler_dummies = pd.get_dummies(df['compiler_version'].apply(lambda x: x if x in top_compilers else 'Other'), prefix='comp')
    X_compilers = compiler_dummies.values.astype(np.float32)
    
    # Concatenate all node features: [X_runtime (3) || X_tools (48) || X_compilers (21)]
    X_contracts = np.hstack([X_runtime, X_tools, X_compilers]).astype(np.float32)
    print(f"       Contract node feature matrix shape: {X_contracts.shape} ({X_contracts.shape[1]} features)")
    
    # ------------------------------------------------------------------
    # Step 3: Multi-Label Ground Truth Target Matrix (DASP Top 8)
    # ------------------------------------------------------------------
    print("[3/6] Formatting multi-label target matrix...")
    vuln_cols = ['Reentrancy', 'Access Control', 'Arithmetic', 'Unchecked Return Values', 'DoS', 'Bad Randomness', 'Front Running', 'Time manipulation']
    Y = df[vuln_cols].fillna(0).astype(np.int64).values
    print(f"       Multi-label target matrix Y shape: {Y.shape} (8 binary targets)")
    
    # ------------------------------------------------------------------
    # Step 4: Heterogeneous Edge Construction
    # ------------------------------------------------------------------
    print("[4/6] Constructing heterogeneous graph edges...")
    
    # Edge Type A: Contract-to-Compiler Bipartite Edges ('contract', 'compiled_with', 'compiler')
    unique_compilers = df['compiler_version'].unique().tolist()
    compiler_to_idx = {c: i for i, c in enumerate(unique_compilers)}
    
    src_contract_comp = []
    dst_compiler = []
    for c_idx, comp_ver in enumerate(df['compiler_version']):
        src_contract_comp.append(c_idx)
        dst_compiler.append(compiler_to_idx[comp_ver])
        
    edge_index_compiled_with = torch.tensor([src_contract_comp, dst_compiler], dtype=torch.long)
    edge_index_compiles = torch.tensor([dst_compiler, src_contract_comp], dtype=torch.long)
    print(f"       Contract <-> Compiler bipartite edges: {edge_index_compiled_with.shape[1]:,} edges")
    
    # Edge Type B: Semantic k-NN Topology ('contract', 'semantic_knn', 'contract')
    # Connect contracts with similar behavioral profiles (Runtime + Tool vector)
    print("       Computing k-Nearest Neighbors semantic affinity graph (k=5)...")
    nbrs = NearestNeighbors(n_neighbors=6, metric='cosine').fit(X_contracts)
    distances, indices = nbrs.kneighbors(X_contracts)
    
    src_knn = []
    dst_knn = []
    for i in range(N):
        for neighbor in indices[i, 1:]: # exclude self-loop (index 0)
            src_knn.append(i)
            dst_knn.append(neighbor)
            
    edge_index_knn = torch.tensor([src_knn, dst_knn], dtype=torch.long)
    print(f"       Contract <-> Contract semantic k-NN edges: {edge_index_knn.shape[1]:,} edges")
    
    # ------------------------------------------------------------------
    # Step 5: Data Partitioning (Train / Val / Test Masks)
    # ------------------------------------------------------------------
    print("[5/6] Creating stratified train/validation/test masks...")
    rng = np.random.RandomState(42)
    perm = rng.permutation(N)
    
    n_train = int(0.70 * N)
    n_val = int(0.15 * N)
    
    train_mask = torch.zeros(N, dtype=torch.bool)
    val_mask = torch.zeros(N, dtype=torch.bool)
    test_mask = torch.zeros(N, dtype=torch.bool)
    
    train_mask[perm[:n_train]] = True
    val_mask[perm[n_train:n_train + n_val]] = True
    test_mask[perm[n_train + n_val:]] = True
    
    print(f"       Train Nodes: {train_mask.sum().item():,} (70%)")
    print(f"       Val Nodes:   {val_mask.sum().item():,} (15%)")
    print(f"       Test Nodes:  {test_mask.sum().item():,} (15%)")
    
    # ------------------------------------------------------------------
    # Step 6: Assemble PyTorch Geometric HeteroData Object
    # ------------------------------------------------------------------
    print("[6/6] Assembling PyTorch Geometric HeteroData & Data objects...")
    
    # Heterogeneous Graph Data Object
    data_hetero = HeteroData()
    data_hetero['contract'].x = torch.tensor(X_contracts, dtype=torch.float)
    data_hetero['contract'].y = torch.tensor(Y, dtype=torch.float)
    data_hetero['contract'].train_mask = train_mask
    data_hetero['contract'].val_mask = val_mask
    data_hetero['contract'].test_mask = test_mask
    data_hetero['contract'].address = df['contractAddress'].tolist()
    
    # Compiler node features (One-hot identity)
    n_compilers = len(unique_compilers)
    data_hetero['compiler'].x = torch.eye(n_compilers, dtype=torch.float)
    data_hetero['compiler'].name = unique_compilers
    
    # Add Edge Relations
    data_hetero['contract', 'compiled_with', 'compiler'].edge_index = edge_index_compiled_with
    data_hetero['compiler', 'compiles', 'contract'].edge_index = edge_index_compiles
    data_hetero['contract', 'semantic_knn', 'contract'].edge_index = edge_index_knn
    
    # Homogeneous Graph Projection (Contract-only view with KNN edges)
    data_homo = Data(
        x=torch.tensor(X_contracts, dtype=torch.float),
        edge_index=edge_index_knn,
        y=torch.tensor(Y, dtype=torch.float),
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask
    )
    
    # Save Graph Objects
    hetero_path = "data/graph/vs_hgnn_hetero_graph.pt"
    homo_path = "data/graph/vs_hgnn_homo_graph.pt"
    torch.save(data_hetero, hetero_path)
    torch.save(data_homo, homo_path)
    
    # Save Graph Metadata Profile
    graph_meta = {
        "num_contract_nodes": N,
        "num_compiler_nodes": n_compilers,
        "contract_features_dim": X_contracts.shape[1],
        "target_vulnerability_classes": 8,
        "edge_types": [
            "('contract', 'compiled_with', 'compiler')",
            "('compiler', 'compiles', 'contract')",
            "('contract', 'semantic_knn', 'contract')"
        ],
        "num_edges_compiled_with": int(edge_index_compiled_with.shape[1]),
        "num_edges_semantic_knn": int(edge_index_knn.shape[1]),
        "total_heterogeneous_edges": int(edge_index_compiled_with.shape[1] * 2 + edge_index_knn.shape[1]),
        "train_nodes": int(train_mask.sum()),
        "val_nodes": int(val_mask.sum()),
        "test_nodes": int(test_mask.sum()),
        "files_saved": [hetero_path, homo_path]
    }
    
    meta_path = "data/graph/graph_summary.json"
    with open(meta_path, "w") as f:
        json.dump(graph_meta, f, indent=2)
        
    print("\n=== Graph Construction Completed Successfully! ===")
    print(f"Heterogeneous Graph saved to: {hetero_path}")
    print(f"Homogeneous Graph saved to:   {homo_path}")
    print(f"Summary metadata saved to:    {meta_path}")
    print(f"Total Nodes: {N + n_compilers:,} (Contracts: {N:,}, Compilers: {n_compilers})")
    print(f"Total Edges: {graph_meta['total_heterogeneous_edges']:,}")
    return graph_meta

if __name__ == "__main__":
    construct_vs_hgnn_graph()
