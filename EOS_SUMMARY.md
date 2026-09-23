# Exploratory Data Summary (EDS / EOS) & Statistical Overview
## Solidity SmartBugs Wild and DIVE Datasets Analysis

---

### Executive Overview

This document presents a comprehensive **Exploratory Data Summary (EDS / EOS)** of two major benchmark datasets used in smart contract security, static analysis, and machine learning for Solidity vulnerability detection:

1. **SmartBugs Wild Dataset**: A large-scale Ethereum mainnet dataset comprising **972,975 smart contract metadata records** (representing **47,398 unique smart contract source code files**).
2. **DIVE Dataset**: A multi-label smart contract vulnerability dataset containing **22,330 ground-truth labeled smart contracts**, **32,766 account/contract addresses**, **156 EVM opcode metrics**, and evaluation results across **6 static analysis tools** (MAIAN, Mythril, Semgrep, Slither, Solhint, VeriSmart).

Both datasets were accessed, parsed, and analyzed directly via **online streaming links** (GitHub Raw endpoints and Zenodo APIs) without needing heavy local manual file storage.

---

### 1. SmartBugs Wild Dataset Analysis

#### A. Key Dataset Dimensions & Metrics
| Metric | Empirical Value |
| :--- | :--- |
| **Total Metadata Entries** | 972,975 |
| **Unique Smart Contract Addresses** | 972,975 |
| **Total On-Chain Transactions** | 194,744,321 |
| **Mean Transactions per Contract** | 200.15 |
| **Median Transactions per Contract** | 2.00 |
| **Maximum Transactions (Single Contract)** | 11,119,405 |
| **Zero-Balance Contracts (`0 ETH`)** | 867,427 (89.15%) |
| **Non-Zero Balance Contracts (`>0 ETH`)** | 105,548 (10.85%) |
| **Distinct Solidity Compiler Versions** | 359 |

#### B. Top 10 Solidity Compiler Versions
The dataset reflects contracts compiled primarily between 2016 and 2019. The distribution of top compiler versions is summarized below:

| Compiler Version | Contract Count | Percentage |
| :--- | :---: | :---: |
| `v0.4.11+commit.68ef5810` | 684,290 | 70.33% |
| `v0.4.16-nightly.2017.8.11+commit.c84de7fa` | 116,878 | 12.01% |
| `v0.4.24+commit.e67f0147` | 71,445 | 7.34% |
| `v0.3.2+commit.81ae2a7` | 14,101 | 1.45% |
| `v0.4.15+commit.bbb8e64f` | 11,324 | 1.16% |
| `v0.3.5+commit.5f97274` | 10,818 | 1.11% |
| `v0.4.23+commit.124ca40d` | 9,582 | 0.98% |
| `v0.4.19+commit.c4cbbb05` | 9,439 | 0.97% |
| `v0.4.25+commit.59dbf8f1` | 8,233 | 0.85% |
| `v0.4.18+commit.9cf6e910` | 6,418 | 0.66% |

---

### 2. DIVE Dataset Analysis

#### A. Multi-Label Vulnerability Class Distribution (DASP Top 8)
The DIVE dataset provides ground-truth multi-label tags for **22,330 smart contracts** across 8 Decentralized Application Security Project (DASP) vulnerability categories:

| Vulnerability Category | Affected Contracts Count | Prevalence Rate (%) |
| :--- | :---: | :---: |
| **Access Control** | 16,723 | 74.89% |
| **Reentrancy** | 11,400 | 51.05% |
| **Arithmetic (Overflow/Underflow)** | 9,542 | 42.73% |
| **Time Manipulation** | 6,322 | 28.31% |
| **Unchecked Return Values** | 5,911 | 26.47% |
| **Denial of Service (DoS)** | 3,781 | 16.93% |
| **Bad Randomness** | 634 | 2.84% |
| **Front Running** | 606 | 2.71% |

#### B. Multi-Vulnerability Complexity Profile
Smart contracts in DIVE frequently exhibit multiple co-occurring vulnerabilities:

- **Clean Contracts (0 Vulnerabilities)**: 2,686 (12.03%)
- **Single Vulnerability Contracts (1 Vulnerability)**: 4,221 (18.90%)
- **Multi-Vulnerability Contracts (>1 Vulnerability)**: 15,423 (69.07%)

#### C. Integrated Static Analysis Tools Benchmark
DIVE incorporates evaluation outputs from **6 major automated static analysis tools**:
1. **MAIAN** (Vulnerability detection for trace analysis)
2. **Mythril** (Symbolic execution framework)
3. **Semgrep** (Pattern-matching static analyzer)
4. **Slither** (Static analysis framework)
5. **Solhint** (Solidity linter & security rule checker)
6. **VeriSmart** (Precise automated verifier)

---

### 3. Comparative Summary Matrix

| Comparative Dimension | SmartBugs Wild Dataset | DIVE Dataset |
| :--- | :--- | :--- |
| **Primary Goal** | Broad empirical evaluation of tool scalability & real-world behavior | Supervised machine learning & multi-label vulnerability detection |
| **Dataset Size** | 972,975 entries (47,398 unique source files) | 22,330 labeled contracts / 32,766 addresses |
| **Ground-Truth Annotations** | Uncurated tool outputs | Multi-label ground truth (8 DASP categories) |
| **Feature Set** | Metadata, transaction counts, ETH balance, compiler flags | EVM Opcodes (156), ABI, Account info, Bytecode features |
| **Online Access Source** | `github.com/smartbugs/smartbugs-wild` | Zenodo (DOI `10.5281/zenodo.18519253`) & GitHub (`DIVE4Data/DIVE`) |

---

### 4. Notebook Implementation (`vsgnn.ipynb`)

The interactive Jupyter Notebook [`vsgnn.ipynb`](file:///Users/hamisulawal/Documents/VS-HGNN/vsgnn.ipynb) streams both datasets live and generates:
- **Bar Charts**: Top compiler versions distribution, DIVE vulnerability prevalence.
- **Correlation Heatmap**: Co-occurrence matrix across all 8 vulnerability types.
- **Pie Charts**: Single vs. multi-vulnerability contract breakdown.
- **Summary Tables**: Clean, structured Pandas DataFrames for quick exploration.
