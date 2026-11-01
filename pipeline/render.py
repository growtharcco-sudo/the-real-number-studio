"""The Real Number notebook style, as a reusable engine.

A reel is described by a spec (see specs/*.json). Times are given in phrases, not seconds:
  "at": 3            -> when phrase 3 starts
  "at": [3, 0.5]     -> halfway through phrase 3
  "at": -1           -> visible from the first frame (the hook)
  "delay": 0.3       -> extra seconds after that point
A scene ends when phrase "until" starts (or at the end of the video when "until" is "end").
"""
import math, os, random, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "fonts")
COL = {"ink": (24, 28, 46), "blue": (35, 75, 215), "red": (214, 58, 42), "green": (22, 122, 78), "grey": (92, 88, 82)}
FILL = {"red": (246, 205, 196), "green": (200, 232, 212), "blue": (205, 216, 246), "ink": (220, 220, 225), "grey": (225, 222, 215)}
HL = (255, 219, 75)
CX = 495                                  # visual centre used by the channel (clear of the IG side buttons)
_fc = {}


def font(kind, size):
    name = {"head": "space-grotesk-700", "sans": "space-grotesk-700", "hand": "caveat-700"}[kind]
    key = (name, size)
    if key not in _fc: _fc[key] = ImageFont.truetype(os.path.join(FD, name + ".ttf"), size)
    return _fc[key]


def ease(p): p = max(0., min(1., p)); return 1 - (1 - p) ** 3


def make_paper():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - 540) / 620) ** 2 + ((yy - 900) / 1050) ** 2)
    k = np.clip(r, 0, 1.25) ** 1.6
    c0, c1 = np.array([247, 242, 235]), np.array([221, 212, 195])
    a = c0 + (c1 - c0) * np.clip(k, 0, 1)[..., None]
    g = np.zeros((H, W), bool)
    for x in range(52, W, 54): g[:, x:x + 2] = True
    for y in range(20, H, 54): g[y:y + 2, :] = True
    a[g] = a[g] * 0.94 + np.array([200, 196, 215]) * 0.06 - 4
    a[:, 62:64] = np.array([218, 160, 145])
    a += np.random.default_rng(2).normal(0, 1.2, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def timg(txt, f, color, rot=0, pad=14):
    l, t, r, b = f.getbbox(txt)
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=f, fill=color + (255,))
    return im.rotate(rot, resample=Image.BICUBIC, expand=True) if rot else im


def fade(im, a):
    if a >= 1: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a))); return im


def hl_shape(d, x0, y0, x1, y1, a=1.0, skew=8):
    d.polygon([(x0 + skew, y0), (x1 + skew * 0.4, y0 + 2), (x1 - skew * 0.3, y1), (x0 - skew * 0.6, y1 - 1)],
              fill=HL + (int(235 * a),), outline=(214, 180, 60, int(200 * a)))


# ---------------- elements ----------------
class El:
    def __init__(s, t0, t1, dur): s.t0, s.t1, s.dur = t0, t1, dur
    def p(s, t): return 0. if t < s.t0 else min(1., (t - s.t0) / max(s.dur, 1e-3))
    def a(s, t): return max(0., min(1., (s.t1 - t) / 0.2))


class Text(El):
    def __init__(s, txt, f, color, x, y, t0, t1, anchor="c", rot=0, mode="write"):
        s.txt, s.f = txt, f
        s.img = timg(txt, f, color, rot)
        s.x = (CX if x == "c" else x) - s.img.width // 2 if anchor == "c" else x
        s.y, s.mode = y, mode
        super().__init__(t0, t1, 0.3 if mode != "write" else min(0.8, 0.15 + 0.03 * len(txt)))
    @property
    def box(s): return (s.x + 14, s.y + 14, s.x + s.img.width - 14, s.y + s.img.height - 14)
    def part_box(s, part):
        i = s.txt.find(part)
        if i < 0: return s.box
        x0 = s.box[0] + s.f.getlength(s.txt[:i])
        return (x0, s.box[1], x0 + s.f.getlength(part), s.box[3])
    def draw(s, fr, d, t):
        p, a = s.p(t), s.a(t)
        if p <= 0 or a <= 0: return
        if s.mode == "write":
            im = s.img.crop((0, 0, max(1, int(s.img.width * ease(p))), s.img.height)); y = s.y
        else:
            im = s.img; y = s.y + int(16 * (1 - ease(p))); a *= ease(p)
        fr.alpha_composite(fade(im, a), (int(s.x), int(y)))


class Hi(El):
    def __init__(s, box, t0, t1): super().__init__(t0, t1, 0.3); s.box = box
    def draw(s, fr, d, t):
        p, a = ease(s.p(t)), s.a(t)
        if p <= 0 or a <= 0: return
        x0, y0, x1, y1 = s.box
        hl_shape(d, x0 - 12, y0 - 4, x0 - 12 + (x1 - x0 + 24) * p, y1 + 6, a)


