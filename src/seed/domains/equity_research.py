"""Equity research and financial statement structuring helpers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from seed.agents.codex import run_codex_prompt
from seed.library import init_library, slugify


EQUITY_RESEARCH_ANALYZER_SKILL_PATH = Path("skills/equity-research-report-analyzer/SKILL.md")
FINANCIAL_STATEMENT_REVIEWER_SKILL_PATH = Path("skills/financial-statement-reviewer/SKILL.md")


def equity_research_note_output_path(
    *,
    library_root: Path,
    report_path: Path,
    report_id: str | None = None,
) -> Path:
    init_library(library_root)
    stem = report_id or report_path.stem
    return library_root / "notes" / f"{slugify(stem)}.research-note.md"


def equity_research_output_path(*, library_root: Path, report_path: Path, report_id: str | None = None) -> Path:
    init_library(library_root)
    stem = report_id or report_path.stem
    return library_root / "semantics" / f"{slugify(stem)}.equity-research.json"


def financial_statement_review_output_path(*, library_root: Path, identifier: str) -> Path:
    init_library(library_root)
    return library_root / "distilled" / f"{slugify(identifier)}.financial-statement-review.json"


def read_optional_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_equity_research_note_prompt(
    *,
    report_path: Path,
    report_id: str | None = None,
    skill_path: Path = EQUITY_RESEARCH_ANALYZER_SKILL_PATH,
    issuer: str | None = None,
    ticker: str | None = None,
    report_date: str | None = None,
) -> str:
    report_text = report_path.read_text(encoding="utf-8")
    skill = read_optional_text(skill_path)
    generated_at = datetime.now(UTC).isoformat()
    return f"""Use the following equity research analysis skill to extract grounded notes from the report.

Return only final markdown notes. Do not wrap in Markdown code block.

Output notes are used as input for structured claim parsing; keep section references and source locations as much as possible.

Metadata:
- Report id: {report_id or report_path.stem}
- Issuer: {issuer or "unknown"}
- Ticker: {ticker or "unknown"}
- Report date: {report_date or "unknown"}
- Generated at: {generated_at}
- Report path: {report_path}

<equity_research_analyzer_skill>
{skill}
</equity_research_analyzer_skill>

<report>
{report_text}
</report>
"""


def run_equity_research_note_extraction(
    *,
    report_path: Path,
    output_path: Path,
    skill_path: Path = EQUITY_RESEARCH_ANALYZER_SKILL_PATH,
    title: str | None = None,
    issuer: str | None = None,
    ticker: str | None = None,
    report_date: str | None = None,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    prompt = build_equity_research_note_prompt(
        report_path=report_path,
        report_id=title or report_path.stem,
        skill_path=skill_path,
        issuer=issuer,
        ticker=ticker,
        report_date=report_date,
    )
    return run_codex_prompt(
        prompt=prompt,
        output_path=output_path,
        model=model,
        cwd=cwd or Path.cwd(),
        dry_run=dry_run,
    )


def build_equity_research_json_prompt(
    *,
    report_path: Path,
    note_path: Path,
    title: str | None = None,
    issuer: str | None = None,
    ticker: str | None = None,
    report_date: str | None = None,
    skill_path: Path = EQUITY_RESEARCH_ANALYZER_SKILL_PATH,
) -> str:
    notes = note_path.read_text(encoding="utf-8")
    skill = read_optional_text(skill_path)
    generated_at = datetime.now(UTC).isoformat()
    return f"""Convert the notes into a structured equity research claim ledger.

Return only valid JSON. Do not wrap it in Markdown.

This ledger tracks only creator/analyst claims, evidence refs and uncertainty, and is not a trading signal.

Do not infer missing numbers or exact ratios. For missing data, use null/[]/空字符串，不要猜测缺失指标。

Metadata:
- Report id: {title or report_path.stem}
- Issuer: {issuer or "unknown"}
- Ticker: {ticker or "unknown"}
- Report date: {report_date or "unknown"}
- Report path: {report_path}
- Generated at: {generated_at}
- Notes path: {note_path}

<equity_research_analyzer_skill>
{skill}
</equity_research_analyzer_skill>

