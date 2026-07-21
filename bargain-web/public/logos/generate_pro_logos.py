#!/usr/bin/env python3
"""Generate professional BargainHuntrs logo and social media assets from SVG.

Creates clean, scalable vector-based logos in all required sizes:
  - X/Twitter: 400x400 profile, 1500x500 header
  - Facebook: 1080x1080 profile, 1640x856 cover
  - Instagram: 320x320 profile, 1080x1080 cover
"""
import cairosvg
import io
import os
from PIL import Image

OUT_DIR = "/Volumes/Os_Sites/Bargain/bargain-web/public/logos"
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================
# BRAND COLORS
# ============================================================
EMERALD = "#10b981"
EMERALD_DARK = "#059669"
EMERALD_LIGHT = "#34d399"
DARK_BG = "#0a0a0b"
DARK_BG2 = "#18181b"
WHITE = "#ffffff"
TRANSPARENT = (0, 0, 0, 0)
ZINC_LIGHT = "#a1a1aa"
ZINC_MUTED = "#71717a"


# ============================================================
# SVG: PROFILE ICON (square, works for all platforms)
# ============================================================
def svg_profile_icon(size=400):
    """Shopping bag with lightning bolt — clean, modern, professional."""
    s = size
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 400 400">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#18181b"/>
      <stop offset="100%" stop-color="#0a0a0b"/>
    </linearGradient>
    <linearGradient id="bag" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#10b981" flood-opacity="0.3"/>
    </filter>
  </defs>

  <!-- Transparent background — no dark square -->

  <!-- Shopping bag with lightning bolt -->
  <g filter="url(#shadow)" transform="translate(0, 10)">
    <!-- Bag handles -->
    <path d="M 140 155 Q 140 110 170 110 Q 200 110 200 155"
          stroke="#ffffff" stroke-width="14" fill="none" stroke-linecap="round"/>
    <path d="M 200 155 Q 200 110 230 110 Q 260 110 260 155"
          stroke="#ffffff" stroke-width="14" fill="none" stroke-linecap="round"/>

    <!-- Bag body -->
    <rect x="120" y="155" width="160" height="170" rx="20" fill="url(#bag)"/>

    <!-- Lightning bolt (centered original shape) -->
    <path d="M 210 175 L 170 245 L 195 245 L 175 305 L 230 220 L 205 220 L 225 175 Z"
          fill="#ffffff"/>
  </g>

  <text x="155" y="248" text-anchor="middle" font-family="Helvetica, Arial, sans-serif"
        font-size="52" font-weight="bold" fill="#ffffff">B</text>
  <text x="245" y="288" text-anchor="middle" font-family="Helvetica, Arial, sans-serif"
        font-size="52" font-weight="bold" fill="#ffffff">H</text>
</svg>"""


# ============================================================
# SVG: X/TWITTER HEADER (1500x500)
# ============================================================
def svg_cover_x():
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="500" viewBox="0 0 1500 500">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#18181b"/>
      <stop offset="100%" stop-color="#0a0a0b"/>
    </linearGradient>
    <linearGradient id="bag" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="6" stdDeviation="12" flood-color="#10b981" flood-opacity="0.25"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="1500" height="500" fill="url(#bg)"/>

  <!-- Subtle accent line -->
  <rect x="0" y="0" width="500" height="500" fill="#10b981" opacity="0.03"/>

  <!-- Shopping bag icon (left side) -->
  <g filter="url(#glow)" transform="translate(250, 250)">
    <!-- Handles -->
    <path d="M -60 -45 Q -60 -95 -30 -95 Q 0 -95 0 -45"
          stroke="#52525b" stroke-width="16" fill="none" stroke-linecap="round"/>
    <path d="M 0 -45 Q 0 -95 30 -95 Q 60 -95 60 -45"
          stroke="#52525b" stroke-width="16" fill="none" stroke-linecap="round"/>
    <!-- Bag body -->
    <rect x="-80" y="-45" width="160" height="170" rx="24" fill="url(#bag)"/>
    <!-- Lightning bolt -->
    <path d="M 15 -25 L -25 45 L 0 45 L -20 105 L 35 20 L 10 20 L 30 -25 Z"
          fill="#ffffff"/>
  </g>

  <!-- Wordmark -->
  <text x="560" y="200" font-family="Helvetica, Arial, sans-serif"
        font-size="100" font-weight="bold" fill="#ffffff">Bargain</text>
  <text x="560" y="300" font-family="Helvetica, Arial, sans-serif"
        font-size="100" font-weight="bold" fill="#10b981">Huntrs</text>

  <!-- Tagline -->
  <text x="560" y="370" font-family="Helvetica, Arial, sans-serif"
        font-size="32" fill="#a1a1aa">Find bargains before anyone else</text>

  <!-- Deal sources -->
  <text x="560" y="420" font-family="Helvetica, Arial, sans-serif"
        font-size="22" fill="#34d399">Amazon  |  Walmart  |  eBay  |  ADOR  |  50+ brands</text>
</svg>"""


