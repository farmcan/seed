from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from seed.agents.codex import run_codex_prompt
from seed.library import init_library, slugify
from seed.skill_refs import read_video_analysis_lenses


def finance_signals_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "semantics" / f"{slugify(title)}.finance-signals.json"


def build_finance_signals_prompt(
    *,
    semantics_path: Path,
    title: str | None = None,
    owner: str | None = None,
    platform: str | None = None,
) -> str:
    semantics = semantics_path.read_text(encoding="utf-8")
    lenses = read_video_analysis_lenses(domains=["finance"])
    generated_at = datetime.now(UTC).isoformat()
    return f"""Extract finance-domain signals from this video semantics artifact.

Return only valid JSON. Do not wrap it in Markdown. Do not modify files.

Treat every trade or investment statement as a creator claim, not as advice from Seed.
If an instrument, action, horizon, price level, or evidence reference is missing, use null or an empty list instead of guessing.

Metadata:
- Title: {title or semantics_path.stem}
- Owner: {owner or "unknown"}
- Platform: {platform or "unknown"}
- Generated at: {generated_at}
- Semantics path: {semantics_path}

<analysis_lenses>
{lenses}
</analysis_lenses>

JSON schema:
{{
  "version": 1,
  "domain": "finance",
  "title": string,
  "owner": string,
  "platform": string,
  "generated_at": string,
  "basis_path": string,
  "not_investment_advice": true,
  "stance_summary": string,
  "instruments": [
    {{
      "name": string,
      "ticker": string | null,
      "market": string | null,
      "asset_class": string | null,
      "mentioned_as": string | null,
      "evidence_refs": [string]
    }}
  ],
  "recommendations": [
    {{
      "instrument": string,
      "action": "buy" | "sell" | "hold" | "watch" | "avoid" | "add" | "reduce" | "allocate" | "unknown",
      "direction": "bullish" | "bearish" | "neutral" | "mixed" | "unknown",
      "horizon": string | null,
      "conviction": "high" | "medium" | "low" | "unknown",
      "rationale": string,
      "price_levels": [string],
      "catalysts": [string],
      "risk_controls": [string],
      "evidence_refs": [string],
      "uncertainty": string | null
    }}
  ],
  "macro_theses": [
    {{
      "thesis": string,
      "variables": [string],
      "evidence_refs": [string],
      "uncertainty": string | null
    }}
  ],
  "methodology_signals": [
    {{
      "method": string,
      "decision_rule": string,
      "when_it_applies": string | null,
      "failure_modes": [string],
      "evidence_refs": [string]
    }}
  ],
  "risk_flags": [string],
  "evidence_gaps": [string]
}}

<video_semantics>
{semantics}
</video_semantics>
"""


def run_finance_signals_extraction(
    *,
    semantics_path: Path,
    output_path: Path,
    title: str | None = None,
    owner: str | None = None,
    platform: str | None = None,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    prompt = build_finance_signals_prompt(
        semantics_path=semantics_path,
        title=title,
        owner=owner,
        platform=platform,
    )
    return run_codex_prompt(
        prompt=prompt,
        output_path=output_path,
        model=model,
        cwd=cwd or Path.cwd(),
        dry_run=dry_run,
    )