JSON schema:
{
  "version": 1,
  "kind": "equity_research_ledger",
  "not_investment_advice": true,
  "report": {
    "issuer": string,
    "ticker": string | null,
    "report_id": string,
    "report_date": string | null,
    "as_of_date": string | null,
    "rating": string | null,
    "target_price_range": string | null
  },
  "basis": {
    "notes_path": string,
    "report_path": string
  },
  "viewpoint_events": [
    {
      "claim": string,
      "support": [string],
      "support_refs": [string],
      "evidence_level": "reported" | "modeled" | "weakly_supported" | "uncertain" | "conflicted",
      "conviction": "high" | "medium" | "low" | "unknown",
      "horizon": string | null,
      "exit_or_invalidation": string | null,
      "risk_flags": [string],
      "open_questions": [string],
      "uncertainty": string | null
    }
  ],
  "first_principles": {
    "business_model": string | null,
    "revenue_logic": string | null,
    "core_differentiators": string | null,
    "competitors": [string],
    "competitive_pressure": string | null,
    "customer_dependency": string | null,
    "single_customer_risk": string | null,
    "aicoding_or_automation_risk": string | null,
    "overseas_revenue_ratio": string | null,
    "internationalization_progress": string | null,
    "internationalization_notes": [string],
    "ecosystem_implications": {
      "tooling_or_platform_playbooks": [string],
      "model_company_implication": string | null,
      "compute_or_hardware_signal": string | null,
      "model_or_chip_companies_to_watch": [string],
      "spillover_uncertainties": [string]
    },
    "first_principles_uncertainties": [string]
  },
  "source_gaps": [string],
  "open_questions": [string],
  "notes_summary": string
}

<research_note>
{notes}
</research_note>
"""


def run_equity_research_json_extraction(
    *,
    report_path: Path,
    note_path: Path,
    output_path: Path,
    title: str | None = None,
    issuer: str | None = None,
    ticker: str | None = None,
    report_date: str | None = None,
    skill_path: Path = EQUITY_RESEARCH_ANALYZER_SKILL_PATH,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    prompt = build_equity_research_json_prompt(
        report_path=report_path,
        note_path=note_path,
        title=title,
        issuer=issuer,
        ticker=ticker,
        report_date=report_date,
        skill_path=skill_path,
    )
    return run_codex_prompt(
        prompt=prompt,
        output_path=output_path,
        model=model,
        cwd=cwd or Path.cwd(),
        dry_run=dry_run,
    )


def build_financial_statement_review_prompt(
    *,
    sec_earnings_path: Path,
    identifier: str,
) -> str:
    artifact = json.loads(sec_earnings_path.read_text(encoding="utf-8"))
    skill = read_optional_text(FINANCIAL_STATEMENT_REVIEWER_SKILL_PATH)
    return f"""Review SEC/financial statement artifacts for accounting-grounded signals.

Return only valid JSON. Do not wrap it in Markdown.

Input artifact path: {sec_earnings_path}

<financial_statement_reviewer_skill>
{skill}
</financial_statement_reviewer_skill>

JSON schema:
{
  "version": 1,
  "kind": "financial_statement_review",
  "company": {
    "cik": string | null,
    "ticker": string | null,
    "title": string | null
  },
  "not_investment_advice": true,
  "fiscal_period": string | null,
  "period": string | null,
  "currency": string | null,
  "unit": string | null,
  "report_type": string | null,
  "publish_date": string | null,
  "income_statement": object,
  "balance_sheet": object,
  "cash_flow": object,
  "segment_data": object,
  "evidence_gaps": [string],
  "inconsistencies": [string],
  "open_questions": [string],
  "basis": {
    "source_path": string
  }
}

<sec_earnings_artifact>
{json.dumps(artifact, ensure_ascii=False, indent=2)}
</sec_earnings_artifact>
"""


def run_financial_statement_review(
    *,
    sec_earnings_path: Path,
    output_path: Path,
    identifier: str,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    prompt = build_financial_statement_review_prompt(
        sec_earnings_path=sec_earnings_path,
        identifier=identifier,
    )
    return run_codex_prompt(
        prompt=prompt,
        output_path=output_path,
        model=model,
        cwd=cwd or Path.cwd(),
        dry_run=dry_run,
    )
