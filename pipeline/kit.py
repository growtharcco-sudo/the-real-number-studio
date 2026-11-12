"""Reel kit: turn a short brief into a full dark-style spec, using ready-made, pre-tested scene blocks.

Why: writing a 150-line spec and eyeballing 18 stills per Reel is what costs Claude usage. With the kit,
a Reel is a ~30-line brief; the layouts are fixed and already checked, so only 4 stills need a look.

Brief format (briefs/<id>.json):
{
  "id": "048_slug", "series": "The Penny Question", "speed": 1.08,
  "keywords": ["guess", "years"],                      # words that light up green in captions
  "beats": [                                            # one beat = one spoken phrase
    {"say": "...", "cap": "...", "pause": 0.3,          # cap/pause optional
     "show": {"kind": "question", ...}},                # optional: starts a new scene at this beat
    ...
  ],
  "cover": {...}, "sources": [...], "post": {...}       # same as a normal spec
}

Dark-style scene kinds (default, "style": "dark") and their fields. For the notebook look see nb_block below.
Scene kinds and their fields ("@n" = appears at beat n of THIS scene, counted from 0; default 0):
  question  top, big, sub, options=[a, b] (pills; b shows at @1 if given), or_word
  guess     line ("LOCK IN YOUR GUESS"), big ("$?"), note
  counter   title, subtitle, rate, start, end, prefix, suffix, decimals, color (green|gold|red),
            payoff_color, payoff_after, years=[from, to], badge, at (beat in scene when counting starts),
            dur (seconds)
  bars      a={label,value,frac,color}, b={...}, big, note
  countdown n (4,3,2,1), title, value, note, color
  myth      myth, truth (truth shows at @1)
  calendar  title, cells, cols, gold_from, value_start, value_end, prefix, dur
  ending    wrong, right=[line1, line2], source, disclaimer
"""
import json, sys

Y_TOP = 300


def T(text, y, at, **k): return dict(type="text", text=text, y=y, at=at, **k)


