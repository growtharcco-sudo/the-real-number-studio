"""Dark 'Penny Question' style: big bold numbers on deep navy, green and gold, constant motion.

Same interface as render.py (render, cover). A spec picks it with "style": "dark".
Element types: text, count, pill, box, meter, hbar, strike, grid, follow.
Colours: white, green, gold, grey, dim, red.
"""
import math, os, re, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "fonts")
COL = {"white": (244, 246, 250), "green": (34, 211, 148), "gold": (255, 196, 56), "grey": (138, 148, 166),
       "dim": (70, 80, 98), "red": (255, 92, 92), "ink": (10, 14, 24)}
BG0, BG1 = (5, 8, 16), (13, 20, 36)
CX = 525                       # visual centre, a little left of middle (clear of the Reels side buttons)
CAP_Y = 1500
DY = 110                       # content block sits a little lower, closer to the captions
_fc = {}


def font(weight, size):
    k = (weight, size)
    if k not in _fc:
        name = {"bold": "Poppins-Bold", "semi": "Poppins-SemiBold", "extra": "Poppins-ExtraBold",
                "medium": "Poppins-Medium"}[weight]
        _fc[k] = ImageFont.truetype(os.path.join(FD, name + ".ttf"), size)
    return _fc[k]


def ease(p): p = max(0., min(1., p)); return 1 - (1 - p) ** 3
def back(p): p = max(0., min(1., p)); c = 1.6; return 1 + (c + 1) * (p - 1) ** 3 + c * (p - 1) ** 2


def make_bg():
    import numpy as np
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot((xx - W / 2) / W, (yy - H * 0.42) / H); k = np.clip(1 - r * 1.9, 0, 1)[..., None]
    arr = np.array(BG0, float) + (np.array(BG1, float) - np.array(BG0, float)) * k
    glow = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow)
    g.ellipse([W * 0.15, H * 0.2, W * 0.85, H * 0.62], fill=(6, 40, 34))
    arr += np.asarray(glow.filter(ImageFilter.GaussianBlur(160)), float) * 0.5
    im = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))
    d = ImageDraw.Draw(im)
    for y in range(60, H, 54):
        for x in range(27, W, 54): d.point((x, y), fill=(28, 36, 52))
    return im.convert("RGBA")


def timg(txt, f, color, track=0):
    if track:
        ws = [f.getlength(ch) + track for ch in txt]; w = int(sum(ws)) + 8
    else:
        w = int(f.getlength(txt)) + 8
    asc, desc = f.getmetrics(); h = asc + desc + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if track:
        x = 4
        for ch, cw in zip(txt, ws): d.text((x, 4), ch, font=f, fill=color + (255,)); x += cw
    else:
        d.text((4, 4), txt, font=f, fill=color + (255,))
    return im


def fade(im, a):
    if a >= 1: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a))); return im


def rrect(d, box, r, fill=None, outline=None, width=2):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


class El:
    def __init__(s, t0, t1, dur=0.35): s.t0, s.t1, s.dur = t0, t1, dur
    def p(s, t): return 1.0 if s.t0 < 0 else (t - s.t0) / s.dur
    def a(s, t): return 1.0 if t < s.t1 - 0.2 else max(0, (s.t1 - t) / 0.2)
    box = (0, 0, 0, 0)


