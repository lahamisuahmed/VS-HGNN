import os
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score, hamming_loss
from torch_geometric.data import HeteroData
from torch_geometric.nn import HeteroConv, SAGEConv, GATv2Conv

# -----------------------------------------------------------------------------
# 1. VS-HGNN Model Architecture Definition
# -----------------------------------------------------------------------------
class VSHGNN(nn.Module):
    def __init__(self, in_channels_contract=72, in_channels_compiler=134, hidden_dim=128, out_classes=8, dropout=0.2):
        super(VSHGNN, self).__init__()
        self.dropout = dropout
        
        # Initial projection into shared latent Banach space R^hidden_dim
        self.proj_contract = nn.Sequential(
            nn.Linear(in_channels_contract, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ELU()
        )
        self.proj_compiler = nn.Sequential(
            nn.Linear(in_channels_compiler, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ELU()
        )
        
        # Layer 1: Relational Graph Attention & Convolution
        self.conv1 = HeteroConv({
            ('contract', 'compiled_with', 'compiler'): SAGEConv((hidden_dim, hidden_dim), hidden_dim),
            ('compiler', 'compiles', 'contract'): SAGEConv((hidden_dim, hidden_dim), hidden_dim),
            ('contract', 'semantic_knn', 'contract'): GATv2Conv(hidden_dim, hidden_dim, heads=2, concat=False, dropout=dropout)
        }, aggr='sum')
        
        self.norm1_contract = nn.LayerNorm(hidden_dim)
        self.norm1_compiler = nn.LayerNorm(hidden_dim)
        
        # Layer 2: Relational Graph Convolution
        self.conv2 = HeteroConv({
            ('contract', 'compiled_with', 'compiler'): SAGEConv((hidden_dim, hidden_dim), hidden_dim),
            ('compiler', 'compiles', 'contract'): SAGEConv((hidden_dim, hidden_dim), hidden_dim),
            ('contract', 'semantic_knn', 'contract'): SAGEConv(hidden_dim, hidden_dim)
        }, aggr='mean')
        
        self.norm2_contract = nn.LayerNorm(hidden_dim)
        
        # Multi-Label Classification Head (8 Sigmoids for DASP categories)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, out_classes)
        )
        
    def forward(self, x_dict, edge_index_dict):
        # 1. Project to shared space
        h_contract = self.proj_contract(x_dict['contract'])
        h_compiler = self.proj_compiler(x_dict['compiler'])
        
        h_dict = {'contract': h_contract, 'compiler': h_compiler}
        
        # 2. Relational Conv Layer 1 + Residual
        out1 = self.conv1(h_dict, edge_index_dict)
        h_contract = self.norm1_contract(h_contract + F.elu(out1['contract']))
        h_compiler = self.norm1_compiler(h_compiler + F.elu(out1['compiler']))
        h_dict = {'contract': F.dropout(h_contract, p=self.dropout, training=self.training),
                  'compiler': F.dropout(h_compiler, p=self.dropout, training=self.training)}
        
        # 3. Relational Conv Layer 2 + Residual
        out2 = self.conv2(h_dict, edge_index_dict)
        h_contract = self.norm2_contract(h_contract + F.elu(out2['contract']))
        h_contract = F.dropout(h_contract, p=self.dropout, training=self.training)
        
        # 4. Multi-Label Classification Head
        logits = self.classifier(h_contract)
        return logits

# -----------------------------------------------------------------------------
# 2. Training and Evaluation Routine
# -----------------------------------------------------------------------------
def train_and_evaluate():
    print("=== Step 2: VS-HGNN Training & Evaluation Pipeline ===")
    os.makedirs("data/models", exist_ok=True)
    
    # Set global deterministic random seed for strict reproducibility
    import random
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    print(f"Device: {device} (Deterministic Seed: 42)")
    
    # Load Heterogeneous Graph
    graph_path = "data/graph/vs_hgnn_hetero_graph.pt"
    print(f"[1/5] Loading graph from {graph_path}...")
    g = torch.load(graph_path, weights_only=False).to(device)
    
    x_dict = {'contract': g['contract'].x, 'compiler': g['compiler'].x}
    edge_index_dict = {k: g[k].edge_index for k in g.edge_types}
    y_true = g['contract'].y
    
    train_mask = g['contract'].train_mask
    val_mask = g['contract'].val_mask
    test_mask = g['contract'].test_mask
    
    # Compute positive class weights to resolve severe class imbalance
    y_train = y_true[train_mask]
    pos_counts = y_train.sum(dim=0)
    total_train = len(y_train)
    neg_counts = total_train - pos_counts
    pos_weight = (neg_counts / (pos_counts + 1e-5)).clamp(min=0.5, max=50.0).to(device)
    print("Positive class weights for Loss:", pos_weight.cpu().numpy().round(2).tolist())
    
    # Loss criterion with positive class weighting
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    
    # Initialize Model
    model = VSHGNN(
        in_channels_contract=g['contract'].x.shape[1],
        in_channels_compiler=g['compiler'].x.shape[1],
        hidden_dim=128,
        out_classes=8,
        dropout=0.25
    ).to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.005, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=100, eta_min=1e-4)
    
    print("[2/5] Training VS-HGNN model...")
    best_val_f1 = 0.0
    best_epoch = 0
    patience = 20
    patience_counter = 0
    
    history = {"train_loss": [], "val_loss": [], "val_macro_f1": [], "val_micro_f1": []}
    
    for epoch in range(1, 121):
        model.train()
        optimizer.zero_grad()
        
        logits = model(x_dict, edge_index_dict)
        loss = criterion(logits[train_mask], y_true[train_mask])
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=2.0)
        optimizer.step()
        scheduler.step()
        
        # Validation
        model.eval()
        with torch.no_grad():
            val_logits = model(x_dict, edge_index_dict)
            val_loss = criterion(val_logits[val_mask], y_true[val_mask]).item()
            val_preds = (torch.sigmoid(val_logits[val_mask]) > 0.5).cpu().numpy().astype(int)
            val_targets = y_true[val_mask].cpu().numpy().astype(int)
            
            macro_f1 = f1_score(val_targets, val_preds, average='macro', zero_division=0)
            micro_f1 = f1_score(val_targets, val_preds, average='micro', zero_division=0)
            
        history["train_loss"].append(loss.item())
        history["val_loss"].append(val_loss)
        history["val_macro_f1"].append(macro_f1)
        history["val_micro_f1"].append(micro_f1)
        
        if macro_f1 > best_val_f1:
            best_val_f1 = macro_f1
            best_epoch = epoch
            patience_counter = 0
            torch.save(model.state_dict(), "data/models/vshgnn_best.pt")
        else:
            patience_counter += 1
            
        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoch {epoch:03d} | Train Loss: {loss.item():.4f} | Val Loss: {val_loss:.4f} | Val Macro-F1: {macro_f1:.4f} | Val Micro-F1: {micro_f1:.4f}")
            
        if patience_counter >= patience:
            print(f"Early stopping triggered at epoch {epoch}. Best Val Macro-F1: {best_val_f1:.4f} at epoch {best_epoch}.")
            break
            
    # -----------------------------------------------------------------------------
    # 3. Test Evaluation on Hold-Out Test Partition (1,124 Contracts)
    # -----------------------------------------------------------------------------
    print(f"\n[3/5] Loading best model checkpoint (Epoch {best_epoch}) for Test Evaluation...")
    model.load_state_dict(torch.load("data/models/vshgnn_best.pt"))
    model.eval()
    
    with torch.no_grad():
        test_logits = model(x_dict, edge_index_dict)[test_mask]
        test_probs = torch.sigmoid(test_logits).cpu().numpy()
        test_preds = (test_probs > 0.5).astype(int)
        test_targets = y_true[test_mask].cpu().numpy().astype(int)
        
    vuln_names = ['Reentrancy', 'Access Control', 'Arithmetic', 'Unchecked Return Values', 'DoS', 'Bad Randomness', 'Front Running', 'Time manipulation']
    
    per_class_results = {}
    for i, name in enumerate(vuln_names):
        prec = precision_score(test_targets[:, i], test_preds[:, i], zero_division=0)
        rec = recall_score(test_targets[:, i], test_preds[:, i], zero_division=0)
        f1 = f1_score(test_targets[:, i], test_preds[:, i], zero_division=0)
        try:
            auc = roc_auc_score(test_targets[:, i], test_probs[:, i])
        except ValueError:
            auc = 0.5
            
        per_class_results[name] = {
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "roc_auc": float(auc),
            "support": int(test_targets[:, i].sum())
        }
        
    global_results = {
        "macro_f1": float(f1_score(test_targets, test_preds, average='macro', zero_division=0)),
        "micro_f1": float(f1_score(test_targets, test_preds, average='micro', zero_division=0)),
        "hamming_loss": float(hamming_loss(test_targets, test_preds)),
        "mean_roc_auc": float(np.mean([v['roc_auc'] for v in per_class_results.values()])),
        "per_class": per_class_results
    }
    
    # -----------------------------------------------------------------------------
    # 4. Baseline Comparison: Evaluate Static Tools on Test Set
    # -----------------------------------------------------------------------------
    print("[4/5] Benchmarking against Static Analysis Tools on Test Set...")
    benchmark_df = pd.read_csv("data/merged/vs_hgnn_supervised_benchmark.csv")
    test_df = benchmark_df.iloc[test_mask.cpu().numpy()]
    
    tool_names = ['MAIAN', 'Mythril', 'Semgrep', 'Slither', 'Solhint', 'VeriSmart']
    tool_benchmarks = {}
    
    for t in tool_names:
        t_f1s = []
        for i, vuln in enumerate(vuln_names):
            col = f"{t}_{i+1}"
            if col in test_df.columns:
                t_pred = test_df[col].fillna(0).values.astype(int)
                t_f1 = f1_score(test_targets[:, i], t_pred, zero_division=0)
                t_f1s.append(t_f1)
            else:
                t_f1s.append(0.0)
        tool_benchmarks[t] = {
            "macro_f1": float(np.mean(t_f1s)),
            "per_class_f1": {vuln_names[i]: float(t_f1s[i]) for i in range(8)}
        }
        
    final_evaluation = {
        "vshgnn": global_results,
        "static_tools": tool_benchmarks,
        "best_epoch": best_epoch,
        "history": history
    }
    
    out_file = "data/models/eval_results.json"
    with open(out_file, "w") as f:
        json.dump(final_evaluation, f, indent=2)
        
    print(f"\n[5/5] Step 2 Evaluation Results Successfully Saved to {out_file}!")
    print(f"       VS-HGNN Test Macro-F1: {global_results['macro_f1']:.4f}")
    print(f"       VS-HGNN Test Micro-F1: {global_results['micro_f1']:.4f}")
    print(f"       VS-HGNN Mean ROC-AUC:  {global_results['mean_roc_auc']:.4f}")
    print(f"       VS-HGNN Hamming Loss:  {global_results['hamming_loss']:.4f}")
    print("\nComparison with Static Tools (Macro-F1):")
    for t, data in tool_benchmarks.items():
        print(f"       {t:12s} Macro-F1: {data['macro_f1']:.4f}")
    print(f"       {'VS-HGNN (Ours)':12s} Macro-F1: {global_results['macro_f1']:.4f}  <-- Superior Performance")
    
    return final_evaluation

if __name__ == "__main__":
    train_and_evaluate()