def block(kind, s, b, nb):
    """Return elements for one scene. b = global index of the scene's first beat, nb = beats in scene."""
    def at(n=0):
        n = min(n, nb - 1); return b + n
    if kind == "question":
        els = [T(s.get("top", "WOULD YOU RATHER"), Y_TOP, -1 if b == 0 else at(), size=46),
               {"type": "box", "y": 390, "h": 250, "w": 760, "at": -1 if b == 0 else at()},
               T(s["big"], 400, -1 if b == 0 else at(), weight="extra", size=150, mode="pop"),
               T(s.get("sub", ""), 575, -1 if b == 0 else at(), weight="semi", size=40, color="grey")]
        opts = s.get("options", [])
        if opts:
            els.append({"type": "pill", "text": opts[0], "color": "gold", "y": 700, "at": at(), "delay": 1.0})
        if len(opts) > 1:
            els += [T(s.get("or_word", "OR"), 800, at(1), weight="extra", size=56, color="green"),
                    {"type": "pill", "text": opts[1], "color": "green", "filled": False, "y": 890, "at": at(1), "delay": 0.3}]
        return els
    if kind == "guess":
        return [{"type": "pill", "text": s.get("line", "LOCK IN YOUR GUESS"), "color": "gold", "y": 380, "at": at()},
                T(s.get("big", "$?"), 470, at(), weight="extra", size=260, color="gold", mode="pop", glow=True, delay=0.2),
                T(s.get("note", "THE ANSWER IS AT THE END"), 820, at(), weight="semi", size=40, color="grey", delay=1.0)]
    if kind == "counter":
        c = s.get("color", "green"); st = at(s.get("at", 0))
        els = [T(s["title"], 320, at(), size=60, color=c)]
        if s.get("subtitle"): els.append(T(s["subtitle"], 400, at(), weight="medium", size=32, color="grey", delay=0.3))
        if s.get("rate"): els.append({"type": "pill", "text": s["rate"], "color": c, "y": 470, "at": at(), "delay": 1.0})
        n = len(f'{s.get("prefix", "")}{s["end"]:,.{s.get("decimals", 0)}f}{s.get("suffix", "")}')
        size = 150 if n <= 9 else 128 if n <= 11 else 108
        els += [{"type": "count", "prefix": s.get("prefix", ""), "suffix": s.get("suffix", ""), "from": s.get("start", 1),
                 "value": s["end"], "decimals": s.get("decimals", 0), "curve": s.get("curve", "exp"), "y": 600, "size": size,
                 "color": "white" if c != "red" else "red", "at": st, "dur": s.get("dur", 2.5),
                 **({"color_after": s["payoff_color"], "after": s["payoff_after"]} if s.get("payoff_color") else {})},
                {"type": "meter", "y": 820, "w": 760, "from": 0, "to": 1, "color": c, "at": st, "dur": s.get("dur", 2.5)}]
        if s.get("years"):
            els += [T(str(s["years"][0]), 850, st, weight="semi", size=30, color="grey", x=145),
                    T(str(s["years"][1]), 850, st, weight="semi", size=30, color="grey", x=825)]
        if s.get("badge"):
            els.append({"type": "pill", "text": s["badge"], "color": s.get("payoff_color", c), "filled": False, "y": 930,
                        "at": at(nb - 1), "delay": 0.4})
        return els
    if kind == "bars":
        a, bb = s["a"], s["b"]
        els = [{"type": "hbar", "label": a["label"], "value": a["value"], "frac": a["frac"], "color": a.get("color", "green"), "y": 360, "at": at()},
               {"type": "hbar", "label": bb["label"], "value": bb["value"], "frac": bb["frac"], "color": bb.get("color", "gold"), "y": 540, "at": at(), "delay": 0.3}]
        if s.get("big"): els.append(T(s["big"], 730, at(), weight="extra", size=200, color="gold", mode="pop", glow=True, delay=1.2))
        if s.get("note"): els.append(T(s["note"], 1010, at(1), size=50, color="green"))
        return els
    if kind == "countdown":
        c = s.get("color", "gold" if s["n"] == 1 else "green")
        els = [T(f'#{s["n"]}', 300, at(), weight="extra", size=120, color=c, mode="pop", glow=s["n"] == 1),
               T(s["title"], 470, at(), size=54)]
        if s.get("value"): els.append(T(s["value"], 580, at(min(1, nb - 1)), weight="extra", size=140, color=c, mode="pop"))
        if s.get("note"): els.append(T(s["note"], 800, at(min(1, nb - 1)), weight="semi", size=40, color="grey", delay=0.6))
        els.append({"type": "meter", "y": 1000, "w": 600, "from": (4 - s["n"]) / 4, "to": (5 - s["n"]) / 4, "color": c, "at": at(), "dur": 0.8})
        return els
    if kind == "myth":
        return [T("MYTH", 320, at(), weight="extra", size=56, color="red"),
                T(s["myth"], 420, at(), size=56, id="m"),
                {"type": "strike", "of": "m", "color": "red", "at": at(1)},
                T("THE REAL NUMBER", 600, at(1), weight="extra", size=56, color="green"),
                T(s["truth"], 700, at(1), weight="extra", size=110, color="gold", mode="pop", glow=True, delay=0.4)]
    if kind == "calendar":
        st = at(s.get("at", 0))
        return [T(s["title"], 300, at(), size=52),
                {"type": "grid", "n": s.get("cells", 30), "cols": s.get("cols", 6), "y": 400, "lit_to": s.get("cells", 30),
                 "color": "green", "gold_from": s.get("gold_from"), "at": st, "dur": s.get("dur", 4)},
                {"type": "count", "prefix": s.get("prefix", "$"), "from": s.get("value_start", 0.01), "value": s["value_end"],
                 "decimals": s.get("decimals", 0), "curve": "exp", "y": 830, "size": 120, "color": "white",
                 "color_after": "gold", "after": s.get("value_end") * 0.5, "at": st, "dur": s.get("dur", 4)}]
    if kind == "ending":
        r = s["right"] if isinstance(s["right"], list) else [s["right"]]
        els = [T("THE REAL NUMBER ISN'T", 400, at(), weight="semi", size=40, color="grey"),
               T(s["wrong"], 470, at(), weight="extra", size=84, id="w", delay=0.5),
               {"type": "strike", "of": "w", "color": "red", "at": at(1)},
               T("IT'S", 620, at(1), weight="semi", size=40, color="grey", delay=0.2)]
        for i, line in enumerate(r[:2]):
            els.append(T(line, 690 + 110 * i, at(1), weight="extra", size=92, color="green", glow=True, delay=0.4 + 0.4 * i))
        els += [{"type": "follow", "y": 970, "at": at(2)},
                T(s.get("source", ""), 1100, at(2), weight="medium", size=26, color="grey"),
                T(s.get("disclaimer", "Not financial advice."), 1140, at(2), weight="medium", size=26, color="grey")]
        return els
    raise ValueError("unknown scene kind: " + kind)


