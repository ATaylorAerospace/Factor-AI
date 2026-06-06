"""Generate the Factor-AI architecture diagram.

Recreates the original look-and-feel (white background, solid-fill rounded
boxes with drop shadows, "~ " title prefixes, color emojis and italic
sublabels) and adds the Financial-Guardrail & Telemetry Harness tier.

Emojis are composited with Pillow because matplotlib cannot render the
color-bitmap NotoColorEmoji font directly.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont
import io

# ── palette (sampled from the original docs/legal.png) ───────────────
WHITE      = "#FFFFFF"
BLACK      = "#1A1A1A"
ORANGE     = "#E07407"   # supervisor / bedrock
GREEN      = "#309341"   # risk analysis
AMBER      = "#EDC263"   # cross-reference
PURPLE     = "#40299B"   # knowledge base
# harness family (distinct but in the same saturated register)
CRIMSON    = "#C0392B"   # circuit breaker
TEAL       = "#0E8174"   # budget / loop / guarded model
INDIGO     = "#3B3F9E"   # phoenix
SHADOW     = "#BDBDBD"
DASH_GREY  = "#9E9E9E"
GREY_TEXT  = "#555555"

EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
DPI = 130

# collected as (data_x_right_anchor, data_y_center, char, target_px)
_emoji_queue = []


def add_shadow(ax, x, y, w, h, radius):
    sh = FancyBboxPatch(
        (x + 0.05, y - 0.06), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=SHADOW, edgecolor="none", zorder=1, alpha=0.55,
    )
    ax.add_patch(sh)


def draw_box(ax, x, y, w, h, title, sublabel=None, *,
             fill=ORANGE, edge=BLACK, text_color=WHITE,
             title_size=11, sub_size=7.6, radius=0.04,
             emoji=None, shadow=True, prefix="~ ", lw=1.6):
    if shadow:
        add_shadow(ax, x, y, w, h, radius)
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=fill, edgecolor=edge, linewidth=lw, zorder=2,
    )
    ax.add_patch(box)

    title_txt = f"{prefix}{title}"
    if sublabel:
        t = ax.text(x + w / 2, y + h * 0.66, title_txt,
                    ha="center", va="center", fontsize=title_size,
                    fontweight="bold", color=text_color, zorder=4)
        ax.text(x + w / 2, y + h * 0.28, sublabel,
                ha="center", va="center", fontsize=sub_size,
                fontstyle="italic", color=text_color, zorder=4)
    else:
        t = ax.text(x + w / 2, y + h / 2, title_txt,
                    ha="center", va="center", fontsize=title_size,
                    fontweight="bold", color=text_color, zorder=4)

    if emoji:
        # anchor emoji just right of the box title block, vertically centred
        cy = y + h * 0.66 if sublabel else y + h / 2
        _emoji_queue.append((t, cy, emoji, title_size))


def arrow(ax, x1, y1, x2, y2, color=BLACK, lw=1.5):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                shrinkA=0, shrinkB=0), zorder=1)


def elbow(ax, x1, y1, x2, y2, color=BLACK, lw=1.5):
    """Vertical-then-horizontal-then-vertical connector."""
    ymid = (y1 + y2) / 2
    ax.plot([x1, x1], [y1, ymid], color=color, lw=lw, zorder=1, solid_capstyle="round")
    ax.plot([x1, x2], [ymid, ymid], color=color, lw=lw, zorder=1, solid_capstyle="round")
    arrow(ax, x2, ymid, x2, y2, color, lw)


def dashed_container(ax, x, y, w, h, label=None, label_color=BLACK):
    box = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.06",
        facecolor="none", edgecolor=DASH_GREY, linewidth=1.3,
        linestyle=(0, (6, 4)), zorder=0,
    )
    ax.add_patch(box)


def header(ax, cx, y, label, color=BLACK):
    ax.text(cx, y, label, ha="center", va="center", fontsize=10.5,
            fontweight="bold", color=color, zorder=5,
            bbox=dict(boxstyle="round,pad=0.35", facecolor=WHITE,
                      edgecolor=color, linewidth=1.4))


# ── build figure ──────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10.6, 13.6))
fig.patch.set_facecolor(WHITE)
ax.set_facecolor(WHITE)
ax.set_xlim(0, 10.6)
ax.set_ylim(0, 13.6)
ax.axis("off")

# title
ax.text(5.3, 13.2, "FACTOR-AI", ha="center", va="center",
        fontsize=24, fontweight="bold", color=BLACK)
ax.text(5.3, 12.78, "Agentic AI Legal Due Diligence Platform",
        ha="center", va="center", fontsize=12.5, color=GREY_TEXT)

# user / client
draw_box(ax, 4.0, 12.0, 2.6, 0.55, "User / Client",
         fill=WHITE, text_color=BLACK, title_size=11.5,
         prefix="", emoji="👤", radius=0.05)
arrow(ax, 5.3, 12.0, 5.3, 11.55)

# ── orchestration container ──────────────────────────────────────────
dashed_container(ax, 0.35, 6.95, 9.9, 4.55)
header(ax, 5.3, 11.35, "MULTI-AGENT CONTRACT ORCHESTRATION", ORANGE)

# supervisor
draw_box(ax, 1.9, 9.95, 6.8, 1.0,
         "Supervisor Agent (Strands SDK)",
         "Classifies document type, extracts\nentities, and routes tasks.",
         fill=ORANGE, text_color=WHITE, title_size=12, emoji="🔐")
arrow(ax, 5.3, 11.12, 5.3, 10.95, ORANGE)

# three sub-agents
ay, ah, aw = 7.2, 1.25, 2.7
rx, cx_, kx = 0.7, 3.9, 7.1
draw_box(ax, rx, ay, aw, ah, "Risk Analysis\nAgent",
         "Identifies liabilities and\nnon-standard clauses.",
         fill=GREEN, text_color=WHITE, title_size=11, emoji="🛡️")
draw_box(ax, cx_, ay, aw, ah, "Cross-Reference\nAgent",
         "Detects inconsistencies and\nmissing provisions.",
         fill=AMBER, text_color=BLACK, title_size=11, emoji="🔍")
draw_box(ax, kx, ay, aw, ah, "Legal Knowledge\nBase (Semantic)",
         "Vector store of standard\nclauses and definitions.",
         fill=PURPLE, text_color=WHITE, title_size=11, emoji="📚")

for tx in (rx + aw / 2, cx_ + aw / 2, kx + aw / 2):
    elbow(ax, 5.3, 9.95, tx, ay + ah, ORANGE)

# ── harness container ────────────────────────────────────────────────
dashed_container(ax, 0.35, 2.9, 9.9, 3.75)
header(ax, 5.3, 6.5, "FINANCIAL-GUARDRAIL & TELEMETRY HARNESS", INDIGO)

hy, hh, hw, hgap = 4.85, 1.25, 2.15, 0.27
hx = [0.6, 0.6 + (hw + hgap), 0.6 + 2 * (hw + hgap), 0.6 + 3 * (hw + hgap)]
draw_box(ax, hx[0], hy, hw, hh, "Circuit\nBreaker",
         "Hard-halts agents on\nbudget or loop breach.",
         fill=CRIMSON, text_color=WHITE, title_size=10.5, emoji="🛑")
draw_box(ax, hx[1], hy, hw, hh, "Budget\nTracker",
         "Per-session token cost\n($3 / $15 per 1M).",
         fill=TEAL, text_color=WHITE, title_size=10.5, emoji="💰")
draw_box(ax, hx[2], hy, hw, hh, "Loop\nDetector",
         "Sliding-window catch of\nrepetitive reasoning.",
         fill=TEAL, text_color=WHITE, title_size=10.5, emoji="🔁")
draw_box(ax, hx[3], hy, hw, hh, "Arize Phoenix\n(OpenTelemetry)",
         "Trace UI + per-step\ntoken audit via OTLP.",
         fill=INDIGO, text_color=WHITE, title_size=10.5, emoji="📡")

for x0 in hx:
    arrow(ax, x0 + hw / 2, 6.28, x0 + hw / 2, hy + hh, INDIGO)

# guarded model bar
gy = 3.35
draw_box(ax, 2.2, gy, 6.2, 0.6,
         "GuardedBedrockModel — checks breaker before every call",
         fill=TEAL, text_color=WHITE, title_size=9.8, prefix="",
         emoji="🔒", radius=0.05)
for x0 in hx:
    arrow(ax, x0 + hw / 2, hy, x0 + hw / 2, gy + 0.6, INDIGO)

# ── AWS Bedrock ───────────────────────────────────────────────────────
by = 2.05
draw_box(ax, 2.9, by, 4.8, 0.7, "AWS Bedrock",
         fill=ORANGE, text_color=WHITE, title_size=14, prefix="",
         emoji="☁️", radius=0.05)
arrow(ax, 5.3, gy, 5.3, by + 0.7, ORANGE)

# ── bottom services ──────────────────────────────────────────────────
sy, sh, sw = 0.45, 0.78, 2.7
sx = [0.7, 3.9, 7.1]
draw_box(ax, sx[0], sy, sw, sh, "Contract\nSummarizer",
         fill=WHITE, text_color=BLACK, title_size=10, prefix="",
         emoji="📝", radius=0.05)
draw_box(ax, sx[1], sy, sw, sh, "Document\nParser",
         fill=WHITE, text_color=BLACK, title_size=10, prefix="",
         emoji="📄", radius=0.05)
draw_box(ax, sx[2], sy, sw, sh, "Titan Embed\nText",
         fill=WHITE, text_color=BLACK, title_size=10, prefix="",
         emoji="🧬", radius=0.05)
for x0 in sx:
    elbow(ax, 5.3, by, x0 + sw / 2, sy + sh, ORANGE)

# ── render + composite emojis with Pillow ────────────────────────────
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
H = int(fig.bbox.height)

buf = io.BytesIO()
fig.savefig(buf, dpi=DPI, facecolor=WHITE, format="png")
plt.close(fig)
buf.seek(0)
canvas = Image.open(buf).convert("RGBA")
scale = canvas.height / H  # savefig dpi vs display dpi

# NotoColorEmoji only ships a 109px strike
base_font = ImageFont.truetype(EMOJI_FONT, 109)


def render_emoji(char, target_px):
    layer = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((8, 8), char, font=base_font, embedded_color=True)
    bbox = layer.getbbox()
    if not bbox:
        return None
    glyph = layer.crop(bbox)
    ratio = target_px / max(glyph.size)
    return glyph.resize(
        (max(1, int(glyph.width * ratio)), max(1, int(glyph.height * ratio))),
        Image.LANCZOS,
    )


for text_obj, data_cy, char, fontsize in _emoji_queue:
    ext = text_obj.get_window_extent(renderer)  # display px, origin bottom-left
    target = int(fontsize * DPI / 72 * 1.35)
    glyph = render_emoji(char, target)
    if glyph is None:
        continue
    px_right = ext.x1 * scale
    cy_disp = (ext.y0 + ext.y1) / 2.0
    py_center = (H - cy_disp) * scale
    paste_x = int(px_right + 6 * scale)
    paste_y = int(py_center - glyph.height / 2)
    canvas.alpha_composite(glyph, (paste_x, paste_y))

canvas.save("/home/user/Factor-AI/docs/legal.png")
print("Saved docs/legal.png", canvas.size)
