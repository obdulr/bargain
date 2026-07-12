#!/usr/bin/env python3
"""Generate social media assets for BargainHuntrs.

Creates:
  - profile-icon.png    — 400x400 square profile picture (X, Facebook, Instagram)
  - cover-x.png         — 1500x500 X/Twitter header banner
  - cover-facebook.png  — 1640x856 Facebook cover
  - cover-instagram.png — 1080x1080 Instagram profile (square)
"""
from PIL import Image, ImageDraw, ImageFont
import math
import os

# Brand colors
EMERALD = (16, 185, 129, 255)
EMERALD_DARK = (5, 150, 105, 255)
EMERALD_LIGHT = (52, 211, 153, 255)
EMERALD_GRAD_TOP = (16, 185, 129, 255)
EMERALD_GRAD_BOT = (5, 120, 85, 255)
ZINC = (39, 39, 42, 255)
ZINC_DARK = (24, 24, 27, 255)
ZINC_LIGHT = (82, 82, 91, 255)
WHITE = (255, 255, 255, 255)
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


def draw_vertical_gradient(img, color_top, color_bot):
    """Draw a vertical gradient on the image."""
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


def draw_centered_text(draw, cx, cy, text, color, font, letter_spacing=0):
    """Draw text centered at (cx, cy)."""
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


