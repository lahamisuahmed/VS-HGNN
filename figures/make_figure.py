"""
Generate the VS-HGNN research architecture figure as a self-contained SVG.
Every number in the labels is taken from the repository artifacts:
  data/merged/merge_summary_stats.json, data/graph/graph_summary.json,
  data/models/eval_results.json, data/models/comprehensive_benchmark.json,
  scripts/train_vshgnn.py, scripts/construct_graph.py, scripts/scan_contract.py.
Usage:  python figures/make_figure.py   (writes figures/vs_hgnn_architecture.svg)
"""
import html
import os

W, H = 1400, 1266
FONT = "DejaVu Sans, Verdana, Arial, sans-serif"

INK = "#1f2933"
MUTED = "#52606d"
LINE = "#9aa5b1"
PANEL = "#f5f7fa"
PANEL_EDGE = "#cbd2d9"
BOX = "#ffffff"
ACC = "#2f5d8a"      # learned model / representations
ACC_FILL = "#e8eff6"
SUP = "#b45f06"      # ground-truth labels / supervision
SUP_FILL = "#fbf1e6"

parts = []


def add(s):
    parts.append(s)


def esc(s):
    return html.escape(s, quote=False)


def text(x, y, s, size=13, weight="normal", anchor="start", fill=INK, style="normal"):
    add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
        f'font-style="{style}" text-anchor="{anchor}" fill="{fill}">{esc(s)}</text>')


def lines(x, y, rows, size=11.5, lh=None, anchor="start", fill=INK, weight="normal"):
    lh = lh or round(size * 1.32)
    for i, r in enumerate(rows):
        if isinstance(r, tuple):
            t, w, f = r
            text(x, y + i * lh, t, size=size, weight=w, anchor=anchor, fill=f)
        else:
            text(x, y + i * lh, r, size=size, weight=weight, anchor=anchor, fill=fill)


def rect(x, y, w, h, fill=BOX, stroke=LINE, sw=1.2, r=6, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" ry="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def panel(x, y, w, h, title, subtitle=None, sub_pos="top"):
    rect(x, y, w, h, fill=PANEL, stroke=PANEL_EDGE, sw=1.2, r=10)
    text(x + 14, y + 26, title, size=16, weight="bold")
    if subtitle:
        sy = y + 26 if sub_pos == "top" else y + h - 9
        text(x + w - 16, sy, subtitle, size=11.5, fill=MUTED, style="italic", anchor="end")


def box(x, y, w, h, title, rows=(), fill=BOX, stroke=LINE, title_size=13, row_size=11.5, title_fill=INK, r=6):
    rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.3, r=r)
    text(x + 10, y + 19, title, size=title_size, weight="bold", fill=title_fill)
    lines(x + 10, y + 19 + round(row_size * 1.5), rows, size=row_size, fill=INK)