class Text(El):
    def __init__(s, txt, f, col, y, t0, t1, x="c", mode="rise", track=0, glow=False):
        super().__init__(t0, t1, 0.4 if mode == "pop" else 0.35)
        s.img = timg(txt, f, col, track); s.mode = mode
        if glow:
            g = s.img.filter(ImageFilter.GaussianBlur(14)); base = Image.new("RGBA", s.img.size, (0, 0, 0, 0))
            base.alpha_composite(fade(g, 0.8)); base.alpha_composite(s.img); s.img = base
        s.x = int(CX - s.img.width / 2) if x == "c" else int(x); s.y = y
        s.box = (s.x + 4, y + 4, s.x + s.img.width - 4, y + s.img.height - 4)

    def draw(s, fr, d, t):
        p = s.p(t); a = s.a(t) * min(1, max(0, p) * 2.5)
        if a <= 0: return
        if s.mode == "pop" and p < 1:
            k = 0.6 + 0.4 * back(p); im = s.img.resize((max(1, int(s.img.width * k)), max(1, int(s.img.height * k))))
            fr.alpha_composite(fade(im, a), (int(s.x + (s.img.width - im.width) / 2), int(s.y + (s.img.height - im.height) / 2)))
        else:
            dy = 0 if s.mode == "fade" else int(26 * (1 - ease(p)))
            fr.alpha_composite(fade(s.img, a), (s.x, s.y + dy))


class Count(El):
    """Counts up (exponential by default, so it feels like compounding) and lands on the exact value."""
    def __init__(s, pre, v0, v1, suf, dec, f, col, y, t0, t1, dur, curve, col_after=None, after=None):
        super().__init__(t0, t1, dur)
        s.pre, s.v0, s.v1, s.suf, s.dec, s.f, s.col, s.y, s.curve = pre, v0, v1, suf, dec, f, col, y, curve
        s.col_after, s.after = col_after, after
        txt = s.fmt(v1); w = f.getlength(txt); s.box = (CX - w / 2, y, CX + w / 2, y + f.size)

    def fmt(s, v): return f"{s.pre}{v:,.{s.dec}f}{s.suf}"

    def val(s, t):
        p = max(0., min(1., s.p(t)))
        if s.curve == "exp" and s.v0 > 0:
            q = p ** 1.15; return s.v0 * (s.v1 / s.v0) ** q
        return s.v0 + (s.v1 - s.v0) * ease(p)

    def draw(s, fr, d, t):
        a = s.a(t)
        if a <= 0: return
        v = s.val(t); col = s.col
        if s.col_after and s.after is not None and v >= s.after: col = s.col_after
        im = timg(s.fmt(v), s.f, col)
        fr.alpha_composite(fade(im, a), (int(CX - im.width / 2), s.y))


