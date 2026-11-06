#!/usr/bin/env python3
"""Draw REDSHIFT's magazine adverts: python3 tools/mkads.py

These adverts are fictional pastiches of BBC Micro software adverts of
1987-88. Doppler Software, its logo, its address, its telephone number and
its offer are all made up; no real company's branding is copied. The game
and its screenshots (docs/media) are real.

Writes docs/press/adverts/full-page.png, half-page.png and quarter-page.png.
The stills are the game's own screens, brought back to the BBC's 256x192 and
scaled up by whole factors, nearest-neighbour, so the pixels stay square.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(ROOT, "docs", "media")
OUT = os.path.join(ROOT, "docs", "press", "adverts")
URW = "/usr/share/fonts/opentype/urw-base35"

# The type of a 1987 advert: Avant Garde (URW Gothic) and Bookman for display,
# Century Schoolbook (C059) for the body, Helvetica Narrow for small print.
FACES = {
    "gothic": "URWGothic-Demi.otf",
    "gothic-book": "URWGothic-Book.otf",
    "bookman": "URWBookman-Demi.otf",
    "bookman-it": "URWBookman-DemiItalic.otf",
    "body": "C059-Roman.otf",
    "body-bold": "C059-Bold.otf",
    "body-it": "C059-Italic.otf",
    "narrow": "NimbusSansNarrow-Bold.otf",
    "narrow-reg": "NimbusSansNarrow-Regular.otf",
    "sans": "NimbusSans-Bold.otf",
    "sans-reg": "NimbusSans-Regular.otf",
    "mono": "NimbusMonoPS-Bold.otf",
}
SYMBOLS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# The BBC Micro's colours, and the advert's inks.
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
RED, BLUE = (255, 0, 0), (0, 0, 255)
YELLOW, CYAN, MAGENTA = (255, 255, 0), (0, 255, 255), (255, 0, 255)
INK_RED, INK_BLUE = (220, 30, 30), (20, 60, 200)
PAPER = (250, 247, 238)
NIGHT = (10, 10, 30)

_fonts = {}


def font(face, size):
    key = (face, size)
    if key not in _fonts:
        path = SYMBOLS if face == "symbols" else os.path.join(URW, FACES[face])
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]


def text_w(text, f):
    return f.getlength(text)


def fit(text, face, width, start=400):
    """The largest size of face at which text is no wider than width."""
    size = start
    while size > 6 and text_w(text, font(face, size)) > width:
        size -= 2
    return font(face, size)


def centred(d, cx, y, text, f, fill):
    d.text((cx - text_w(text, f) / 2, y), text, font=f, fill=fill)


def spaced(d, x, y, text, f, fill, track):
    """Letter-spaced caps, the way the small labels were set."""
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += text_w(ch, f) + track
    return x


def spaced_w(text, f, track):
    return sum(text_w(ch, f) + track for ch in text) - track


def wrap(text, f, width):
    lines, line = [], []
    for word in text.split():
        trial = " ".join(line + [word])
        if line and text_w(trial, f) > width:
            lines.append(line)
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(line)
    return lines


def paragraph(d, x, y, width, text, f, fill, leading, justify=True):
    """Set text in a column, justified but for its last line; returns the y under it."""
    lines = wrap(text, f, width)
    for i, words in enumerate(lines):
        if justify and i < len(lines) - 1 and len(words) > 1:
            gap = (width - sum(text_w(w, f) for w in words)) / (len(words) - 1)
            xx = x
            for w in words:
                d.text((xx, y), w, font=f, fill=fill)
                xx += text_w(w, f) + gap
        else:
            d.text((x, y), " ".join(words), font=f, fill=fill)
        y += leading
    return y


def bullets(d, x, y, width, items, f, fill, mark, leading, space):
    """A list with a solid triangle for each point."""
    for item in items:
        s = f.size
        d.polygon([(x, y + s * 0.2), (x + s * 0.55, y + s * 0.5), (x, y + s * 0.8)], fill=mark)
        y = paragraph(d, x + s * 0.9, y, width - s * 0.9, item, f, fill, leading, justify=False)
        y += space
    return y


def still(name, k):
    """A screen from docs/media at k times the BBC's own pixels."""
    im = Image.open(os.path.join(MEDIA, name + ".png")).convert("RGB")
    native = im.resize((256, 192), Image.NEAREST)
    return native.resize((256 * k, 192 * k), Image.NEAREST)


