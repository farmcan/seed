from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seed.agents.codex import run_codex_prompt
from seed.library import init_library, slugify
from seed.skill_refs import read_video_analysis_lenses
from seed.http_fetch import fetch_json_with_cache


SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
DEFAULT_SEC_USER_AGENT = "seed/0.1 local-research set-SEED_SEC_USER_AGENT"
DEFAULT_SEC_CACHE_TTL_SECONDS = 3600 * 12
EARNINGS_PARSER_SKILL_PATH = Path("skills/earnings-parser/SKILL.md")

IMPORTANT_CONCEPTS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "gross_profit": ["GrossProfit"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "diluted_eps": ["EarningsPerShareDiluted"],
    "basic_eps": ["EarningsPerShareBasic"],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "capital_expenditure": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "assets": ["Assets"],
    "liabilities": ["Liabilities"],
    "equity": ["StockholdersEquity"],
}

UNIT_PRIORITY = ["USD", "USD/shares", "shares", "pure"]


def earnings_artifact_output_path(*, library_root: Path, identifier: str) -> Path:
    init_library(library_root)
    return library_root / "earnings" / f"{slugify(identifier)}.sec-earnings.json"


def earnings_digest_output_path(*, library_root: Path, identifier: str) -> Path:
    init_library(library_root)
    return library_root / "distilled" / f"{slugify(identifier)}.earnings-digest.json"


def earnings_analysis_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "semantics" / f"{slugify(title)}.earnings-analysis.json"


def resolve_sec_user_agent(user_agent: str | None = None) -> str:
    return user_agent or os.environ.get("SEED_SEC_USER_AGENT") or DEFAULT_SEC_USER_AGENT


def normalize_cik(value: str | int) -> str:
    text = str(value).strip().upper().removeprefix("CIK")
    if not text.isdigit():
        raise ValueError(f"CIK must be numeric: {value}")
    return text.zfill(10)


def sec_submissions_url(cik: str) -> str:
    return SEC_SUBMISSIONS_URL.format(cik=normalize_cik(cik))


def sec_companyfacts_url(cik: str) -> str:
    return SEC_COMPANYFACTS_URL.format(cik=normalize_cik(cik))


def sec_filing_index_url(*, cik: str, accession_number: str) -> str:
    normalized_cik = str(int(normalize_cik(cik)))
    accession_no_dash = accession_number.replace("-", "")
    return (
        "https://www.sec.gov/Archives/edgar/data/"
        f"{normalized_cik}/{accession_no_dash}/{accession_number}-index.html"
    )


