#!/usr/bin/env python3
"""Generate 5 distinct logo concepts for BargainHuntrs."""
from PIL import Image, ImageDraw, ImageFont
import math
import os

# Brand colors
EMERALD = (16, 185, 129, 255)        # #10b981
EMERALD_DARK = (5, 150, 105, 255)    # darker emerald
EMERALD_LIGHT = (52, 211, 153, 255)  # lighter emerald
ZINC = (39, 39, 42, 255)             # zinc-800
ZINC_DARK = (24, 24, 27, 255)        # zinc-900
WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)

OUT_DIR = "/Volumes/Os_Sites/Bargain/bargain-web/public/logos"
os.makedirs(OUT_DIR, exist_ok=True)

# Canvas: high-res for quality. 1600x900 gives room for icon + wordmark.
W, H = 1600, 900

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

def draw_wordmark(draw, cx, cy, text, color, font, letter_spacing=0):
    """Draw centered wordmark."""
    total = 0
    widths = []
    for ch in text:
        w, _ = text_size(draw, ch, font)
        widths.append(w)
        total += w + letter_spacing
    total -= letter_spacing
    x = cx - total // 2
    for ch, w in zip(text, widths):
        draw.text((x, cy), ch, font=font, fill=color)
        x += w + letter_spacing

def rounded_rect(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def save(img, name):
    path = os.path.join(OUT_DIR, name)
    img.save(path, "PNG")
    print("Saved:", path)
    return path


# ============================================================
# OPTION 1: Magnifying glass + price tag hybrid
# ============================================================
def option1():
    img = Image.new("RGBA", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Icon area: left side. Icon center ~ (300, 380), size ~ 360
    cx, cy = 300, 380
    R = 150  # lens radius

    # Price tag shape (a rounded rectangle with a notch at top-left and a hole)
    # Draw tag behind/overlapping the lens lower-right
    tag_pts = []
    # Tag as a polygon: starts at a point (notch) top-left
    notch = (cx + 40, cy + 30)
    tag_pts = [
        (cx + 40, cy + 30),       # notch point (top-left tip)
        (cx + 230, cy + 10),      # top-right
        (cx + 260, cy + 60),      # right upper
        (cx + 250, cy + 220),     # bottom-right
        (cx + 60, cy + 250),      # bottom-left
        (cx + 30, cy + 200),      # left lower
        (cx + 35, cy + 80),       # left upper
    ]
    d.polygon(tag_pts, fill=EMERALD)

    # Tag hole
    hole_cx, hole_cy = cx + 80, cy + 70
    d.ellipse([hole_cx-16, hole_cy-16, hole_cx+16, hole_cy+16], fill=WHITE)
    d.ellipse([hole_cx-9, hole_cy-9, hole_cx+9, hole_cy+9], fill=ZINC_DARK)

    # Percent sign on the tag (deal symbol)
    try:
        pfont = find_font(90, bold=True)
    except Exception:
        pfont = find_font(90)
    d.text((cx + 130, cy + 110), "%", font=pfont, fill=WHITE)

    # Magnifying glass: lens (ring) + handle, drawn over the tag's left
    # Lens ring
    lens_cx, lens_cy = cx - 30, cy - 20
    d.ellipse([lens_cx-R, lens_cy-R, lens_cx+R, lens_cy+R], outline=ZINC_DARK, width=34)
    # Inner glass tint
    d.ellipse([lens_cx-R+22, lens_cy-R+22, lens_cx+R-22, lens_cy+R-22], fill=(16,185,129,40))
    # Handle
    hx1, hy1 = lens_cx + int(R*0.72), lens_cy + int(R*0.72)
    ang = math.radians(45)
    hx2 = hx1 + int(150*math.cos(ang))
    hy2 = hy1 + int(150*math.sin(ang))
    d.line([hx1, hy1, hx2, hy2], fill=ZINC_DARK, width=46)
    # handle cap rounded
    d.ellipse([hx2-23, hy2-23, hx2+23, hy2+23], fill=ZINC_DARK)

    # Wordmark
    wfont = find_font(150, bold=True)
    draw_wordmark(d, 950, 320, "Bargain", ZINC_DARK, wfont)
    draw_wordmark(d, 950, 470, "Huntrs", EMERALD, wfont)

    # Tagline
    tfont = find_font(40)
    draw_wordmark(d, 950, 620, "Find bargains before anyone else", (82,82,91,255), tfont)

    # Crop to content with padding
    img = img.crop((0, 0, W, H))
    return save(img, "logo-option-1.png")


# ============================================================
# OPTION 2: Stylized "B" with downward arrow (price dropping)
# ============================================================
def option2():
    img = Image.new("RGBA", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Icon: a bold "B" lettermark inside a rounded square, with a downward arrow
    # cutting through / integrated into the lower bowl of the B.
    box_x0, box_y0 = 130, 200
    box_x1, box_y1 = 530, 600
    rounded_rect(d, [box_x0, box_y0, box_x1, box_y1], 60, fill=EMERALD)

    # Draw a custom "B" using thick strokes
    bx = 250
    top_y = 250
    bot_y = 550
    stroke = 46
    # Vertical stem
    d.rounded_rectangle([bx, top_y, bx+stroke, bot_y], radius=stroke//2, fill=WHITE)
    # Top bowl
    d.arc([bx, top_y, bx+170, top_y+150], start=270, end=90, fill=WHITE, width=stroke)
    d.line([bx+stroke//2, top_y, bx+170, top_y+75], fill=WHITE, width=stroke)  # top bar close
    # Bottom bowl - but we replace lower part with an arrow
    # Lower bowl partial arc
    d.arc([bx, top_y+150, bx+200, bot_y], start=270, end=70, fill=WHITE, width=stroke)

    # Downward arrow integrated into lower-right of B (price drop)
    ar_cx = bx + 175
    ar_top = top_y + 200
    ar_bot = bot_y - 30
    # arrow shaft
    d.rounded_rectangle([ar_cx-18, ar_top, ar_cx+18, ar_bot-40], radius=14, fill=WHITE)
    # arrowhead
    head = [
        (ar_cx, ar_bot + 10),
        (ar_cx-45, ar_bot-55),
        (ar_cx-18, ar_bot-55),
        (ar_cx-18, ar_bot-40),
        (ar_cx+18, ar_bot-40),
        (ar_cx+18, ar_bot-55),
        (ar_cx+45, ar_bot-55),
    ]
    d.polygon(head, fill=WHITE)

    # Wordmark: "BargainHuntrs" inline, with arrow accent
    wfont = find_font(150, bold=True)
    text = "Bargain"
    text2 = "Huntrs"
    # measure
    w1, _ = text_size(d, text, wfont)
    w2, _ = text_size(d, text2, wfont)
    gap = 20
    total = w1 + gap + w2
    start_x = 950 - total//2
    y = 360
    d.text((start_x, y), text, font=wfont, fill=ZINC_DARK)
    d.text((start_x + w1 + gap, y), text2, font=wfont, fill=EMERALD)

    # Small downward arrow accent after wordmark (price drop motif)
    ax = start_x + w1 + gap + w2 + 25
    ay = y + 60
    d.polygon([(ax, ay-40),(ax-30, ay+10),(ax-12, ay+10),(ax-12, ay+50),(ax+12, ay+50),(ax+12, ay+10),(ax+30, ay+10)], fill=EMERALD)

    # Tagline
    tfont = find_font(40)
    draw_wordmark(d, 950, 540, "Find bargains before anyone else", (82,82,91,255), tfont)

    return save(img, "logo-option-2.png")


# ============================================================
# OPTION 3: Crosshair/target with dollar sign (hunting bargains)
# ============================================================
def option3():
    img = Image.new("RGBA", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    cx, cy = 330, 380
    R = 170

    # Outer target ring
    d.ellipse([cx-R, cy-R, cx+R, cy+R], outline=ZINC_DARK, width=30)
    # Middle ring
    d.ellipse([cx-R+55, cy-R+55, cx+R-55, cy+R-55], outline=EMERALD, width=26)
    # Inner filled circle
    inner_r = R - 110
    d.ellipse([cx-inner_r, cy-inner_r, cx+inner_r, cy+inner_r], fill=EMERALD_DARK)

    # Crosshair lines (broken at center)
    gap = 60
    # horizontal
    d.line([cx-R-30, cy, cx-gap, cy], fill=ZINC_DARK, width=24)
    d.line([cx+gap, cy, cx+R+30, cy], fill=ZINC_DARK, width=24)
    # vertical
    d.line([cx, cy-R-30, cx, cy-gap], fill=ZINC_DARK, width=24)
    d.line([cx, cy+gap, cx, cy+R+30], fill=ZINC_DARK, width=24)

    # Dollar sign in center
    sfont = find_font(120, bold=True)
    sw, sh = text_size(d, "$", sfont)
    d.text((cx - sw//2, cy - sh//2 - 10), "$", font=sfont, fill=WHITE)

    # Wordmark
    wfont = find_font(150, bold=True)
    draw_wordmark(d, 950, 320, "Bargain", ZINC_DARK, wfont)
    draw_wordmark(d, 950, 470, "Huntrs", EMERALD, wfont)

    tfont = find_font(40)
    draw_wordmark(d, 950, 620, "Find bargains before anyone else", (82,82,91,255), tfont)

    return save(img, "logo-option-3.png")


# ============================================================
# OPTION 4: Shopping bag with lightning bolt (fast deals)
# ============================================================
def option4():
    img = Image.new("RGBA", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Shopping bag
    bx0, by0 = 170, 250
    bx1, by1 = 490, 560
    # Bag body (rounded rectangle)
    rounded_rect(d, [bx0, by0, bx1, by1], 28, fill=EMERALD)
    # Bag handles (two arcs)
    hcx1 = bx0 + 95
    hcx2 = bx1 - 95
    hy = by0
    d.arc([hcx1-70, hy-110, hcx1+70, hy+30], start=180, end=360, fill=ZINC_DARK, width=26)
    d.arc([hcx2-70, hy-110, hcx2+70, hy+30], start=180, end=360, fill=ZINC_DARK, width=26)

    # Lightning bolt cut into bag (white bolt)
    bolt_pts = [
        (bx0+175, by0+40),
        (bx0+120, by0+170),
        (bx0+165, by0+170),
        (bx0+130, by0+300),
        (bx0+230, by0+140),
        (bx0+180, by0+140),
        (bx0+215, by0+40),
    ]
    d.polygon(bolt_pts, fill=WHITE)

    # Wordmark
    wfont = find_font(150, bold=True)
    draw_wordmark(d, 950, 320, "Bargain", ZINC_DARK, wfont)
    draw_wordmark(d, 950, 470, "Huntrs", EMERALD, wfont)

    tfont = find_font(40)
    draw_wordmark(d, 950, 620, "Find bargains before anyone else", (82,82,91,255), tfont)

    return save(img, "logo-option-4.png")


# ============================================================
# OPTION 5: Clean wordmark with embedded icon in the "B"
# ============================================================
def option5():
    img = Image.new("RGBA", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # A clean wordmark where the "B" is a custom badge containing a downward
    # arrow / price-drop notch, and the "H" has a small magnifier dot.
    # We'll render the wordmark large and replace the B with a custom drawn badge.

    wfont = find_font(170, bold=True)
    text = "argainHuntrs"
    # measure "argainHuntrs"
    w_rem, h_rem = text_size(d, text, wfont)
    # B badge size ~ height of text
    bh = h_rem
    bw = int(bh * 0.78)

    total = bw + 8 + w_rem
    start_x = (W - total)//2
    y = 300

    # Draw B badge (rounded square with custom B + arrow)
    badge_x0 = start_x
    badge_y0 = y + 5
    badge_x1 = start_x + bw
    badge_y1 = y + 5 + bh
    rounded_rect(d, [badge_x0, badge_y0, badge_x1, badge_y1], 36, fill=EMERALD)

    # Custom B inside badge (white) with downward arrow in lower bowl
    pad = int(bh*0.16)
    sx = badge_x0 + pad
    sy = badge_y0 + pad
    ex = badge_x1 - pad
    ey = badge_y1 - pad
    stem_w = int(bh*0.13)
    # stem
    d.rounded_rectangle([sx, sy, sx+stem_w, ey], radius=stem_w//2, fill=WHITE)
    # top bowl
    mid_y = (sy+ey)//2 - int(bh*0.04)
    bowl_r = (mid_y - sy)
    d.arc([sx, sy, ex, sy+2*bowl_r], start=270, end=90, fill=WHITE, width=stem_w)
    # lower bowl -> arrow instead
    # partial arc lower
    lbowl_r = (ey - mid_y)
    d.arc([sx, mid_y, ex, mid_y+2*lbowl_r], start=270, end=80, fill=WHITE, width=stem_w)
    # arrow head at bottom right of badge
    ar_cx = ex - int(bw*0.18)
    ar_bot = ey - int(bh*0.06)
    head = [
        (ar_cx, ar_bot + int(bh*0.10)),
        (ar_cx-int(bh*0.16), ar_bot - int(bh*0.14)),
        (ar_cx-int(bh*0.07), ar_bot - int(bh*0.14)),
        (ar_cx-int(bh*0.07), ar_bot - int(bh*0.22)),
        (ar_cx+int(bh*0.07), ar_bot - int(bh*0.22)),
        (ar_cx+int(bh*0.07), ar_bot - int(bh*0.14)),
        (ar_cx+int(bh*0.16), ar_bot - int(bh*0.14)),
    ]
    d.polygon(head, fill=WHITE)

    # rest of wordmark
    d.text((start_x + bw + 8, y), text, font=wfont, fill=ZINC_DARK)
    # color "Huntrs" portion emerald
    # find where "Huntrs" starts within "argainHuntrs"
    pre = "argain"
    w_pre, _ = text_size(d, pre, wfont)
    # erase and recolor: draw "argain" in zinc then "Huntrs" in emerald
    # (we already drew whole in zinc; redraw pre part to ensure clean, then Huntrs)
    d.text((start_x + bw + 8, y), "argain", font=wfont, fill=ZINC_DARK)
    d.text((start_x + bw + 8 + w_pre, y), "Huntrs", font=wfont, fill=EMERALD)

    # Tagline
    tfont = find_font(44)
    draw_wordmark(d, W//2, y + h_rem + 90, "Find bargains before anyone else", (82,82,91,255), tfont)

    return save(img, "logo-option-5.png")


if __name__ == "__main__":
    option1()
    option2()
    option3()
    option4()
    option5()
    print("All logos generated.")
