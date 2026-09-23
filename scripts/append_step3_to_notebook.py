#!/usr/bin/env python3
"""
scripts/append_step3_to_notebook.py
Appends Section 10 (Step 3: Practical Contract Scanner & GNN Explainer) to vsgnn.ipynb.
"""

import json
import os

def append_section_10():
    nb_path = "vsgnn.ipynb"
    if not os.path.exists(nb_path):
        raise FileNotFoundError(f"{nb_path} not found.")
        
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    # Check if Section 10 is already present
    for cell in nb["cells"]:
        if cell["cell_type"] == "markdown":
            for line in cell.get("source", []):
                if "## 10. Step 3: Practical Contract Scanner" in line:
                    print("[i] Section 10 is already present in notebook. Overwriting Section 10.")
                    # Remove existing Section 10 cells
                    idx = nb["cells"].index(cell)
                    nb["cells"] = nb["cells"][:idx]
                    break
                    
    # Define Section 10 Markdown Cell
    markdown_content = [
        "## 10. Step 3: Practical Contract Scanner, Inductive Graph Insertion & GNN Explainer\n",
        "\n",
        "Step 3 operationalizes the validated **VS-HGNN** architecture from a testbed into a production-grade, interpretable security tool:\n",
        "\n",
        "1. **Inductive Dynamic Graph Insertion**:\n",
        "   Arbitrary unseen smart contracts $u^*$ (not present in the training corpus) are dynamically projected into the heterogeneous graph via cosine metric affinity ($K=5$ semantic peers) and bipartite compiler version links, enabling $\\mathcal{O}(1)$ insertion without full retraining.\n",
        "2. **Calibrated Decision Thresholds ($\\boldsymbol{\\tau}^*$)**:\n",
        "   Predictions are evaluated against validation-calibrated optimal thresholds $\\boldsymbol{\\tau}^* = [0.530, 0.370, 0.540, 0.410, 0.810, 0.380, 0.450, 0.600]$, eliminating false positives on imbalanced classes.\n",
        "3. **GNN Explainer & Gradient Saliency Attribution**:\n",
        "   Deconstructs neural verdicts via Input-$\\times$-Gradient saliency:\n",
        "   $$\\mathbf{s}_{u^*, k} = \\left| \\nabla_{\\mathbf{x}_{u^*}} z_{u^*, k} \\right| \\odot |\\mathbf{x}_{u^*}|$$\n",
        "   partitioning influence into **Runtime Dynamics**, **Static Tool Consensus**, and **Compiler Version Affinity**, and extracting topological historical peer influences.\n",
        "\n",
        "The cell below initializes the `ContractScanner` and executes full forensic audits across both indexed contracts (Reentrancy exploit, Clean baseline) and a novel synthesized contract (The DAO exploit profile in inductive mode).\n"
    ]
    
    code_content = [
        "# =============================================================================\n",
        "# Section 10: Step 3 Practical Contract Scanner & GNN Explainer Demonstration\n",
        "# =============================================================================\n",
        "import os\n",
        "import sys\n",
        "import json\n",
        "import torch\n",
        "import numpy as np\n",
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "\n",
        "# Ensure scripts directory is in path\n",
        "sys.path.insert(0, os.getcwd())\n",
        "from scripts.scan_contract import ContractScanner\n",
        "\n",
        "# Initialize the Practical Scanner\n",
        "scanner = ContractScanner()\n",
        "print('=' * 85)\n",
        "print('VS-HGNN STEP 3: PRACTICAL CONTRACT SCANNER & GNN EXPLAINER READY')\n",
        "print('=' * 85)\n",
        "\n",
        "# 1. Case Study 1: Verified Reentrancy Exploit Contract\n",
        "addr_reentrancy = '0xee6d409e9d08af082c2493ea955a0d3ea418dc0f'\n",
        "report_reent = scanner.scan_address(addr_reentrancy)\n",
        "scanner.print_audit_report(report_reent)\n",
        "\n",
        "# 2. Case Study 2: Verified Clean Contract (Safe Baseline)\n",
        "addr_clean = '0xef02c45c5913629dd12e7a9446455049775eec32'\n",
        "report_clean = scanner.scan_address(addr_clean)\n",
        "scanner.print_audit_report(report_clean)\n",
        "\n",
        "# 3. Case Study 3: Novel Synthesized Inductive Scan (The DAO Exploit Signature)\n",
        "print('\\n>>> EXECUTING INDUCTIVE SCAN: The DAO Exploit Profile...')\n",
        "report_dao = scanner.scan_custom_profile(\n",
        "    nb_transactions=1250,\n",
        "    balance_eth=250000.0,\n",
        "    lifecycle_days=45,\n",
        "    static_flags={\n",
        "        'Slither': ['Reentrancy'],\n",
        "        'Mythril': ['Reentrancy'],\n",
        "        'Semgrep': ['Reentrancy']\n",
        "    },\n",
        "    compiler_version='v0.4.24+commit.e67f0147',\n",
        "    address_label='0xbb9bc244d798123fde783fcc1c72d3bb8c189413 (The DAO Reentrancy Signature)'\n",
        ")\n",
        "scanner.print_audit_report(report_dao)\n",
        "\n",
        "# 4. Visual Saliency Attribution Decomposition\n",
        "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
        "\n",
        "# Modality Pie Chart\n",
        "dao_sal = report_dao['gnn_explainer_feature_attribution']['Reentrancy']['modality_breakdown']\n",
        "labels = ['Runtime Dynamics', 'Static Tool Consensus', 'Compiler Version Affinity']\n",
        "sizes = [dao_sal['runtime_dynamics_pct'], dao_sal['static_tool_consensus_pct'], dao_sal['compiler_version_affinity_pct']]\n",
        "colors = ['#3B82F6', '#10B981', '#F59E0B']\n",
        "\n",
        "axes[0].pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140, \n",
        "            textprops={'fontsize': 10, 'weight': 'bold'}, explode=(0.05, 0.05, 0.05))\n",
        "axes[0].set_title('The DAO Exploit: Modality Saliency Decomposition (s_k)', fontsize=11, fontweight='bold', pad=10)\n",
        "\n",
        "# Top-5 Driving Features Bar Chart\n",
        "top_feats = report_dao['gnn_explainer_feature_attribution']['Reentrancy']['top_driving_features']\n",
        "feat_names = [f['feature_name'] for f in top_feats][::-1]\n",
        "feat_impacts = [f['saliency_score'] for f in top_feats][::-1]\n",
        "\n",
        "axes[1].barh(feat_names, feat_impacts, color='#0F294A', edgecolor='#2563EB', alpha=0.85)\n",
        "axes[1].set_xlabel('Attribution Saliency Impact (%)', fontsize=10, fontweight='bold')\n",
        "axes[1].set_title('Top Driving Features for Reentrancy Verdict', fontsize=11, fontweight='bold')\n",
        "axes[1].grid(axis='x', linestyle='--', alpha=0.5)\n",
        "\n",
        "plt.tight_layout()\n",
        "os.makedirs('data/models', exist_ok=True)\n",
        "plt.savefig('data/models/step3_attribution_demo.png', dpi=300)\n",
        "plt.show()\n",
        "plt.close()\n",
        "print('[+] Step 3 Contract Scanner & GNN Explainer Demonstration Completed Successfully!')\n"
    ]
    
    # Append cells
    cell_md = {
        "cell_type": "markdown",
        "metadata": {},
        "source": markdown_content
    }
    
    cell_code = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": code_content
    }
    
    nb["cells"].append(cell_md)
    nb["cells"].append(cell_code)
    
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
        
    print(f"[+] Successfully appended Section 10 to {nb_path} (Total cells: {len(nb['cells'])})")

if __name__ == "__main__":
    append_section_10()
