"""Film title cards as transparent square PNGs (opening + closing).

    python tools/titles.py projects/<name> [--size 1080]

Text comes from project.json "titles":
    {"open": {"number": "5", "caps": "ANOS"}, "close": {"caps": "CINCO ANOS", "italic": "de nós."}}
Fonts and layout come from the style's "typography". Layout is designed at 1080 and scaled, so a 4K
master gets native-resolution type instead of an upscaled PNG. Writes work/title_open_<size>.png and
work/title_close_<size>.png.
"""
import argparse
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from gf import Project

FONT_DIRS = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
             Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
             Path("/Library/Fonts"), Path.home() / "Library/Fonts", Path("/usr/share/fonts"), Path.home() / ".fonts"]


def font(name, fallbacks, size):
    for n in [name, *fallbacks]:
        for d in FONT_DIRS:
            hits = [p for p in d.rglob("*") if p.name.lower() == n.lower()] if d.exists() else []
            if hits:
                return ImageFont.truetype(str(hits[0]), size)
    sys.exit(f"font not found: {name} (also tried {fallbacks})")


def draw_tracked(draw, cx, y, text, f, tracking, fill):
    w = sum(draw.textlength(ch, font=f) for ch in text) + tracking * (len(text) - 1)
    x = cx - w / 2
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + tracking


def with_shadow(layer, blur, opacity):
    """Soft dark glow under the type so it reads over bright sand or sky."""
    alpha = layer.split()[3].filter(ImageFilter.GaussianBlur(blur))
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shadow.putalpha(alpha.point(lambda a: min(255, int(a * opacity))))
    return Image.alpha_composite(shadow, layer)


def build(prj, size):
    ty = prj.style["typography"]
    titles = prj.data.get("titles", {})
    k = size / 1080
    cx = size / 2
    fb = ty.get("fallback_fonts", [])
    sh = ty["shadow"]
    out = {}

    o = titles.get("open")
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if o:
        d = ImageDraw.Draw(img)
        big = font(ty["number_font"], fb, round(ty["open"]["number_size"] * k))
        caps = font(ty["caps_font"], fb, round(ty["open"]["caps_size"] * k))
        box = d.textbbox((0, 0), o["number"], font=big)
        d.text((cx - (box[2] + box[0]) / 2, 330 * k - box[1]), o["number"], font=big, fill=(255, 255, 255, 240))
        d.line([(cx - 70 * k, 600 * k), (cx + 70 * k, 600 * k)], fill=(255, 255, 255, 170), width=round(2 * k))
        draw_tracked(d, cx, 628 * k, o["caps"], caps, ty["open"]["caps_tracking"] * k, (255, 255, 255, 235))
    out["open"] = prj.work / f"title_open_{size}.png"
    with_shadow(img, sh["blur"] * k, sh["opacity"]).save(out["open"])

    c = titles.get("close")
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if c:
        d = ImageDraw.Draw(img)
        small = font(ty["caps_font"], fb, round(ty["close"]["caps_size"] * k))
        ital = font(ty["italic_font"], fb, round(ty["close"]["italic_size"] * k))
        if c.get("caps"):
            draw_tracked(d, cx, 790 * k, c["caps"], small, ty["close"]["caps_tracking"] * k, (255, 255, 255, 200))
        w = d.textlength(c["italic"], font=ital)
        d.text((cx - w / 2, 822 * k), c["italic"], font=ital, fill=(255, 255, 255, 245))
    out["close"] = prj.work / f"title_close_{size}.png"
    with_shadow(img, sh["blur"] * k, sh["opacity"]).save(out["close"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--size", type=int, default=1080)
    a = ap.parse_args()
    for p in build(Project(a.project), a.size).values():
        print(p)


if __name__ == "__main__":
    main()
