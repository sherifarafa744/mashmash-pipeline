# Hekayat Basbusa - automated Egyptian-Arabic cat-story Shorts

Fully automatic pipeline (GitHub Actions): Gemini writes the next episode ->
Gemini TTS narrates -> Cloudflare Workers AI flux-1-schnell draws the scenes
-> ffmpeg assembles (9:16, crossfades, Arabic subtitles, hook text, soft
outro) -> YouTube Data API uploads public and adds the video to the current
storyline's playlist.

- 4 Shorts/day publish at 11:00, 14:00, 17:00, 20:00 Africa/Cairo (built ~1h earlier and scheduled on YouTube with publishAt, see "Scheduled publishing"), 2 parallel story
  arcs alternating (story_state_arc1.json / story_state_arc2.json).
- Long-form compilations twice a week (Wed + Sat, scheduled 13:00/13:30 Cairo) (pipeline/weekly.py).
- Costs: $0. Licenses: flux-1-schnell Apache-2.0; music "Sneaky Snitch"
  Kevin MacLeod CC-BY 4.0 (attributed in every description); fonts Noto (OFL).

## Milestone celebrations

When Studio numbers cross a milestone (subscribers 10/50/100/500/1000, total
views 10K/100K), the review agent commits a flag file at the repo root:

    milestone.json: {"pending": true, "kind": "subscribers"|"views",
                     "value": <verified number>, "flagged_at": "<ISO time>"}

The next daily slot then runs pipeline/celebrate.py INSTEAD of a story
episode: a ~20-30s Short of Basbusa celebrating and thanking viewers (no
cliffhanger, no part number, arc state untouched, not added to a story
playlist). The archive commit moves episode.json to episodes/celebrations/
and deletes milestone.json, re-arming the trigger. The narration never states
an exact number, so the Short stays true whenever it publishes; only the
review agent tracks the real counts.

## Engagement (from 2026-11-26)

- Audience vote: every story episode ends with an either-or question about
  what Basbusa does next (episode.json records vote.question / option_a /
  option_b). The channel also posts the question as a comment under the video
  (commentThreads.insert, youtube.force-ssl scope; pinning has no API - pin by
  hand in Studio if wanted). Before the arc's next episode, pipeline/vote.py
  counts matching comments on the previous video and writes
  state.vote_result (winner a/b/tie/none); gen_script then follows the
  majority. Comments quoting both options and the channel's own comment are
  not counted.
- Recurring companion: each arc invents exactly one secondary character
  (friend or rival) kept identical across the arc in state.companion (name,
  role, English visual description embedded in image prompts).

## Scheduled publishing (from 2026-11-26)

GitHub's cron delays fires by up to ~40 min, so nothing publishes "when the
workflow runs". Build fires start at 08/11/14/17 UTC; pipeline/slot.py picks the
next slot (09/12/15/18 UTC, >=12 min ahead), the arc follows that slot, and
upload.py sends the video PRIVATE with status.publishAt = slot. YouTube flips it
public at exactly that time. The guard skips a fire if a successful run already
served the same slot. Releases (cross-post kit) state the publish time in their
notes: post to other platforms at/after it. Weekly compilations use the same
mechanism (11:00 UTC arc1, 11:30 UTC arc2). Hook rotation (hook_style) is
unchanged and recorded per episode in episode.json for the review agent.
