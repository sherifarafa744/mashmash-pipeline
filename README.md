# Mashmash - automated Egyptian-Arabic cat-story Shorts

Daily pipeline (GitHub Actions cron): Gemini writes the next episode ->
Gemini TTS narrates (1 request/episode, free tier) -> Cloudflare Workers AI
flux-1-schnell draws the scenes (free 10k neurons/day) -> ffmpeg assembles
(9:16, crossfades, Arabic subtitles) -> YouTube Data API uploads PRIVATE.

Costs: $0. Licenses: flux-1-schnell Apache-2.0; Gemini API free tier output
usable (free-tier content improves Google products); fonts Noto (OFL).

Publishing an episode public is a human decision; uploads stay private.
