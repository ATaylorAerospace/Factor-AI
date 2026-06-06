"""Generate the Factor-AI architecture diagram with guardrail harness."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


# ── colours (matched from original) ──────────────────────────────────
WHITE       = "#FFFFFF"
BLACK       = "#000000"
TEAL        = "#1A7A6D"
TEAL_FILL   = "#E6F5F2"
ORANGE      = "#D4760A"
ORANGE_FILL = "#FFF3E0"
ORANGE_DARK = "#C05600"
RED_ORANGE  = "#B8400A"
RED_FILL    = "#FFF0EB"
GREEN       = "#1A7A6D"
GREEN_FILL  = "#E6F5F2"
PURPLE      = "#6B21A8"
PURPLE_FILL = "#F3E8FF"
GREY_TEXT   = "#444444"
LIGHT_GREY  = "#F5F5F5"


def draw_box(ax, x, y, w, h, label, sublabel=None,
             border_color=ORANGE, fill_color=ORANGE_FILL,
             text_color=BLACK, fontsize=10, bold=True,
             sublabel_size=7.5, radius=0.02, emoji=None):
    """Draw a rounded rectangle with centred text."""
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=fill_color, edgecolor=border_color,
        linewidth=1.8, zorder=2,
    )
    ax.add_patch(box)
    weight = "bold" if bold else "normal"
    txt = f"{emoji} {label}" if emoji else label
    if sublabel:
        ax.text(x + w / 2, y + h * 0.62, txt,
                ha="center", va="center", fontsize=fontsize,
                fontweight=weight, color=text_color, zorder=3)
        ax.text(x + w / 2, y + h * 0.28, sublabel,
                ha="center", va="center", fontsize=sublabel_size,
                fontstyle="italic", color=GREY_TEXT, zorder=3,
                wrap=True)
    else:
        ax.text(x + w / 2, y + h / 2, txt,
                ha="center", va="center", fontsize=fontsize,
                fontweight=weight, color=text_color, zorder=3)


def draw_arrow(ax, x1, y1, x2, y2, color=ORANGE):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=1.5, shrinkA=0, shrinkB=0),
                zorder=1)


def draw_section_header(ax, x, y, w, label, color=ORANGE):
    ax.text(x + w / 2, y, label,
            ha="center", va="center", fontsize=9.5,
            fontweight="bold", color=color,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=WHITE,
                      edgecolor=color, linewidth=1.2),
            zorder=3)


# ── figure ────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10.5, 12.5))
fig.patch.set_facecolor(WHITE)
ax.set_facecolor(WHITE)
ax.set_xlim(0, 10.5)
ax.set_ylim(0, 12.5)
ax.axis("off")

# ── title ─────────────────────────────────────────────────────────────
ax.text(5.25, 12.1, "FACTOR-AI",
        ha="center", va="center", fontsize=22, fontweight="bold",
        color=BLACK, zorder=3)
ax.text(5.25, 11.7, "Agentic AI Legal Due Diligence Platform",
        ha="center", va="center", fontsize=12, color=GREY_TEXT, zorder=3)

# ── user / client ────────────────────────────────────────────────────
draw_box(ax, 3.75, 10.9, 3.0, 0.55, "User / Client",
         border_color=TEAL, fill_color=TEAL_FILL,
         text_color=TEAL, fontsize=11)

# arrow down
draw_arrow(ax, 5.25, 10.9, 5.25, 10.55, TEAL)

# ── multi-agent orchestration header ─────────────────────────────────
draw_section_header(ax, 1.0, 10.35, 8.5,
                    "MULTI-AGENT CONTRACT ORCHESTRATION", ORANGE)

# ── supervisor agent ─────────────────────────────────────────────────
draw_box(ax, 2.0, 9.25, 6.5, 0.8,
         "Supervisor Agent (Strands SDK)",
         sublabel="Classifies document type, extracts\nentities, and routes tasks.",
         border_color=ORANGE, fill_color=ORANGE_FILL,
         fontsize=11)

# arrow from header to supervisor
draw_arrow(ax, 5.25, 10.12, 5.25, 10.05, ORANGE)

# ── three sub-agents ─────────────────────────────────────────────────
agent_y = 7.7
agent_h = 1.1
agent_w = 2.6
gap = 0.35

# risk analysis
rx = 0.65
draw_box(ax, rx, agent_y, agent_w, agent_h,
         "Risk Analysis\nAgent",
         sublabel="Identifies liabilities and\nnon-standard clauses.",
         border_color=RED_ORANGE, fill_color=RED_FILL,
         text_color=RED_ORANGE, fontsize=10)

# cross-reference
cx = rx + agent_w + gap
draw_box(ax, cx, agent_y, agent_w, agent_h,
         "Cross-Reference\nAgent",
         sublabel="Detects inconsistencies and\nmissing provisions.",
         border_color=ORANGE, fill_color=ORANGE_FILL,
         text_color=ORANGE_DARK, fontsize=10)

# knowledge base
kx = cx + agent_w + gap
draw_box(ax, kx, agent_y, agent_w, agent_h,
         "Legal Knowledge\nBase (Semantic)",
         sublabel="Vector store of standard\nclauses and definitions.",
         border_color=GREEN, fill_color=GREEN_FILL,
         text_color=GREEN, fontsize=10)

# arrows from supervisor to sub-agents
for ax_x in [rx + agent_w / 2, cx + agent_w / 2, kx + agent_w / 2]:
    draw_arrow(ax, 5.25, 9.25, ax_x, agent_y + agent_h, ORANGE)

# ── guardrail harness section header ─────────────────────────────────
harness_header_y = 7.15
draw_section_header(ax, 1.0, harness_header_y, 8.5,
                    "FINANCIAL-GUARDRAIL & TELEMETRY HARNESS", PURPLE)

# ── harness boxes ────────────────────────────────────────────────────
hbox_y = 5.65
hbox_h = 1.1
hbox_w = 2.1
hgap = 0.3

# circuit breaker
hx1 = 0.5
draw_box(ax, hx1, hbox_y, hbox_w, hbox_h,
         "Circuit\nBreaker",
         sublabel="Hard-halts agents on\nbudget or loop violations.",
         border_color=PURPLE, fill_color=PURPLE_FILL,
         text_color=PURPLE, fontsize=10)

# budget tracker
hx2 = hx1 + hbox_w + hgap
draw_box(ax, hx2, hbox_y, hbox_w, hbox_h,
         "Budget\nTracker",
         sublabel="Per-session token cost\naccounting ($3/$15 per 1M).",
         border_color=PURPLE, fill_color=PURPLE_FILL,
         text_color=PURPLE, fontsize=10)

# loop detector
hx3 = hx2 + hbox_w + hgap
draw_box(ax, hx3, hbox_y, hbox_w, hbox_h,
         "Loop\nDetector",
         sublabel="Sliding-window detection\nof repetitive reasoning.",
         border_color=PURPLE, fill_color=PURPLE_FILL,
         text_color=PURPLE, fontsize=10)

# phoenix
hx4 = hx3 + hbox_w + hgap
draw_box(ax, hx4, hbox_y, hbox_w, hbox_h,
         "Arize Phoenix\n(OpenTelemetry)",
         sublabel="Trace UI + per-step\ntoken auditing via OTLP.",
         border_color=PURPLE, fill_color=PURPLE_FILL,
         text_color=PURPLE, fontsize=10)

# arrows from agents row to harness
for ax_x in [hx1 + hbox_w / 2, hx2 + hbox_w / 2,
             hx3 + hbox_w / 2, hx4 + hbox_w / 2]:
    draw_arrow(ax, ax_x, harness_header_y - 0.22, ax_x, hbox_y + hbox_h, PURPLE)

# ── guarded model connector ──────────────────────────────────────────
gm_y = 4.85
draw_box(ax, 2.5, gm_y, 5.5, 0.55,
         "GuardedBedrockModel — checks breaker before every invocation",
         border_color=PURPLE, fill_color=PURPLE_FILL,
         text_color=PURPLE, fontsize=9, bold=True)

# arrows from harness to guarded model
mid_harness = (hx1 + hbox_w / 2 + hx4 + hbox_w / 2) / 2
draw_arrow(ax, 5.25, hbox_y, 5.25, gm_y + 0.55, PURPLE)

# ── AWS Bedrock ───────────────────────────────────────────────────────
bedrock_y = 3.8
draw_box(ax, 2.75, bedrock_y, 5.0, 0.65, "AWS Bedrock",
         border_color=ORANGE, fill_color=ORANGE_FILL,
         text_color=ORANGE_DARK, fontsize=13, bold=True)

# arrow from guarded model to bedrock
draw_arrow(ax, 5.25, gm_y, 5.25, bedrock_y + 0.65, ORANGE)

# ── bottom services ──────────────────────────────────────────────────
svc_y = 2.7
svc_h = 0.7
svc_w = 2.6

sx1 = 0.65
draw_box(ax, sx1, svc_y, svc_w, svc_h,
         "Contract\nSummarizer",
         border_color=ORANGE, fill_color=ORANGE_FILL,
         text_color=ORANGE_DARK, fontsize=9.5)

sx2 = sx1 + svc_w + gap
draw_box(ax, sx2, svc_y, svc_w, svc_h,
         "Document\nParser",
         border_color=ORANGE, fill_color=ORANGE_FILL,
         text_color=ORANGE_DARK, fontsize=9.5)

sx3 = sx2 + svc_w + gap
draw_box(ax, sx3, svc_y, svc_w, svc_h,
         "Titan Embed\nText",
         border_color=ORANGE, fill_color=ORANGE_FILL,
         text_color=ORANGE_DARK, fontsize=9.5)

# arrows from bedrock to bottom
for sx in [sx1 + svc_w / 2, sx2 + svc_w / 2, sx3 + svc_w / 2]:
    draw_arrow(ax, 5.25, bedrock_y, sx, svc_y + svc_h, ORANGE)

# ── save ──────────────────────────────────────────────────────────────
plt.tight_layout(pad=0.3)
fig.savefig("/home/user/Factor-AI/docs/legal.png",
            dpi=120, facecolor=WHITE, bbox_inches="tight",
            pad_inches=0.3)
plt.close()
print("Saved updated docs/legal.png")
PYEOF