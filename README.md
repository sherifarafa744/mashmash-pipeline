# Hekayat Basbusa - automated Egyptian-Arabic cat-story Shorts

Fully automatic pipeline (GitHub Actions): Gemini writes the next episode ->
Gemini TTS narrates -> Cloudflare Workers AI flux-1-schnell draws the scenes
-> ffmpeg assembles (9:16, crossfades, Arabic subtitles, hook text, soft
outro) -> YouTube Data API uploads public and adds the video to the current
storyline's playlist.

- 4 Shorts/day (11:00, 14:00, 17:00, 20:00 Africa/Cairo), 2 parallel story
  arcs alternating (story_state_arc1.json / story_state_arc2.json).
- Weekly long-form compilation on Saturdays (pipeline/weekly.py).
- Costs: $0. Licenses: flux-1-schnell Apache-2.0; music "Sneaky Snitch"
  Kevin MacLeod CC-BY 4.0 (attributed in every description); fonts Noto (OFL).
