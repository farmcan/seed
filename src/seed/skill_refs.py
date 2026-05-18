from __future__ import annotations

from pathlib import Path


DEFAULT_VIDEO_ANALYSIS_LENSES_PATH = Path(
    "skills/video-semantics-analyzer/references/video-analysis-lenses.md"
)
DOMAIN_LENS_PATHS = {
    "finance": Path("skills/video-semantics-analyzer/references/domain-finance-lenses.md"),
    "news": Path("skills/video-semantics-analyzer/references/domain-news-lenses.md"),
    "earnings": Path("skills/video-semantics-analyzer/references/domain-earnings-lenses.md"),
    "ai-practices": Path("skills/video-semantics-analyzer/references/domain-ai-practices-lenses.md"),
}


def read_video_analysis_lenses(
    path: Path = DEFAULT_VIDEO_ANALYSIS_LENSES_PATH,
    domains: list[str] | None = None,
) -> str:
    sections = [path.read_text(encoding="utf-8") if path.exists() else ""]
    for domain in domains or []:
        domain_path = DOMAIN_LENS_PATHS.get(domain)
        if domain_path and domain_path.exists():
            sections.append(domain_path.read_text(encoding="utf-8"))
    return "\n\n".join(section for section in sections if section.strip())