def draw_percent_badge(draw, cx, cy, radius, bg_color, text_color):
    """Draw a circular badge with % symbol."""
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=bg_color)
    pfont = find_font(int(radius * 1.1), bold=True)
    sw, sh = text_size(draw, "%", pfont)
    draw.text((cx - sw // 2, cy - sh // 2 - int(radius * 0.1)), "%", font=pfont, fill=text_color)


def draw_magnifying_glass(draw, cx, cy, r, ring_color, glass_tint, handle_color):
    """Draw a magnifying glass."""
    # Lens ring
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ring_color, width=int(r * 0.18))
    # Inner glass tint
    inner = int(r * 0.82)
    draw.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], fill=glass_tint)
    # Handle
    hx1 = cx + int(r * 0.72)
    hy1 = cy + int(r * 0.72)
    ang = math.radians(45)
    handle_len = int(r * 0.9)
    hx2 = hx1 + int(handle_len * math.cos(ang))
    hy2 = hy1 + int(handle_len * math.sin(ang))
    hw = int(r * 0.28)
    draw.line([hx1, hy1, hx2, hy2], fill=handle_color, width=hw)
    draw.ellipse([hx2 - hw // 2, hy2 - hw // 2, hx2 + hw // 2, hy2 + hw // 2], fill=handle_color)


def draw_price_tag(draw, cx, cy, size, color, hole_color):
    """Draw a price tag shape."""
    s = size
    pts = [
        (cx, cy),              # notch point (top-left tip)
        (cx + int(s * 1.2), cy - int(s * 0.15)),  # top-right
        (cx + int(s * 1.35), cy + int(s * 0.3)),  # right upper
        (cx + int(s * 1.25), cy + int(s * 1.1)),  # bottom-right
        (cx + int(s * 0.2), cy + int(s * 1.2)),   # bottom-left
        (cx - int(s * 0.05), cy + int(s * 0.9)),  # left lower
        (cx, cy + int(s * 0.3)),                  # left upper
    ]
    draw.polygon(pts, fill=color)
    # Tag hole
    hr = int(s * 0.1)
    hcx = cx + int(s * 0.25)
    hcy = cy + int(s * 0.25)
    draw.ellipse([hcx - hr, hcy - hr, hcx + hr, hcy + hr], fill=hole_color)


def save(img, name):
    path = os.path.join(OUT_DIR, name)
    img.save(path, "PNG")
    print(f"Saved: {path}")
    return path


# ============================================================
# PROFILE ICON — 400x400 square (X, Facebook, Instagram)
# ============================================================
def profile_icon():
    size = 400
    img = Image.new("RGBA", (size, size), TRANSPARENT)
    d = ImageDraw.Draw(img)

    # Background: rounded square with emerald gradient
    bg = Image.new("RGBA", (size, size), TRANSPARENT)
    draw_vertical_gradient(bg, EMERALD_GRAD_TOP, EMERALD_GRAD_BOT)

    # Create a mask for rounded corners
    mask = Image.new("RGBA", (size, size), TRANSPARENT)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, size, size], radius=80, fill=(255, 255, 255, 255))

    # Composite gradient with mask
    img = Image.new("RGBA", (size, size), TRANSPARENT)
    img.paste(bg, (0, 0), mask)
    d = ImageDraw.Draw(img)

    # Draw magnifying glass (hunting for bargains)
    cx, cy = size // 2, size // 2 - 10
    r = 90
    draw_magnifying_glass(d, cx, cy, r, WHITE, (255, 255, 255, 30), WHITE)

    # Draw % badge inside the lens
    draw_percent_badge(d, cx - 5, cy - 5, 45, WHITE, EMERALD_DARK)

    # "BH" text at bottom
    font = find_font(70, bold=True)
    draw_centered_text(d, size // 2, size - 80, "BH", WHITE, font, letter_spacing=4)

    return save(img, "profile-icon.png")


# ============================================================
# X/TWITTER COVER — 1500x500
# ============================================================
def cover_x():
    W, H = 1500, 500
    img = Image.new("RGBA", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Left panel: emerald gradient
    left_w = 500
    left = Image.new("RGBA", (left_w, H), TRANSPARENT)
    draw_vertical_gradient(left, EMERALD_GRAD_TOP, EMERALD_GRAD_BOT)
    img.paste(left, (0, 0), left)

    # Draw magnifying glass + % badge on left panel
    cx, cy = 250, 250
    r = 110
    draw_magnifying_glass(d, cx, cy, r, WHITE, (255, 255, 255, 30), WHITE)
    draw_percent_badge(d, cx - 5, cy - 5, 55, WHITE, EMERALD_DARK)

    # Right side: white background with text
    # Wordmark
    wfont = find_font(110, bold=True)
    d.text((560, 120), "Bargain", font=wfont, fill=ZINC_DARK)
    d.text((560, 230), "Huntrs", font=wfont, fill=EMERALD)

    # Tagline
    tfont = find_font(36)
    d.text((560, 360), "Find bargains before anyone else", font=tfont, fill=ZINC_LIGHT)

    # Deal categories on right
    cfont = find_font(24)
    cats = ["Amazon  |  Walmart  |  eBay  |  ADOR  |  50+ brands"]
    d.text((560, 420), cats[0], font=cfont, fill=EMERALD_DARK)

    return save(img, "cover-x.png")


# ============================================================
# FACEBOOK COVER — 1640x856
# ============================================================
def cover_facebook():
    W, H = 1640, 856
    img = Image.new("RGBA", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Full gradient background
    bg = Image.new("RGBA", (W, H), TRANSPARENT)
    draw_vertical_gradient(bg, EMERALD_GRAD_TOP, EMERALD_GRAD_BOT)
    img.paste(bg, (0, 0), bg)
    d = ImageDraw.Draw(img)

    # Left: magnifying glass + % badge
    cx, cy = 300, 380
    r = 160
    draw_magnifying_glass(d, cx, cy, r, WHITE, (255, 255, 255, 30), WHITE)
    draw_percent_badge(d, cx - 8, cy - 8, 80, WHITE, EMERALD_DARK)

    # Center/right: wordmark
    wfont = find_font(140, bold=True)
    d.text((620, 250), "Bargain", font=wfont, fill=WHITE)
    d.text((620, 390), "Huntrs", font=wfont, fill=WHITE)

    # Tagline
    tfont = find_font(44)
    d.text((620, 560), "Find bargains before anyone else", font=tfont, fill=(220, 255, 235, 255))

    # Deal sources
    cfont = find_font(30)
    d.text((620, 640), "Amazon  |  Walmart  |  eBay  |  ADOR  |  50+ brands", font=cfont, fill=(200, 255, 220, 255))

    # URL
    ufont = find_font(34, bold=True)
    d.text((620, 700), "bargainhuntrs.com", font=ufont, fill=WHITE)

    return save(img, "cover-facebook.png")


# ============================================================
# INSTAGRAM COVER — 1080x1080 (square)
# ============================================================
def cover_instagram():
    W, H = 1080, 1080
    img = Image.new("RGBA", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Full gradient background
    bg = Image.new("RGBA", (W, H), TRANSPARENT)
    draw_vertical_gradient(bg, EMERALD_GRAD_TOP, EMERALD_GRAD_BOT)
    img.paste(bg, (0, 0), bg)
    d = ImageDraw.Draw(img)

    # Center: magnifying glass + % badge
    cx, cy = 540, 380
    r = 180
    draw_magnifying_glass(d, cx, cy, r, WHITE, (255, 255, 255, 30), WHITE)
    draw_percent_badge(d, cx - 10, cy - 10, 90, WHITE, EMERALD_DARK)

    # Wordmark
    wfont = find_font(130, bold=True)
    draw_centered_text(d, W // 2, 640, "Bargain", WHITE, wfont, letter_spacing=2)
    draw_centered_text(d, W // 2, 770, "Huntrs", WHITE, wfont, letter_spacing=2)

    # Tagline
    tfont = find_font(40)
    draw_centered_text(d, W // 2, 910, "Find bargains before anyone else", (220, 255, 235, 255), tfont)

    # URL
    ufont = find_font(36, bold=True)
    draw_centered_text(d, W // 2, 970, "bargainhuntrs.com", WHITE, ufont)

    return save(img, "cover-instagram.png")


# ============================================================
# Generate all
# ============================================================
if __name__ == "__main__":
    print("Generating social media assets...")
    profile_icon()
    cover_x()
    cover_facebook()
    cover_instagram()
    print("\nAll assets generated in:", OUT_DIR)
