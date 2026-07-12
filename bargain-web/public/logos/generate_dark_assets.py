#!/usr/bin/env python3
"""Generate dark-themed social media covers using logo-option-4 design.

Shopping bag + lightning bolt on dark background.

Creates:
  - cover-x-dark.png         — 1500x500 X/Twitter header
  - cover-facebook-dark.png  — 1640x856 Facebook cover
  - cover-instagram-dark.png — 1080x1080 Instagram
  - profile-icon-dark.png    — 400x400 profile picture
"""
from PIL import Image, ImageDraw, ImageFont
import math
import os

# Brand colors
EMERALD = (16, 185, 129, 255)
EMERALD_DARK = (5, 150, 105, 255)
EMERALD_LIGHT = (52, 211, 153, 255)
ZINC_DARK = (24, 24, 27, 255)       # near-black
ZINC_DARKER = (9, 9, 11, 255)       # almost black
ZINC = (39, 39, 42, 255)
ZINC_LIGHT = (82, 82, 91, 255)
ZINC_MUTED = (113, 113, 122, 255)
WHITE = (255, 255, 255, 255)
OFF_WHITE = (244, 244, 245, 255)
TRANSPARENT = (0, 0, 0, 0)

OUT_DIR = "/Volumes/Os_Sites/Bargain/bargain-web/public/logos"
os.makedirs(OUT_DIR, exist_ok=True)


def find_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_centered_text(draw, cx, cy, text, color, font, letter_spacing=0):
    widths = []
    total = 0
    for ch in text:
        w, _ = text_size(draw, ch, font)
        widths.append(w)
        total += w + letter_spacing
    total -= letter_spacing
    x = cx - total // 2
    for ch, w in zip(text, widths):
        draw.text((x, cy), ch, font=font, fill=color)
        x += w + letter_spacing