# ---------------- notebook style (the original graph-paper look, engine: render.py) ----------------
# Brief with "style": "notebook". Kinds:
#   hook     big, sub, date, color (red|green), photo (optional local image path, only one Samrit sent)
#   facts    label, lines=[up to 4]; line i appears at beat i of the scene; last line is highlighted
#   number   label, value, prefix, suffix, decimals, note, color
#   compare  label, a={label, value, frac}, b={...}, color
#   ending   lines=[note card lines] (as-of date, sources, "Education only. Not financial advice.")
def nb_block(kind, s, b, nb):
    def at(n=0): return b + min(n, nb - 1)
    first = -1 if b == 0 else at()
    c = s.get("color", "red")
    if kind == "hook":
        els = []; y = 400
        if s.get("photo"):
            els.append({"type": "photo", "src": s["photo"], "y": 345, "w": 380, "at": first}); y = 800
        if s.get("sub") and s.get("photo"):
            els.append(T(s["sub"], y, first, font="hand", size=54, color="blue", rot=-1.5, mode="fade")); y += 75
        els.append(T(s["big"], y, first, font="head", size=120 if s.get("photo") else 170, color=c, mode="fade", id="hero"))
        if s.get("sub") and not s.get("photo"):
            els.append(T(s["sub"], y + 230, first, font="hand", size=60, color="blue", rot=-1.5, mode="fade"))
        if s.get("date") and not s.get("photo"):
            els.append(T(s["date"], y + 330, first, font="hand", size=44, color="grey", mode="fade"))
        return els
    if kind == "facts":
        els = [T(s["label"], 380, at(), font="hand", size=60, color="blue")]
        for i, line in enumerate(s["lines"][:4]):
            last = i == len(s["lines"][:4]) - 1
            els.append(T(line, 480 + 110 * i, at(i), size=46, **({"id": f"f{b}"} if last else {})))
        els.append({"type": "highlight", "of": f"f{b}", "at": at(len(s["lines"][:4]) - 1), "delay": 0.4})
        return els
    if kind == "number":
        els = [T(s["label"], 380, at(), font="hand", size=60, color="blue"),
               {"type": "count", "value": s["value"], "prefix": s.get("prefix", ""), "suffix": s.get("suffix", ""),
                "decimals": s.get("decimals", 0), "y": 480, "size": 150, "color": c, "at": at(), "id": f"n{b}"},
               {"type": "underline", "of": f"n{b}", "color": c, "at": at(), "delay": 1.0}]
        if s.get("note"): els.append(T(s["note"], 720, at(min(1, nb - 1)), font="hand", size=54, color="grey"))
        return els
    if kind == "compare":
        a, bb = s["a"], s["b"]
        return [T(s["label"], 380, at(), font="hand", size=60, color="blue"),
                T(a["label"], 480, at(), size=40, color="grey", x=135),
                {"type": "bar", "x": 135, "y": 540, "w": max(30, int(725 * a["frac"])), "color": a.get("color", "grey"), "at": at(), "delay": 0.2},
                T(a["value"], 600, at(), font="head", size=56, x=135),
                T(bb["label"], 700, at(min(1, nb - 1)), size=40, color="grey", x=135),
                {"type": "bar", "x": 135, "y": 760, "w": max(30, int(725 * bb["frac"])), "color": bb.get("color", c), "at": at(min(1, nb - 1)), "delay": 0.2},
                T(bb["value"], 820, at(min(1, nb - 1)), font="head", size=56, color=c, x=135, id=f"c{b}"),
                {"type": "highlight", "of": f"c{b}", "at": at(min(1, nb - 1)), "delay": 0.8}]
    if kind == "ending":
        return [{"type": "card", "label": "note:", "lines": s["lines"][:4], "y": 380, "at": at()},
                T("follow for", 930, at(), font="hand", size=52, color="blue"),
                T("The Real Number", 1000, at(), font="head", size=66, delay=0.18, mode="fade", id="rn"),
                {"type": "highlight", "of": "rn", "at": at(), "delay": 0.33}]
    raise ValueError("unknown notebook scene kind: " + kind)


