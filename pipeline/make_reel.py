"""spec.json -> voice -> video -> cover -> queue/<id>/

Usage:
  python pipeline/make_reel.py specs/<id>.json            # full build into queue/<id>/
  python pipeline/make_reel.py specs/<id>.json --stills   # quick check frames only
"""
import json, os, sys, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voice, render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EM_DASH = "—"


def check_spec(spec):
    """Hard rules from the channel playbook. Fails loudly instead of posting something wrong."""
    errs = []
    post = spec.get("post", {})
    for k in ("post_at", "instagram_caption", "youtube_title", "youtube_description"):
        if not post.get(k): errs.append(f"post.{k} is missing")
    every_text = json.dumps(spec, ensure_ascii=False)
    if EM_DASH in every_text: errs.append("em dash found (channel rule: no em dashes)")
    ig = post.get("instagram_caption", "")
    tags = [w for w in ig.split() if w.startswith("#")]
    if len(tags) != 5: errs.append(f"Instagram caption needs exactly 5 hashtags, has {len(tags)}")
    if "#therealnumber" not in tags: errs.append("Instagram caption must include #therealnumber")
    if "Not financial advice" not in ig: errs.append("Instagram caption must say 'Not financial advice'")
    if len(post.get("youtube_title", "")) > 100: errs.append("YouTube title over 100 characters")
    if not spec.get("sources"): errs.append("spec.sources is empty: every number needs a source")
    for bad in ("guaranteed return", "guaranteed profit", "you should buy", "buy now", "will 10x", "risk-free"):
        if bad in every_text.lower(): errs.append(f"forbidden phrase: {bad!r}")
    if errs: raise SystemExit("SPEC CHECK FAILED:\n- " + "\n- ".join(errs))


def main():
    path = sys.argv[1]
    spec = json.load(open(path))
    check_spec(spec)
    global render
    if spec.get("style") == "dark":
        import render_dark as render
    out = os.path.join(ROOT, "queue", spec["id"])
    os.makedirs(out, exist_ok=True)
    wav = os.path.join(out, "voice.wav")
    _, times, total = voice.synth(spec["phrases"], wav, spec.get("voice", "am_michael"), spec.get("speed", 1.08))
    json.dump({"phrase_times": times, "total": total}, open(os.path.join(out, "timing.json"), "w"), indent=1)
    if "--stills" in sys.argv:
        ts = [0.0] + [round((s + e) / 2, 2) for s, e in times]
        render.render(spec, times, total, wav, os.path.join(out, "check"), stills=ts)
        print("stills written to", out); return
    mp4 = os.path.join(out, "video.mp4")
    render.render(spec, times, total, wav, mp4)
    render.cover(spec, os.path.join(out, "cover.png"))
    os.remove(wav)
    for f in os.listdir(out):
        if ".still_" in f: os.remove(os.path.join(out, f))
    shutil.copy(path, os.path.join(out, "spec.json"))
    json.dump(spec["post"], open(os.path.join(out, "post.json"), "w"), indent=1, ensure_ascii=False)
    print(f"ready: {mp4} ({total:.1f}s), post_at {spec['post']['post_at']}")


if __name__ == "__main__":
    main()