class Pill(El):
    def __init__(s, txt, col, y, t0, t1, filled=True, size=34):
        super().__init__(t0, t1, 0.3)
        f = font("bold", size); w = int(f.getlength(txt)) + 56; h = size + 30
        s.img = Image.new("RGBA", (w + 4, h + 4), (0, 0, 0, 0)); d = ImageDraw.Draw(s.img)
        if filled:
            rrect(d, (2, 2, w, h), h // 2, fill=col + (255,)); d.text((30, 13), txt, font=f, fill=COL["ink"] + (255,))
        else:
            rrect(d, (2, 2, w, h), h // 2, outline=col + (255,), width=3); d.text((30, 13), txt, font=f, fill=col + (255,))
        s.x = int(CX - s.img.width / 2); s.y = y; s.box = (s.x, y, s.x + w, y + h)

    def draw(s, fr, d, t):
        p = s.p(t); a = s.a(t) * min(1, max(0, p) * 2)
        if a > 0:
            k = 0.7 + 0.3 * back(min(1, max(0, p)))
            im = s.img.resize((int(s.img.width * k), int(s.img.height * k)))
            fr.alpha_composite(fade(im, a), (int(CX - im.width / 2), int(s.y + (s.img.height - im.height) / 2)))


class Box(El):
    def __init__(s, y, h, w, t0, t1, col=None):
        super().__init__(t0, t1, 0.3); s.y, s.h, s.w = y, h, w; s.col = col

    def draw(s, fr, d, t):
        a = s.a(t) * min(1, max(0, s.p(t)) * 2)
        if a <= 0: return
        lay = Image.new("RGBA", fr.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        rrect(dl, (CX - s.w // 2, s.y, CX + s.w // 2, s.y + s.h), 28, fill=(20, 28, 46, 235),
              outline=(s.col or (40, 52, 76)) + (255,), width=3)
        fr.alpha_composite(fade(lay, a))


class Meter(El):
    def __init__(s, y, w, f0, f1, col, t0, t1, dur):
        super().__init__(t0, t1, dur); s.y, s.w, s.f0, s.f1, s.col = y, w, f0, f1, col

    def draw(s, fr, d, t):
        a = s.a(t)
        if a <= 0: return
        f = s.f0 + (s.f1 - s.f0) * ease(s.p(t)); x0 = CX - s.w // 2
        rrect(d, (x0, s.y, x0 + s.w, s.y + 18), 9, fill=(34, 44, 64, int(255 * a)))
        if f > 0: rrect(d, (x0, s.y, x0 + max(18, int(s.w * min(1, f))), s.y + 18), 9, fill=s.col + (int(255 * a),))


class HBar(El):
    """Comparison bar: label on top, bar grows to frac of full width, value text at the end."""
    def __init__(s, label, value, frac, col, y, t0, t1, dur=1.2):
        super().__init__(t0, t1, dur); s.label, s.value, s.frac, s.col, s.y = label, value, frac, col, y
        s.lf, s.vf = font("semi", 36), font("extra", 54)

    def draw(s, fr, d, t):
        a = s.a(t)
        if a <= 0: return
        p = ease(s.p(t)); x0 = CX - 400; full = 800
        d.text((x0, s.y), s.label, font=s.lf, fill=COL["grey"] + (int(255 * a),))
        w = max(14, int(full * s.frac * p))
        rrect(d, (x0, s.y + 56, x0 + w, s.y + 112), 14, fill=s.col + (int(255 * a),))
        vt = s.value if p > 0.98 else ""
        if vt:
            vw = s.vf.getlength(vt); vx = x0 + w + 20 if x0 + w + 20 + vw < CX + 470 else x0 + w - vw - 20
            vc = COL["ink"] if vx < x0 + w else s.col
            d.text((vx, s.y + 46), vt, font=s.vf, fill=vc + (int(255 * a),))


class Strike(El):
    def __init__(s, box, col, t0, t1): super().__init__(t0, t1, 0.35); s.b, s.col = box, col

    def draw(s, fr, d, t):
        a = s.a(t)
        if a <= 0: return
        x0, y0, x1, y1 = s.b; ym = (y0 + y1) / 2 + 4; p = ease(s.p(t))
        d.line([(x0 - 10, ym), (x0 - 10 + (x1 - x0 + 20) * p, ym)], fill=s.col + (int(255 * a),), width=7)


class Grid(El):
    """Calendar-style grid of numbered cells that light up one by one (cells n0..n1 over dur)."""
    def __init__(s, n, cols, y, lit0, lit1, col, t0, t1, dur, gold_from=None):
        super().__init__(t0, t1, dur); s.n, s.cols, s.y, s.l0, s.l1, s.col, s.gold = n, cols, y, lit0, lit1, col, gold_from
        s.f = font("semi", 30)

    def draw(s, fr, d, t):
        a = s.a(t)
        if a <= 0: return
        lit = s.l0 + (s.l1 - s.l0) * max(0, min(1, s.p(t))); cw = 104; gap = 14
        x0 = CX - (s.cols * cw + (s.cols - 1) * gap) // 2
        for i in range(s.n):
            r, c = divmod(i, s.cols); x = x0 + c * (cw + gap); y = s.y + r * (cw * 0.62 + gap)
            on = i + 1 <= lit; col = (COL["gold"] if s.gold and i + 1 >= s.gold else s.col) if on else (30, 40, 58)
            rrect(d, (x, y, x + cw, y + cw * 0.62), 14, fill=col + (int(255 * a),))
            tc = COL["ink"] if on else COL["grey"]; txt = str(i + 1)
            d.text((x + cw / 2 - s.f.getlength(txt) / 2, y + 12), txt, font=s.f, fill=tc + (int(255 * a),))


def build(spec, times, total):
    def at(v, delay=0.0):
        if v == -1 or v is None: return -1.0
        if isinstance(v, list):
            s, e = times[v[0]]; return s + (e - s) * v[1] + delay
        return times[v][0] + delay

    els, ids = [], {}
    for sc in spec["scenes"]:
        u = sc.get("until", "end")
        t1 = total + 5 if u == "end" else times[u][0] - 0.05
        for e in sc["els"]:
            e = dict(e); e["y"] = e["y"] + DY if "y" in e else None
            ty = e["type"]; t0 = at(e.get("at"), e.get("delay", 0.0)); c = COL[e.get("color", "white")]
            if ty == "text":
                ob = Text(e["text"], font(e.get("weight", "bold"), e.get("size", 56)), c, e["y"], t0, t1,
                          e.get("x", "c"), e.get("mode", "rise"), e.get("track", 0), e.get("glow", False))
            elif ty == "count":
                ob = Count(e.get("prefix", ""), e.get("from", 0), e["value"], e.get("suffix", ""), e.get("decimals", 0),
                           font(e.get("weight", "extra"), e.get("size", 150)), c, e["y"], t0, t1, e.get("dur", 2.0),
                           e.get("curve", "lin"), COL.get(e.get("color_after", ""), None), e.get("after"))
            elif ty == "pill":
                ob = Pill(e["text"], c, e["y"], t0, t1, e.get("filled", True), e.get("size", 34))
            elif ty == "box":
                ob = Box(e["y"], e["h"], e.get("w", 820), t0, t1, COL.get(e.get("color", ""), None))
            elif ty == "meter":
                ob = Meter(e["y"], e.get("w", 760), e.get("from", 0), e["to"], c, t0, t1, e.get("dur", 1.2))
            elif ty == "hbar":
                ob = HBar(e["label"], e["value"], e["frac"], c, e["y"], t0, t1, e.get("dur", 1.2))
            elif ty == "strike":
                ob = Strike(ids[e["of"]].box, c, t0, t1)
            elif ty == "grid":
                ob = Grid(e["n"], e.get("cols", 6), e["y"], e.get("lit_from", 0), e["lit_to"], c, t0, t1,
                          e.get("dur", 1.0), e.get("gold_from"))
            elif ty == "follow":
                ob = Pill("+ FOLLOW", COL["white"], e["y"], t0, t1, True, 38)
            else:
                raise ValueError("unknown element type " + ty)
            if "id" in e: ids[e["id"]] = ob
            els.append(ob)
    return els


# ---------------- captions: bold uppercase, spoken word lights up ----------------
CF = 66
SPOKEN_EXTRA = {"%": 3, "$": 2}


def caption_chunks(spec, times):
    chunks = []
    for ph, (s, e) in zip(spec["phrases"], times):
        words = ph.get("cap", ph["say"]).split()
        wts = [len(re.sub(r"[^\w]", "", w)) + 1.6 + sum(v for k, v in SPOKEN_EXTRA.items() if k in w)
               + (2 if re.search(r"\d", w) else 0) for w in words]
        tot = sum(wts); acc = s; timed = []
        for w, k in zip(words, wts):
            dd = (e - s) * k / tot; timed.append((w, acc, acc + dd)); acc += dd
        cur = []
        for it in timed:
            cur.append(it)
            txt = " ".join(x[0] for x in cur)
            if len(cur) >= 4 or len(txt) >= 20 or it[0][-1] in ",.?:":
                chunks.append(cur); cur = []
        if cur: chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        st, en = c[0][1], c[-1][2]
        nxt = chunks[i + 1][0][1] if i + 1 < len(chunks) else en + 1.5
        out.append((st, min(nxt, en + 0.45), c))
    return out


def draw_caption(fr, t, chunks, keys):
    f = font("extra", CF); sp = f.getlength(" ")
    for st, en, words in chunks:
        if not (st <= t < en): continue
        a = min(1, (t - st) / 0.1); k = 0.92 + 0.08 * ease((t - st) / 0.15)
        lines, cur = [], []
        for w in words:
            if cur and f.getlength(" ".join(x[0].upper() for x in cur + [w])) > 860: lines.append(cur); cur = [w]
            else: cur.append(w)
        lines.append(cur)
        lh = 84; y0 = CAP_Y - (len(lines) - 1) * lh // 2
        lay = Image.new("RGBA", fr.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        for li, ln in enumerate(lines):
            ws = [x[0].upper() for x in ln]; widths = [f.getlength(w) for w in ws]
            x = CX - (sum(widths) + sp * (len(ln) - 1)) / 2; y = y0 + li * lh
            for (w0, ws0, we0), w, wd in zip(ln, ws, widths):
                key = re.sub(r"[^\w$%.,]", "", w0)
                col = COL["gold"] if re.search(r"\d", w0) else COL["green"] if key.lower().strip(".,") in keys else COL["white"]
                if ws0 <= t < max(we0, ws0 + 0.18) and col == COL["white"]: col = COL["green"]
                dl.text((x + 3, y + 5), w, font=f, fill=(0, 0, 0, 160))
                dl.text((x, y), w, font=f, fill=col + (255,)); x += wd + sp
        fr.alpha_composite(fade(lay, a))


def render(spec, times, total, wav, out_mp4, stills=None):
    bg = make_bg()
    els = build(spec, times, total)
    chunks = caption_chunks(spec, times)
    keys = set(w.lower() for w in spec.get("caption_keywords", []))
    label = timg(spec.get("series", "The Real Number").upper(), font("medium", 30), COL["grey"], track=3)
    handle = timg("@the_real.number", font("medium", 26), COL["dim"])
    dur = round(total + 0.4, 2)

    def frame(t):
        fr = bg.copy(); d = ImageDraw.Draw(fr)
        d.rectangle([0, 0, int(W * min(1, t / dur)), 7], fill=COL["green"] + (255,))
        fr.alpha_composite(label, (int(CX - label.width / 2), 168))
        fr.alpha_composite(handle, (int(CX - handle.width / 2), 1790))
        for e in sorted(els, key=lambda e: not isinstance(e, Box)):
            if e.t0 <= t + 0.01 and t < e.t1: e.draw(fr, d, t)
        draw_caption(fr, t, chunks, keys)
        return fr.convert("RGB")

    if stills:
        for t in stills: frame(t).save(f"{out_mp4}.still_{t:05.1f}.png")
        return
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                          "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                          "-af", "apad", "-t", str(dur), "-movflags", "+faststart", out_mp4], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode: raise RuntimeError("ffmpeg failed")


def cover(spec, out_png):
    """Cover: series label, a short question, the big number in gold, a one-line sub."""
    c = spec["cover"]; im = make_bg()
    def put(txt, f, col, y, track=0, glow=False):
        t = timg(txt, f, col, track)
        if glow:
            g = t.filter(ImageFilter.GaussianBlur(18)); im.alpha_composite(fade(g, 0.9), (int(CX - t.width / 2), y))
        im.alpha_composite(t, (int(CX - t.width / 2), y)); return t.height
    put(spec.get("series", "The Real Number").upper(), font("medium", 34), COL["grey"], 330, track=3)
    y = 470
    for line in c["kicker"].split("\n"): y += put(line.upper(), font("extra", 70), COL["white"], y) + 4
    y += 30
    y += put(c["big"], font("extra", c.get("big_size", 170)), COL[c.get("big_color", "gold")], y, glow=True) + 20
    for line in c["sub"].split("\n"): y += put(line.upper(), font("bold", 52), COL["green"], y) + 4
    if c.get("date"): put(c["date"], font("medium", 36), COL["grey"], y + 30)
    im.convert("RGB").save(out_png)
