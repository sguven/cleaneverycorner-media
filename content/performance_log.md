# @cleaneverycorner — weekly performance log

Data: Windsor.ai Instagram connector (account 17841441974005717), media_info + media_insights, cached copy
(the plan does not allow on-request refresh). Times below are America/New_York.

## 2026-11-22 (week of 2026-11-15 → 2026-11-21, 7 Reels)

Baseline (2026-11-15 analysis): ~67% skip in the first 3 s, ~100 avg views, 0 comments, car > home.

| | This week (7) | Previous week 11-08→11-14 (8) |
|---|---|---|
| Avg views | **132** (median 131) | 106 (median 116.5) |
| Avg reach | 115 | 98 |
| Avg 3-s skip rate | **60.2%** | 67.5% |
| Avg watch time (median) | **4.8 s** | 3.9 s |
| Likes / comments / saves / shares | 3 / **0** / **4** / 0 | 8 / 0 / 0 / 1 |
| Followers (today) | 24 | not recorded (first log) |

By category (this week): home n=4 → 133 views, 62.3% skip, 3 saves · car n=3 → 130 views, **57.2% skip**, 1 save.
By posting time (both weeks, 15 Reels): 12–13 h → 119 views / 63.2% skip · 14–17 h → 126 / 60.0% · late night/early → 107 / 76.2%.

Best 2 (lowest skip, then saves/shares):
1. 11-16 sink-drain-deodorize (home) — 50.0% skip, 137 views, 5.5 s watch. Hook: "Sink smells? It's probably not your drain."
2. 11-17 foggy-headlights (car) — 54.0% skip, 125 views. Hook: toothpaste myth ("looks great… for a few weeks").
   (11-19 leather-seats-winter: 55.3% skip + 1 save.) 11-18 guest-ready-bathroom had the most saves (2) despite 66.4% skip.

Worst 2:
1. 11-15 mattress-refresh (home) — 68.9% skip, generic question hook, posted 16:43.
2. 11-20 greasy-kitchen-cabinets (home) — 64.1% skip, 0 saves, 3.3 s watch.

What worked: myth-busting / "it's not what you think" hooks; shorter 15–17 s cuts (watch time and skip both improved
after the 2026-11-16 format change); checklist-style home topics earn saves; car topics still skip less.
What didn't: generic question hooks; comments are still 0 even with a comment prompt; late-evening posts.
Data notes: 11-19 avg watch time 27.4 s is longer than the Reel (replays/loops) — treated as an outlier, medians used.
Today's Reel (11-22 clean-as-you-cook) is not in these numbers.

### Önümüzdeki hafta için kurallar
1. Hook: open with a myth-bust or "it's not X, it's Y" claim on a dirty close-up / split screen (best two Reels did this);
   no plain "When did you last…?" questions. Number/time promise goes in the pill, not the headline.
2. Mix: keep 4 home + 3 car, but at least one car topic and the weekly "common mistake" should be myth-busting; keep
   one checklist-style home topic per week for saves.
3. Length 15–18 s, post 12:00–14:30 ET (never late evening), and end the caption with an either/or question that is
   easy to answer in one word (e.g. "Vinegar or dish soap?") to get the first comments.


## 2026-11-26: opening-format test started (owner's request)
State before the test (Windsor, 2026-11-26): 25 followers, 23 posts; Reels since 11-15 sit at ~110–140 views, 50–69% skip
(three low outliers on 11-23, 11-25 with 30–40 views), 0 comments. From 2026-11-27 each Reel uses the `opening` set in
`content/calendar.csv` (`wipe_open`, `quiz_open`, `split` as control; see STYLE.md "Opening formats"). All posts up to
11-26 are `split`.
**Next weekly review:** add a "By opening" table (n, avg views, avg skip, median watch, saves, comments) and compare with
the `split` baseline (avg skip 60.2%). Keep a format that is at least 5 points lower on skip over 2+ Reels, drop one that is
worse than `split`, and fill the next week's `opening` column accordingly.