def arrow(x1, y1, x2, y2, color=INK, sw=1.6, label=None, lx=None, ly=None, dash=None, marker="arr", label_size=11.5, anchor="middle", label_fill=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}" marker-end="url(#{marker})"{d}/>')
    if label:
        text(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else (y1 + y2) / 2 - 6,
             label, size=label_size, anchor=anchor, fill=label_fill or color, style="italic")


def path_arrow(d, color=INK, sw=1.6, dash=None, marker="arr"):
    dd = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" marker-end="url(#{marker})"{dd}/>')


# ------------------------------------------------------------------ header
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
    f'aria-label="End-to-end architecture of the VS-HGNN research pipeline: data fusion, heterogeneous graph construction, '
    f'the VS-HGNN model, training and calibration, and the inductive scanner with explainer.">')
add('<defs>'
    f'<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>'
    f'<marker id="arrA" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{ACC}"/></marker>'
    f'<marker id="arrS" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{SUP}"/></marker>'
    '</defs>')
rect(0, 0, W, H, fill="#ffffff", stroke="none", r=0)

text(W / 2, 34, "VS-HGNN: Cross-Modal Heterogeneous Graph Learning for Multi-Label Smart-Contract Vulnerability Detection",
     size=20, weight="bold", anchor="middle")
text(W / 2, 56, "End-to-end research architecture: data fusion (Step 1), heterogeneous graph construction, model, training and calibration (Step 2), inductive auditing (Step 3)",
     size=13, anchor="middle", fill=MUTED, style="italic")

# ================================================================== TIER 1
T1Y, T1H = 78, 276
AX, AW = 30, 380
BX, BW = 440, 380
CX, CW = 850, 520

panel(AX, T1Y, AW, T1H, "A  Data sources")
box(AX + 16, T1Y + 42, AW - 32, 92, "SmartBugs Wild  (on-chain corpus)",
    ["972,975 Ethereum contracts, 194.7 M transactions",
     "per contract: address, tx count, balance, creation",
     "and last-transaction dates, compiler version, name"])
box(AX + 16, T1Y + 148, AW - 32, 108, "DIVE  (verified multi-label ground truth)",
    ["22,330 labelled contracts, 8 DASP classes",
     "y ∈ {0,1}⁸ per contract",
     "6 static analysers × 8 classes = 48 tool flags",
     "(MAIAN, Mythril, Semgrep, Slither, Solhint, VeriSmart)"],
    fill=SUP_FILL, stroke=SUP, title_fill=SUP)

panel(BX, T1Y, BW, T1H, "B  Step 1: cross-modal fusion", "scripts/merge_datasets.py", sub_pos="bottom")
box(BX + 16, T1Y + 42, BW - 32, 72, "Address canonicalisation  π(a)",
    ["π(a) = lowercase(strip(a \\ \"0x\")) → Σ⁴⁰",
     "idempotent projection onto a common key space"])
box(BX + 16, T1Y + 128, BW - 32, 122, "Hash equi-join on π(a)  ⇒  supervised core",
    ["D_core = D_DIVE ⋈ D_SB  (inner join, de-duplicated)",
     ("7,487 contracts × 66 columns (33.5 % of DIVE)", "bold", INK),
     "runtime metadata + tool flags + ground-truth labels",
     "134 distinct compiler versions"])

panel(CX, T1Y, CW, T1H, "C  Heterogeneous graph  G", "scripts/construct_graph.py")
NW = 230
box(CX + 16, T1Y + 42, NW, 132, "Contract nodes  (7,487)",
    ["x ∈ ℝ⁷² = [ runtime (3) ‖",
     "   tool priors (48) ‖ compiler (21) ]",
     "compiler = one-hot top-20 + other",
     "runtime = log₁₀ tx, log₁₀ balance,",
     "lifecycle days (standardised)",
     "labels y ∈ {0,1}⁸ (from DIVE)"],
    fill=ACC_FILL, stroke=ACC, title_fill=ACC)
box(CX + 16, T1Y + 186, NW, 48, "Compiler nodes  (134)",
    ["identity one-hot, x ∈ ℝ¹³⁴"], fill=ACC_FILL, stroke=ACC, title_fill=ACC)
RX = CX + 16 + NW + 16
RW = CW - 32 - NW - 16
box(RX, T1Y + 42, RW, 132, "Relations (edge types)",
    ["compiled_with / compiles",
     "contract ↔ compiler, 7,487 each",
     "semantic_knn",
     "contract ↔ contract, cosine, k = 5",
     "37,435 directed edges",
     ("7,621 nodes, 52,409 edges in total", "bold", INK)])
box(RX, T1Y + 186, RW, 66, "Node split  (seed 42)",
    ["train 5,240 (70 %) · val 1,123 (15 %)",
     "test 1,124 (15 %), hold-out"])

# tier-1 arrows (colour carries the meaning; boxes state the content)
arrow(AX + AW - 16, T1Y + 88, BX + 16, T1Y + 88)
arrow(AX + AW - 16, T1Y + 202, BX + 16, T1Y + 202, color=SUP, marker="arrS")
arrow(BX + BW - 16, T1Y + 189, CX + 16, T1Y + 189)

# ================================================================== TIER 2  (model)
T2Y, T2H = 388, 444
panel(30, T2Y, 1340, T2H, "D  VS-HGNN model  (class VSHGNN, PyTorch Geometric)",
      "two node-type streams; three relation-specific message-passing operators per layer; residual + LayerNorm")

cy_c = T2Y + 96
bh_c, bh_k = 118, 86
ytop = cy_c + 20 + bh_c            # bottom of contract-lane layer boxes
cy_k = ytop + 76                   # top of compiler-lane boxes

text(44, T2Y + 82, "contract stream", size=12.5, fill=MUTED, style="italic")
text(44, cy_k - 12, "compiler stream", size=12.5, fill=MUTED, style="italic")

# columns
IX, IW = 44, 118
PX, PW = 188, 150
L1x, L1w = 364, 260
L2x, L2w = 664, 260
HX, HW = 964, 176
OX, OW = 1170, 186

box(IX, cy_c + 20, IW, 76, "Input", ["x_contract ∈ ℝ⁷²", "7,487 × 72"], fill=ACC_FILL, stroke=ACC, title_fill=ACC)
box(IX, cy_k, IW, 60, "Input", ["x_compiler ∈ ℝ¹³⁴"], fill=ACC_FILL, stroke=ACC, title_fill=ACC)
box(PX, cy_c + 20, PW, 76, "Projection", ["Linear 72 → 128", "LayerNorm · ELU"], fill=BOX, stroke=ACC)
box(PX, cy_k, PW, 60, "Projection", ["Linear 134 → 128", "LayerNorm · ELU"], fill=BOX, stroke=ACC)


def layer(Lx, Lw, title, top_title, top_rows, bot_title, bot_rows, bot_stroke=ACC):
    rect(Lx - 10, cy_c - 26, Lw + 20, (cy_k + bh_k) - (cy_c - 26) + 12, fill="none", stroke=ACC, sw=1.2, dash="6 4", r=10)
    text(Lx + Lw / 2, cy_c - 9, title, size=13.5, weight="bold", anchor="middle", fill=ACC)
    box(Lx, cy_c + 20, Lw, bh_c, top_title, top_rows, fill=ACC_FILL, stroke=ACC, title_fill=ACC)
    box(Lx, cy_k, Lw, bh_k, bot_title, bot_rows, fill=BOX, stroke=bot_stroke)
    path_arrow(f"M{Lx + 34},{cy_k} L{Lx + 34},{ytop}", color=ACC, marker="arrA")
    path_arrow(f"M{Lx + Lw - 34},{ytop} L{Lx + Lw - 34},{cy_k}", color=ACC, marker="arrA")
    lines(Lx + Lw / 2, ytop + 22,
          ["↑ SAGEConv on compiles",
           "compiler → contract",
           "↓ SAGEConv on compiled_with",
           "contract → compiler"], size=11, lh=13, anchor="middle", fill=ACC)


layer(L1x, L1w, "HeteroConv layer 1   (aggr = sum)",
      "GATv2Conv on semantic_knn",
      ["contract → contract, 2 heads averaged",
       "dynamic attention αᵤᵥ over k-NN peers",
       "attention dropout 0.25",
       "+ residual · LayerNorm · dropout 0.25"],
      "Compiler update  (128 → 128)",
      ["receives contract messages (SAGE)",
       "+ residual · LayerNorm · dropout 0.25"])

layer(L2x, L2w, "HeteroConv layer 2   (aggr = mean)",
      "SAGEConv on semantic_knn",
      ["contract → contract, 128 → 128",
       "2-hop structural context",
       "+ residual · LayerNorm · dropout 0.25",
       "h⁽²⁾ ∈ ℝ¹²⁸ per contract"],
      "Compiler update  (128 → 128)",
      ["computed but not consumed",
       "by the classifier"], bot_stroke=LINE)

box(HX, cy_c + 20, HW, bh_c, "Classification head",
    ["Linear 128 → 64, LN, ELU",
     "Dropout 0.25",
     "Linear 64 → 8",
     "logits z ∈ ℝ⁸"], fill=BOX, stroke=ACC)
box(OX, cy_c + 20, OW, bh_c, "Multi-label output",
    ["pₖ = σ(zₖ),  k = 1..8",
     "Reentrancy, Access Control,",
     "Arithmetic, Unchecked Ret.,",
     "DoS, Bad Randomness,",
     "Front Running, Time manip."], fill=ACC_FILL, stroke=ACC, title_fill=ACC)

# flow arrows, contract lane
yc = cy_c + 20 + bh_c / 2
arrow(IX + IW, cy_c + 58, PX, cy_c + 58, color=ACC, marker="arrA")
arrow(PX + PW, cy_c + 58, L1x, cy_c + 58, color=ACC, marker="arrA")
arrow(L1x + L1w, yc, L2x, yc, color=ACC, marker="arrA", label="h⁽¹⁾", lx=(L1x + L1w + L2x) / 2, ly=yc - 8)
arrow(L2x + L2w, yc, HX, yc, color=ACC, marker="arrA", label="h⁽²⁾", lx=(L2x + L2w + HX) / 2, ly=yc - 8)
arrow(HX + HW, yc, OX, yc, color=ACC, marker="arrA", label="z", lx=(HX + HW + OX) / 2, ly=yc - 8)
# compiler lane
arrow(IX + IW, cy_k + 30, PX, cy_k + 30, color=ACC, marker="arrA")
arrow(PX + PW, cy_k + 30, L1x, cy_k + 30, color=ACC, marker="arrA")
arrow(L1x + L1w, cy_k + 43, L2x, cy_k + 43, color=ACC, marker="arrA", label="h⁽¹⁾", lx=(L1x + L1w + L2x) / 2, ly=cy_k + 35)

# graph -> model
path_arrow(f"M{CX + CW / 2},{T1Y + T1H} L{CX + CW / 2},{T2Y - 16} L{IX + IW / 2},{T2Y - 16} L{IX + IW / 2},{cy_c + 8}", color=ACC, marker="arrA")
text(600, T2Y - 22, "G = (x_dict, edge_index_dict, train / val / test masks)", size=12, fill=ACC, style="italic", anchor="middle")

# ================================================================== TIER 3
T3Y, T3H = 866, 374
EX, EW = 30, 660
FX, FW = 730, 640
BW3 = 300

panel(EX, T3Y, EW, T3H, "E  Step 2: training, evaluation, calibration, benchmarking",
      "scripts/train_vshgnn.py · scripts/calibrate_and_benchmark_baselines.py", sub_pos="bottom")
box(EX + 16, T3Y + 42, BW3, 130, "Weighted BCE loss  (train nodes)",
    ["wₖ⁺ = (N − Nₖ⁺) / Nₖ⁺,  clipped to [0.5, 50]",
     "  = [0.89, 0.50, 1.33, 2.71, 4.59, 33.7, 38.1, 2.52]",
     "AdamW lr 5×10⁻³, wd 10⁻⁴, cosine LR schedule",
     "grad-clip 2.0, ≤ 120 epochs, early stopping (20)",
     "model selection on val macro-F1 (best ep. 106)"],
    fill=SUP_FILL, stroke=SUP, title_fill=SUP)
box(EX + 16, T3Y + 184, BW3, 160, "Hold-out test  (N = 1,124)",
    [("Macro-F1 0.9633   Micro-F1 0.9647", "bold", INK),
     ("mean ROC-AUC 0.9928   Hamming 0.0216", "bold", INK),
     "baselines on the same test contracts (macro-F1):",
     "Slither 0.636 · Mythril 0.427 · Solhint 0.362",
     "GCN on homogeneous k-NN graph 0.858",
     "logistic regression 0.968 · random forest 0.971",
     "significance vs static tools:",
     "Wilcoxon p = 0.0039, McNemar p < 10⁻¹⁵"])
box(EX + 344, T3Y + 42, BW3, 130, "Threshold calibration  (val, N = 1,123)",
    ["τₖ* = argmax over τ ∈ [0.05, 0.95] of",
     "        F₁( y_val,k , 1[σ(z_val,k) ≥ τ] )",
     "τ* = [.53, .37, .54, .41, .81, .38, .45, .60]",
     "replaces the generic τ = 0.5 decision rule",
     "calibrated head micro-F1 0.9700 (vs 0.9647)"],
    fill=SUP_FILL, stroke=SUP, title_fill=SUP)
box(EX + 344, T3Y + 184, BW3, 160, "Persisted artifacts  (data/)",
    ["merged/vs_hgnn_supervised_benchmark.csv",
     "graph/vs_hgnn_hetero_graph.pt",
     "models/vshgnn_best.pt   (frozen weights Θ*)",
     "models/eval_results.json",
     "models/comprehensive_benchmark.json   (τ*)",
     "public repository:",
     "github.com/lahamisuahmed/VS-HGNN"])

panel(FX, T3Y, FW, T3H, "F  Step 3: inductive scanner and GNN explainer", "scripts/scan_contract.py", sub_pos="bottom")
c1, c2, c3 = FX + 16, FX + 232, FX + 448
cw, cw3 = 196, 176
r1h, r2y, r2h = 112, T3Y + 186, 158
box(c1, T3Y + 42, cw, r1h, "Unseen contract  u*",
    ["runtime profile, static-tool",
     "flags, compiler version",
     "→ same feature map and",
     "   scaler as in training:",
     "   x_u* ∈ ℝ⁷²"])
box(c2, T3Y + 42, cw, r1h, "Inductive insertion",
    ["cosine k-NN, K = 5 peers →",
     "bidirectional k-NN edges",
     "+ compiled_with / compiles",
     "   edge to compiler node c_u*",
     "O(1) insertion, no retraining"], fill=ACC_FILL, stroke=ACC, title_fill=ACC)
box(c3, T3Y + 42, cw3, r1h, "Frozen VS-HGNN  Θ*",
    ["forward pass on the",
     "augmented graph",
     "→ z_u* ∈ ℝ⁸",
     "sub-40 ms latency"], fill=ACC_FILL, stroke=ACC, title_fill=ACC)
box(c1, r2y, cw, r2h, "Calibrated decision",
    ["ŷₖ = 1[ σ(zₖ) ≥ τₖ* ]",
     "margin Δₖ = σ(zₖ) − τₖ*",
     "risk level from flagged",
     "classes and margins"])
box(c2, r2y, cw, r2h, "Explainer",
    ["Input×Gradient saliency",
     "sₖ,ᵢ = |∂zₖ / ∂xᵢ| · |xᵢ|",
     "aggregated by modality:",
     "runtime / tools / compiler",
     "GATv2 attention α → peer",
     "influence (labelled peers)"])
box(c3, r2y, cw3, r2h, "Audit report",
    ["flagged DASP classes",
     "confidence margins",
     "modality attribution",
     "top influencing peers",
     "remediation notes"])

ym = T3Y + 98
arrow(c1 + cw, ym, c2, ym, color=ACC, marker="arrA")
arrow(c2 + cw, ym, c3, ym, color=ACC, marker="arrA")
yb = T3Y + 42 + r1h
path_arrow(f"M{c3 + 88},{yb} L{c3 + 88},{yb + 12} L{c1 + cw / 2},{yb + 12} L{c1 + cw / 2},{r2y}", color=ACC, marker="arrA")
path_arrow(f"M{c2 + cw / 2},{yb + 12} L{c2 + cw / 2},{r2y}", color=ACC, marker="arrA")
text(c3 + 96, yb + 26, "z, ∇z", size=11, fill=ACC, style="italic")
yr = r2y + 70
arrow(c1 + cw, yr, c2, yr, color=INK)
arrow(c2 + cw, yr, c3, yr, color=INK)

# ------------------------------------------------------------- inter-tier arrows
yroute = T2Y + T2H - 20
path_arrow(f"M{OX + OW / 2},{cy_c + 20 + bh_c} L{OX + OW / 2},{yroute} L{EX + 166},{yroute} L{EX + 166},{T3Y + 42}", color=ACC, marker="arrA")
text(700, yroute + 14, "logits z on train / val / test masks", size=12, fill=ACC, style="italic", anchor="middle")
path_arrow(f"M{AX},{T1Y + 202} L22,{T1Y + 202} L22,{T3Y + 100} L{EX + 16},{T3Y + 100}", color=SUP, marker="arrS")
add(f'<g transform="rotate(-90 11 640)"><text x="11" y="644" font-family="{FONT}" font-size="11.5" font-style="italic" fill="{SUP}" text-anchor="middle">ground-truth labels y (DIVE)</text></g>')
path_arrow(f"M{EX + 644},{T3Y + 100} L716,{T3Y + 100} L716,{yr} L{c1},{yr}", color=SUP, marker="arrS")
text(716, r2y + 30, "τ*", size=13, fill=SUP, weight="bold", anchor="middle")
yq = T3Y - 12
path_arrow(f"M{EX + 644},{r2y + 45} L700,{r2y + 45} L700,{yq} L{FX + FW - 8},{yq} L{FX + FW - 8},{ym} L{c3 + cw3},{ym}", color=ACC, marker="arrA", dash="5 4")
text(1050, yq - 6, "frozen weights Θ* (vshgnn_best.pt)", size=12, fill=ACC, style="italic", anchor="middle")

# ------------------------------------------------------------- legend / footer
ly = H - 14
lx = 30
add(f'<line x1="{lx}" y1="{ly - 4}" x2="{lx + 36}" y2="{ly - 4}" stroke="{ACC}" stroke-width="1.8" marker-end="url(#arrA)"/>')
text(lx + 44, ly, "learned representations / model flow", size=12, fill=MUTED)
add(f'<line x1="{lx + 310}" y1="{ly - 4}" x2="{lx + 346}" y2="{ly - 4}" stroke="{SUP}" stroke-width="1.8" marker-end="url(#arrS)"/>')
text(lx + 354, ly, "supervision: ground-truth labels, loss, calibrated thresholds", size=12, fill=MUTED)
add(f'<line x1="{lx + 770}" y1="{ly - 4}" x2="{lx + 806}" y2="{ly - 4}" stroke="{ACC}" stroke-width="1.8" stroke-dasharray="5 4" marker-end="url(#arrA)"/>')
text(lx + 814, ly, "reuse of persisted artifacts", size=12, fill=MUTED)
text(W - 30, ly, "All figures from repository artifacts (seed 42)", size=11.5, fill=MUTED, anchor="end", style="italic")

add('</svg>')

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vs_hgnn_architecture.svg")
open(out, "w", encoding="utf-8").write("\n".join(parts))
print("wrote", out)