def fetch_sec_json(
    url: str,
    *,
    user_agent: str | None = None,
    cache_root: Path | None = None,
    cache_ttl_seconds: int = DEFAULT_SEC_CACHE_TTL_SECONDS,
    max_retries: int = 3,
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload, quality = fetch_json_with_cache(
        url=url,
        headers={"User-Agent": resolve_sec_user_agent(user_agent), "Accept": "application/json"},
        cache_root=cache_root,
        cache_ttl_seconds=cache_ttl_seconds,
        max_retries=max_retries,
        timeout=30,
    )
    return payload if isinstance(payload, dict) else {}, quality


def fetch_company_tickers(
    *,
    user_agent: str | None = None,
    cache_root: Path | None = None,
    cache_ttl_seconds: int = DEFAULT_SEC_CACHE_TTL_SECONDS,
    max_retries: int = 3,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload, quality = fetch_sec_json(
        SEC_COMPANY_TICKERS_URL,
        user_agent=user_agent,
        cache_root=cache_root,
        cache_ttl_seconds=cache_ttl_seconds,
        max_retries=max_retries,
    )
    rows: list[dict[str, Any]] = []
    for item in payload.values():
        if isinstance(item, dict):
            rows.append(
                {
                    "cik": normalize_cik(item.get("cik_str", "")),
                    "ticker": str(item.get("ticker") or "").upper(),
                    "title": item.get("title"),
                }
            )
    return rows, quality


def resolve_company_identifier(
    identifier: str,
    *,
    company_tickers: list[dict[str, Any]] | None = None,
    user_agent: str | None = None,
    cache_root: Path | None = None,
    cache_ttl_seconds: int = DEFAULT_SEC_CACHE_TTL_SECONDS,
    max_retries: int = 3,
) -> tuple[dict[str, Any], dict[str, Any]]:
    text = identifier.strip()
    if text.upper().startswith("CIK") or text.isdigit():
        return {"cik": normalize_cik(text), "ticker": None, "title": None}, {
            "provider": "input",
            "status": "ok",
        }

    lookup_quality: dict[str, Any] = {"provider": "sec-company-tickers", "status": "ok"}
    rows = company_tickers
    if rows is None:
        rows, lookup_quality = fetch_company_tickers(
            user_agent=user_agent,
            cache_root=cache_root,
            cache_ttl_seconds=cache_ttl_seconds,
            max_retries=max_retries,
        )
    for row in rows:
        if str(row.get("ticker") or "").upper() == text.upper():
            return row, lookup_quality
    raise ValueError(f"Could not resolve ticker to SEC CIK: {identifier}")


def fetch_sec_earnings_artifact(
    *,
    identifier: str,
    forms: list[str] | None = None,
    filing_limit: int = 10,
    user_agent: str | None = None,
    cache_root: Path | None = None,
    cache_ttl_seconds: int = DEFAULT_SEC_CACHE_TTL_SECONDS,
    max_retries: int = 3,
) -> dict[str, Any]:
    company, company_lookup_quality = resolve_company_identifier(
        identifier,
        user_agent=user_agent,
        cache_root=cache_root,
        cache_ttl_seconds=cache_ttl_seconds,
        max_retries=max_retries,
    )
    cik = company["cik"]
    submissions, submissions_quality = fetch_sec_json(
        sec_submissions_url(cik),
        user_agent=user_agent,
        cache_root=cache_root,
        cache_ttl_seconds=cache_ttl_seconds,
        max_retries=max_retries,
    )
    companyfacts, companyfacts_quality = fetch_sec_json(
        sec_companyfacts_url(cik),
        user_agent=user_agent,
        cache_root=cache_root,
        cache_ttl_seconds=cache_ttl_seconds,
        max_retries=max_retries,
    )
    return build_sec_earnings_artifact(
        identifier=identifier,
        company=company,
        submissions=submissions,
        companyfacts=companyfacts,
        source_quality={
            "submissions": submissions_quality,
            "companyfacts": companyfacts_quality,
            "company_tickers": company_lookup_quality,
        },
        forms=forms,
        filing_limit=filing_limit,
    )


def build_sec_earnings_artifact(
    *,
    identifier: str,
    company: dict[str, Any],
    submissions: dict[str, Any],
    companyfacts: dict[str, Any],
    source_quality: dict[str, Any] | None = None,
    forms: list[str] | None = None,
    filing_limit: int = 10,
) -> dict[str, Any]:
    cik = normalize_cik(company.get("cik") or submissions.get("cik"))
    recent_filings = recent_filings_from_submissions(
        submissions,
        forms=forms or ["10-Q", "10-K", "8-K"],
        limit=filing_limit,
    )
    for filing in recent_filings:
        filing["index_url"] = sec_filing_index_url(
            cik=cik,
            accession_number=str(filing["accession_number"]),
        )
    return {
        "version": 1,
        "kind": "sec_earnings",
        "provider": "sec-edgar",
        "identifier": identifier,
        "company": {
            "cik": cik,
            "ticker": company.get("ticker"),
            "title": company.get("title") or submissions.get("name"),
            "entity_type": submissions.get("entityType"),
            "sic": submissions.get("sic"),
            "sic_description": submissions.get("sicDescription"),
            "fiscal_year_end": submissions.get("fiscalYearEnd"),
        },
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": {
            "submissions_url": sec_submissions_url(cik),
            "companyfacts_url": sec_companyfacts_url(cik),
            "company_tickers_url": SEC_COMPANY_TICKERS_URL,
        },
        "source_quality": source_quality or {},
        "recent_filings": recent_filings,
        "financial_facts": extract_financial_concepts(companyfacts),
    }


def recent_filings_from_submissions(
    submissions: dict[str, Any],
    *,
    forms: list[str],
    limit: int = 10,
) -> list[dict[str, Any]]:
    recent = (submissions.get("filings") or {}).get("recent") or {}
    accessions = recent.get("accessionNumber") or []
    result: list[dict[str, Any]] = []
    wanted = {form.upper() for form in forms}
    for index, accession in enumerate(accessions):
        form = value_at(recent, "form", index)
        if wanted and str(form or "").upper() not in wanted:
            continue
        result.append(
            {
                "accession_number": accession,
                "form": form,
                "filing_date": value_at(recent, "filingDate", index),
                "report_date": value_at(recent, "reportDate", index),
                "acceptance_datetime": value_at(recent, "acceptanceDateTime", index),
                "primary_document": value_at(recent, "primaryDocument", index),
                "primary_doc_description": value_at(recent, "primaryDocDescription", index),
            }
        )
        if len(result) >= limit:
            break
    return result


def value_at(mapping: dict[str, Any], key: str, index: int) -> Any:
    values = mapping.get(key) or []
    if not isinstance(values, list) or index >= len(values):
        return None
    return values[index]


def extract_financial_concepts(companyfacts: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    facts = companyfacts.get("facts") or {}
    extracted: dict[str, list[dict[str, Any]]] = {}
    for metric, tags in IMPORTANT_CONCEPTS.items():
        rows: list[dict[str, Any]] = []
        for taxonomy in ("us-gaap", "ifrs-full"):
            concepts = facts.get(taxonomy) or {}
            for tag in tags:
                if tag not in concepts:
                    continue
                rows.extend(normalize_concept_units(concepts[tag], taxonomy=taxonomy, tag=tag))
        rows.sort(key=lambda row: (str(row.get("filed") or ""), str(row.get("end") or "")), reverse=True)
        if rows:
            extracted[metric] = rows[:8]
    return extracted


def normalize_concept_units(
    concept: dict[str, Any],
    *,
    taxonomy: str,
    tag: str,
) -> list[dict[str, Any]]:
    units = concept.get("units") or {}
    rows: list[dict[str, Any]] = []
    for unit in sorted(units, key=unit_sort_key):
        unit_rows = units.get(unit) or []
        for item in unit_rows:
            if not isinstance(item, dict) or "val" not in item:
                continue
            rows.append(
                {
                    "taxonomy": taxonomy,
                    "tag": tag,
                    "label": concept.get("label"),
                    "description": concept.get("description"),
                    "unit": unit,
                    "value": item.get("val"),
                    "fy": item.get("fy"),
                    "fp": item.get("fp"),
                    "form": item.get("form"),
                    "filed": item.get("filed"),
                    "end": item.get("end"),
                    "frame": item.get("frame"),
                    "accession_number": item.get("accn"),
                }
            )
    return rows


def unit_sort_key(unit: str) -> int:
    try:
        return UNIT_PRIORITY.index(unit)
    except ValueError:
        return len(UNIT_PRIORITY)


def build_earnings_distillation_prompt(*, earnings_artifact_path: Path) -> str:
    artifact = json.loads(earnings_artifact_path.read_text(encoding="utf-8"))
    skill = read_optional_text(EARNINGS_PARSER_SKILL_PATH)
    return f"""Parse this SEC earnings artifact into a factual earnings digest.

Return only valid JSON. Do not wrap it in Markdown. Do not modify files.

Use the SEC artifact as source of truth. Separate reported facts from inference and keep market relevance factual. Do not make investment recommendations.

Input artifact path: {earnings_artifact_path}

<earnings_parser_skill>
{skill}
</earnings_parser_skill>

JSON schema:
{{
  "version": 1,
  "kind": "earnings_digest",
  "provider": "sec-edgar",
  "company": {{
    "cik": string,
    "ticker": string | null,
    "title": string | null
  }},
  "generated_at": string,
  "basis_path": string,
  "latest_filings": [
    {{
      "form": string,
      "filing_date": string | null,
      "report_date": string | null,
      "accession_number": string,
      "source_url": string
    }}
  ],
  "financial_snapshot": [
    {{
      "metric": string,
      "value": number | string,
      "unit": string,
      "period": string | null,
      "filed": string | null,
      "form": string | null,
      "source_accession": string | null,
      "uncertainty": string | null
    }}
  ],
  "fact_summary": [string],
  "changes_and_drivers": [
    {{
      "statement": string,
      "basis_metrics": [string],
      "uncertainty": string | null
    }}
  ],
  "industry_implications": [
    {{
      "industry": string,
      "mechanism": string,
      "possible_direction": "positive" | "negative" | "mixed" | "unclear",
      "uncertainty": string | null
    }}
  ],
  "source_gaps": [string],
  "open_questions": [string],
  "not_investment_advice": true
}}

<sec_earnings_artifact>
{json.dumps(artifact, ensure_ascii=False, indent=2)}
</sec_earnings_artifact>
"""


def run_earnings_distillation(
    *,
    earnings_artifact_path: Path,
    output_path: Path,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    prompt = build_earnings_distillation_prompt(earnings_artifact_path=earnings_artifact_path)
    return run_codex_prompt(
        prompt=prompt,
        output_path=output_path,
        model=model,
        cwd=cwd or Path.cwd(),
        dry_run=dry_run,
    )


def build_earnings_semantics_prompt(
    *,
    semantics_path: Path,
    title: str | None = None,
    owner: str | None = None,
    platform: str | None = None,
) -> str:
    semantics = semantics_path.read_text(encoding="utf-8")
    lenses = read_video_analysis_lenses(domains=["earnings"])
    generated_at = datetime.now(UTC).isoformat()
    return f"""Extract earnings-related claims from this video semantics artifact.

Return only valid JSON. Do not wrap it in Markdown. Do not modify files.

Treat all company or financial statements as claims from the creator until verified against filings or primary sources.

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
  "kind": "video_earnings_analysis",
  "domain": "earnings",
  "title": string,
  "owner": string,
  "platform": string,
  "generated_at": string,
  "basis_path": string,
  "companies": [
    {{
      "name": string,
      "ticker": string | null,
      "cik": string | null,
      "evidence_refs": [string],
      "uncertainty": string | null
    }}
  ],
  "earnings_claims": [
    {{
      "claim": string,
      "metric": string | null,
      "period": string | null,
      "direction": "up" | "down" | "flat" | "mixed" | "unknown",
      "evidence_refs": [string],
      "needs_sec_verification": true,
      "uncertainty": string | null
    }}
  ],
  "drivers": [
    {{
      "driver": string,
      "company_or_industry": string | null,
      "evidence_refs": [string],
      "uncertainty": string | null
    }}
  ],
  "risks": [string],
  "source_gaps": [string]
}}

<video_semantics>
{semantics}
</video_semantics>
"""


def run_earnings_analysis_extraction(
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
    prompt = build_earnings_semantics_prompt(
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


def write_earnings_artifact(path: Path, artifact: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_optional_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