class Ring(El):
    def __init__(s, box, color, t0, t1, padx=22, pady=16, w=5):
        super().__init__(t0, t1, 0.45)
        x0, y0, x1, y1 = box
        cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + padx, (y1 - y0) / 2 + pady
        s.pts = [(cx + rx * (1 + .02 * math.sin(i / 6)) * math.cos(-2.3 + 6.9 * i / 100),
                  cy + ry * (1 + .02 * math.sin(i / 6)) * math.sin(-2.3 + 6.9 * i / 100)) for i in range(101)]
        s.c, s.w = color, w
    def draw(s, fr, d, t):
        p, a = ease(s.p(t)), s.a(t)
        if p > 0 and a > 0: d.line(s.pts[:max(2, int(101 * p))], fill=s.c + (int(255 * a),), width=s.w, joint="curve")


class Ln(El):
    def __init__(s, p0, p1, color, t0, t1, w=4): super().__init__(t0, t1, 0.3); s.p0, s.p1, s.c, s.w = p0, p1, color, w
    def draw(s, fr, d, t):
        p, a = ease(s.p(t)), s.a(t)
        if p <= 0 or a <= 0: return
        (x0, y0), (x1, y1) = s.p0, s.p1
        d.line([(x0, y0), (x0 + (x1 - x0) * p, y0 + (y1 - y0) * p)], fill=s.c + (int(255 * a),), width=s.w)


class Bar(El):
    def __init__(s, x, y, w, h, color, fill, t0, t1):
        super().__init__(t0, t1, 0.6); s.x, s.y, s.w, s.h, s.c, s.f = x, y, w, h, color, fill
    def draw(s, fr, d, t):
        p, a = ease(s.p(t)), s.a(t)
        if p <= 0 or a <= 0: return
        x1 = s.x + s.w * p
        d.rectangle([s.x, s.y, x1, s.y + s.h], fill=s.f + (int(200 * a),))
        d.line([(s.x, s.y + 1), (x1, s.y - 1), (x1 + 1, s.y + s.h), (s.x, s.y + s.h + 1), (s.x, s.y + 1)],
               fill=s.c + (int(255 * a),), width=4)


