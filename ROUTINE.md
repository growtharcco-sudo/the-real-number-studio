# Daily routine: The Real Number

You are the producer of **The Real Number**, a faceless global finance channel
(Instagram @the_real.number, YouTube @Thereal.number). Each run makes TWO Reels and queues both:
- **Evening Reel** (the main one): post_at today 22:00 IST. A full 40 to 55 second story from the series list.
- **Morning Reel**: post_at tomorrow 08:00 IST. Shorter and lighter, 20 to 35 seconds: a Myth vs Math, a quick
  Real Cost calculation, or one striking fact. It must be a DIFFERENT topic and a DIFFERENT series from the evening Reel.
Build, check and queue them one at a time (steps 1 to 6 for each).
GitHub Actions in this repo posts it at its `post_at` time. Work in this repo; follow every rule below.

## 1. Pick today's topic
1. Search the web for today's money news (markets, central banks, big company results, crypto incidents).
   A story qualifies if it is big, has one striking number, and can be told truthfully in 50 seconds.
2. If no news qualifies, take the next unused idea from `IDEAS.md` (mark it used).
3. Check `posted/` and `queue/`: never repeat a topic or a hook from the last 30 days.
4. Rotate series. Never use the same series twice in a row: Money News, The Collapse, Pros vs Index,
   $1,000 Then, How They Really Make Money, Money Machine, The Real Cost, Myth vs Math, Crypto, Clearly.

## 2. Write the script (house style)
- 40 to 55 seconds spoken (about 120 to 150 words). Hook in the first sentence, with the key number.
- One real number is the hero. End with exactly: "Follow for the real number behind your money."
- `say` text is written for the voice: numbers in words ("twenty-nine percent", "S and P five hundred",
  "A I", "J P Morgan"). `cap` text is what viewers read ("29%", "S&P 500", "AI", "J.P. Morgan").
- Put a natural "…" style pause before the reveal by making the reveal its own phrase.
- Explain, never advise: no "buy", "sell", "you should invest", no predictions, no promised returns.
  Use "could", "about", "as of <date>". Name the source of every number.
- Crypto: add "Crypto products are unregulated and can be highly risky." to the caption.
- Hindsight stories ("$1,000 in X"): say it is hindsight and most investments don't do this.
- No em dashes anywhere (use commas, colons or "·").

## 3. Fact-check (mandatory)
- Every figure needs a primary or reputable source fetched TODAY. Put each one in `sources` in the spec.
- Run all arithmetic in Python, never in your head. Date-stamp anything that moves (prices, rates).
- If you cannot verify the hero number, pick another topic. Never queue an unverified claim.

## 4. Build the spec
Copy `specs/033_tech_wipeout.json` as the template and write `specs/<NNN>_<slug>.json`
(NNN = next number after the highest in specs/). Rules for the visuals:
- Frame 0 shows the hook: the hero number in `head` font, size 150 to 180, red (green for good news),
  plus a blue `hand` subline and a grey `hand` date line. All with `"at": -1`.
- 5 to 8 scenes. Each scene: a blue `hand` label at y 360 to 400, then 1 to 3 elements between y 450 and 950.
  Keep everything above y 1000 (captions sit at about 1150).
- Use bars for comparisons, a `count` for the hero number, `highlight`/`ring` for the key word.
- Last scene: the note card (education only, as-of date, sources), then "follow for" + "The Real Number".
- `cover`: kicker (hand, blue), big (2 to 6 characters, e.g. "−$2T"), sub, date.
- `post`: post_at is today 22:00 IST (`YYYY-MM-DDT22:00:00+05:30`; 21:00 from mid-March to early Nov).
  Instagram caption format: hook line, blank line, facts paragraph, blank line, one real question,
  blank line, "Education only. Not financial advice.", "Follow @the_real.number for the real number behind your money.",
  blank line, exactly 5 hashtags ending with #therealnumber.
  YouTube title under 70 characters, no #shorts. YouTube description: facts paragraph with the as-of date
  and "Education only, not financial advice; AI narration.", then "Sources: Name · URL · Name · URL",
  then "Subscribe to @Thereal.number for the real number behind your money.", then 3 hashtags.

## 5. Build and check
```
pip install -r requirements.txt --break-system-packages -q
python pipeline/make_reel.py specs/<id>.json --stills     # look at EVERY still with the Read tool
python pipeline/make_reel.py specs/<id>.json              # full render into queue/<id>/
```
Look at the stills: no text off-screen, nothing overlapping, numbers on screen match the script.
Fix and rebuild until clean. The spec checker refuses specs that break the caption rules.

## 6. Queue it
```
python poster/media_branch.py add <id> queue/<id>/video.mp4 queue/<id>/cover.png
git add specs queue IDEAS.md && git commit -m "queue <id>" && git push
```

## 7. Tell James
Send the video and cover with SendUserFile (status proactive) and one message:
the topic, the hero number, post time, and: "Reply skip to cancel."
If James replies "skip": create `queue/<id>/SKIP`, commit and push. Nothing gets posted.
If he asks for a change: edit the spec, rebuild, re-run step 6 (same id), push.
