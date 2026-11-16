# @cleaneverycorner — Reels style guide and daily workflow

Faceless, animated home & car cleaning tips for a US audience, in English.
One Reel per day, posted automatically via the Windsor.ai for Social Media connector
(Instagram account id `17841441974005717`, action `create_video_post`).

## Weekly mix
4 home + 3 car per week. The plan lives in `content/calendar.csv`; every post is logged in `content/posted.csv`.
When the calendar runs out, add the next 4 weeks of topics (same mix, seasonal, no repeats of `posted.csv`) and commit them.

## Video spec
- 1080x1920, 30 fps, H.264 yuv420p (CRF 18, preset veryfast), AAC 192k, **max 25 s, target 12–22 s** (2026-11-16: replaces the old 25–40 s rule; ~67% of viewers swiped away in the first 3 s).
- Every scene ≤ 2–3 s; at most 2 short text blocks on screen at once (e.g. step card + one pill).
- The last frame must lead back into the first frame so the Reel loops (`make_loop_outro(bg, HOOK(0, D))` in `lib/engine.py`).
- Keep text out of the top 250 px and bottom 350 px (Instagram UI).
- Fonts: Poppins (Bold for titles, Medium for body). No emoji drawn in video.
- Brand colors: teal `#0E96AA`, yellow `#FFC428`, ink `#182634`, white. Green `#28AA64` for do, red `#E24040` for don't.
- Structure: hook (≈2–2.5 s) → short safety scene whenever any chemical/product is used (ventilation, gloves, don't mix) → max 3 numbered steps (card with STEP n + progress dots, animated illustration under it) → before/after reveal → loop outro (save/follow card + comment prompt, cross-fades back into the hook).
- Per-day script lives next to the video: `reels/YYYY-MM-DD-<slug>/render.py` (`python3 render.py stills` → `stills/`, `python3 render.py render`). `work/`, `stills/`, `music.wav` are git-ignored.
- Reference implementation of the look: `tools/reference_render_bleach_tiles.py` (scene-by-scene PIL frames piped to ffmpeg, one file per scene, concat with `-c copy`).
  Reusable helpers belong in `lib/` (create `lib/engine.py` the first time and reuse/extend it on later days instead of rewriting).

## Hook / cover rules (owner's standing request: more engaging)
- The first frame must stop the scroll: big bold amber/yellow headline (≥140 px, **max 6 words**), a surprising or contrarian claim;
  show the finished clean result or a close-up of the dirty surface; method and supplies come later.
- Rotate hook patterns (question, "Stop...", number/time promise, before/after, "Wait for it"); "Stop..." at most 2× per week.
  Examples:
  ("Your grout is NOT supposed to be this color", "Stop cleaning your windshield like this").
- Show the payoff immediately: split-screen dirty vs clean (or before/after wipe) within the first 1 s, with a marker on the problem
  (red circle or arrow) and a check on the result.
- Motion from frame 0: punch-in zoom, quick shake or pop-in scale on the headline; a pill like "5 STEPS" or "30 SECONDS".
- Use that hook frame as the cover (`thumb_offset` in ms pointing at a frame where the full headline is visible).

## Music rules (owner's standing requests: upbeat AND clean-sounding)
- **Clean, clear sound (owner's request, 2026-11-11):** the old saw/noise-based sounds were too metallic and harsh. New Reels use ONLY the
  clean, band-limited styles in `lib/music_clean.py` (piano, marimba, kalimba, glockenspiel, nylon guitar, clean e-piano,
  round sine bass, soft claps/snaps/shaker, light reverb, transparent limiter). Never use `housepop`, `funk`, `disco`,
  `futurebounce`, `dembow`, `trap` or `synthwave` for a new Reel (legacy, kept only to re-render old videos), and do not
  add saw/square leads, white-noise hi-hats or tanh distortion.
- Original, generated in code (no licensed tracks), upbeat and positive, energy from the first beat (no slow intro).
- **118–128 BPM, four-on-the-floor kick, claps on 2 and 4 (2026-11-16):** always call `make_track(..., style=style, seed=seed, upbeat=True)`;
  `upbeat=True` keeps the clean instruments of the picked style but lifts the tempo into range and sets the kick/clap pattern
  (`lib/music_clean.upbeat_variant`). Pass the big opening moment (t=0) as an impact too.
- Accent scene changes with a whoosh into each cut and an impact on the before/after reveal (pass `cuts` and `impacts`).
- Loudness about -14 to -16 LUFS integrated, true peak ≤ -1.5 dB; fade out the last 1.5 s.
- **Style rotation (mandatory for every new Reel):** the sound must differ from video to video. Do not hand-pick style or seed.
  ```python
  from lib.music_styles import pick_style
  style, seed = pick_style(slug)          # reads/writes content/music_state.json, idempotent per slug; returns clean styles only
  make_track(dur, cuts, impacts, music_wav, style=style, seed=seed)
  ```
  Clean styles: `brightpop` 118 BPM, `pianohouse` 122, `tropical` 104, `acoustic` 112, `keysfunk` 108, `kalimbapop` 96.
  The picker never repeats either of the last two styles and evens out usage. Commit `content/music_state.json`
  together with the Reel. Presets live in `lib/music_clean.py` (`STYLES` dict + add the name to `ROTATION` in `lib/music_styles.py`).
- `tools/music_v1_calm.py` is the old calm version — do not use it as-is. Build `lib/music_upbeat.py` once and reuse it.

## Accuracy and safety
- Every tip must be correct and safe. Check claims against reputable sources (manufacturer guidance, EPA/CDC, university extension, car-care makers) before writing.
- Always flag dangerous mixes (bleach + ammonia/vinegar/acids) and surface limits (natural stone, car paint, leather, screens) when relevant.
- No brand names or logos in the video; no claims of being a professional or a real person.

## Caption
- Short and scannable, max ~900 characters (hard limit 2200). Line 1: hook (don't start with "Stop..." every day).
  Then max 3 short steps/tips, one safety line if relevant, a comment question
  ("Home or car — what should I clean next? 👇" / "Did you know this one? 👇"), then
  "Save this for cleaning day 📌 Follow for daily home & car cleaning tips."
- Exactly 5 hashtags total: `#cleaneverycorner` + 4 topic tags (e.g. home: #cleaningtips #cleaninghacks + 2 specific;
  car: #carcleaning #cardetailing + 2 specific). Never more than 5 (Instagram limit).

## Publishing
1. Commit the final mp4 to `reels/YYYY-MM-DD-<slug>/<slug>.mp4` (+ `cover.jpg`) on `main` and push.
2. Check `https://raw.githubusercontent.com/sguven/cleaneverycorner-media/main/reels/...` returns HTTP 200.
3. Windsor `execute_action` → connector `instagram`, action `create_video_post`, account `17841441974005717`,
   params `video_url`, `caption`, `thumb_offset`, `share_to_feed: true`.
4. Append the post to `content/posted.csv` (date, category, slug, media_id, video_url) and push.