def build_spec(brief):
    beats = brief["beats"]; phrases = []; starts = []
    for i, bt in enumerate(beats):
        ph = {"say": bt["say"]}
        if bt.get("cap"): ph["cap"] = bt["cap"]
        ph["pause"] = bt.get("pause", 0.35); phrases.append(ph)
        if bt.get("show"): starts.append(i)
    if not starts or starts[0] != 0: raise ValueError("beat 0 must have a 'show' (the hook frame)")
    scenes = []
    for k, b in enumerate(starts):
        nxt = starts[k + 1] if k + 1 < len(starts) else len(beats)
        sh = beats[b]["show"]
        fn = nb_block if brief.get("style") == "notebook" else block
        scenes.append({"until": nxt if k + 1 < len(starts) else "end", "els": fn(sh["kind"], sh, b, nxt - b)})
    for e in scenes[0]["els"]:            # the hook frame must be fully visible at frame 0 (thumbnail + first look)
        if e.get("at") == 0 and e["type"] not in ("strike",): e["at"] = -1; e.pop("delay", None)
    spec = {"id": brief["id"], "style": brief.get("style", "dark"), "series": brief["series"], "voice": brief.get("voice", "am_michael"),
            "speed": brief.get("speed", 1.08), "caption_keywords": brief.get("keywords", []),
            "phrases": phrases, "scenes": scenes}
    for k in ("cover", "sources", "post"): spec[k] = brief[k]
    return spec


def layout_check(spec):
    """Cheap automatic check so fewer stills need eyeballing: text inside the frame, nothing too wide."""
    if spec.get("style") == "notebook": return []
    sys.path.insert(0, __import__("os").path.dirname(__file__)); import render_dark as R
    problems = []
    for sc in spec["scenes"]:
        for e in sc["els"]:
            if e["type"] in ("text", "pill"):
                f = R.font(e.get("weight", "bold"), e.get("size", 56 if e["type"] == "text" else 34))
                w = f.getlength(e["text"]) + (56 if e["type"] == "pill" else 0)
                if w > 940: problems.append(f'too wide ({int(w)}px): "{e["text"]}"')
            if e.get("y", 0) > 1150: problems.append(f'too low (y {e["y"]}): {e.get("text", e["type"])}')
    return problems


if __name__ == "__main__":
    brief = json.load(open(sys.argv[1])); spec = build_spec(brief)
    probs = layout_check(spec)
    out = f'specs/{spec["id"]}.json'; json.dump(spec, open(out, "w"), indent=1, ensure_ascii=False)
    print("wrote", out)
    if probs: print("LAYOUT PROBLEMS:\n  " + "\n  ".join(probs)); sys.exit(1)
    print("layout ok")
