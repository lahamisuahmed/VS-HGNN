import json

def patch_section_9():
    nb_path = "vsgnn.ipynb"
    with open(nb_path, "r") as f:
        nb = json.load(f)

    # The last cell is Section 9 code cell
    code_cell = nb["cells"][-1]
    
    new_source = [
        "import os\n",
        "import json\n",
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "\n",
        "# 1. If running in fresh Colab/cloud environment, execute the calibration script directly:\n",
        "bench_path = 'data/models/comprehensive_benchmark.json'\n",
        "if not os.path.exists(bench_path):\n",
        "    print('Running baseline training and threshold calibration in active kernel...')\n",
        "    !python scripts/calibrate_and_benchmark_baselines.py\n",
        "\n",
        "# 2. Load comprehensive benchmark results\n",
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
    code_cell["source"] = new_source

    with open(nb_path, "w") as f:
        json.dump(nb, f, indent=1)
    print("Updated Section 9 code cell in vsgnn.ipynb successfully.")

if __name__ == "__main__":
    patch_section_9()