class Count(El):
    def __init__(s, prefix, value, suffix, decimals, f, color, y, t0, t1, dur=1.3):
        super().__init__(t0, t1, dur)
        s.fmt = lambda v: f"{prefix}{v:,.{decimals}f}{suffix}"
        s.v, s.f, s.c, s.y = value, f, color, y
        s.img = timg(s.fmt(value), f, color); s.x = CX - s.img.width // 2
    @property
    def box(s): return (s.x + 14, s.y + 14, s.x + s.img.width - 14, s.y + s.img.height - 14)
    def draw(s, fr, d, t):
        if t < s.t0 or s.a(t) <= 0: return
        im = timg(s.fmt(s.v * ease(s.p(t))), s.f, s.c)
        fr.alpha_composite(fade(im, s.a(t)), (CX - s.img.width // 2, s.y))


class Card(El):
    def __init__(s, label, lines, x, y, w, t0, t1, rot=-1.2):
        super().__init__(t0, t1, 0.3)
        fl, fb = font("hand", 34), font("sans", 32)
        h = 70 + 44 * len(lines)
        im = Image.new("RGBA", (w, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rectangle([4, 14, w - 4, h + 14], fill=(253, 251, 245, 255), outline=(150, 145, 135, 255), width=2)
        d.rectangle([w // 2 - 80, 2, w // 2 + 80, 30], fill=(222, 205, 160, 230))
        d.text((26, 30), label, font=fl, fill=COL["red"] + (255,))
        for i, ln in enumerate(lines): d.text((26, 70 + 44 * i), ln, font=fb, fill=COL["ink"] + (255,))
        s.img = im.rotate(rot, resample=Image.BICUBIC, expand=True); s.x, s.y = x, y
    def draw(s, fr, d, t):
        p = ease(s.p(t)); a = s.a(t) * p
        if a > 0: fr.alpha_composite(fade(s.img, a), (s.x, int(s.y + 24 * (1 - p))))


# ---------------- spec -> elements ----------------
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
            ty = e["type"]; t0 = at(e.get("at"), e.get("delay", 0.0)); c = COL[e.get("color", "ink")]
            if ty == "text":
                ob = Text(e["text"], font(e.get("font", "sans"), e.get("size", 48)), c, e.get("x", "c"), e["y"], t0, t1,
                          anchor="l" if e.get("x", "c") != "c" else "c", rot=e.get("rot", 0), mode=e.get("mode", "write"))
            elif ty == "count":
                ob = Count(e.get("prefix", ""), e["value"], e.get("suffix", ""), e.get("decimals", 0),
                           font("head", e.get("size", 130)), c, e["y"], t0, t1)
            elif ty in ("highlight", "ring"):
                tgt = ids[e["of"]]
                box = tgt.part_box(e["part"]) if e.get("part") and isinstance(tgt, Text) else tgt.box
                ob = Hi(box, t0, t1) if ty == "highlight" else Ring(box, c, t0, t1, e.get("padx", 22), e.get("pady", 16))
            elif ty == "underline":
                tgt = ids[e["of"]]; b = tgt.box
                ob = Ln((b[0], b[3] + 12), (b[2], b[3] + 8), c, t0, t1)
            elif ty == "line":
                ob = Ln(tuple(e["from"]), tuple(e["to"]), c, t0, t1, e.get("width", 4))
            elif ty == "bar":
                ob = Bar(e["x"], e["y"], e["w"], e.get("h", 34), c, FILL[e.get("color", "red")], t0, t1)
            elif ty == "card":
                ob = Card(e.get("label", "note:"), e["lines"], e.get("x", 150), e["y"], e.get("w", 780), t0, t1)
            else:
                raise ValueError("unknown element type " + ty)
            if "id" in e: ids[e["id"]] = ob
            els.append(ob)
    return els


# ---------------- word-by-word captions ----------------
CF_SIZE = 64
SPOKEN_EXTRA = {"%": 3, "$": 2}


def caption_chunks(spec, times):
    cf = font("sans", CF_SIZE)
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
            if len(cur) >= 4 or len(txt) >= 22 or (it[0][-1] in ",.?:" and not re.fullmatch(r"([A-Z]\.)+", it[0])):
                chunks.append(cur); cur = []
        if cur: chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        st, en = c[0][1], c[-1][2]
        nxt = chunks[i + 1][0][1] if i + 1 < len(chunks) else en + 1.5
        out.append((st, min(nxt, en + 0.45), c))
    return out, cf


def draw_caption(fr, d, t, chunks, cf):
    sp = cf.getlength(" ")
    for st, en, words in chunks:
        if not (st <= t < en): continue
        a = min(1, (t - st) / 0.12)
        lines, cur = [], []
        for w in words:
            if cur and cf.getlength(" ".join(x[0] for x in cur + [w])) > 760: lines.append(cur); cur = [w]
            else: cur.append(w)
        lines.append(cur)
        lh = 78; y0 = 1150 - (len(lines) - 1) * lh // 2
        lay = Image.new("RGBA", fr.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        for li, ln in enumerate(lines):
            widths = [cf.getlength(w[0]) for w in ln]
            x = CX - (sum(widths) + sp * (len(ln) - 1)) / 2; y = y0 + li * lh
            for (w, ws, we), wd in zip(ln, widths):
                if ws <= t < max(we, ws + 0.18): hl_shape(d, x - 8, y + 6, x + wd + 8, y + 70, a, skew=7)
                dl.text((x, y), w, font=cf, fill=COL["ink"] + (255,)); x += wd + sp
        fr.alpha_composite(fade(lay, a))


# ---------------- render ----------------
def render(spec, times, total, wav, out_mp4, stills=None):
    paper = make_paper()
    els = build(spec, times, total)
    chunks, cf = caption_chunks(spec, times)
    tag = timg(spec.get("series", "Money News"), font("hand", 54), COL["blue"])
    dur = round(total + 0.4, 2)

    def frame(t):
        fr = paper.copy(); d = ImageDraw.Draw(fr)
        fr.alpha_composite(tag, (88, 248))
        d.line([(100, 330), (100 + 520 * min(1, t / dur), 328)], fill=COL["blue"] + (255,), width=4)
        for e in sorted(els, key=lambda e: not isinstance(e, Hi)):
            if e.t0 <= t + 0.01 and t < e.t1: e.draw(fr, d, t)
        draw_caption(fr, d, t, chunks, cf)
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
    c = spec["cover"]; im = make_paper(); d = ImageDraw.Draw(im)
    def put(txt, f, col, y, rot=0):
        t = timg(txt, f, col, rot); im.alpha_composite(t, ((W - t.width) // 2 - 45, y))
    put(c["kicker"], font("hand", 84), COL["blue"], 400, -2)
    big = timg(c["big"], font("head", c.get("big_size", 280)), COL[c.get("big_color", "red")])
    x = (W - big.width) // 2 - 45; top = 515
    hy0, hy1 = top + int(big.height * 0.2), top + int(big.height * 0.83)
    d.polygon([(x + 10, hy0), (x + big.width + 40, hy0), (x + big.width + 5, hy1), (x - 25, hy1)],
              fill=HL + (255,), outline=(200, 170, 60, 255))
    im.alpha_composite(big, (x, top))
    y = top + big.height + 20
    put(c["sub"], font("sans", 58), COL["ink"], y)
    put(c["date"], font("hand", 64), COL["grey"], y + 100)
    im.convert("RGB").save(out_png)