def place_still(page, d, name, k, x, y, frame=WHITE, shadow=None, border=4):
    im = still(name, k)
    w, h = im.size
    if shadow:
        d.rectangle([x + 10, y + 10, x + w + 10 + border, y + h + 10 + border], fill=shadow)
    d.rectangle([x - border, y - border, x + w + border - 1, y + h + border - 1], fill=frame)
    page.paste(im, (x, y))
    return w, h


def starburst(size, points, fill, edge, lines, faces, colour, angle):
    """The price flash: a jagged star with its words set across it, tilted."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = size / 2
    for r_out, r_in, col in ((c - 2, c * 0.8, edge), (c - 10, c * 0.8 - 8, fill)):
        pts = []
        for i in range(points * 2):
            r = r_out if i % 2 == 0 else r_in
            a = math.pi * i / points
            pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        d.polygon(pts, fill=col)
    heights = [font(face, sz).getbbox(t)[3] for t, (face, sz) in zip(lines, faces)]
    y = c - (sum(heights) + 6 * (len(lines) - 1)) / 2
    for t, (face, sz), h in zip(lines, faces, heights):
        f = font(face, sz)
        d.text((c - text_w(t, f) / 2, y), t, font=f, fill=colour)
        y += h + 6
    return layer.rotate(angle, resample=Image.BICUBIC)


def headline(text, f, top, bottom, shadow, offset, gap=0):
    """The title as the box art did it: graded and cut with scan lines, with a shadow."""
    l, t, r, b = f.getbbox(text)
    w, h = r + offset + 4, b + offset + 4
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((0, 0), text, font=f, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(Image.new("RGBA", (w, h), shadow + (255,)), (offset, offset), mask)
    grad = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(grad)
    for yy in range(h):
        u = max(0.0, min(1.0, (yy - t) / max(1, b - t)))
        col = tuple(int(top[i] + (bottom[i] - top[i]) * u) for i in range(3))
        # Thin dark lines across the lower half, as the airbrushed logos had.
        if gap and yy > t + (b - t) * 0.5 and (yy // gap) % 3 == 0:
            col = shadow
        gd.line([(0, yy), (w, yy)], fill=col + (255,))
    out.paste(grad, (0, 0), mask)
    return out, t


def logo(height, ink, red=INK_RED, blue=INK_BLUE):
    """Doppler Software's mark: a source with its waves bunched ahead and stretched behind."""
    s = 4  # drawn large and shrunk, for smooth arcs
    H = height * s
    f = font("gothic", int(H * 0.62))
    f2 = font("gothic-book", int(H * 0.2))
    word_w = text_w("DOPPLER", f)
    W = int(H * 1.5 + word_w + H * 0.05)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = H * 0.62, H / 2
    d.ellipse([cx - H * 0.09, cy - H * 0.09, cx + H * 0.09, cy + H * 0.09], fill=ink)
    for i, gap in enumerate((0.16, 0.27, 0.40)):  # blue: close together, ahead
        r = H * gap
        d.arc([cx - H * 0.12 * i * 0.3 - r, cy - r, cx - H * 0.12 * i * 0.3 + r, cy + r],
              130, 230, fill=blue, width=int(H * 0.055))
    for i, gap in enumerate((0.20, 0.36, 0.55)):  # red: spread out, behind
        r = H * gap
        off = H * 0.1 * i
        d.arc([cx + off - r, cy - r, cx + off + r, cy + r], -55, 55, fill=red, width=int(H * 0.055))
    x = H * 1.5
    d.text((x, H * 0.02), "DOPPLER", font=f, fill=ink)
    sw = spaced_w("SOFTWARE", f2, H * 0.12)
    spaced(d, x + (word_w - sw) / 2, H * 0.7, "SOFTWARE", f2, ink, H * 0.12)
    return im.resize((W // s, height), Image.LANCZOS)


def paste(page, layer, x, y):
    page.alpha_composite(layer, (int(x), int(y)))


def dashed_rect(d, box, fill, dash=14, gap=9, width=3):
    x0, y0, x1, y1 = box
    for x in range(x0, x1, dash + gap):
        d.line([(x, y0), (min(x + dash, x1), y0)], fill=fill, width=width)
        d.line([(x, y1), (min(x + dash, x1), y1)], fill=fill, width=width)
    for y in range(y0, y1, dash + gap):
        d.line([(x0, y), (x0, min(y + dash, y1))], fill=fill, width=width)
        d.line([(x1, y), (x1, min(y + dash, y1))], fill=fill, width=width)


def compat_strip(d, x, y, w, h, bg, ink, accent):
    """The bar along the foot of every advert: which machines, which media."""
    d.rectangle([x, y, x + w, y + h], fill=bg)
    items = [("BBC MODEL B", "with 16K sideways RAM"), ("MASTER 128", "no extras needed"),
             ('5¼" DISC', "40/80 track")]
    cell = w / len(items)
    big = font("narrow", int(h * 0.42))
    small = font("narrow-reg", int(h * 0.24))
    for i, (a, b) in enumerate(items):
        cx = x + cell * i + cell / 2
        if i:
            d.line([(x + cell * i, y + h * 0.18), (x + cell * i, y + h * 0.82)], fill=accent, width=3)
        centred(d, cx, y + h * 0.12, a, big, ink)
        centred(d, cx, y + h * 0.6, b, small, accent)


def finish(page, name):
    """Save in palette mode: the adverts are flat colour, so 256 inks are plenty."""
    os.makedirs(OUT, exist_ok=True)
    rgb = page.convert("RGB")
    # The BBC's eight colours go in the palette as they are, so the stills keep them exactly.
    bbc = [(r, g, b) for r in (0, 255) for g in (0, 255) for b in (0, 255)]
    rest = rgb.quantize(colors=248, method=Image.Quantize.MEDIANCUT).getpalette()[:248 * 3]
    ref = Image.new("P", (1, 1))
    ref.putpalette([v for c in bbc for v in c] + rest)
    pal = rgb.quantize(palette=ref, dither=Image.Dither.NONE)
    # Pillow's palette matching is approximate, so snap any ink a hair off a BBC colour onto it.
    flat = pal.getpalette()
    for i in range(0, len(flat), 3):
        if all(min(v, 255 - v) <= 8 for v in flat[i:i + 3]):
            flat[i:i + 3] = [0 if v < 128 else 255 for v in flat[i:i + 3]]
    pal.putpalette(flat)
    path = os.path.join(OUT, name)
    pal.save(path, optimize=True)
    print(f"{path}: {pal.size[0]}x{pal.size[1]}, {os.path.getsize(path) // 1024}K")


ADDRESS = ["DOPPLER SOFTWARE LTD", "Unit 3, Lightwell Yard", "Wharfeby", "North Yorkshire WH1 4RS"]
PHONE = "(0909) 214 2189"


def full_page():
    W, H = 1400, 1980
    page = Image.new("RGBA", (W, H), NIGHT + (255,))
    d = ImageDraw.Draw(page)
    M = 60

    # The masthead: the house mark, and a strap across the top.
    lg = logo(70, WHITE, red=(255, 70, 70), blue=(80, 140, 255))
    paste(page, lg, M, 44)
    f = font("narrow", 30)
    t = "BBC MICRO  •  MASTER 128"
    d.text((W - M - text_w(t, f), 64), t, font=f, fill=YELLOW)

    # REDSHIFT, as big as the page allows.
    hf = fit("REDSHIFT", "gothic", W - 2 * M - 120, 300)
    hl, top = headline("REDSHIFT", hf, (255, 240, 80), (230, 0, 0), (0, 40, 200), 12, gap=4)
    paste(page, hl, (W - hl.width) / 2, 136 - top)
    y = 136 + hl.height - top + 4
    tag = "ONE TROOPER.  ONE HARNESS.  TWO REALITIES."
    tf = fit(tag, "bookman-it", W - 2 * M - 60, 52)
    centred(d, W / 2, y, tag, tf, WHITE)
    y += tf.size + 26

    # The hero: one room, one moment, both phases, with the price flash beside it.
    gap = 44
    x0 = M + 6
    lf = font("gothic", 30)
    spaced(d, x0, y, "THE RED PHASE", lf, (255, 80, 80), 3)
    lab = "THE BLUE PHASE"
    spaced(d, x0 + 512 * 2 + gap - spaced_w(lab, lf, 3), y, lab, lf, (90, 160, 255), 3)
    y += 44
    place_still(page, d, "pump_red", 2, x0, y, frame=(255, 80, 80))
    place_still(page, d, "pump_blue", 2, x0 + 512 + gap, y, frame=(90, 160, 255))
    centred(d, x0 + 512 + gap / 2, y + 192 - 26, "⇄", font("symbols", 40), WHITE)
    burst = starburst(290, 16, YELLOW, RED, ["ONLY", "£9.95", "DISC"],
                      [("gothic", 38), ("gothic", 70), ("gothic", 32)], (180, 0, 0), 12)
    paste(page, burst, W - 290 - 16, y + 40)
    y += 384 + 14
    cap = "Screen shots from the BBC Micro version: the PUMP HOUSE, the same instant in each phase."
    y = paragraph(d, x0, y, 512 * 2 + gap, cap, font("body-it", 23), (200, 200, 220), 29,
                  justify=False)
    y += 22

    # The copy, in two columns, with two more screens beside it.
    cx1, cw1 = M, 420
    cx2, cw2 = M + 450, 420
    cx3 = M + 900
    yc = y
    kf = font("bookman", 34)
    d.text((cx1, yc), "Kharon-4, 2189.", font=kf, fill=YELLOW)
    yc += 48
    bf = font("body", 22)
    copy = [
        "The colony's deep mine has broken into THE PRISM, an alien engine that splits "
        "reality in two. In the RED PHASE the Company's own ore trucks and drills have "
        "turned into war machines. In the BLUE PHASE a crystal swarm grows out of the rock.",
        "Seven troopers went down. Seven stopped answering. Now it's your turn, as Trooper "
        "ASH CALDER, in the last working phase harness.",
        "Press SHIFT and the whole world recolours! Barricades turn to ghosts and crystal "
        "bridges span the acid. But every shift costs a precious phase cell...",
    ]
    for p in copy:
        yc = paragraph(d, cx1, yc, cw1, p, bf, WHITE, 28, justify=False) + 10
    left_end = yc

    yc = y
    d.text((cx2, yc), "Look at these!", font=kf, fill=CYAN)
    yc += 48
    feats = [
        "45 flip-screen rooms in FIVE sectors!",
        "Up to eight colour changes down every screen: the most colourful game ever seen on "
        "the BBC Micro!",
        "Smooth, flicker-free sprites!",
        "Drill Sergeants, Gadflies, Trundlers and the dreaded Slivers!",
        "Music that changes when you SHIFT!",
        "THE HINGE: a boss in both phases at once!",
        "Two endings. Only one is good.",
    ]
    yc = bullets(d, cx2, yc, cw2, feats, font("body-bold", 21), WHITE, YELLOW, 27, 7)
    body_end = max(left_end, yc)

    yc = y + 6
    sx = cx3 + (W - M - cx3 - 256) // 2
    for name, label in (("mother_red", "THE MOTHER LODE"), ("hinge_blue", "THE HINGE")):
        place_still(page, d, name, 1, sx, yc, frame=WHITE, border=3)
        centred(d, sx + 128, yc + 198, label, font("narrow", 22), YELLOW)
        yc += 192 + 46
    body_end = max(body_end, yc)

    # The coupon, cut along the dotted line.
    cy0 = body_end + 34
    d.text((M + 4, cy0 - 40), "✂", font=font("symbols", 36), fill=WHITE)
    ink = (20, 20, 20)
    sf = font("sans-reg", 20)
    bold = font("sans", 20)
    x = M + 24
    lw = 790
    yy = cy0 + 16
    tf = font("gothic", 32)
    yy += 48
    rows = []  # drawn once the box behind them is
    rows.append((yy, "para"))
    yy += 2 * 26 + 8
    rows.append((yy, "opts"))
    yy += 36
    rows.append((yy, "payable"))
    yy += 34
    rows.append((yy, "card"))
    yy += 42
    for lab in ("Name", "Address", ""):
        rows.append((yy, "line:" + lab))
        yy += 34
    cy1 = yy + 10
    assert cy1 < H - 112 - 24, cy1
    d.rectangle([M, cy0, W - M, cy1], fill=PAPER)
    dashed_rect(d, (M - 10, cy0 - 10, W - M + 10, cy1 + 10), WHITE)
    d.text((x, cy0 + 16), "ORDER FORM: POST TODAY!", font=tf, fill=INK_RED)
    for ry, kind in rows:
        if kind == "para":
            paragraph(d, x, ry, lw, "Please rush me ...... copies of REDSHIFT on 5¼\" disc for the BBC "
                      "Model B (16K sideways RAM) or Master 128, at £9.95 each, post and packing free.",
                      sf, ink, 26, justify=False)
        elif kind == "opts":
            for i, opt in enumerate(("40 track", "80 track")):
                bx = x + i * 150
                d.rectangle([bx, ry + 1, bx + 21, ry + 22], outline=ink, width=2)
                d.text((bx + 30, ry), opt, font=sf, fill=ink)
            d.text((x + 320, ry), "I enclose a cheque/PO for £ ............", font=sf, fill=ink)
        elif kind == "payable":
            d.text((x, ry), "Cheques/POs payable to DOPPLER SOFTWARE LTD.", font=bold, fill=ink)
        elif kind == "card":
            t = "Or debit my Access/Visa no."
            d.text((x, ry), t, font=sf, fill=ink)
            bx = x + text_w(t, sf) + 14
            for i in range(16):
                xx = bx + i * 26 + (i // 4) * 8
                d.rectangle([xx, ry - 2, xx + 22, ry + 24], outline=ink, width=2)
        else:
            lab = kind[5:]
            d.text((x, ry), lab, font=sf, fill=ink)
            end = x + lw if lab else x + lw - 260
            d.line([(x + 96, ry + 22), (end, ry + 22)], fill=ink, width=1)
            if not lab:
                d.text((end + 14, ry), "Postcode", font=sf, fill=ink)
                d.line([(end + 104, ry + 22), (x + lw, ry + 22)], fill=ink, width=1)

    rx = x + lw + 44
    d.line([(rx - 22, cy0 + 20), (rx - 22, cy1 - 20)], fill=(160, 160, 160), width=2)
    paste(page, logo(48, ink), rx, cy0 + 20)
    ry = cy0 + 86
    for i, line in enumerate(["Send to:"] + ADDRESS):
        d.text((rx, ry), line, font=font("sans" if i < 2 else "sans-reg", 20), fill=ink)
        ry += 26
    ry += 10
    d.text((rx, ry), "Credit card hotline:", font=bold, fill=ink)
    ry += 26
    d.text((rx, ry), PHONE, font=font("gothic", 28), fill=INK_RED)
    ry += 40
    small = font("narrow-reg", 18)
    for line in ("Please allow 28 days for delivery.", "Also from all good computer shops."):
        d.text((rx, ry), line, font=small, fill=(70, 70, 70))
        ry += 22
    assert ry < cy1, (ry, cy1)

    compat_strip(d, 0, H - 112, W, 112, YELLOW, BLACK, (170, 0, 0))
    finish(page, "full-page.png")


def half_page():
    W, H = 1400, 980
    page = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(page)
    M = 48
    d.rectangle([0, 0, W - 1, H - 1], outline=BLACK, width=6)

    # Two lines that say what the game is, red over blue.
    l1 = "THE RED BELONGS TO THE MACHINES."
    l2 = "THE BLUE BELONGS TO THE SWARM."
    f1 = fit(l1, "bookman", W - 2 * M, 90)
    d.text((M, 34), l1, font=f1, fill=INK_RED)
    d.text((M, 34 + f1.size + 4), l2, font=f1, fill=INK_BLUE)
    y = 34 + 2 * f1.size + 30
    d.text((M, y), "And at the heart of the Prism, one thing belongs to both.", font=font("bookman-it", 34),
           fill=BLACK)
    y += 60

    # The Hinge in the Red, with the Blue inset over its corner.
    sx, sy = M + 6, y + 4
    place_still(page, d, "hinge_red", 2, sx, sy, frame=BLACK, shadow=(190, 185, 170), border=5)
    place_still(page, d, "hinge_blue", 1, sx + 512 - 256 + 64, sy + 384 - 192 + 24, frame=BLACK, border=4)
    note = "THE HINGE in the Red and, inset, the Blue."
    d.text((sx, sy + 384 + 42), note, font=font("narrow-reg", 20), fill=(70, 70, 70))
    d.text((sx, sy + 384 + 66), "Screen shots from the BBC Micro version.", font=font("narrow-reg", 20),
           fill=(70, 70, 70))

    # The copy beside it.
    cx = sx + 512 + 120
    cw = W - M - cx
    yy = y
    d.text((cx, yy), "THE HINGE", font=font("gothic", 54), fill=BLACK)
    yy += 66
    bf = font("body", 24)
    yy = paragraph(d, cx, yy, cw,
                   "A Drill Sergeant the size of a house in the Red. A crystal flower shedding Slivers "
                   "in the Blue. One core between them, and whatever you do to one, you do to the other.",
                   bf, BLACK, 31) + 14
    yy = paragraph(d, cx, yy, cw,
                   "Crack its plate with a grenade, SHIFT, and blast the core before the crystal grows "
                   "back, on a floor that is only half there in either phase. Reach it first: "
                   "forty-four rooms of acid, steam, crushers and crystal stand in Ash Calder's way.",
                   bf, BLACK, 31) + 18
    d.text((cx, yy), "REDSHIFT", font=font("gothic", 92), fill=INK_RED)
    d.text((cx + 6, yy + 6), "REDSHIFT", font=font("gothic", 92), fill=INK_BLUE)
    d.text((cx + 3, yy + 3), "REDSHIFT", font=font("gothic", 92), fill=BLACK)
    yy += 108
    d.text((cx, yy), "for the BBC Micro & Master 128", font=font("bookman-it", 25), fill=BLACK)
    yy += 44
    d.text((cx, yy), "From all good dealers, or direct from Doppler:", font=font("sans-reg", 21), fill=BLACK)
    yy += 28
    d.text((cx, yy), "Access/Visa " + PHONE, font=font("sans", 23), fill=INK_RED)
    end_copy = yy + 30

    burst = starburst(230, 14, YELLOW, BLACK, ["£9.95", "DISC"],
                      [("gothic", 58), ("gothic", 30)], BLACK, -10)
    paste(page, burst, W - 230 - 20, H - 106 - 230 - 6)
    assert end_copy < H - 106 - 20, end_copy
    lg = logo(56, BLACK)
    paste(page, lg, sx, H - 106 - 90)

    compat_strip(d, 6, H - 106, W - 12, 100, BLACK, WHITE, YELLOW)
    finish(page, "half-page.png")


def quarter_page():
    W, H = 680, 980
    page = Image.new("RGBA", (W, H), (0, 0, 120, 255))
    d = ImageDraw.Draw(page)
    d.rectangle([0, 0, W - 1, H - 1], outline=YELLOW, width=8)
    M = 34

    paste(page, logo(40, WHITE, red=(255, 80, 80), blue=CYAN), M, 26)
    hf = fit("REDSHIFT", "gothic", W - 2 * M - 10, 200)
    hl, top = headline("REDSHIFT", hf, (255, 255, 255), (255, 210, 0), (200, 0, 0), 6)
    paste(page, hl, (W - hl.width) / 2, 86 - top)
    y = 86 + hl.height - top + 6
    centred(d, W / 2, y, "WHICH SIDE ARE YOU ON?", font("bookman-it", 34), CYAN)
    y += 52

    x = (W - 512) // 2
    place_still(page, d, "outfall_red", 2, x, y, frame=WHITE, border=4)
    burst = starburst(190, 12, YELLOW, RED, ["£9.95", "DISC"],
                      [("gothic", 48), ("gothic", 24)], (180, 0, 0), 8)
    paste(page, burst, W - 190 - 6, y + 384 - 170)
    y += 384 + 10
    centred(d, W / 2, y, "OUTFALL, Sector 3. In the Blue it's bone dry.", font("body-it", 21), WHITE)
    y += 36

    f = font("gothic", 32)
    for line, col in (("45 SCREENS!  5 SECTORS!", YELLOW), ("2 PHASES!  1 TROOPER!", WHITE)):
        centred(d, W / 2, y, line, f, col)
        y += 40
    y += 6
    sf = font("sans-reg", 19)
    y = paragraph(d, M + 4, y, W - 2 * M - 8,
                  "By post: send £9.95 (40 or 80 track, please say) to Doppler Software Ltd, "
                  "Unit 3, Lightwell Yard, Wharfeby, North Yorkshire WH1 4RS. Cheques/POs payable to "
                  "Doppler Software Ltd. Post free. Access/Visa: " + PHONE + ".",
                  sf, WHITE, 24, justify=False)
    assert y < H - 96, y

    compat_strip(d, 8, H - 88, W - 16, 80, YELLOW, BLACK, (170, 0, 0))
    finish(page, "quarter-page.png")


if __name__ == "__main__":
    full_page()
    half_page()
    quarter_page()
