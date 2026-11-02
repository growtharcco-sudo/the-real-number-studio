# The Real Number Studio

Fully automatic, free pipeline for The Real Number (Instagram @the_real.number, YouTube @Thereal.number).

| Time (IST) | What happens | Where |
|---|---|---|
| ~5 PM | Pick a topic, write and fact-check the script, generate the voice (Kokoro "Michael"), build the Reel and cover, queue it, notify Samrit | Claude scheduled task (cloud), following `ROUTINE.md` |
| until post time | Samrit can reply "skip" to cancel | Claude |
| 9:05 / 10:05 PM | Post to Instagram (official API, AI label on) and YouTube Shorts (official API, synthetic-content disclosure on) | GitHub Actions, `.github/workflows/post.yml` |

Nothing needs your Mac. Setup: see `SETUP.md`.

## Folders
- `pipeline/` voice (`voice.py`), notebook-style video engine (`render.py`), builder (`make_reel.py`)
- `specs/` one JSON file per Reel: phrases, scenes, cover, captions, sources
- `queue/` Reels waiting to post (`post.json`); videos live on the `media` branch (GitHub Pages)
- `posted/` what went out, with Instagram and YouTube links in `result.json`
- `poster/` Instagram and YouTube posting, media branch handling
- `IDEAS.md` checked idea bank; `ROUTINE.md` the daily instructions Claude follows

## Manual commands
```
python pipeline/make_reel.py specs/<id>.json --stills   # preview frames
python pipeline/make_reel.py specs/<id>.json            # build video + cover into queue/<id>/
python poster/media_branch.py add <id> queue/<id>/video.mp4 queue/<id>/cover.png
python poster/publish_due.py --dry-run                  # show what would post now
```
Voice: Kokoro v1.0 (Apache 2.0), downloaded on first use. Fonts: Space Grotesk and Caveat (SIL OFL).
