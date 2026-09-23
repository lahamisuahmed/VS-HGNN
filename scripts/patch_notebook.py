import json

with open("vsgnn.ipynb", "r") as f:
    nb = json.load(f)

# Update Cell 1 markdown instructions
nb["cells"][1]["source"] = [
    "---\n",
    "## 0. Kernel Selection & Automated Dependency Bootstrap\n",
    "\n",
    "> **Kernel Selection (Instant & Recommended):**\n",
    "> In VS Code or JupyterLab, click the **Kernel Selector** in the top-right corner and select:\n",
    "> **`Python (VS-HGNN venv)`** *(registered kernel pointing to `./venv/bin/python`)*.\n",
    "> All required dependencies (`torch`, `torch-geometric`, `scikit-learn`, `networkx`, `pandas`) are already pre-installed.\n",
    ">\n",
    "> If running in **Google Colab** or an unconfigured environment, execute the cell below to install all dependencies automatically.\n"
]

# Update Cell 2 code
nb["cells"][2]["source"] = [
    "# Auto-bootstrap dependencies in Colab or fresh kernels\n",
    "import sys\n",
    "import subprocess\n",
    "\n",
    "required_packages = ['torch', 'torch_geometric', 'scikit-learn', 'networkx', 'seaborn']\n",
    "missing_packages = []\n",
    "\n",
    "for pkg in required_packages:\n",
    "    try:\n",
    "        __import__(pkg)\n",
    "    except ImportError:\n",
    "        missing_packages.append('torch-geometric' if pkg == 'torch_geometric' else 'scikit-learn' if pkg == 'scikit-learn' else pkg)\n",
    "\n",
    "if missing_packages:\n",
    "    print(f'Missing packages detected in current kernel: {missing_packages}')\n",
    "    print('Auto-installing required packages via pip into active kernel...')\n",
    "    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q'] + missing_packages)\n",
    "    print('All dependencies installed successfully!')\n",
    "else:\n",
    "    print('All required dependencies are already available in this environment.')\n"
]

# In Cell 5, make sure 'sys' is imported at the top
source5 = "".join(nb["cells"][5]["source"])
if "import sys" not in source5:
    nb["cells"][5]["source"].insert(0, "import sys\n")

with open("vsgnn.ipynb", "w") as f:
    json.dump(nb, f, indent=1)

print("Updated notebook successfully!")