def draw_vertical_gradient(img, color_top, color_bot):
    w, h = img.size
    px = img.load()
    for y in range(h):
        ratio = y / max(h - 1, 1)
        r = int(color_top[0] + (color_bot[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bot[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bot[2] - color_top[2]) * ratio)
        a = int(color_top[3] + (color_bot[3] - color_top[3]) * ratio)
        for x in range(w):
            px[x, y] = (r, g, b, a)


def draw_shopping_bag_with_bolt(draw, cx, cy, scale=1.0, bag_color=None, bolt_color=None, handle_color=None):
    """Draw the shopping bag with lightning bolt (logo-option-4 design).

    cx, cy is the CENTER of the bag body (not including handles).
    Handles are drawn above the bag body.
    """
    if bag_color is None:
        bag_color = EMERALD
    if bolt_color is None:
        bolt_color = WHITE
    if handle_color is None:
        handle_color = ZINC_LIGHT

    s = scale
    bw = int(320 * s)
    bh = int(310 * s)

    # Bag body positioned so cy is the center of the body
    bx0 = cx - bw // 2
    by0 = cy - bh // 2
    bx1 = bx0 + bw
    by1 = by0 + bh

    # Bag body (rounded rectangle)
    radius = int(28 * s)
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=radius, fill=bag_color)

    # Bag handles (two arcs) — drawn above the bag, fully visible
    hcx1 = bx0 + int(95 * s)
    hcx2 = bx1 - int(95 * s)
    hy = by0
    hw = int(26 * s)
    # Arc spans from hy-110 to hy+30 (handle rises above bag top)
    draw.arc([hcx1 - int(70 * s), hy - int(110 * s), hcx1 + int(70 * s), hy + int(30 * s)],
             start=180, end=360, fill=handle_color, width=hw)
    draw.arc([hcx2 - int(70 * s), hy - int(110 * s), hcx2 + int(70 * s), hy + int(30 * s)],
             start=180, end=360, fill=handle_color, width=hw)

    # Lightning bolt (white) cut into bag
    bolt_pts = [
        (bx0 + int(175 * s), by0 + int(40 * s)),
        (bx0 + int(120 * s), by0 + int(170 * s)),
        (bx0 + int(165 * s), by0 + int(170 * s)),
        (bx0 + int(130 * s), by0 + int(300 * s)),
        (bx0 + int(230 * s), by0 + int(140 * s)),
        (bx0 + int(180 * s), by0 + int(140 * s)),
        (bx0 + int(215 * s), by0 + int(40 * s)),
    ]
    draw.polygon(bolt_pts, fill=bolt_color)


def save(img, name):
    path = os.path.join(OUT_DIR, name)
    img.save(path, "PNG")
    print(f"Saved: {path}")
    return path


# ============================================================
# PROFILE ICON — 400x400 (dark)
# ============================================================
def profile_icon_dark():
    size = 400
    img = Image.new("RGBA", (size, size), TRANSPARENT)

    # Dark gradient background
    bg = Image.new("RGBA", (size, size), TRANSPARENT)
    draw_vertical_gradient(bg, ZINC_DARK, ZINC_DARKER)

    # Rounded square mask
    mask = Image.new("RGBA", (size, size), TRANSPARENT)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, size, size], radius=80, fill=(255, 255, 255, 255))

    img = Image.new("RGBA", (size, size), TRANSPARENT)
    img.paste(bg, (0, 0), mask)
    d = ImageDraw.Draw(img)

    # Shopping bag with lightning bolt (shifted down so handles aren't cut)
    draw_shopping_bag_with_bolt(d, size // 2, size // 2 + 20, scale=0.65,
                                handle_color=ZINC_LIGHT)

    # "BH" text at bottom
    font = find_font(50, bold=True)
    draw_centered_text(d, size // 2, size - 60, "BH", WHITE, font, letter_spacing=4)

    return save(img, "profile-icon-dark.png")


# ============================================================
# X/TWITTER COVER — 1500x500 (dark)
# ============================================================
def cover_x_dark():
    W, H = 1500, 500
    img = Image.new("RGBA", (W, H), ZINC_DARKER)
    d = ImageDraw.Draw(img)

    # Subtle gradient
    bg = Image.new("RGBA", (W, H), TRANSPARENT)
    draw_vertical_gradient(bg, ZINC_DARK, ZINC_DARKER)
    img.paste(bg, (0, 0), bg)
    d = ImageDraw.Draw(img)

    # Left: shopping bag with bolt (shifted down so handles fit)
    draw_shopping_bag_with_bolt(d, 250, 280, scale=0.85, handle_color=ZINC_LIGHT)

    # Right: wordmark
    wfont = find_font(110, bold=True)
    d.text((560, 120), "Bargain", font=wfont, fill=WHITE)
    d.text((560, 230), "Huntrs", font=wfont, fill=EMERALD)

    # Tagline
    tfont = find_font(34)
    d.text((560, 360), "Find bargains before anyone else", font=tfont, fill=ZINC_LIGHT)

    # Deal sources
    cfont = find_font(22)
    d.text((560, 420), "Amazon  |  Walmart  |  eBay  |  ADOR  |  50+ brands", font=cfont, fill=EMERALD_LIGHT)

    return save(img, "cover-x-dark.png")


# ============================================================
# FACEBOOK COVER — 1640x856 (dark)
# ============================================================
def cover_facebook_dark():
    W, H = 1640, 856
    img = Image.new("RGBA", (W, H), ZINC_DARKER)
    d = ImageDraw.Draw(img)

    # Gradient background
    bg = Image.new("RGBA", (W, H), TRANSPARENT)
    draw_vertical_gradient(bg, ZINC_DARK, ZINC_DARKER)
    img.paste(bg, (0, 0), bg)
    d = ImageDraw.Draw(img)

    # Left: shopping bag with bolt (larger, shifted down for handles)
    draw_shopping_bag_with_bolt(d, 350, 460, scale=1.3, handle_color=ZINC_LIGHT)

    # Right: wordmark
    wfont = find_font(140, bold=True)
    d.text((700, 250), "Bargain", font=wfont, fill=WHITE)
    d.text((700, 390), "Huntrs", font=wfont, fill=EMERALD)

    # Tagline
    tfont = find_font(42)
    d.text((700, 560), "Find bargains before anyone else", font=tfont, fill=ZINC_LIGHT)

    # Deal sources
    cfont = find_font(28)
    d.text((700, 640), "Amazon  |  Walmart  |  eBay  |  ADOR  |  50+ brands", font=cfont, fill=EMERALD_LIGHT)

    # URL
    ufont = find_font(32, bold=True)
    d.text((700, 700), "bargainhuntrs.com", font=ufont, fill=WHITE)

    return save(img, "cover-facebook-dark.png")


# ============================================================
# INSTAGRAM COVER — 1080x1080 (dark)
# ============================================================
def cover_instagram_dark():
    W, H = 1080, 1080
    img = Image.new("RGBA", (W, H), ZINC_DARKER)
    d = ImageDraw.Draw(img)

    # Gradient background
    bg = Image.new("RGBA", (W, H), TRANSPARENT)
    draw_vertical_gradient(bg, ZINC_DARK, ZINC_DARKER)
    img.paste(bg, (0, 0), bg)
    d = ImageDraw.Draw(img)

    # Center: shopping bag with bolt (shifted down so handles fit)
    draw_shopping_bag_with_bolt(d, 540, 420, scale=1.4, handle_color=ZINC_LIGHT)

    # Wordmark
    wfont = find_font(120, bold=True)
    draw_centered_text(d, W // 2, 640, "Bargain", WHITE, wfont, letter_spacing=2)
    draw_centered_text(d, W // 2, 770, "Huntrs", EMERALD, wfont, letter_spacing=2)

    # Tagline
    tfont = find_font(38)
    draw_centered_text(d, W // 2, 910, "Find bargains before anyone else", ZINC_LIGHT, tfont)

    # URL
    ufont = find_font(34, bold=True)
    draw_centered_text(d, W // 2, 970, "bargainhuntrs.com", WHITE, ufont)

    return save(img, "cover-instagram-dark.png")


if __name__ == "__main__":
    print("Generating dark-themed social media assets...")
    profile_icon_dark()
    cover_x_dark()
    cover_facebook_dark()
    cover_instagram_dark()
    print("\nAll dark assets generated in:", OUT_DIR)
