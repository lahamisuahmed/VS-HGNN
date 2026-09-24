#!/usr/bin/env python3
"""
scripts/append_step4_to_notebook.py
Appends Section 11 (Step 4: Architectural Ablation Studies & Sensitivity Analysis) to vsgnn.ipynb.
Specifically configured for Google Colab execution so heavy training runs on Colab's cloud GPU.
"""

import json
import os

def append_section_11():
    nb_path = "vsgnn.ipynb"
    if not os.path.exists(nb_path):
        raise FileNotFoundError(f"{nb_path} not found.")
        
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    # Check if Section 11 is already present and remove if so
    for cell in nb["cells"]:
        if cell["cell_type"] == "markdown":
            for line in cell.get("source", []):
                if "## 11. Step 4: Architectural Ablation Studies" in line:
                    print("[i] Section 11 is already present in notebook. Overwriting Section 11.")
                    idx = nb["cells"].index(cell)
                    nb["cells"] = nb["cells"][:idx]
                    break
                    
    # Define Section 11 Markdown Cell
    markdown_content = [
        "## 11. Step 4: Architectural Ablation Studies & Component Sensitivity Analysis\n",
        "\n",
        "To rigorously prove the causal necessity of each module in the **VS-HGNN** framework for peer-reviewed publication, this section executes a controlled ablation suite isolating structural, feature, and optimization components:\n",
        "\n",
        "1. **Variant 0 (Full VS-HGNN + Calibrated $\\boldsymbol{\\tau}^*$)**: Baseline gold standard with all components active.\n",
        "2. **Ablation 1 (w/o Compiler Nodes)**: Strips $\\mathcal{V}_{\\text{compiler}}$ and bipartite edges (`compiled_with`, `compiles`), evaluating a homogeneous contract $k$-NN graph.\n",
        "3. **Ablation 2 (w/o Relational Attention)**: Replaces dynamic GATv2 anisotropic attention on contract $k$-NN with uniform isotropic mean aggregation (`SAGEConv`).\n",
        "4. **Ablation 3 (w/o Runtime Dynamics)**: Zeroes out transaction count, balance, and lifecycle days, testing a purely static tool feature setup.\n",
        "5. **Ablation 4 (w/o Static Tool Priors)**: Zeroes out all 48 static analyzer detection features, testing whether graph topology and runtime dynamics alone can deduce vulnerabilities from scratch.\n",
        "6. **Ablation 5 (w/o Positive-Class Loss Weighting)**: Trains with standard unweighted BCE loss ($w_{\\text{pos}} = 1.0$), demonstrating minority exploit gradient collapse.\n",
        "7. **Ablation 6 (w/o Threshold Calibration)**: Evaluates the full model with the canonical threshold $\\tau = 0.5$ versus validation-calibrated $\\boldsymbol{\\tau}^*$.\n",
        "\n",
        "> **Google Colab Cloud Execution Notice**: The cell below is configured for cloud acceleration. If running in Colab, you can execute `!python scripts/run_ablations.py` to train all variants on Colab's cloud GPU (T4/V100/A100) without using local computer compute.\n"
    ]
    
    code_content = [
        "# =============================================================================\n",
        "# Section 11: Architectural Ablation Suite Execution & Sensitivity Analysis\n",
        "# (Configured for Google Colab Cloud GPU Training)\n",
        "# =============================================================================\n",
        "import os\n",
        "import sys\n",
        "import json\n",
        "import torch\n",
        "import numpy as np\n",
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "\n",
        "# 1. Hardware Environment Check\n",
        "device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')\n",
        "print(f'[+] Execution Environment Device: {device}')\n",
        "if torch.cuda.is_available():\n",
        "    print(f'[+] Google Colab Cloud GPU Detected: {torch.cuda.get_device_name(0)}')\n",
        "\n",
        "# Set to True if you wish to trigger a full re-training of all 6 ablations on Colab GPU:\n",
        "FORCE_COLAB_RETRAIN = False\n",
        "\n",
        "ablation_json = 'data/models/ablation_results.json'\n",
        "if FORCE_COLAB_RETRAIN or not os.path.exists(ablation_json):\n",
        "    print('[*] Initiating full architectural ablation suite execution...')\n",
        "    os.system('python scripts/run_ablations.py')\n",
        "else:\n",
        "    print(f'[+] Found existing benchmark results at {ablation_json}. Loading for analysis...')\n",
        "\n",
        "# 2. Load and Display Comparative Ablation Matrix\n",
        "with open(ablation_json, 'r') as f:\n",
        "    abl_data = json.load(f)\n",
        "\n",
        "records = []\n",
        "for model_name, stats in abl_data.items():\n",
        "    delta = f\"{stats['macro_f1_delta']:+.4f}\" if not stats.get('is_baseline', False) else 'BASELINE'\n",
        "    records.append({\n",
        "        'Architectural Variant': model_name,\n",
        "        'Macro-F1': round(stats['macro_f1'], 4),\n",
        "        'Micro-F1': round(stats['micro_f1'], 4),\n",
        "        'Hamming Loss': round(stats['hamming_loss'], 4),\n",
        "        'Delta vs Baseline': delta\n",
        "    })\n",
        "\n",
        "df_ablations = pd.DataFrame(records)\n",
        "print('\\n' + '=' * 105)\n",
        "print('MASTER ARCHITECTURAL ABLATION SUITE (1,124 Unseen Test Contracts across 8 DASP Classes)')\n",
        "print('=' * 105)\n",
        "display(df_ablations) if 'display' in globals() else print(df_ablations.to_string(index=False))\n",
        "print('=' * 105)\n",
        "\n",
        "# 3. Plot Component Sensitivity Bar Chart\n",
        "fig, ax = plt.subplots(figsize=(12, 6))\n",
        "\n",
        "variants = [r['Architectural Variant'].split(':')[0] for r in records]\n",
        "macro_f1s = [r['Macro-F1'] for r in records]\n",
        "colors = ['#10B981', '#3B82F6', '#6366F1', '#8B5CF6', '#F59E0B', '#EF4444', '#EC4899']\n",
        "\n",
        "bars = ax.barh(variants[::-1], macro_f1s[::-1], color=colors[::-1], edgecolor='#0F294A', alpha=0.85, height=0.6)\n",
        "ax.set_xlim(0, 1.05)\n",
        "ax.set_xlabel('Macro-F1 Score on Unseen Test Contracts', fontsize=11, fontweight='bold')\n",
        "ax.set_title('VS-HGNN Architectural Component Ablation & Sensitivity Analysis', fontsize=13, fontweight='bold', pad=12)\n",
        "ax.grid(axis='x', linestyle='--', alpha=0.5)\n",
        "\n",
        "# Annotate exact scores\n",
        "for bar in bars:\n",
        "    width = bar.get_width()\n",
        "    ax.text(width + 0.015, bar.get_y() + bar.get_height()/2, f'{width:.4f}', \n",
        "            ha='left', va='center', fontsize=9.5, fontweight='bold', color='#0F294A')\n",
        "\n",
        "plt.tight_layout()\n",
        "os.makedirs('data/models', exist_ok=True)\n",
        "plt.savefig('data/models/ablation_sensitivity_radar.png', dpi=300)\n",
        "plt.show()\n",
        "plt.close()\n",
        "print('[+] Section 11 Ablation Analysis Completed Successfully!')\n"
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
        
    print(f"[+] Successfully appended Section 11 to {nb_path} (Total cells: {len(nb['cells'])})")

if __name__ == "__main__":
    append_section_11()
