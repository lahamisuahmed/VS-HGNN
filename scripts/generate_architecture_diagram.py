#!/usr/bin/env python3
"""
scripts/generate_architecture_diagram.py
=============================================================================
VS-HGNN Architectural Blueprint & System Diagram Generator
Generates a publication-quality vector schematic (PNG at 300 DPI)
illustrating the complete end-to-end VS-HGNN architecture:
  1. Multi-Modal Node Feature Ingestion (72-dim Contract, 134-dim Compiler)
  2. Heterogeneous Relational Topology (Bipartite + Semantic k-NN)
  3. Relational Deep Neural Backbone (Projections + 2-Layer HeteroConv)
  4. Multi-Label Decision Head with Calibrated Thresholds (tau_k*)
  5. GNN Explainer & Subgraph Saliency Attribution Engine
=============================================================================
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, PathPatch
import matplotlib.patheffects as patheffects

def draw_rounded_box(ax, x, y, w, h, boxstyle="round,pad=0.03,rounding_size=0.02",
                     facecolor="#FFFFFF", edgecolor="#0F294A", linewidth=1.5, alpha=1.0, zorder=2):
    box = FancyBboxPatch((x, y), w, h, boxstyle=boxstyle,
                         facecolor=facecolor, edgecolor=edgecolor,
                         linewidth=linewidth, alpha=alpha, zorder=zorder)
    ax.add_patch(box)
    return box

def draw_arrow(ax, x1, y1, x2, y2, color="#0F294A", width=1.5, zorder=3):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle='-|>',
                            mutation_scale=14,
                            linewidth=width,
                            color=color,
                            zorder=zorder)
    ax.add_patch(arrow)

def generate_diagram():
    fig = plt.figure(figsize=(20, 11), dpi=300)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 11)
    ax.axis('off')
    
    # Background Canvas: clean white/light slate
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')
    
    # -------------------------------------------------------------------------
    # MASTER HEADER
    # -------------------------------------------------------------------------
    ax.text(10.0, 10.45, "VS-HGNN: Vulnerability-Specific Heterogeneous Graph Neural Network",
            ha='center', va='center', fontsize=18, fontweight='bold', color='#0F294A')
    ax.text(10.0, 10.12, "End-to-End System Architecture: Multi-Modal Ingestion, Relational Message Passing, Calibrated Decision Boundaries, and GNN Explainer",
            ha='center', va='center', fontsize=11, fontstyle='italic', color='#475569')

    # =========================================================================
    # COLUMN 1: MULTI-MODAL FEATURE INGESTION & GRAPH TOPOLOGY
    # =========================================================================
    # Outer Container 1
    draw_rounded_box(ax, 0.5, 0.7, 4.2, 9.1, facecolor="#EFF6FF", edgecolor="#3B82F6", linewidth=1.8)
    ax.text(2.6, 9.55, "PHASE 1: FEATURE INGESTION &\nRELATIONAL GRAPH TOPOLOGY", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#1D4ED8')
    
    # Box 1A: Smart Contract Node Representation
    draw_rounded_box(ax, 0.75, 5.85, 3.7, 3.4, facecolor="#FFFFFF", edgecolor="#2563EB", linewidth=1.2)
    ax.text(2.6, 9.0, "Contract Nodes: V_c (N = 7,487)", ha='center', va='center', fontsize=10, fontweight='bold', color='#0F294A')
    
    # Feature Slices inside Contract Box
    # Runtime
    draw_rounded_box(ax, 0.95, 8.05, 3.3, 0.7, facecolor="#DBEAFE", edgecolor="#3B82F6", linewidth=1.0)
    ax.text(2.6, 8.52, "Runtime Dynamics (d = 3)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#1E40AF')
    ax.text(2.6, 8.22, "log10(Tx + 1), log10(Balance + 1), Lifecycle", ha='center', va='center', fontsize=7.5, color='#334155')
    
    # Static Tools
    draw_rounded_box(ax, 0.95, 7.0, 3.3, 0.95, facecolor="#FEF3C7", edgecolor="#F59E0B", linewidth=1.0)
    ax.text(2.6, 7.68, "Static Tool Priors (d = 48)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#92400E')
    ax.text(2.6, 7.4, "6 Analyzers x 8 DASP Categories", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#B45309')
    ax.text(2.6, 7.15, "Slither, Mythril, Semgrep, Solhint, MAIAN, VeriSmart", ha='center', va='center', fontsize=7, color='#78350F')
    
    # Compiler Dummies
    draw_rounded_box(ax, 0.95, 6.05, 3.3, 0.85, facecolor="#E0E7FF", edgecolor="#6366F1", linewidth=1.0)
    ax.text(2.6, 6.65, "Compiler Affinity Vector (d = 21)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#3730A3')
    ax.text(2.6, 6.40, "Top 20 Solc Versions (One-Hot) + Other", ha='center', va='center', fontsize=7.5, color='#4338CA')
    ax.text(2.6, 6.18, "Combined: x_contract in R^72", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#1E293B')

    # Box 1B: Compiler Nodes
    draw_rounded_box(ax, 0.75, 4.45, 3.7, 1.25, facecolor="#FFFFFF", edgecolor="#0D9488", linewidth=1.2)
    ax.text(2.6, 5.48, "Compiler Nodes: V_m (M = 134)", ha='center', va='center', fontsize=10, fontweight='bold', color='#0F294A')
    ax.text(2.6, 5.15, "One-Hot Identity Matrix: x_compiler in R^134", ha='center', va='center', fontsize=8, color='#0F766E')
    ax.text(2.6, 4.80, "Represents exact Solc compiler releases\n(e.g., v0.4.24, v0.4.25, nightly)", ha='center', va='center', fontsize=7.5, color='#334155')

    # Box 1C: Heterogeneous Relational Topology
    draw_rounded_box(ax, 0.75, 0.95, 3.7, 3.3, facecolor="#F0FDF4", edgecolor="#16A34A", linewidth=1.2)
    ax.text(2.6, 4.05, "Heterogeneous Edge Relations (E)", ha='center', va='center', fontsize=10, fontweight='bold', color='#166534')
    
    # Relation 1
    draw_rounded_box(ax, 0.95, 3.1, 3.3, 0.75, facecolor="#FFFFFF", edgecolor="#22C55E", linewidth=1.0)
    ax.text(2.6, 3.6, "1. ('contract', 'compiled_with', 'compiler')", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#15803D')
    ax.text(2.6, 3.3, "Bipartite Link (7,487 edges)", ha='center', va='center', fontsize=7.5, color='#374151')

    # Relation 2
    draw_rounded_box(ax, 0.95, 2.15, 3.3, 0.8, facecolor="#FFFFFF", edgecolor="#22C55E", linewidth=1.0)
    ax.text(2.6, 2.7, "2. ('compiler', 'compiles', 'contract')", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#15803D')
    ax.text(2.6, 2.38, "Inverse Bipartite Link (7,487 edges)", ha='center', va='center', fontsize=7.5, color='#374151')

    # Relation 3
    draw_rounded_box(ax, 0.95, 1.15, 3.3, 0.85, facecolor="#FFFFFF", edgecolor="#16A34A", linewidth=1.0)
    ax.text(2.6, 1.75, "3. ('contract', 'semantic_knn', 'contract')", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#15803D')
    ax.text(2.6, 1.48, "Cosine Metric Affinity (K = 5)", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#047857')
    ax.text(2.6, 1.28, "37,435 Homogeneous Contract Edges", ha='center', va='center', fontsize=7, color='#4B5563')

    # Connector 1 -> 2
    draw_arrow(ax, 4.7, 5.25, 5.3, 5.25, color="#2563EB", width=2.5)

    # =========================================================================
    # COLUMN 2: RELATIONAL DEEP NEURAL BACKBONE (VS-HGNN CORE)
    # =========================================================================
    draw_rounded_box(ax, 5.3, 0.7, 5.2, 9.1, facecolor="#F8FAFC", edgecolor="#0F294A", linewidth=1.8)
    ax.text(7.9, 9.55, "PHASE 2: RELATIONAL MESSAGE PASSING\nDEEP NEURAL BACKBONE", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#0F294A')

    # Shared Input Projections
    draw_rounded_box(ax, 5.55, 7.8, 4.7, 1.4, facecolor="#FFFFFF", edgecolor="#64748B", linewidth=1.2)
    ax.text(7.9, 8.95, "Shared Latent Projection Layers", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#0F294A')
    ax.text(7.9, 8.6, "Proj_contract: Linear(72 -> 128) + LayerNorm + ELU", ha='center', va='center', fontsize=8, color='#1E293B')
    ax.text(7.9, 8.3, "Proj_compiler: Linear(134 -> 128) + LayerNorm + ELU", ha='center', va='center', fontsize=8, color='#1E293B')
    ax.text(7.9, 8.0, "Common Latent Banach Space: h in R^128", ha='center', va='center', fontsize=8, fontweight='bold', color='#2563EB')

    draw_arrow(ax, 7.9, 7.8, 7.9, 7.4, color="#64748B", width=1.5)

    # Layer 1: HeteroConv (Attention & Convolution)
    draw_rounded_box(ax, 5.55, 4.4, 4.7, 3.0, facecolor="#EFF6FF", edgecolor="#2563EB", linewidth=1.4)
    ax.text(7.9, 7.15, "Relational Layer 1: HeteroConv (aggr = 'sum')", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#1D4ED8')
    
    # Sub-convolutions
    draw_rounded_box(ax, 5.75, 6.2, 4.3, 0.65, facecolor="#FFFFFF", edgecolor="#3B82F6", linewidth=1.0)
    ax.text(7.9, 6.55, "('contract', 'semantic_knn', 'contract'):", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#1E3A8A')
    ax.text(7.9, 6.32, "GATv2Conv(128 -> 128, heads=2, concat=False, dropout=0.25)", ha='center', va='center', fontsize=7.2, color='#1E40AF')

    draw_rounded_box(ax, 5.75, 5.4, 4.3, 0.65, facecolor="#FFFFFF", edgecolor="#3B82F6", linewidth=1.0)
    ax.text(7.9, 5.75, "('contract', 'compiled_with', 'compiler'):", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#1E3A8A')
    ax.text(7.9, 5.52, "SAGEConv((128, 128) -> 128)", ha='center', va='center', fontsize=7.2, color='#1E40AF')

    draw_rounded_box(ax, 5.75, 4.6, 4.3, 0.65, facecolor="#FFFFFF", edgecolor="#3B82F6", linewidth=1.0)
    ax.text(7.9, 4.95, "('compiler', 'compiles', 'contract'):", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#1E3A8A')
    ax.text(7.9, 4.72, "SAGEConv((128, 128) -> 128)", ha='center', va='center', fontsize=7.2, color='#1E40AF')

    # Residual 1 + Norm
    draw_rounded_box(ax, 5.55, 3.8, 4.7, 0.5, facecolor="#DBEAFE", edgecolor="#2563EB", linewidth=1.0)
    ax.text(7.9, 4.05, "h^(1) = LayerNorm(h^(0) + ELU(out1)) + Dropout(p=0.25)", ha='center', va='center', fontsize=8, fontweight='bold', color='#1E3A8A')

    draw_arrow(ax, 7.9, 3.8, 7.9, 3.4, color="#64748B", width=1.5)

    # Layer 2: HeteroConv (Mean Aggregation)
    draw_rounded_box(ax, 5.55, 1.45, 4.7, 1.95, facecolor="#F0FDF4", edgecolor="#16A34A", linewidth=1.4)
    ax.text(7.9, 3.18, "Relational Layer 2: HeteroConv (aggr = 'mean')", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#15803D')
    ax.text(7.9, 2.85, "Captures 2-hop structural context over heterogeneous paths", ha='center', va='center', fontsize=7.5, color='#166534')
    ax.text(7.9, 2.55, "SAGEConv on semantic_knn, compiled_with, compiles", ha='center', va='center', fontsize=7.5, color='#166534')
    
    # Residual 2 + Norm
    draw_rounded_box(ax, 5.75, 1.6, 4.3, 0.65, facecolor="#FFFFFF", edgecolor="#16A34A", linewidth=1.0)
    ax.text(7.9, 1.95, "h^(2) = LayerNorm(h^(1) + ELU(out2))", ha='center', va='center', fontsize=8, fontweight='bold', color='#14532D')
    ax.text(7.9, 1.73, "Final Contract Embedding: h_contract in R^128", ha='center', va='center', fontsize=7.5, color='#166534')

    # Connector 2 -> 3
    draw_arrow(ax, 10.5, 5.25, 11.1, 5.25, color="#0F294A", width=2.5)

    # =========================================================================
    # COLUMN 3: MULTI-LABEL CLASSIFIER & CALIBRATED DECISION HEAD
    # =========================================================================
    draw_rounded_box(ax, 11.1, 4.5, 4.2, 5.3, facecolor="#FEF3C7", edgecolor="#D97706", linewidth=1.8)
    ax.text(13.2, 9.55, "PHASE 3: CALIBRATED DECISION HEAD\n& LOSS REGIME", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#B45309')

    # Multi-Label Classification Head
    draw_rounded_box(ax, 11.35, 7.45, 3.7, 1.7, facecolor="#FFFFFF", edgecolor="#F59E0B", linewidth=1.2)
    ax.text(13.2, 8.9, "Multi-Label Classification Head", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#0F294A')
    ax.text(13.2, 8.55, "Linear(128 -> 64) + LayerNorm + ELU", ha='center', va='center', fontsize=8, color='#1E293B')
    ax.text(13.2, 8.25, "Dropout(0.25) + Linear(64 -> 8)", ha='center', va='center', fontsize=8, color='#1E293B')
    ax.text(13.2, 7.8, "Output Logits: z in R^8  |  Sigmoids: p in [0,1]^8", ha='center', va='center', fontsize=8, fontweight='bold', color='#B45309')

    # Training Loss: Positive-Class Weighted BCE
    draw_rounded_box(ax, 11.35, 6.0, 3.7, 1.25, facecolor="#FFFFFF", edgecolor="#F59E0B", linewidth=1.2)
    ax.text(13.2, 7.0, "Positive-Class Weighted BCE Loss", ha='center', va='center', fontsize=9, fontweight='bold', color='#92400E')
    ax.text(13.2, 6.65, "Loss = - sum [ w_k y_k log(p_k) + (1-y_k) log(1-p_k) ]", ha='center', va='center', fontsize=7.2, color='#78350F')
    ax.text(13.2, 6.25, "w_pos = (N_neg / N_pos) clamped [0.5, 50.0]", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#92400E')

    # Optimal Decision Boundaries Table
    draw_rounded_box(ax, 11.35, 4.65, 3.7, 1.2, facecolor="#FFFFFF", edgecolor="#B45309", linewidth=1.2)
    ax.text(13.2, 5.65, "Validation-Calibrated Optimal Thresholds (tau*)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#92400E')
    ax.text(13.2, 5.35, "Reentrancy: 0.530 | Access Control: 0.370", ha='center', va='center', fontsize=7.5, color='#1E293B')
    ax.text(13.2, 5.10, "Arithmetic: 0.540 | Unchecked Returns: 0.410", ha='center', va='center', fontsize=7.5, color='#1E293B')
    ax.text(13.2, 4.85, "DoS: 0.810 | Bad Rand: 0.380 | FR: 0.450 | Time: 0.600", ha='center', va='center', fontsize=7.2, color='#1E293B')

    # =========================================================================
    # COLUMN 4: GNN EXPLAINER & SUBGRAPH ATTRIBUTION ENGINE
    # =========================================================================
    draw_rounded_box(ax, 11.1, 0.7, 4.2, 3.6, facecolor="#FDF2F8", edgecolor="#DB2777", linewidth=1.8)
    ax.text(13.2, 4.05, "PHASE 4: GNN EXPLAINER &\nSUBGRAPH ATTRIBUTION", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#BE185D')

    # Saliency Box
    draw_rounded_box(ax, 11.35, 2.3, 3.7, 1.5, facecolor="#FFFFFF", edgecolor="#EC4899", linewidth=1.2)
    ax.text(13.2, 3.55, "Input-x-Gradient Saliency Attribution", ha='center', va='center', fontsize=9, fontweight='bold', color='#9D174D')
    ax.text(13.2, 3.25, "s_k = | partial z_k / partial x | * | x |", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#BE185D')
    ax.text(13.2, 2.95, "Modality Influence Partitioning:", ha='center', va='center', fontsize=7.5, color='#831843')
    ax.text(13.2, 2.70, "Runtime Dynamics  ||  Tool Consensus  ||  Solc Affinity", ha='center', va='center', fontsize=7.2, fontweight='bold', color='#0F294A')
    ax.text(13.2, 2.45, "Provides axiomatic proof of root-cause drivers", ha='center', va='center', fontsize=7, color='#475569')

    # Relational Topology Box
    draw_rounded_box(ax, 11.35, 0.9, 3.7, 1.25, facecolor="#FFFFFF", edgecolor="#EC4899", linewidth=1.2)
    ax.text(13.2, 1.95, "Topological Peer Provenance", ha='center', va='center', fontsize=9, fontweight='bold', color='#9D174D')
    ax.text(13.2, 1.65, "Traces GATv2 relational attention alpha_{u, v}", ha='center', va='center', fontsize=7.5, color='#831843')
    ax.text(13.2, 1.35, "Retrieves nearest historical exploit contracts\n(e.g., The DAO-era reentrancy peers)", ha='center', va='center', fontsize=7.2, color='#1E293B')

    # Connector 3 -> 5
    draw_arrow(ax, 15.3, 5.25, 15.9, 5.25, color="#10B981", width=2.5)

    # =========================================================================
    # COLUMN 5: AUDITOR-FACING SECURITY VERDICTS & REMEDIATION
    # =========================================================================
    draw_rounded_box(ax, 15.9, 0.7, 3.6, 9.1, facecolor="#ECFDF5", edgecolor="#059669", linewidth=1.8)
    ax.text(17.7, 9.55, "OUTPUT: AUDITOR MONOGRAPH &\nACTIONABLE MITIGATIONS", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#047857')

    # Output Card 1: Calibrated Multi-Label Classification
    draw_rounded_box(ax, 16.15, 6.2, 3.1, 2.9, facecolor="#FFFFFF", edgecolor="#10B981", linewidth=1.2)
    ax.text(17.7, 8.85, "Calibrated Audit Verdict", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#065F46')
    
    categories = [
        ("Reentrancy", "p=0.997", "VULN [!]"),
        ("Access Control", "p=0.312", "CLEAN"),
        ("Arithmetic", "p=0.066", "CLEAN"),
        ("Unchecked Ret", "p=0.015", "CLEAN"),
        ("DoS", "p=0.022", "CLEAN"),
        ("Bad Randomness", "p=0.010", "CLEAN"),
        ("Front Running", "p=0.025", "CLEAN"),
        ("Time Manip", "p=0.048", "CLEAN")
    ]
    for i, (cat, p_str, stat) in enumerate(categories):
        y_pos = 8.45 - i * 0.28
        ax.text(16.35, y_pos, cat, ha='left', va='center', fontsize=7, color='#1E293B')
        ax.text(17.55, y_pos, p_str, ha='center', va='center', fontsize=7, color='#475569')
        c_stat = "#DC2626" if "VULN" in stat else "#059669"
        ax.text(18.95, y_pos, stat, ha='right', va='center', fontsize=7, fontweight='bold', color=c_stat)

    # Output Card 2: Risk Assessment
    draw_rounded_box(ax, 16.15, 4.45, 3.1, 1.55, facecolor="#FFFFFF", edgecolor="#DC2626", linewidth=1.2)
    ax.text(17.7, 5.75, "Overall Risk Level", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#991B1B')
    
    draw_rounded_box(ax, 16.4, 4.95, 2.6, 0.55, facecolor="#FEE2E2", edgecolor="#DC2626", linewidth=1.0)
    ax.text(17.7, 5.22, "CRITICAL RISK", ha='center', va='center', fontsize=9, fontweight='bold', color='#991B1B')
    ax.text(17.7, 4.65, "Confidence Margin: Delta = +0.4670", ha='center', va='center', fontsize=7.5, fontstyle='italic', color='#7F1D1D')

    # Output Card 3: Actionable Mitigations
    draw_rounded_box(ax, 16.15, 1.0, 3.1, 3.25, facecolor="#FFFFFF", edgecolor="#10B981", linewidth=1.2)
    ax.text(17.7, 4.0, "Auditor Mitigation Guide", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#065F46')
    
    remediations = [
        "1. Checks-Effects-Interactions (CEI)",
        "2. OpenZeppelin ReentrancyGuard",
        "3. SafeMath / Solidity ^0.8.0 Guard",
        "4. Enforce strict require(success)",
        "5. Pull-over-push withdrawal pattern",
        "6. Chainlink VRF for true entropy",
        "7. Commit-Reveal against MEV / FR",
        "8. Avoid block.timestamp equality"
    ]
    for i, rem in enumerate(remediations):
        y_pos = 3.65 - i * 0.32
        ax.text(16.35, y_pos, rem, ha='left', va='center', fontsize=7, color='#1E293B')

    # -------------------------------------------------------------------------
    # FOOTER BAR: SUMMARY SPECIFICATIONS
    # -------------------------------------------------------------------------
    footer_text = (
        "Dataset: 7,487 Contracts | 23.3M Transactions | 7,621 Nodes (7,487 Contracts + 134 Compilers) | 52,409 Edges\n"
        "Performance: Test Macro-F1 = 0.9633 (+32.78 vs Slither) | Wilcoxon p = 0.003906 | McNemar chi^2 = 900.55 (p < 10^-15) | Latency = 4.81 ms/contract (GPU)"
    )
    ax.text(10.0, 0.35, footer_text, ha='center', va='center', fontsize=8.5, color='#475569')

    # Save
    out_dir = "data/models"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "vshgnn_architecture.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    
    # Also save to root for easy user access
    root_path = "VS_HGNN_ARCHITECTURE.png"
    import shutil
    shutil.copyfile(out_path, root_path)
    print(f"[+] Architecture schematic generated successfully at:\n    1. {out_path}\n    2. {root_path}")
    return root_path

if __name__ == "__main__":
    generate_diagram()
