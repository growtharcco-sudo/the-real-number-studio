"""Free voiceover with Kokoro (Apache-2.0, commercial use allowed). Voice: am_michael.

Each phrase is generated separately, so we know exactly when every phrase starts and ends.
Returns the path of a 48 kHz WAV and a list of (start, end) seconds per phrase.
"""
import os, subprocess, urllib.request
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.environ.get("KOKORO_DIR", os.path.join(HERE, "models"))
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]


def ensure_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for f in FILES:
        p = os.path.join(MODEL_DIR, f)
        if not os.path.exists(p) or os.path.getsize(p) < 1_000_000:
            print("downloading", f)
            try:
                urllib.request.urlretrieve(BASE + f, p)
            except Exception:  # some sandboxes only allow curl through their proxy
                subprocess.run(["curl", "-sSL", "-o", p, BASE + f], check=True)
    return [os.path.join(MODEL_DIR, f) for f in FILES]


def synth(phrases, out_wav, voice="am_michael", speed=1.08, lead=0.15, tail=0.25):
    """phrases: list of dicts with 'say' and optional 'pause' (seconds of silence BEFORE the phrase)."""
    from kokoro_onnx import Kokoro
    k = Kokoro(*ensure_model())
    lang = "en-gb" if voice.startswith("b") else "en-us"
    chunks, times, t, sr = [], [], lead, 24000
    chunks.append(np.zeros(int(lead * sr), np.float32))
    for i, ph in enumerate(phrases):
        if i:
            gap = float(ph.get("pause", 0.4))
            chunks.append(np.zeros(int(gap * sr), np.float32)); t += gap
        a, sr = k.create(ph["say"], voice=voice, speed=float(ph.get("speed", speed)), lang=lang)
        a = np.asarray(a, np.float32)
        nz = np.where(np.abs(a) > 0.01 * np.abs(a).max())[0]
        a = a[max(0, nz[0] - 240):min(len(a), nz[-1] + 480)]           # trim silence, keep soft edges
        chunks.append(a); times.append((round(t, 3), round(t + len(a) / sr, 3))); t += len(a) / sr
    chunks.append(np.zeros(int(tail * sr), np.float32))
    y = np.concatenate(chunks)
    raw = out_wav + ".raw.wav"
    sf.write(raw, y / np.abs(y).max() * 0.9, sr)
    # loudness for Reels/Shorts (about -14 LUFS) and 48 kHz
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000", "-ar", "48000", out_wav], check=True)
    os.remove(raw)
    return out_wav, times, len(y) / sr
