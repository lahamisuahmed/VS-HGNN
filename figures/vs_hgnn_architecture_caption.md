# Figure: VS-HGNN research architecture

Files in this folder

| File | Use |
| --- | --- |
| `vs_hgnn_architecture.svg` | editable vector source (Inkscape, Illustrator, browsers) |
| `vs_hgnn_architecture.pdf` | vector, fonts embedded; insert into Word or LaTeX (`\includegraphics`) |
| `vs_hgnn_architecture.png` | 4200 x 3798 px, 300 dpi, for Word or slides when vector import is not available |
| `make_figure.py` | regenerates the SVG; run `python figures/make_figure.py` from the repository root after any change |

Recommended placement: full-width figure on a landscape page (or rotated full page) so the smallest labels print at about 8 pt.

## Caption (thesis / paper)

**Figure X.** End-to-end architecture of the VS-HGNN framework for multi-label smart-contract vulnerability detection. **(A)** Two complementary sources: SmartBugs Wild supplies on-chain runtime metadata for 972,975 contracts, and DIVE supplies verified multi-label ground truth for 22,330 contracts across eight DASP classes together with the outputs of six static analysers. **(B)** Step 1 canonicalises contract addresses and performs an exact hash equi-join, yielding a supervised core of 7,487 contracts with 66 attributes. **(C)** The core is lifted to a heterogeneous graph with 7,487 contract nodes (72-dimensional features: standardised runtime statistics, 48 static-tool priors and a 21-way compiler encoding), 134 compiler nodes, bipartite `compiled_with`/`compiles` relations and a cosine k-nearest-neighbour `semantic_knn` relation (k = 5), giving 7,621 nodes and 52,409 edges; nodes are split 70/15/15 with seed 42. **(D)** VS-HGNN projects both node types into a 128-dimensional space and applies two `HeteroConv` layers: layer 1 combines GATv2 attention over semantic peers with SAGE convolutions across the contract-compiler relations (sum aggregation); layer 2 uses SAGE convolutions throughout (mean aggregation). Residual connections, LayerNorm and dropout (0.25) follow each layer, and a two-layer head produces eight independent logits. **(E)** Step 2 trains with a positive-class-weighted binary cross-entropy loss (AdamW, cosine schedule, early stopping), selects the checkpoint by validation macro-F1, evaluates on the 1,124 held-out contracts (macro-F1 0.9633, micro-F1 0.9647, mean ROC-AUC 0.9928, Hamming loss 0.0216), calibrates per-class decision thresholds τ* on the validation partition, and benchmarks against six static analysers, two tabular learners and a homogeneous GCN on the same test contracts. **(F)** Step 3 deploys the frozen model as an inductive scanner: an unseen contract is mapped with the training feature scaler, inserted into the graph through k-NN and compiler edges without retraining, scored against τ*, and explained through Input x Gradient saliency (aggregated by runtime, tool and compiler modality) and GATv2 attention over labelled peers, producing an audit report. Blue arrows denote learned representations and model flow; orange arrows denote supervision (ground-truth labels, loss, calibrated thresholds); dashed arrows denote reuse of persisted artifacts.

## Provenance of every number in the figure

| Item | Source file |
| --- | --- |
| Corpus sizes, overlap, 66 columns, 134 compilers | `data/merged/merge_summary_stats.json` |
| Node and edge counts, feature dimension, split sizes | `data/graph/graph_summary.json`, `scripts/construct_graph.py` |
| Layer definitions, hidden size, dropout, optimiser, loss weights | `scripts/train_vshgnn.py`, notebook section 5 |
| Test metrics, best epoch, per-class results | `data/models/eval_results.json` |
| Calibrated thresholds τ*, baseline macro-F1 values | `data/models/comprehensive_benchmark.json` |
| Inductive insertion, saliency and attention explainer, latency | `scripts/scan_contract.py`, `STEP3_INFERENCE_REPORT.md` |
| Wilcoxon and McNemar statistics | `STEP3_INFERENCE_REPORT.md` (Section 1) |

Note for the thesis text: the Wilcoxon and McNemar values are quoted from the Step 3 report; confirm they are reproduced by the benchmarking script before citing them in the examined document.
