from PIL import Image
import math
import os

CELL = 32
SCALE = 4
WIDTH = CELL * 4
HEIGHT = CELL

out_dir = os.path.join("resources", "gfx", "indicator")
os.makedirs(out_dir, exist_ok=True)

img = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE), (255, 255, 255, 0))

def clamp01(x):
    return max(0.0, min(1.0, x))

def put_alpha(px, py, alpha):
    if alpha <= 0:
        return

    old = img.getpixel((px, py))
    new_alpha = max(old[3], int(clamp01(alpha) * 255))
    img.putpixel((px, py), (255, 255, 255, new_alpha))

def draw_cell(cell_index, alpha_func):
    x0 = cell_index * CELL * SCALE

    for py in range(CELL * SCALE):
        for px in range(CELL * SCALE):
            lx = (px + 0.5) / SCALE
            ly = (py + 0.5) / SCALE
            alpha = alpha_func(lx, ly)
            put_alpha(x0 + px, py, alpha)


# ---------------------------------------------------------------------------
# Generic shape factory.
#
# Every indicator sprite is an ellipse, configured by a small set of knobs so
# the look of each shape can be tweaked from one place (see SHAPES below).
#
#   mode          "ring"  -> hollow outline ellipse
#                 "fill"  -> opaque soft-edged ellipse
#                 "blob"  -> gaussian (fuzzy) ellipse
#   length        semi-axis along x (horizontal size)
#   width         semi-axis along y (vertical size)
#   squash        ground-projection deform; > 1 flattens the shape vertically
#                 so it reads as if painted on the floor
#   thickness     ring line width (only used by "ring")
#   edge          edge softness / fade distance for "fill" and "blob"
#   opacity       peak alpha of the shape body (0..1)
#   glow          strength of the surrounding glow (0 = no glow)
#   glow_spread   how far the glow bleeds out
#   center_clear  fade out the inner part below this normalized radius
#                 (0 = disabled); keeps the middle see-through for rings
# ---------------------------------------------------------------------------
def shape_alpha(
    mode="fill",
    cx=16.0,
    cy=16.0,
    length=10.0,
    width=5.0,
    squash=1.0,
    thickness=0.16,
    edge=0.18,
    opacity=1.0,
    glow=0.0,
    glow_spread=0.42,
    center_clear=0.0,
):
    def f(x, y):
        dx = x - cx
        dy = (y - cy) * squash  # deform: squash toward the ground plane

        ex = dx / length
        ey = dy / width
        d = math.sqrt(ex * ex + ey * ey)

        if mode == "ring":
            core = math.exp(-((d - 1.0) / thickness) ** 2) * opacity
            g = math.exp(-((d - 1.0) / glow_spread) ** 2) * glow
        elif mode == "blob":
            core = math.exp(-(d / max(edge, 1e-6)) ** 2) * opacity
            g = math.exp(-(d / glow_spread) ** 2) * glow
        else:  # "fill" -> opaque ellipse with a soft edge
            core = clamp01((1.0 - d) / max(edge, 1e-6)) * opacity
            g = math.exp(-((d - 1.0) / glow_spread) ** 2) * glow

        a = max(core, g)

        if center_clear > 0.0:
            a *= clamp01((d - center_clear) / 0.25)

        return a

    return f


# ---------------------------------------------------------------------------
# Per-shape configuration. Tweak these to change how each indicator looks.
# ---------------------------------------------------------------------------
SHAPES = {
    # Soft floor ellipse/ring with a glow and a transparent center.
    "marker": dict(
        mode="ring",
        length=10.5,
        width=5.2,
        squash=1.0,
        thickness=0.16,
        opacity=0.95,
        glow=0.28,
        glow_spread=0.42,
        center_clear=0.35,
    ),
    # Opaque ellipse with a glow (replaces the old dot/cross center).
    "center": dict(
        mode="fill",
        length=5.2,
        width=2.6,
        squash=1.0,
        edge=0.14,
        opacity=1.0,
        glow=0.45,
        glow_spread=0.55,
    ),
    # Small soft floor dot.
    "trail": dict(
        mode="blob",
        length=4.2,
        width=2.6,
        squash=1.0,
        edge=0.86,
        opacity=0.78,
    ),
    # Small vertical bead/capsule with a glow.
    "tether": dict(
        mode="blob",
        length=1.45,
        width=4.8,
        squash=1.0,
        edge=0.93,
        opacity=0.9,
        glow=0.22,
        glow_spread=1.69,
    ),
}

draw_cell(0, shape_alpha(**SHAPES["marker"]))
draw_cell(1, shape_alpha(**SHAPES["center"]))
draw_cell(2, shape_alpha(**SHAPES["trail"]))
draw_cell(3, shape_alpha(**SHAPES["tether"]))

img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
img.save(os.path.join(out_dir, "indicators.png"))

print("Wrote resources/gfx/indicator/indicators.png")