# ============================================================
# SVG: FACEBOOK COVER (1640x856)
# ============================================================
def svg_cover_facebook():
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1640" height="856" viewBox="0 0 1640 856">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#18181b"/>
      <stop offset="100%" stop-color="#0a0a0b"/>
    </linearGradient>
    <linearGradient id="bag" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="8" stdDeviation="16" flood-color="#10b981" flood-opacity="0.3"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="1640" height="856" fill="url(#bg)"/>

  <!-- Accent panel -->
  <rect x="0" y="0" width="600" height="856" fill="#10b981" opacity="0.04"/>

  <!-- Shopping bag icon (larger, left) -->
  <g filter="url(#glow)" transform="translate(320, 460)">
    <!-- Handles -->
    <path d="M -90 -70 Q -90 -145 -45 -145 Q 0 -145 0 -70"
          stroke="#52525b" stroke-width="22" fill="none" stroke-linecap="round"/>
    <path d="M 0 -70 Q 0 -145 45 -145 Q 90 -145 90 -70"
          stroke="#52525b" stroke-width="22" fill="none" stroke-linecap="round"/>
    <!-- Bag body -->
    <rect x="-120" y="-70" width="240" height="255" rx="32" fill="url(#bag)"/>
    <!-- Lightning bolt -->
    <path d="M 22 -38 L -38 68 L 0 68 L -30 158 L 52 32 L 15 32 L 45 -38 Z"
          fill="#ffffff"/>
  </g>

  <!-- Wordmark -->
  <text x="700" y="340" font-family="Helvetica, Arial, sans-serif"
        font-size="130" font-weight="bold" fill="#ffffff">Bargain</text>
  <text x="700" y="470" font-family="Helvetica, Arial, sans-serif"
        font-size="130" font-weight="bold" fill="#10b981">Huntrs</text>

  <!-- Tagline -->
  <text x="700" y="560" font-family="Helvetica, Arial, sans-serif"
        font-size="42" fill="#a1a1aa">Find bargains before anyone else</text>

  <!-- Deal sources -->
  <text x="700" y="640" font-family="Helvetica, Arial, sans-serif"
        font-size="28" fill="#34d399">Amazon  |  Walmart  |  eBay  |  ADOR  |  50+ brands</text>

  <!-- URL -->
  <text x="700" y="710" font-family="Helvetica, Arial, sans-serif"
        font-size="34" font-weight="bold" fill="#ffffff">bargainhuntrs.com</text>
</svg>"""


# ============================================================
# SVG: INSTAGRAM COVER (1080x1080)
# ============================================================
def svg_cover_instagram():
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#18181b"/>
      <stop offset="100%" stop-color="#0a0a0b"/>
    </linearGradient>
    <linearGradient id="bag" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="10" stdDeviation="20" flood-color="#10b981" flood-opacity="0.3"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="1080" height="1080" fill="url(#bg)"/>

  <!-- Shopping bag icon (centered, large) -->
  <g filter="url(#glow)" transform="translate(540, 420)">
    <!-- Handles -->
    <path d="M -100 -75 Q -100 -155 -50 -155 Q 0 -155 0 -75"
          stroke="#52525b" stroke-width="24" fill="none" stroke-linecap="round"/>
    <path d="M 0 -75 Q 0 -155 50 -155 Q 100 -155 100 -75"
          stroke="#52525b" stroke-width="24" fill="none" stroke-linecap="round"/>
    <!-- Bag body -->
    <rect x="-130" y="-75" width="260" height="275" rx="34" fill="url(#bag)"/>
    <!-- Lightning bolt -->
    <path d="M 25 -40 L -40 72 L 0 72 L -32 170 L 56 34 L 18 34 L 50 -40 Z"
          fill="#ffffff"/>
  </g>

  <!-- Wordmark -->
  <text x="540" y="720" text-anchor="middle" font-family="Helvetica, Arial, sans-serif"
        font-size="110" font-weight="bold" fill="#ffffff">Bargain</text>
  <text x="540" y="840" text-anchor="middle" font-family="Helvetica, Arial, sans-serif"
        font-size="110" font-weight="bold" fill="#10b981">Huntrs</text>

  <!-- Tagline -->
  <text x="540" y="920" text-anchor="middle" font-family="Helvetica, Arial, sans-serif"
        font-size="38" fill="#a1a1aa">Find bargains before anyone else</text>

  <!-- URL -->
  <text x="540" y="980" text-anchor="middle" font-family="Helvetica, Arial, sans-serif"
        font-size="34" font-weight="bold" fill="#ffffff">bargainhuntrs.com</text>
</svg>"""


