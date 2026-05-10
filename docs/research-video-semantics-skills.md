# Video Semantics Skill Research

Date: 2026-05-10

## Goal

Find reusable open-source skills, prompt patterns, and product patterns for Seed's next layer: fusing spoken transcript and visual notes into stable video semantics that can later be aggregated by creator/UP.

## Useful References

| Source | What it does | What Seed should learn |
| --- | --- | --- |
| `danielmiessler/Fabric` `extract_wisdom` | MIT-licensed prompt pattern for extracting summaries, ideas, insights, quotes, habits, facts, references, takeaways, and recommendations from text. | Reuse the extraction shape: separate raw ideas from refined insights, and keep methodology candidates distinct from quotes/facts. Do not copy wholesale; adapt the structure to video semantics. |
| `danielmiessler/Fabric` `summarize` | Concise Markdown summary pattern with one-sentence summary, main points, and takeaways. | Keep the semantics artifact compact at the top, then place deeper extraction below. |
| `openclaw/skills` `youtube-knowledge-extractor` | Multimodal YouTube analysis skill that treats audio transcript as what is said and frame analysis as what is shown, then synchronizes both channels. | Adopt the two-channel model directly: verbal language and visual language are separate evidence streams before fusion. |
| `github/awesome-copilot` `automate-this` | Screen-recording skill that extracts frames and narration, reconstructs steps, decisions, data flow, repetition, and pain points. | For tutorials/product demos, extract operational flow, decision points, and friction instead of only making a generic summary. |
| Atris YouTube skill | Processes YouTube with Gemini native multimodal analysis and can store results as agent knowledge. | Seed should preserve artifacts locally and make them reusable by agents, rather than treating analysis as one-off chat output. |
| Short-form script frameworks | Common structures include Hook -> Value/Body -> Retention -> CTA, and Hook -> Context -> Problem -> Reveal -> CTA. | Add a video-structure section for viral/short-form analysis without forcing every video into a marketing template. |

## Design Decision

Seed should not vendor a full external skill yet. The best immediate path is an attributed internal skill:

- Use Fabric-inspired sections for insights, methods, quotes, facts, references, and takeaways.
- Use multimodal YouTube skill patterns for the verbal/visual evidence split.
- Use short-form frameworks only as optional structure analysis when the video is short-form or performance-oriented.
- Keep the prompt in `skills/video-semantics-analyzer/SKILL.md` so it can be edited or replaced later.

## Sources

- Fabric repository and pattern documentation: https://github.com/danielmiessler/fabric
- Fabric `extract_wisdom` pattern: https://raw.githubusercontent.com/danielmiessler/Fabric/main/data/patterns/extract_wisdom/system.md
- Fabric `summarize` pattern: https://raw.githubusercontent.com/danielmiessler/Fabric/main/data/patterns/summarize/system.md
- YouTube knowledge extractor skill: https://playbooks.com/skills/openclaw/skills/youtube-knowledge-extractor
- Automate This skill: https://eliteai.tools/agent-skills/automate-this
- Atris YouTube skill: https://app.unpkg.com/atris%402.5.3/files/atris/skills/youtube/SKILL.md
- Hook/Value/Retention/CTA framework: https://livestreamvideo.ca/video-script-structure-hook-value-retention-cta/
- Hook/Context/Problem/Reveal/CTA framework: https://www.lomero.app/blog/anatomy-of-viral-short-form-video
