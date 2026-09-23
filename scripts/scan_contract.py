#!/usr/bin/env python3
"""
scripts/scan_contract.py
=============================================================================
VS-HGNN Step 3: Practical Contract Scanner & GNN Explainer
=============================================================================
An end-to-end inference and interpretability engine for Ethereum smart contract
vulnerability auditing.

Key Capabilities:
  1. Inductive Graph Insertion: Ingests arbitrary smart contracts (either from
     the historical corpus or via arbitrary 72-dimensional feature vectors),
     dynamically constructs relational edges to compiler nodes and semantic
     k-NN peer contracts, and evaluates against calibrated decision thresholds.
  2. Optimal Threshold Calibration: Leverages validation-optimized thresholds
     tau_k* across all 8 DASP vulnerability categories.
  3. GNN Explainer & Gradient Saliency: Deconstructs model verdicts via
     Input-x-Gradient saliency attribution s_k = |grad_{x} z_k| * |x| to reveal
     the exact driving features (runtime dynamics, compiler affinities, and
     static tool priors).
  4. Relational Subgraph Attribution: Identifies the historical Ethereum peers
     that exerted the strongest topological influence on the classification.
  5. Executive Security Monograph Generation: Outputs structured JSON reports
     and auditor-facing forensic narratives with remediation guidance.

Author: VS-HGNN Research Initiative
=============================================================================
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

# Suppress PyTorch 3.14 JIT warning if present
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from torch_geometric.data import HeteroData
from torch_geometric.nn import HeteroConv, SAGEConv, GATv2Conv

# -----------------------------------------------------------------------------
# 1. Model Architecture Definition (Strictly Matches Best Checkpoint)
# -----------------------------------------------------------------------------
class VSHGNN(nn.Module):
    def __init__(self, in_channels_contract=72, in_channels_compiler=134, hidden_dim=128, out_classes=8, dropout=0.25):
        super(VSHGNN, self).__init__()
        self.dropout = dropout
        
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
        
        self.conv1 = HeteroConv({
            ('contract', 'compiled_with', 'compiler'): SAGEConv((hidden_dim, hidden_dim), hidden_dim),
            ('compiler', 'compiles', 'contract'): SAGEConv((hidden_dim, hidden_dim), hidden_dim),
            ('contract', 'semantic_knn', 'contract'): GATv2Conv(hidden_dim, hidden_dim, heads=2, concat=False, dropout=dropout)
        }, aggr='sum')
        
        self.norm1_contract = nn.LayerNorm(hidden_dim)
        self.norm1_compiler = nn.LayerNorm(hidden_dim)
        
        self.conv2 = HeteroConv({
            ('contract', 'compiled_with', 'compiler'): SAGEConv((hidden_dim, hidden_dim), hidden_dim),
            ('compiler', 'compiles', 'contract'): SAGEConv((hidden_dim, hidden_dim), hidden_dim),
            ('contract', 'semantic_knn', 'contract'): SAGEConv(hidden_dim, hidden_dim)
        }, aggr='mean')
        
        self.norm2_contract = nn.LayerNorm(hidden_dim)
        
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, out_classes)
        )
        
    def forward(self, x_dict, edge_index_dict):
        h_contract = self.proj_contract(x_dict['contract'])
        h_compiler = self.proj_compiler(x_dict['compiler'])
        h_dict = {'contract': h_contract, 'compiler': h_compiler}
        
        out1 = self.conv1(h_dict, edge_index_dict)
        h_contract = self.norm1_contract(h_contract + F.elu(out1['contract']))
        h_compiler = self.norm1_compiler(h_compiler + F.elu(out1['compiler']))
        h_dict = {
            'contract': F.dropout(h_contract, p=self.dropout, training=self.training),
            'compiler': F.dropout(h_compiler, p=self.dropout, training=self.training)
        }
        
        out2 = self.conv2(h_dict, edge_index_dict)
        h_contract = self.norm2_contract(h_contract + F.elu(out2['contract']))
        h_contract = F.dropout(h_contract, p=self.dropout, training=self.training)
        
        logits = self.classifier(h_contract)
        return logits

# -----------------------------------------------------------------------------
# 2. Scanner & Explainer Engine
# -----------------------------------------------------------------------------
class ContractScanner:
    """
    Practical Smart Contract Vulnerability Scanner & GNN Explainer.
    Executes inductive relational inference and feature attribution on arbitrary contracts.
    """
    
    # 8 Standard DASP Vulnerability Categories
    VULN_NAMES = [
        'Reentrancy',
        'Access Control',
        'Arithmetic',
        'Unchecked Return Values',
        'DoS',
        'Bad Randomness',
        'Front Running',
        'Time manipulation'
    ]
    
    # Validation-Calibrated Optimal Decision Thresholds (tau_k*)
    CALIBRATED_THRESHOLDS = {
        'Reentrancy': 0.530,
        'Access Control': 0.370,
        'Arithmetic': 0.540,
        'Unchecked Return Values': 0.410,
        'DoS': 0.810,
        'Bad Randomness': 0.380,
        'Front Running': 0.450,
        'Time manipulation': 0.600
    }
    
    # Remediation recommendations for each vulnerability class
    REMEDIATIONS = {
        'Reentrancy': "Implement Checks-Effects-Interactions pattern and utilize OpenZeppelin ReentrancyGuard on external calls.",
        'Access Control': "Enforce strict ownership modifiers (e.g. onlyOwner), restrict delegatecall targets, and audit administrative role assignments.",
        'Arithmetic': "Adopt Solidity ^0.8.0 built-in overflow checks or SafeMath library; guard against integer underflow in balance subtractions.",
        'Unchecked Return Values': "Ensure low-level call return values are explicitly checked: require(success, 'Call failed'); avoid unhandled send() calls.",
        'DoS': "Avoid unbounded loops over dynamic arrays; replace push-payment patterns with pull-payment withdrawal mechanisms.",
        'Bad Randomness': "Never rely on block.timestamp, blockhash, or block.difficulty for entropy; integrate Chainlink VRF or commit-reveal schemes.",
        'Front Running': "Implement commit-reveal schemes, batch auctions, or maximum slippage tolerance limits to mitigate transaction reordering / MEV.",
        'Time manipulation': "Do not rely on block.timestamp for strict temporal logic; tolerate clock drifts of up to +/- 15 seconds."
    }

    def __init__(self, 
                 graph_path="data/graph/vs_hgnn_hetero_graph.pt", 
                 model_path="data/models/vshgnn_best.pt",
                 benchmark_csv="data/merged/vs_hgnn_supervised_benchmark.csv",
                 device=None):
        
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
        
        # Load pre-constructed heterogeneous graph
        if not os.path.exists(graph_path):
            raise FileNotFoundError(f"Missing graph file at {graph_path}. Run scripts/construct_graph.py first.")
        self.graph = torch.load(graph_path, weights_only=False).to(self.device)
        
        # Load trained VS-HGNN checkpoint
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Missing model checkpoint at {model_path}. Run scripts/train_vshgnn.py first.")
            
        in_c = self.graph['contract'].x.shape[1]
        in_m = self.graph['compiler'].x.shape[1]
        self.model = VSHGNN(
            in_channels_contract=in_c,
            in_channels_compiler=in_m,
            hidden_dim=128,
            out_classes=8,
            dropout=0.0 # Deterministic inference
        ).to(self.device)
        
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        
        # Build address lookup index
        self.addresses = [a.lower() for a in self.graph['contract'].address]
        self.addr_to_idx = {addr: i for i, addr in enumerate(self.addresses)}
        
        # Compiler version metadata
        self.compiler_names = self.graph['compiler'].name
        self.compiler_to_idx = {name: i for i, name in enumerate(self.compiler_names)}
        
        # Feature column schema (72 features total)
        self.feature_names = self._build_feature_names()
        
        # Fitted StandardScaler parameters for runtime features [log_tx, log_balance, lifecycle_days]
        self.runtime_scaler_mean = np.array([1.604427, 2.105493, 136.199395], dtype=np.float32)
        self.runtime_scaler_scale = np.array([1.126165, 5.520811, 174.286426], dtype=np.float32)
        
        # Pre-normalize contract features for fast cosine nearest-neighbor search
        with torch.no_grad():
            self.x_contracts_norm = F.normalize(self.graph['contract'].x, p=2, dim=1)

    def _build_feature_names(self):
        """Builds standardized list of 72 feature names matching construct_graph.py"""
        names = ['runtime_log_tx', 'runtime_log_balance', 'runtime_lifecycle_days']
        tools = ['MAIAN', 'Mythril', 'Semgrep', 'Slither', 'Solhint', 'VeriSmart']
        for tool in tools:
            for k in range(1, 9):
                names.append(f"{tool}_{k}")
        
        # 21 compiler dummy columns in alphabetical order
        top_compilers_alpha = [
            'comp_Other', 'comp_v0.4.11+commit.68ef5810', 'comp_v0.4.12+commit.194ff033', 
            'comp_v0.4.13+commit.fb4cb1a', 'comp_v0.4.14+commit.c2215d46', 'comp_v0.4.15+commit.bbb8e64f', 
            'comp_v0.4.16+commit.d7661dd9', 'comp_v0.4.17+commit.bdeb9e52', 'comp_v0.4.18+commit.9cf6e910', 
            'comp_v0.4.19+commit.c4cbbb05', 'comp_v0.4.19-nightly.2017.11.11+commit.284c3839', 
            'comp_v0.4.20+commit.3155dd80', 'comp_v0.4.20-nightly.2018.1.6+commit.2548228b', 
            'comp_v0.4.21+commit.dfe3193c', 'comp_v0.4.22+commit.4cb486ee', 'comp_v0.4.23+commit.124ca40d', 
            'comp_v0.4.24+commit.e67f0147', 'comp_v0.4.24-nightly.2018.5.16+commit.7f965c86', 
            'comp_v0.4.25+commit.59dbf8f1', 'comp_v0.4.26+commit.4563c3fc', 'comp_v0.4.8+commit.60cc1668'
        ]
        names.extend(top_compilers_alpha)
        return names

    def scan_address(self, address):
        """
        Scans a contract already indexed in the benchmark corpus.
        Computes forward predictions, calibrated thresholds, and gradient feature attribution.
        """
        clean_addr = address.strip().lower()
        if clean_addr not in self.addr_to_idx:
            raise KeyError(f"Address {address} not found in the indexed benchmark corpus. Use scan_features() for novel contracts.")
            
        target_idx = self.addr_to_idx[clean_addr]
        return self._evaluate_and_explain(target_idx, is_novel=False, address_label=clean_addr)

    def scan_features(self, feature_vector, compiler_version=None, address_label="Novel_Contract_0x"):
        """
        Inductively scans an unseen arbitrary contract feature vector.
        Performs dynamic heterogeneous graph insertion, nearest-neighbor peer linking,
        forward inference, and gradient attribution.
        """
        feat_tensor = torch.tensor(feature_vector, dtype=torch.float32, device=self.device)
        if feat_tensor.dim() == 1:
            feat_tensor = feat_tensor.unsqueeze(0)
            
        if feat_tensor.shape[1] != 72:
            raise ValueError(f"Expected 72 features, got {feat_tensor.shape[1]}")
            
        # 1. Identify Compiler Node Link
        comp_idx = 0 # Default to first compiler node ('Other' or top)
        if compiler_version and compiler_version in self.compiler_to_idx:
            comp_idx = self.compiler_to_idx[compiler_version]
            
        # 2. Find K=5 Nearest Neighbors in Contract Semantic Space
        with torch.no_grad():
            q_norm = F.normalize(feat_tensor, p=2, dim=1)
            sims = torch.mm(q_norm, self.x_contracts_norm.t()).squeeze(0)
            top_peer_indices = torch.topk(sims, k=5).indices.cpu().tolist()
            top_peer_sims = sims[top_peer_indices].cpu().tolist()
            
        # 3. Dynamic Inductive Graph Augmentation
        N_orig = self.graph['contract'].x.shape[0]
        N_new = N_orig # Index of novel contract
        
        # Append node feature
        feat_tensor.requires_grad_(True)
        aug_x_contract = torch.cat([self.graph['contract'].x, feat_tensor], dim=0)
        
        # Construct dynamic edges
        # A. Compiler bipartite edges
        edge_comp = self.graph['contract', 'compiled_with', 'compiler'].edge_index
        edge_inv_comp = self.graph['compiler', 'compiles', 'contract'].edge_index
        
        new_edge_comp = torch.cat([edge_comp, torch.tensor([[N_new], [comp_idx]], dtype=torch.long, device=self.device)], dim=1)
        new_edge_inv_comp = torch.cat([edge_inv_comp, torch.tensor([[comp_idx], [N_new]], dtype=torch.long, device=self.device)], dim=1)
        
        # B. Semantic k-NN edges
        edge_knn = self.graph['contract', 'semantic_knn', 'contract'].edge_index
        knn_src, knn_dst = [], []
        for p in top_peer_indices:
            knn_src.extend([N_new, p])
            knn_dst.extend([p, N_new])
        new_edge_knn = torch.cat([edge_knn, torch.tensor([knn_src, knn_dst], dtype=torch.long, device=self.device)], dim=1)
        
        aug_edges = {
            ('contract', 'compiled_with', 'compiler'): new_edge_comp,
            ('compiler', 'compiles', 'contract'): new_edge_inv_comp,
            ('contract', 'semantic_knn', 'contract'): new_edge_knn
        }
        
        return self._evaluate_and_explain(
            target_idx=N_new, 
            is_novel=True, 
            address_label=address_label,
            custom_x_contract=aug_x_contract,
            custom_edges=aug_edges,
            peer_indices=top_peer_indices,
            peer_similarities=top_peer_sims,
            novel_input_tensor=feat_tensor
        )

    def scan_custom_profile(self, 
                            nb_transactions=100, 
                            balance_eth=0.5, 
                            lifecycle_days=30, 
                            static_flags=None, 
                            compiler_version="v0.4.24+commit.e67f0147",
                            address_label="Simulated_Contract"):
        """
        High-level auditor interface: Ingests intuitive operational metrics,
        constructs the standardized 72-dim feature vector, and runs inductive scan.
        """
        # 1. Scale Runtime Features
        log_tx = np.log10(max(nb_transactions, 0) + 1.0)
        log_bal = np.log10(max(balance_eth, 0) + 1.0)
        lc_days = max(lifecycle_days, 0)
        
        runtime_raw = np.array([log_tx, log_bal, lc_days], dtype=np.float32)
        runtime_scaled = (runtime_raw - self.runtime_scaler_mean) / self.runtime_scaler_scale
        
        # 2. Static Tool Flags (48 features)
        tools = ['MAIAN', 'Mythril', 'Semgrep', 'Slither', 'Solhint', 'VeriSmart']
        tool_vec = np.zeros(48, dtype=np.float32)
        if static_flags:
            # static_flags: dict mapping tool name to list of detected vuln names
            for t_idx, tool in enumerate(tools):
                detected_vulns = static_flags.get(tool, [])
                for v in detected_vulns:
                    if v in self.VULN_NAMES:
                        k_idx = self.VULN_NAMES.index(v)
                        tool_vec[t_idx * 8 + k_idx] = 1.0
                        
        # 3. Compiler Dummy Vector (21 features)
        top_compilers_alpha = [
            'comp_Other', 'comp_v0.4.11+commit.68ef5810', 'comp_v0.4.12+commit.194ff033', 
            'comp_v0.4.13+commit.fb4cb1a', 'comp_v0.4.14+commit.c2215d46', 'comp_v0.4.15+commit.bbb8e64f', 
            'comp_v0.4.16+commit.d7661dd9', 'comp_v0.4.17+commit.bdeb9e52', 'comp_v0.4.18+commit.9cf6e910', 
            'comp_v0.4.19+commit.c4cbbb05', 'comp_v0.4.19-nightly.2017.11.11+commit.284c3839', 
            'comp_v0.4.20+commit.3155dd80', 'comp_v0.4.20-nightly.2018.1.6+commit.2548228b', 
            'comp_v0.4.21+commit.dfe3193c', 'comp_v0.4.22+commit.4cb486ee', 'comp_v0.4.23+commit.124ca40d', 
            'comp_v0.4.24+commit.e67f0147', 'comp_v0.4.24-nightly.2018.5.16+commit.7f965c86', 
            'comp_v0.4.25+commit.59dbf8f1', 'comp_v0.4.26+commit.4563c3fc', 'comp_v0.4.8+commit.60cc1668'
        ]
        comp_vec = np.zeros(len(top_compilers_alpha), dtype=np.float32)
        target_comp_key = f"comp_{compiler_version}"
        if target_comp_key in top_compilers_alpha:
            comp_vec[top_compilers_alpha.index(target_comp_key)] = 1.0
        else:
            comp_vec[0] = 1.0 # comp_Other
            
        full_feat = np.hstack([runtime_scaled, tool_vec, comp_vec]).astype(np.float32)
        return self.scan_features(full_feat, compiler_version=compiler_version, address_label=address_label)

    def _evaluate_and_explain(self, target_idx, is_novel=False, address_label="", 
                              custom_x_contract=None, custom_edges=None,
                              peer_indices=None, peer_similarities=None, novel_input_tensor=None):
        """
        Core inference & attribution execution loop.
        Computes forward logits, calibrated thresholds, and gradient-based feature attribution.
        """
        if custom_x_contract is not None:
            x_c = custom_x_contract
            edges = custom_edges
        else:
            x_c = self.graph['contract'].x.clone().detach()
            x_c.requires_grad_(True)
            edges = {k: self.graph[k].edge_index for k in self.graph.edge_types}
            
        x_dict = {'contract': x_c, 'compiler': self.graph['compiler'].x}
        
        # Forward pass
        logits = self.model(x_dict, edges)
        target_logits = logits[target_idx]
        probs = torch.sigmoid(target_logits).detach().cpu().numpy()
        
        # Ground truth check if indexed
        ground_truth = None
        if not is_novel and 'y' in self.graph['contract']:
            ground_truth = self.graph['contract'].y[target_idx].cpu().numpy().astype(int).tolist()
            
        # Calibrated decision classification
        verdict = {}
        flagged_categories = []
        highest_prob = 0.0
        
        for k, name in enumerate(self.VULN_NAMES):
            p = float(probs[k])
            tau = self.CALIBRATED_THRESHOLDS[name]
            is_vuln = bool(p >= tau)
            margin = float(p - tau)
            
            if is_vuln:
                flagged_categories.append(name)
            highest_prob = max(highest_prob, p)
            
            verdict[name] = {
                "probability": round(p, 4),
                "calibrated_threshold": tau,
                "is_vulnerable": is_vuln,
                "confidence_margin": round(margin, 4),
                "ground_truth": ground_truth[k] if ground_truth is not None else None
            }
            
        # Determine Overall Risk Level
        num_flagged = len(flagged_categories)
        if num_flagged >= 3 or any(name in ['Reentrancy', 'Access Control'] and verdict[name]['is_vulnerable'] for name in flagged_categories):
            risk_level = "CRITICAL"
        elif num_flagged >= 1:
            risk_level = "HIGH" if any(verdict[v]['probability'] > 0.85 for v in flagged_categories) else "MEDIUM"
        else:
            risk_level = "LOW / SAFE"
            
        # ---------------------------------------------------------------------
        # Feature Attribution via Input-x-Gradient Saliency
        # ---------------------------------------------------------------------
        attributions = {}
        # Explain each flagged vulnerability (or top predicted class if none flagged)
        classes_to_explain = [self.VULN_NAMES.index(v) for v in flagged_categories] if flagged_categories else [int(np.argmax(probs))]
        
        for class_idx in classes_to_explain:
            vuln_name = self.VULN_NAMES[class_idx]
            
            # Reset gradients
            if is_novel and novel_input_tensor is not None:
                if novel_input_tensor.grad is not None:
                    novel_input_tensor.grad.zero_()
            else:
                if x_c.grad is not None:
                    x_c.grad.zero_()
                    
            # Compute score and backward
            score = target_logits[class_idx]
            score.backward(retain_graph=True)
            
            if is_novel and novel_input_tensor is not None:
                grad_vec = novel_input_tensor.grad.squeeze(0).abs().cpu().numpy()
                feat_val = novel_input_tensor.detach().squeeze(0).abs().cpu().numpy()
            else:
                grad_vec = x_c.grad[target_idx].abs().cpu().numpy()
                feat_val = x_c[target_idx].detach().abs().cpu().numpy()
                
            # Input-x-Gradient Saliency: s = |grad| * |input|
            saliency = grad_vec * feat_val
            
            # Normalize saliency to percentages
            total_s = float(np.sum(saliency))
            s_norm = (saliency / (total_s + 1e-8)) * 100.0
            
            # Group saliency by feature modalities
            runtime_sal = float(np.sum(s_norm[0:3]))
            tools_sal = float(np.sum(s_norm[3:51]))
            compiler_sal = float(np.sum(s_norm[51:72]))
            
            # Rank top 5 individual contributing features
            top_feat_indices = np.argsort(saliency)[-5:][::-1]
            top_features = []
            for fi in top_feat_indices:
                top_features.append({
                    "feature_name": self.feature_names[fi],
                    "saliency_score": round(float(s_norm[fi]), 2),
                    "raw_input_value": round(float(feat_val[fi]), 4)
                })
                
            attributions[vuln_name] = {
                "modality_breakdown": {
                    "runtime_dynamics_pct": round(runtime_sal, 2),
                    "static_tool_consensus_pct": round(tools_sal, 2),
                    "compiler_version_affinity_pct": round(compiler_sal, 2)
                },
                "top_driving_features": top_features,
                "recommended_mitigation": self.REMEDIATIONS.get(vuln_name, "Audit external call pathways and access controls.")
            }
            
        # ---------------------------------------------------------------------
        # Relational Subgraph / Peer Attribution
        # ---------------------------------------------------------------------
        peer_attribution = []
        if is_novel and peer_indices is not None:
            for rank, p_idx in enumerate(peer_indices):
                peer_addr = self.addresses[p_idx]
                p_sim = peer_similarities[rank]
                peer_vulns = [self.VULN_NAMES[k] for k, v in enumerate(self.graph['contract'].y[p_idx]) if v == 1]
                peer_attribution.append({
                    "peer_address": peer_addr,
                    "cosine_similarity": round(float(p_sim), 4),
                    "peer_known_vulnerabilities": peer_vulns
                })
        elif not is_novel:
            # Query existing KNN neighbors for this indexed contract
            knn_edges = self.graph['contract', 'semantic_knn', 'contract'].edge_index
            src_mask = (knn_edges[0] == target_idx)
            neighbor_indices = knn_edges[1][src_mask].cpu().numpy().tolist()
            for p_idx in neighbor_indices[:5]:
                peer_addr = self.addresses[p_idx]
                peer_vulns = [self.VULN_NAMES[k] for k, v in enumerate(self.graph['contract'].y[p_idx]) if v == 1]
                peer_attribution.append({
                    "peer_address": peer_addr,
                    "peer_known_vulnerabilities": peer_vulns
                })
                
        # Synthesize Full Security Audit Report
        audit_report = {
            "target_contract": address_label,
            "is_novel_contract": is_novel,
            "overall_risk_assessment": risk_level,
            "flagged_vulnerabilities_count": num_flagged,
            "flagged_vulnerabilities": flagged_categories,
            "calibrated_vulnerability_verdicts": verdict,
            "gnn_explainer_feature_attribution": attributions,
            "topological_peer_influences": peer_attribution
        }
        
        return audit_report

    def print_audit_report(self, report):
        """
        Prints a formatted, human-readable terminal security monograph.
        """
        print("\n" + "=" * 90)
        print("          VS-HGNN PRACTICAL CONTRACT AUDIT & INTERPRETABILITY REPORT          ")
        print("=" * 90)
        print(f" Target Contract:   {report['target_contract']}")
        print(f" Ingestion Mode:    {'Inductive Dynamic Graph Insertion' if report['is_novel_contract'] else 'Transductive Corpus Index'}")
        
        # Color-coded Risk Level
        risk = report['overall_risk_assessment']
        print(f" OVERALL RISK LEVEL: [{risk}]")
        print(f" Flagged Categories: {report['flagged_vulnerabilities_count']} / 8")
        print("-" * 90)
        
        # Calibrated Verdict Table
        print(f"{'Vulnerability Category':<26} | {'Probability':<12} | {'Calibrated τ*':<14} | {'Status':<15} | {'Margin'}")
        print("-" * 90)
        for name, v in report['calibrated_vulnerability_verdicts'].items():
            status_str = "VULNERABLE [!]" if v['is_vulnerable'] else "CLEAN [OK]"
            margin_str = f"{v['confidence_margin']:+.4f}"
            print(f"{name:<26} | {v['probability']:<12.4f} | {v['calibrated_threshold']:<14.3f} | {status_str:<15} | {margin_str}")
        print("-" * 90)
        
        # GNN Explainer / Saliency Narrative
        print("\n>>> GNN EXPLAINER: FORENSIC FEATURE ATTRIBUTION & ROOT CAUSE ANALYSIS")
        print("    Deconstructs neural verdict via Input-x-Gradient saliency s_k = |∇_x z_k| ⊙ |x|")
        print("-" * 90)
        for vuln_name, attr in report['gnn_explainer_feature_attribution'].items():
            mod = attr['modality_breakdown']
            print(f" [*] Alert Breakdown for: {vuln_name.upper()}")
            print(f"     Modality Influence: Runtime Dynamics: {mod['runtime_dynamics_pct']:.1f}% | Static Tool Consensus: {mod['static_tool_consensus_pct']:.1f}% | Compiler Version Affinity: {mod['compiler_version_affinity_pct']:.1f}%")
            print("     Top Contributing Features:")
            for rank, feat in enumerate(attr['top_driving_features'], 1):
                print(f"       {rank}. {feat['feature_name']:<35} (Impact: {feat['saliency_score']:.1f}%, Value: {feat['raw_input_value']:.3f})")
            print(f"     Actionable Remediation: {attr['recommended_mitigation']}")
            print()
            
        # Peer Affinity / Relational Neighborhood
        if report['topological_peer_influences']:
            print(">>> RELATIONAL TOPOLOGY: TOP INFLUENTIAL HISTORICAL PEER CONTRACTS")
            print("    Identifies semantic k-NN neighbors passing topological messages through GATv2 layer")
            print("-" * 90)
            for rank, peer in enumerate(report['topological_peer_influences'], 1):
                sim_str = f" | Cosine Sim: {peer['cosine_similarity']:.4f}" if 'cosine_similarity' in peer else ""
                vulns_str = ", ".join(peer['peer_known_vulnerabilities']) if peer['peer_known_vulnerabilities'] else "None (Clean)"
                print(f"   [{rank}] Peer {peer['peer_address']}{sim_str}")
                print(f"       Historical Ground-Truth Exploits: {vulns_str}")
        print("=" * 90 + "\n")


# -----------------------------------------------------------------------------
# 3. Demonstration & CLI Entry Point
# -----------------------------------------------------------------------------
def run_demonstration(scanner):
    """
    Executes a comprehensive, multi-profile security audit demonstration across:
      1. Historical Reentrancy Exploit
      2. Historical Denial-of-Service (DoS) Exploit
      3. Multi-Vulnerability Exploit Contract (6 DASP Categories)
      4. Safe ERC-20 Token (Clean Baseline)
      5. Synthesized Novel Contract: The DAO Reentrancy Signature (Inductive Mode)
    """
    print("\n" + "#" * 90)
    print("      VS-HGNN STEP 3: COMPREHENSIVE PRACTICAL CONTRACT AUDIT SUITE")
    print("#" * 90)
    
    test_cases = [
        {
            "name": "Case Study 1: Reentrancy Exploit Contract",
            "address": "0xee6d409e9d08af082c2493ea955a0d3ea418dc0f"
        },
        {
            "name": "Case Study 2: Denial-of-Service (DoS) Exploit Contract",
            "address": "0xee045942b043b92cca0c454a553649eaa80873ea"
        },
        {
            "name": "Case Study 3: Multi-Vulnerability Exploit Contract (6 DASP Classes)",
            "address": "0xee58ee0b1519bb47801812a3a9c83ab600c63d81"
        },
        {
            "name": "Case Study 4: Verified Clean Contract (Safe Baseline)",
            "address": "0xef02c45c5913629dd12e7a9446455049775eec32"
        }
    ]
    
    for case in test_cases:
        print(f"\n[DEMO EXECUTION] Scanning {case['name']}...")
        report = scanner.scan_address(case['address'])
        scanner.print_audit_report(report)
        
    # Case Study 5: Novel Inductive Scan (Synthesized The DAO Reentrancy Profile)
    print("\n[DEMO EXECUTION] Scanning Case Study 5: Novel Synthesized Contract (The DAO Exploit Signature - Inductive Graph Insertion)...")
    dao_report = scanner.scan_custom_profile(
        nb_transactions=1250,
        balance_eth=250000.0,
        lifecycle_days=45,
        static_flags={
            'Slither': ['Reentrancy'],
            'Mythril': ['Reentrancy'],
            'Semgrep': ['Reentrancy']
        },
        compiler_version="v0.4.24+commit.e67f0147",
        address_label="0xbb9bc244d798123fde783fcc1c72d3bb8c189413 (The DAO Reentrancy Profile)"
    )
    scanner.print_audit_report(dao_report)

def main():
    parser = argparse.ArgumentParser(description="VS-HGNN Step 3: Practical Smart Contract Scanner & GNN Explainer")
    parser.add_argument("--address", type=str, help="Scan an existing indexed contract by 0x address")
    parser.add_argument("--demo", action="store_true", help="Run multi-contract security audit demonstration")
    parser.add_argument("--json", action="store_true", help="Output audit results in JSON format")
    parser.add_argument("--save-report", type=str, help="Save JSON audit report to file")
    
    args = parser.parse_args()
    
    # Initialize Scanner
    scanner = ContractScanner()
    
    if args.demo:
        run_demonstration(scanner)
        return
        
    if args.address:
        report = scanner.scan_address(args.address)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            scanner.print_audit_report(report)
            
        if args.save_report:
            with open(args.save_report, "w") as f:
                json.dump(report, f, indent=2)
            print(f"[+] Audit report saved to {args.save_report}")
        return
        
    # Default behavior if no args provided: run demo
    print("[i] No arguments specified. Running default demonstration suite (--demo). Use --help for CLI options.")
    run_demonstration(scanner)

if __name__ == "__main__":
    main()