# ============================================================
# Render SVG to PNG
# ============================================================
def render_svg(svg_string, output_name, width=None, height=None):
    """Render SVG to PNG file."""
    path = os.path.join(OUT_DIR, output_name)

    if width and height:
        cairosvg.svg2png(
            bytestring=svg_string.encode("utf-8"),
            write_to=path,
            output_width=width,
            output_height=height,
        )
    else:
        cairosvg.svg2png(
            bytestring=svg_string.encode("utf-8"),
            write_to=path,
        )

    size_kb = os.path.getsize(path) // 1024
    print(f"  {output_name}: {size_kb}KB")
    return path


def render_profile_cutout(output_name, size=400):
    """Render the profile icon so B, lightning bolt, and H are transparent cutouts."""
    bag_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 400 400">
  <defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#10b981" flood-opacity="0.3"/>
    </filter>
  </defs>
  <g filter="url(#shadow)">
    <path d="M 140 165 Q 140 120 170 120 Q 200 120 200 165"
          stroke="#10b981" stroke-width="14" fill="none" stroke-linecap="round"/>
    <path d="M 200 165 Q 200 120 230 120 Q 260 120 260 165"
          stroke="#10b981" stroke-width="14" fill="none" stroke-linecap="round"/>
    <rect x="120" y="165" width="160" height="170" rx="20" fill="#10b981"/>
  </g>
</svg>"""
    holes_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 400 400">
  <rect x="0" y="0" width="400" height="400" fill="white"/>
  <text x="148" y="248" text-anchor="middle" font-family="Helvetica, Arial, sans-serif"
        font-size="58" font-weight="bold" fill="black">B</text>
  <text x="252" y="288" text-anchor="middle" font-family="Helvetica, Arial, sans-serif"
        font-size="58" font-weight="bold" fill="black">H</text>
  <path d="M 210 185 L 170 255 L 195 255 L 175 315 L 230 230 L 205 230 L 225 185 Z"
        fill="black"/>
</svg>"""
    bag_png = cairosvg.svg2png(
        bytestring=bag_svg.encode("utf-8"), output_width=size, output_height=size
    )
    holes_png = cairosvg.svg2png(
        bytestring=holes_svg.encode("utf-8"), output_width=size, output_height=size
    )
    bag = Image.open(io.BytesIO(bag_png)).convert("RGBA")
    holes = Image.open(io.BytesIO(holes_png)).convert("L")
    final = Image.new("RGBA", (size, size), TRANSPARENT)
    final.paste(bag, (0, 0), holes)
    path = os.path.join(OUT_DIR, output_name)
    final.save(path)
    size_kb = os.path.getsize(path) // 1024
    print(f"  {output_name}: {size_kb}KB")
    return path


# ============================================================
# Generate all assets
# ============================================================
if __name__ == "__main__":
    print("Generating professional SVG-based social media assets...\n")

    # Profile icons (all sizes)
    print("Profile icons:")
    render_profile_cutout("profile-icon-dark.png", 400)
    render_profile_cutout("profile-icon-facebook.png", 1080)
    render_profile_cutout("profile-icon-instagram.png", 320)

    # Covers
    print("\nCover images:")
    render_svg(svg_cover_x(), "cover-x-dark.png")
    render_svg(svg_cover_facebook(), "cover-facebook-dark.png")
    render_svg(svg_cover_instagram(), "cover-instagram-dark.png")

    # Also save the SVG source
    with open(os.path.join(OUT_DIR, "bargainhuntrs-logo.svg"), "w") as f:
        f.write(svg_profile_icon(400))
    print("\n  bargainhuntrs-logo.svg (source)")

    print("\nAll assets generated in:", OUT_DIR)
