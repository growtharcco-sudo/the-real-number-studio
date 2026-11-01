"""The `media` branch holds only the videos waiting to be posted, served by GitHub Pages.

It is rebuilt as a single fresh commit every time, so its history never grows.
  python poster/media_branch.py add <id> <video.mp4> <cover.png>   # queue a video
  python poster/media_branch.py prune                               # drop everything already posted
"""
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(*a, cwd=None, check=True):
    return subprocess.run(a, cwd=cwd, check=check, text=True, capture_output=True)


def _checkout():
    url = sh("git", "remote", "get-url", "origin", cwd=ROOT).stdout.strip()
    tmp = tempfile.mkdtemp()
    r = sh("git", "clone", "--depth", "1", "--branch", "media", url, tmp, check=False)
    if r.returncode:                               # first run: no media branch yet
        shutil.rmtree(tmp); os.makedirs(tmp)
        sh("git", "init", "-q", cwd=tmp); sh("git", "remote", "add", "origin", url, cwd=tmp)
    return tmp


def _publish(tmp):
    open(os.path.join(tmp, ".nojekyll"), "w").close()
    shutil.rmtree(os.path.join(tmp, ".git"), ignore_errors=True)
    url = sh("git", "remote", "get-url", "origin", cwd=ROOT).stdout.strip()
    sh("git", "init", "-q", "-b", "media", cwd=tmp)
    sh("git", "config", "user.name", "trn-bot", cwd=tmp); sh("git", "config", "user.email", "trn-bot@users.noreply.github.com", cwd=tmp)
    sh("git", "add", "-A", cwd=tmp); sh("git", "commit", "-q", "-m", "media queue", "--allow-empty", cwd=tmp)
    sh("git", "push", "-q", "-f", url, "media", cwd=tmp)


def add(vid, video, cover):
    tmp = _checkout()
    d = os.path.join(tmp, vid); os.makedirs(d, exist_ok=True)
    shutil.copy(video, os.path.join(d, "video.mp4")); shutil.copy(cover, os.path.join(d, "cover.png"))
    _publish(tmp)


def prune():
    tmp = _checkout()
    queued = set(os.listdir(os.path.join(ROOT, "queue"))) if os.path.isdir(os.path.join(ROOT, "queue")) else set()
    for name in os.listdir(tmp):
        if name.startswith(".") or name in queued: continue
        shutil.rmtree(os.path.join(tmp, name), ignore_errors=True)
    _publish(tmp)


if __name__ == "__main__":
    if sys.argv[1] == "add": add(*sys.argv[2:5])
    elif sys.argv[1] == "prune": prune()
