import json

def append_section_9():
    nb_path = "vsgnn.ipynb"
    with open(nb_path, "r") as f:
        nb = json.load(f)
        
    markdown_cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "---\n",
            "## 9. Decision Threshold Calibration & Master Comparative Benchmark\n",
            "\n",
            "### 9.1 Validation-Guided Threshold Calibration ($\\tau_k^*$)\n",
            "In real-world Ethereum smart contracts, vulnerabilities are heavily imbalanced (e.g., Access Control at 73.1% vs. Front Running at 2.56%). Standard classifiers use a generic decision threshold of $\\tau = 0.5$, which penalizes sparse and complex exploit categories.\n",
            "\n",
            "We calibrate optimal decision boundaries $\\tau_k^* \\in [0.05, 0.95]$ on the validation partition to maximize per-class $F_1$:\n",
            "$$\\tau_k^* = \\arg\\max_{\\tau \\in (0, 1)} F_1^{(k)}(\\tau)$$\n",
            "\n",
            "### 9.2 Comprehensive Baseline Benchmark\n",
            "To prove both the value of multi-modal features and the necessity of heterogeneous relational message passing, we benchmark **VS-HGNN** against:\n",
            "1. **Automated Static Analyzers**: Slither, Mythril, Solhint, VeriSmart, MAIAN, Semgrep.\n",
            "2. **Classical Machine Learning (Tabular Features)**: Class-Weighted Logistic Regression & Balanced Random Forest.\n",
            "3. **Homogeneous Graph GNN**: 2-layer Graph Convolutional Network (GCN) on the contract-only $k$-NN topology.\n",
            "4. **VS-HGNN (Ours)**: Default ($\\tau = 0.5$) and Calibrated ($\\tau = \\tau^*$) models."
        ]
    }
    
    code_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import json\n",
            "import pandas as pd\n",
            "import matplotlib.pyplot as plt\n",
            "\n",
            "# Load comprehensive benchmark results\n",
            "bench_path = 'data/models/comprehensive_benchmark.json'\n",
            "with open(bench_path, 'r') as f:\n",
            "    bench_data = json.load(f)\n",
            "\n",
            "print('=== CALIBRATED OPTIMAL THRESHOLDS (\\u03c4*) PER CLASS ===')\n",
            "for vuln, stats in bench_data['calibrated_thresholds'].items():\n",
            "    print(f\"{vuln:<25}: \\u03c4* = {stats['optimal_tau']:.3f} (Val F1: {stats['val_f1_at_optimal']:.4f})\")\n",
            "\n",
            "# Prepare DataFrame\n",
            "rows = []\n",
            "for model_name, metrics in bench_data['models'].items():\n",
            "    rows.append({\n",
            "        'Model / Tool': model_name,\n",
            "        'Paradigm': metrics['paradigm'],\n",
            "        'Macro-F1': metrics['macro_f1'],\n",
            "        'Micro-F1': metrics['micro_f1'],\n",
            "        'Hamming Loss': metrics['hamming_loss']\n",
            "    })\n",
            "\n",
            "df_all = pd.DataFrame(rows).sort_values('Macro-F1', ascending=True)\n",
            "print('\\n=== MASTER COMPARATIVE BENCHMARK TABLE ===')\n",
            "display(df_all)\n",
            "\n",
            "# Plot Master Benchmark Bar Chart\n",
            "plt.figure(figsize=(11, 6))\n",
            "palette = []\n",
            "for m in df_all['Model / Tool']:\n",
            "    if 'VS-HGNN' in m:\n",
            "        palette.append('#1d4ed8')  # deep blue\n",
            "    elif 'GNN' in m:\n",
            "        palette.append('#60a5fa')  # light blue\n",
            "    elif 'Regression' in m or 'Forest' in m:\n",
            "        palette.append('#10b981')  # emerald green\n",
            "    else:\n",
            "        palette.append('#94a3b8')  # slate gray for static tools\n",
            "\n",
            "bars = plt.barh(df_all['Model / Tool'], df_all['Macro-F1'], color=palette, edgecolor='black')\n",
            "for bar in bars:\n",
            "    w = bar.get_width()\n",
            "    plt.text(w + 0.015, bar.get_y() + bar.get_height()/2, f\"{w:.4f}\", va='center', fontweight='bold', fontsize=9.5)\n",
            "\n",
            "plt.title('Master Benchmark: VS-HGNN vs. ML, Homogeneous GNN & Static Analyzers', fontsize=13, fontweight='bold')\n",
            "plt.xlabel('Test Macro-F1 Score (N = 1,124 Unseen Test Contracts)', fontsize=11)\n",
            "plt.xlim(0, 1.14)\n",
            "plt.grid(axis='x', linestyle='--', alpha=0.5)\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    }
    
    nb["cells"].extend([markdown_cell, code_cell])
    
    with open(nb_path, "w") as f:
        json.dump(nb, f, indent=1)
        
    print(f"Successfully appended Section 9 to {nb_path}. Total cells: {len(nb['cells'])}")

if __name__ == "__main__":
    append_section_9()
