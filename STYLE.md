# @cleaneverycorner — Reels style guide and daily workflow

Faceless, animated home & car cleaning tips for a US audience, in English.
One Reel per day, posted automatically via the Windsor.ai for Social Media connector
(Instagram account id `17841441974005717`, action `create_video_post`).

## Weekly mix
4 home + 3 car per week. The plan lives in `content/calendar.csv`; every post is logged in `content/posted.csv`.
When the calendar runs out, add the next 4 weeks of topics (same mix, seasonal, no repeats of `posted.csv`) and commit them.

## Video spec
- 1080x1920, 30 fps, H.264 yuv420p (CRF 18, preset veryfast), AAC 192k, 25–40 s.
- Keep text out of the top 250 px and bottom 350 px (Instagram UI).
- Fonts: Poppins (Bold for titles, Medium for body). No emoji drawn in video.
- Brand colors: teal `#0E96AA`, yellow `#FFC428`, ink `#182634`, white. Green `#28AA64` for do, red `#E24040` for don't.
- Structure: hook (≈3 s) → safety/“before you start” if any chemical is involved → numbered steps (card with STEP n + progress dots, animated illustration under it) → before/after reveal → outro card "Save this for cleaning day!" + "Follow @cleaneverycorner".
- Reference implementation of the look: `tools/reference_render_bleach_tiles.py` (scene-by-scene PIL frames piped to ffmpeg, one file per scene, concat with `-c copy`).
  Reusable helpers belong in `lib/` (create `lib/engine.py` the first time and reuse/extend it on later days instead of rewriting).

## Hook / cover rules (owner's standing request: more engaging)
- The first frame must stop the scroll: big bold headline (≥140 px, white with dark stroke or yellow), a problem statement or bold claim
  ("Your grout is NOT supposed to be this color", "Stop cleaning your windshield like this").
- Show the payoff immediately: split-screen dirty vs clean (or before/after wipe) within the first 1 s, with a marker on the problem
  (red circle or arrow) and a check on the result.
- Motion from frame 0: punch-in zoom, quick shake or pop-in scale on the headline; a pill like "5 STEPS" or "30 SECONDS".
- Use that hook frame as the cover (`thumb_offset` in ms pointing at a frame where the full headline is visible).

## Music rules (owner's standing request: more upbeat)
- Original, generated in code (no licensed tracks): 118–128 BPM, four-on-the-floor kick, claps on 2 and 4, offbeat hats,
  bouncy bass, bright synth stab or pluck hook; energy from the first beat (no slow intro).
- Accent scene changes with a whoosh/riser into each cut and an impact on the before/after reveal.
- Loudness about -14 to -16 LUFS integrated, true peak ≤ -1.5 dB; fade out the last 1.5 s.
- **Style rotation (mandatory for every new Reel):** the sound must differ from video to video. Do not call `make_track` with a hand-picked seed.
  ```python
  from lib.music_styles import pick_style
  style, seed = pick_style(slug)          # reads/writes content/music_state.json, idempotent per slug
  make_track(dur, cuts, impacts, music_wav, style=style, seed=seed)
  ```
  Styles: `housepop` (original), `funk` 106 BPM, `disco` 118, `futurebounce` 126, `dembow` 98, `trap` 140, `synthwave` 112 — all upbeat,
  all generated in code. The picker never repeats either of the last two styles and evens out usage. Commit `content/music_state.json`
  together with the Reel. Presets live in `lib/music_styles.py` (`STYLES` dict); to add a style add one entry, no other change needed.
- `tools/music_v1_calm.py` is the old calm version — do not use it as-is. Build `lib/music_upbeat.py` once and reuse it.

## Accuracy and safety
- Every tip must be correct and safe. Check claims against reputable sources (manufacturer guidance, EPA/CDC, university extension, car-care makers) before writing.
- Always flag dangerous mixes (bleach + ammonia/vinegar/acids) and surface limits (natural stone, car paint, leather, screens) when relevant.
- No brand names or logos in the video; no claims of being a professional or a real person.

## Caption
- Line 1: hook. Then the numbered steps (short), one safety line if relevant, then
  "Save this for cleaning day 📌 Follow for daily home & car cleaning tips."
- Exactly 5 hashtags total: `#cleaneverycorner` + 4 topic tags (e.g. home: #cleaningtips #cleaninghacks + 2 specific;
  car: #carcleaning #cardetailing + 2 specific). Never more than 5 (Instagram limit).

## Publishing
1. Commit the final mp4 to `reels/YYYY-MM-DD-<slug>/<slug>.mp4` (+ `cover.jpg`) on `main` and push.
2. Check `https://raw.githubusercontent.com/sguven/cleaneverycorner-media/main/reels/...` returns HTTP 200.
3. Windsor `execute_action` → connector `instagram`, action `create_video_post`, account `17841441974005717`,
   params `video_url`, `caption`, `thumb_offset`, `share_to_feed: true`.
4. Append the post to `content/posted.csv` (date, category, slug, media_id, video_url) and push.
