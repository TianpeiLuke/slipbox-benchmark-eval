import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

MH = {"slipbox v2": (0.356, 0.501, 0.110), "slipbox v3": (0.331, 0.496, 0.107),
      "slipbox v4": (0.337, 0.504, 0.093), "chunks": (0.351, 0.499, 0.113),
      "HippoRAG": (0.222, 0.310, 0.043)}
TW = {"slipbox": None, "chunks": (0.589, 0.703, 0.385), "HippoRAG": (0.720, 0.900, 0.770)}
METRICS = ["R@2", "R@5", "AR@5"]
CLR = {"slipbox v2": "#3B6BA5", "slipbox v3": "#5B87BE", "slipbox v4": "#7FA6D4",
       "slipbox": "#3B6BA5", "chunks": "#8C8C8C", "HippoRAG": "#C0392B"}

fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.6), gridspec_kw={"width_ratios": [5, 3]})

def panel(ax, data, title, sub, ymax=1.05):
    names = list(data); x = np.arange(len(METRICS)); w = 0.8 / len(names)
    for i, n in enumerate(names):
        vals = data[n]; off = (i - (len(names) - 1) / 2) * w
        if vals is None:
            ax.bar(x + off, [ymax * 0.30] * len(METRICS), w, color="#f2f2f2",
                   edgecolor="#cccccc", linestyle=":", linewidth=1.1, zorder=0)
            for xi in x:
                ax.text(xi + off, ymax * 0.15, "not\nbuilt", ha="center", va="center",
                        fontsize=8, color="#999", style="italic")
            continue
        b = ax.bar(x + off, vals, w, color=CLR[n], edgecolor="white", linewidth=0.7, zorder=3)
        for r, v in zip(b, vals):
            ax.text(r.get_x() + r.get_width() / 2, v + 0.015, f"{v:.3f}",
                    ha="center", va="bottom", fontsize=8, zorder=4)
    ax.set_xticks(x); ax.set_xticklabels(METRICS, fontsize=11.5)
    ax.set_ylim(0, ymax); ax.set_ylabel("document-level recall", fontsize=10.5)
    ax.set_title(f"{title}\n{sub}", fontsize=11.5, fontweight="bold", pad=10, linespacing=1.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6); ax.set_axisbelow(True)

panel(axes[0], MH, "MultiHop-RAG — the hop is bibliographic",
      "which publisher said what, on which date  ·  37 docs  ·  300 questions")
panel(axes[1], TW, "2WikiMultiHopQA — the hop is an entity bridge",
      "an entity the query never names  ·  200 questions")

axes[0].annotate("every note vault beats HippoRAG by ~0.19 R@5,\nand all of them merely tie chunks",
                 xy=(1.32, 0.318), xytext=(0.62, 0.80), fontsize=9, color="#333",
                 ha="left", arrowprops=dict(arrowstyle="->", color="#777", lw=1.0,
                 connectionstyle="arc3,rad=-0.15"))
axes[1].annotate("same implementation: +0.198 R@5,\nand twice the All-Recall", xy=(2.13, 0.775),
                 xytext=(0.55, 0.93), fontsize=9, color="#333", ha="center",
                 arrowprops=dict(arrowstyle="->", color="#777", lw=1.0,
                 connectionstyle="arc3,rad=-0.25"))

handles = [Patch(facecolor=CLR[n], label=n) for n in
           ["slipbox v2", "slipbox v3", "slipbox v4", "chunks", "HippoRAG"]]
handles.append(Patch(facecolor="#f2f2f2", edgecolor="#cccccc", linestyle=":",
                     label="slipbox on 2Wiki — not built"))
fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False,
           fontsize=9.5, bbox_to_anchor=(0.5, 0.055))
fig.suptitle("The slipbox against HippoRAG: each is inert where the other pays",
             fontsize=14, fontweight="bold", y=0.985)
fig.text(0.5, 0.012, "Matched ground: identical documents, questions, document-level credit and k.  "
         "Retrieval only — neither system has an answer-quality number here.",
         ha="center", fontsize=9, color="#666")
fig.tight_layout(rect=[0, 0.10, 1, 0.94])
for out in ("src/buyer_abuse_slipbox_agent/abuse_slipbox/resources/diagrams/slipbox_vs_hipporag_matched.png",
            "src/buyer_abuse_slipbox_agent/source_assets/archives/experiments/slipbox_vs_hipporag_matched.png"):
    fig.savefig(out, dpi=170, bbox_inches="tight")
print("regenerated")
