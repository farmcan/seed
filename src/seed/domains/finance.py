from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seed.agents.codex import run_codex_prompt
from seed.library import init_library, slugify
from seed.skill_refs import read_video_analysis_lenses

EVENT_PRICE_HORIZONS_DAYS = [1, 5, 20, 60]


def finance_signals_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "semantics" / f"{slugify(title)}.finance-signals.json"


def finance_digest_output_path(
    *,
    library_root: Path,
    owner: str,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> Path:
    init_library(library_root)
    window = finance_window_slug(published_after=published_after, published_before=published_before)
    return library_root / "distilled" / f"{slugify(owner)}.{window}.finance-digest.json"


def priced_finance_digest_output_path(*, digest_path: Path) -> Path:
    name = digest_path.name
    if name.endswith(".finance-digest.json"):
        return digest_path.with_name(name.replace(".finance-digest.json", ".finance-digest.priced.json"))
    return digest_path.with_suffix(".priced.json")


def news_context_finance_digest_output_path(*, digest_path: Path) -> Path:
    name = digest_path.name
    if name.endswith(".json"):
        return digest_path.with_name(name.removesuffix(".json") + ".news-context.json")
    return digest_path.with_suffix(".news-context.json")


def finance_window_slug(
    *,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> str:
    if not published_after and not published_before:
        return "all"
    after = date_slug(published_after) if published_after else "start"
    before = date_slug(published_before) if published_before else "now"
    return f"{after}-to-{before}"


def date_slug(value: datetime | None) -> str:
    if value is None:
        return "none"
    resolved = value if value.tzinfo else value.replace(tzinfo=UTC)
    return resolved.astimezone(UTC).strftime("%Y%m%d")


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
      "action": "buy" | "sell" | "hold" | "watch" | "avoid" | "add" | "reduce" | "allocate" | "don't buy" | "short sell" | "unknown",
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
  "viewpoint_events": [
    {{
      "event_id": string,
      "video_title": string,
      "published_at": string | null,
      "instrument": string,
      "ticker": string | null,
      "asset_class": string | null,
      "action": "buy" | "sell" | "hold" | "watch" | "avoid" | "add" | "reduce" | "allocate" | "don't buy" | "short sell" | "unknown",
      "direction": "bullish" | "bearish" | "neutral" | "mixed" | "unknown",
      "horizon": string | null,
      "conviction": "high" | "medium" | "low" | "unknown",
      "entry_condition": string | null,
      "exit_or_invalidation": string | null,
      "risk_flags": [string],
      "evidence_refs": [string],
      "timestamp_start": string | null,
      "timestamp_end": string | null,
      "modality_evidence": {{
        "transcript_refs": [string],
        "visual_refs": [string],
        "frame_refs": [string]
      }},
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


def load_finance_signals(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_finance_signal_files(*, library_root: Path, owner: str | None = None) -> list[Path]:
    semantics_dir = library_root / "semantics"
    if not semantics_dir.exists():
        return []
    paths = sorted(semantics_dir.glob("*.finance-signals.json"))
    if owner is None:
        return paths
    return [
        path
        for path in paths
        if (load_finance_signals(path).get("owner") or "").casefold() == owner.casefold()
    ]


def build_finance_digest_artifact(
    *,
    signal_paths: list[Path],
    owner: str,
    platform: str | None = None,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    video_metadata_by_title: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    metadata = video_metadata_by_title or {}
    records = [
        build_finance_digest_record(path, metadata_by_title=metadata)
        for path in signal_paths
        if path.exists()
    ]
    records = [
        record
        for record in records
        if record_matches_window(
            record,
            published_after=published_after,
            published_before=published_before,
        )
    ]
    recommendations = [
        {**recommendation, "video_title": record["title"], "signal_path": record["signal_path"]}
        for record in records
        for recommendation in record["recommendations"]
    ]
    viewpoint_events = [
        {**event, "video_title": event.get("video_title") or record["title"], "signal_path": record["signal_path"]}
        for record in records
        for event in record["viewpoint_events"]
    ]
    instruments = summarize_named_items(
        [instrument for record in records for instrument in record["instruments"]],
        name_key="name",
    )
    methodologies = summarize_named_items(
        [method for record in records for method in record["methodology_signals"]],
        name_key="method",
    )
    return {
        "version": 1,
        "kind": "finance_digest",
        "domain": "finance",
        "owner": owner,
        "platform": platform or infer_platform(records),
        "generated_at": datetime.now(UTC).isoformat(),
        "window": {
            "published_after": normalize_datetime(published_after),
            "published_before": normalize_datetime(published_before),
        },
        "not_investment_advice": True,
        "videos_analyzed": len(records),
        "signal_paths": [record["signal_path"] for record in records],
        "totals": {
            "instruments": len(instruments),
            "recommendations": len(recommendations),
            "viewpoint_events": len(viewpoint_events),
            "macro_theses": sum(len(record["macro_theses"]) for record in records),
            "methodology_signals": len(methodologies),
        },
        "instruments": instruments,
        "recommendations": recommendations,
        "viewpoint_events": viewpoint_events,
        "macro_theses": [
            {**thesis, "video_title": record["title"], "signal_path": record["signal_path"]}
            for record in records
            for thesis in record["macro_theses"]
        ],
        "methodology_signals": methodologies,
        "risk_flags": sorted({flag for record in records for flag in record["risk_flags"]}),
        "evidence_gaps": sorted({gap for record in records for gap in record["evidence_gaps"]}),
        "video_records": records,
    }


def build_finance_digest_record(
    path: Path,
    *,
    metadata_by_title: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    signals = load_finance_signals(path)
    title = str(signals.get("title") or path.stem.removesuffix(".finance-signals"))
    metadata = metadata_by_title.get(title, {})
    return {
        "title": title,
        "owner": signals.get("owner"),
        "platform": signals.get("platform"),
        "published_at": metadata.get("published_at"),
        "url": metadata.get("url"),
        "video_id": metadata.get("video_id"),
        "signal_path": str(path),
        "stance_summary": signals.get("stance_summary"),
        "instruments": signals.get("instruments") or [],
        "recommendations": signals.get("recommendations") or [],
        "viewpoint_events": signals.get("viewpoint_events")
        or build_legacy_viewpoint_events(
            title=title,
            recommendations=signals.get("recommendations") or [],
            instruments=signals.get("instruments") or [],
            published_at=metadata.get("published_at"),
        ),
        "macro_theses": signals.get("macro_theses") or [],
        "methodology_signals": signals.get("methodology_signals") or [],
        "risk_flags": signals.get("risk_flags") or [],
        "evidence_gaps": signals.get("evidence_gaps") or [],
    }


def build_legacy_viewpoint_events(
    *,
    title: str,
    recommendations: list[dict[str, Any]],
    instruments: list[dict[str, Any]],
    published_at: str | None,
) -> list[dict[str, Any]]:
    instrument_tickers = {
        str(item.get("name") or "").casefold(): item.get("ticker") for item in instruments
    }
    events: list[dict[str, Any]] = []
    for index, recommendation in enumerate(recommendations):
        instrument = str(recommendation.get("instrument") or "unknown").strip()
        events.append(
            {
                "event_id": f"{slugify(title)}-{slugify(instrument or 'unknown')}-{index + 1}",
                "video_title": title,
                "published_at": published_at,
                "instrument": instrument,
                "ticker": instrument_tickers.get(instrument.casefold()),
                "asset_class": None,
                "action": recommendation.get("action") or "unknown",
                "direction": recommendation.get("direction") or "unknown",
                "horizon": recommendation.get("horizon"),
                "conviction": recommendation.get("conviction") or "unknown",
                "entry_condition": recommendation.get("rationale"),
                "exit_or_invalidation": None,
                "risk_flags": recommendation.get("risk_controls") or [],
                "evidence_refs": recommendation.get("evidence_refs") or [],
                "timestamp_start": None,
                "timestamp_end": None,
                "modality_evidence": {
                    "transcript_refs": [],
                    "visual_refs": [],
                    "frame_refs": [],
                },
                "uncertainty": recommendation.get("uncertainty"),
            }
        )
    return events


def record_matches_window(
    record: dict[str, Any],
    *,
    published_after: datetime | None,
    published_before: datetime | None,
) -> bool:
    if published_after is None and published_before is None:
        return True
    published_at = parse_datetime(record.get("published_at"))
    if published_at is None:
        return False
    after = ensure_utc(published_after)
    before = ensure_utc(published_before)
    if after and published_at < after:
        return False
    if before and published_at >= before:
        return False
    return True


def summarize_named_items(items: list[dict[str, Any]], *, name_key: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in items:
        name = str(item.get(name_key) or item.get("instrument") or "unknown")
        key = name.casefold()
        current = grouped.setdefault(key, {name_key: name, "mentions": 0, "examples": []})
        current["mentions"] += 1
        if len(current["examples"]) < 5:
            current["examples"].append(item)
    return sorted(grouped.values(), key=lambda value: (-int(value["mentions"]), str(value[name_key])))


def infer_platform(records: list[dict[str, Any]]) -> str | None:
    platforms = [record.get("platform") for record in records if record.get("platform")]
    return str(platforms[0]) if platforms else None


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return ensure_utc(value)
    try:
        return ensure_utc(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
    except ValueError:
        return None


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def normalize_datetime(value: datetime | None) -> str | None:
    resolved = ensure_utc(value)
    return resolved.isoformat() if resolved else None


def write_finance_digest_artifact(path: Path, artifact: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def enrich_finance_digest_with_news_context(
    digest: dict[str, Any],
    *,
    news_digest_paths: list[Path],
    max_contexts_per_event: int = 5,
) -> dict[str, Any]:
    news_records = [
        build_news_context_record(path)
        for path in news_digest_paths
        if path.exists()
    ]
    enriched_events = [
        {
            **event,
            "news_context": match_news_context_for_event(
                event,
                news_records=news_records,
                max_contexts=max_contexts_per_event,
            ),
        }
        for event in digest.get("viewpoint_events") or []
    ]
    enriched = {
        **digest,
        "kind": finance_digest_news_context_kind(digest.get("kind")),
        "news_context": {
            "provider": "seed-deterministic-news-facts",
            "generated_at": datetime.now(UTC).isoformat(),
            "news_digest_paths": [str(path) for path in news_digest_paths],
            "matching_policy": "entity, ticker, instrument, sector, and fact_ref overlap",
            "not_investment_advice": True,
        },
        "viewpoint_events": enriched_events,
    }
    enriched["totals"] = {
        **(digest.get("totals") or {}),
        "news_digests": len(news_records),
        "events_with_news_context": sum(1 for event in enriched_events if event.get("news_context")),
        "news_context_matches": sum(len(event.get("news_context") or []) for event in enriched_events),
    }
    return enriched


def finance_digest_news_context_kind(kind: Any) -> str:
    text = str(kind or "finance_digest")
    if text.endswith("_with_news_context"):
        return text
    return f"{text}_with_news_context"


def build_news_context_record(path: Path) -> dict[str, Any]:
    artifact = json.loads(path.read_text(encoding="utf-8"))
    facts = {
        str(fact.get("fact_id") or f"fact-{index + 1}"): fact
        for index, fact in enumerate(artifact.get("facts") or [])
        if isinstance(fact, dict)
    }
    return {
        "path": str(path),
        "topic": artifact.get("topic") or artifact.get("query") or path.stem,
        "basis_path": artifact.get("basis_path"),
        "facts": facts,
        "industry_impacts": [
            item for item in artifact.get("industry_impacts") or [] if isinstance(item, dict)
        ],
        "market_relevance": [
            item for item in artifact.get("market_relevance") or [] if isinstance(item, dict)
        ],
        "source_gaps": artifact.get("source_gaps") or [],
        "open_questions": artifact.get("open_questions") or [],
    }


def match_news_context_for_event(
    event: dict[str, Any],
    *,
    news_records: list[dict[str, Any]],
    max_contexts: int,
) -> list[dict[str, Any]]:
    terms = event_match_terms(event)
    if not terms:
        return []
    matches = [
        context
        for context in (
            build_event_news_context(event_terms=terms, news_record=record)
            for record in news_records
        )
        if context.get("fact_refs") or context.get("industry_impacts") or context.get("market_relevance")
    ]
    matches.sort(key=lambda item: (-int(item.get("match_score") or 0), str(item.get("topic") or "")))
    return matches[:max_contexts]


def build_event_news_context(
    *,
    event_terms: list[str],
    news_record: dict[str, Any],
) -> dict[str, Any]:
    facts: dict[str, dict[str, Any]] = news_record.get("facts") or {}
    matched_facts: dict[str, dict[str, Any]] = {}
    matched_impacts = []
    matched_relevance = []
    matched_terms: set[str] = set()
    score = 0

    for fact_id, fact in facts.items():
        item_score, terms = score_news_item(
            event_terms,
            primary_values=fact.get("entities") or [],
            secondary_values=[fact.get("statement"), fact.get("evidence_notes")],
        )
        if item_score <= 0:
            continue
        matched_facts[fact_id] = fact
        matched_terms.update(terms)
        score += item_score

    for index, impact in enumerate(news_record.get("industry_impacts") or []):
        item_score, terms = score_news_item(
            event_terms,
            primary_values=[impact.get("industry"), *(impact.get("affected_entities") or [])],
            secondary_values=[impact.get("mechanism")],
        )
        if item_score <= 0:
            continue
        fact_refs = [str(ref) for ref in impact.get("fact_refs") or []]
        for ref in fact_refs:
            if ref in facts:
                matched_facts[ref] = facts[ref]
        matched_impacts.append(
            {
                "impact_id": f"industry-impact-{index + 1}",
                "industry": impact.get("industry"),
                "mechanism": impact.get("mechanism"),
                "possible_direction": impact.get("possible_direction"),
                "affected_entities": impact.get("affected_entities") or [],
                "fact_refs": fact_refs,
                "uncertainty": impact.get("uncertainty"),
            }
        )
        matched_terms.update(terms)
        score += item_score

    for index, relevance in enumerate(news_record.get("market_relevance") or []):
        item_score, terms = score_news_item(
            event_terms,
            primary_values=[relevance.get("asset_or_sector")],
            secondary_values=[relevance.get("relevance")],
        )
        if item_score <= 0:
            continue
        fact_refs = [str(ref) for ref in relevance.get("fact_refs") or []]
        for ref in fact_refs:
            if ref in facts:
                matched_facts[ref] = facts[ref]
        matched_relevance.append(
            {
                "relevance_id": f"market-relevance-{index + 1}",
                "asset_or_sector": relevance.get("asset_or_sector"),
                "relevance": relevance.get("relevance"),
                "fact_refs": fact_refs,
                "uncertainty": relevance.get("uncertainty"),
            }
        )
        matched_terms.update(terms)
        score += item_score

    source_urls = dedupe_preserve_order(
        [
            str(url)
            for fact in matched_facts.values()
            for url in fact.get("source_urls") or []
            if url
        ]
    )
    return {
        "topic": news_record.get("topic"),
        "news_digest_path": news_record.get("path"),
        "basis_path": news_record.get("basis_path"),
        "matched_terms": sorted(matched_terms),
        "match_score": score,
        "fact_refs": sorted(matched_facts),
        "facts": [compact_news_fact(fact_id, fact) for fact_id, fact in sorted(matched_facts.items())],
        "industry_impacts": matched_impacts,
        "market_relevance": matched_relevance,
        "source_urls": source_urls,
        "source_gaps": news_record.get("source_gaps") or [],
        "open_questions": news_record.get("open_questions") or [],
        "usage_note": "Factual context only; do not treat this as Seed investment advice.",
    }


def compact_news_fact(fact_id: str, fact: dict[str, Any]) -> dict[str, Any]:
    return {
        "fact_id": fact_id,
        "statement": fact.get("statement"),
        "status": fact.get("status"),
        "entities": fact.get("entities") or [],
        "source_urls": fact.get("source_urls") or [],
        "source_titles": fact.get("source_titles") or [],
        "uncertainty": fact.get("uncertainty"),
    }


def score_news_item(
    terms: list[str],
    *,
    primary_values: list[Any],
    secondary_values: list[Any],
) -> tuple[int, list[str]]:
    score = 0
    matched_terms: list[str] = []
    primary_text = " ".join(str(value) for value in primary_values if value)
    secondary_text = " ".join(str(value) for value in secondary_values if value)
    for term in terms:
        if text_contains_term(primary_text, term):
            score += 3
            matched_terms.append(term)
        elif text_contains_term(secondary_text, term):
            score += 1
            matched_terms.append(term)
    return score, dedupe_preserve_order(matched_terms)


def event_match_terms(event: dict[str, Any]) -> list[str]:
    raw_terms = [
        event.get("instrument"),
        event.get("ticker"),
        ticker_root(event.get("ticker")),
        event.get("asset_class"),
    ]
    terms = []
    for value in raw_terms:
        term = str(value or "").strip()
        if not term or is_generic_market_term(term):
            continue
        if len(term.encode("utf-8")) < 2:
            continue
        terms.append(term)
    return dedupe_preserve_order(terms)


def ticker_root(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    return re.split(r"[.:/\\-]", text, maxsplit=1)[0]


def is_generic_market_term(value: str) -> bool:
    return value.casefold() in {
        "stock",
        "stocks",
        "equity",
        "equities",
        "market",
        "markets",
        "fund",
        "etf",
        "index",
        "bond",
        "cash",
        "unknown",
    }


def text_contains_term(text: str, term: str) -> bool:
    if not text or not term:
        return False
    if term.isascii() and re.fullmatch(r"[A-Za-z0-9_.:/\\-]+", term):
        root = re.escape(term.casefold())
        return re.search(rf"(?<![a-z0-9]){root}(?![a-z0-9])", text.casefold()) is not None
    return normalize_match_text(term) in normalize_match_text(text)


def normalize_match_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def enrich_finance_digest_with_prices(
    digest: dict[str, Any],
    *,
    ticker_map: dict[str, str],
    benchmark_ticker: str | None = None,
    provider: str = "stooq",
) -> dict[str, Any]:
    if provider != "stooq":
        raise ValueError(f"Unsupported market data provider: {provider}")
    histories: dict[str, list[dict[str, Any]]] = {}

    def history_for(ticker: str | None) -> list[dict[str, Any]]:
        if not ticker:
            return []
        normalized = ticker.strip().lower()
        if normalized not in histories:
            histories[normalized] = fetch_stooq_daily_history(normalized)
        return histories[normalized]

    event_ticker_map = {
        str(event.get("instrument") or "").casefold(): event.get("ticker")
        for event in digest.get("viewpoint_events") or []
        if event.get("instrument") and event.get("ticker")
    }
    priced_recommendations = []
    for recommendation in digest.get("recommendations") or []:
        instrument = str(recommendation.get("instrument") or "")
        mapped = (
            event_ticker_map.get(instrument.casefold())
            or ticker_map.get(instrument)
            or ticker_map.get(instrument.casefold())
        )
        published_at = published_at_for_recommendation(digest, recommendation)
        market_data = build_market_data_record(
            ticker=mapped,
            published_at=published_at,
            history=history_for(mapped),
            benchmark_ticker=benchmark_ticker,
            benchmark_history=history_for(benchmark_ticker),
            provider=provider,
        )
        priced_recommendations.append(
            {
                **recommendation,
                "market_data": market_data,
                "ticker": mapped,
                "ticker_source": "event" if event_ticker_map.get(instrument.casefold()) else "mapping",
            }
        )

    priced_viewpoint_events = []
    for event in digest.get("viewpoint_events") or []:
        ticker = event.get("ticker")
        if not ticker:
            instrument = str(event.get("instrument") or "")
            ticker = ticker_map.get(instrument) or ticker_map.get(instrument.casefold())
        event_ticker_source = "map"
        if event.get("ticker"):
            event_ticker_source = "signal"
        elif instrument_ticker := event_ticker_map.get(str(event.get("instrument") or "").casefold()):
            event_ticker_source = "event"
            ticker = instrument_ticker
        published_at = parse_datetime(event.get("published_at"))
        if published_at is None:
            title = event.get("video_title")
            for record in digest.get("video_records") or []:
                if record.get("title") == title:
                    published_at = parse_datetime(record.get("published_at"))
                    break
        event_outcomes = build_market_data_outcomes(
            ticker=ticker,
            published_at=published_at,
            history=history_for(ticker),
            benchmark_ticker=benchmark_ticker,
            benchmark_history=history_for(benchmark_ticker),
            provider=provider,
        )
        priced_viewpoint_events.append(
            {
                **event,
                "ticker": ticker,
                "ticker_source": event_ticker_source if ticker else None,
                "event_outcomes": event_outcomes,
            }
        )

    enriched = {
        **digest,
        "kind": "priced_finance_digest",
        "market_data": {
            "provider": provider,
            "benchmark_ticker": benchmark_ticker,
            "ticker_map": ticker_map,
            "generated_at": datetime.now(UTC).isoformat(),
            "not_investment_advice": True,
        },
        "recommendations": priced_recommendations,
        "viewpoint_events": priced_viewpoint_events,
    }
    enriched["totals"] = {
        **(digest.get("totals") or {}),
        "priced_recommendations": sum(
            1
            for recommendation in priced_recommendations
            if recommendation.get("market_data", {}).get("status") == "priced"
        ),
        "priced_viewpoint_events": sum(
            1
            for event in priced_viewpoint_events
            if event.get("event_outcomes", {}).get("status") == "priced"
        ),
    }
    return enriched


def build_market_data_outcomes(
    *,
    ticker: str | None,
    published_at: datetime | None,
    history: list[dict[str, Any]],
    benchmark_ticker: str | None,
    benchmark_history: list[dict[str, Any]],
    provider: str,
) -> dict[str, Any]:
    if not ticker:
        return {"status": "missing_ticker", "provider": provider}
    if published_at is None:
        return {"status": "missing_published_at", "provider": provider, "ticker": ticker}
    if not history:
        return {"status": "no_price_history", "provider": provider, "ticker": ticker}

    publish_index = select_price_index_on_or_before(history, published_at)
    if publish_index is None:
        return {"status": "no_price_on_or_before_publish_date", "provider": provider, "ticker": ticker}

    latest_index = len(history) - 1
    outcomes: dict[str, Any] = {}
    for horizon_days in EVENT_PRICE_HORIZONS_DAYS:
        outcomes[f"{horizon_days}D"] = build_horizon_price_outcome(
            history=history,
            benchmark_history=benchmark_history,
            ticker=ticker,
            horizon_days=horizon_days,
            publish_index=publish_index,
            benchmark_ticker=benchmark_ticker,
            provider=provider,
        )

    latest_outcome = build_latest_price_outcome(
        ticker=ticker,
        history=history,
        benchmark_ticker=benchmark_ticker,
        benchmark_history=benchmark_history,
        publish_index=publish_index,
        latest_index=latest_index,
        provider=provider,
    )
    return {
        "status": "priced",
        "provider": provider,
        "ticker": ticker,
        "horizons": outcomes,
        "latest": latest_outcome,
    }


def build_horizon_price_outcome(
    *,
    history: list[dict[str, Any]],
    benchmark_history: list[dict[str, Any]],
    ticker: str,
    horizon_days: int,
    publish_index: int,
    benchmark_ticker: str | None,
    provider: str,
) -> dict[str, Any]:
    target_index = publish_index + horizon_days
    if target_index >= len(history):
        return {
            "horizon_days": horizon_days,
            "status": "insufficient_history",
            "provider": provider,
            "ticker": ticker,
            "published_price_date": history[publish_index]["date"],
        }

    published = history[publish_index]
    target = history[target_index]
    asset_return = percent_change(float(published["close"]), float(target["close"]))
    max_drawdown = compute_max_drawdown(history[publish_index : target_index + 1])
    benchmark_return = None
    relative_return = None
    if benchmark_ticker and benchmark_history:
        benchmark_publish_index = select_price_index_on_or_before(
            benchmark_history,
            datetime.fromisoformat(published["date"] + "T00:00:00+00:00"),
        )
        if benchmark_publish_index is not None:
            benchmark_target_index = select_price_index_or_last(
                benchmark_history,
                benchmark_publish_index + horizon_days,
            )
            benchmark_published = benchmark_history[benchmark_publish_index]
            benchmark_target = benchmark_history[benchmark_target_index]
            benchmark_return = percent_change(
                float(benchmark_published["close"]),
                float(benchmark_target["close"]),
            )
            relative_return = round(asset_return - benchmark_return, 4)

    return {
        "horizon_days": horizon_days,
        "status": "priced",
        "provider": provider,
        "ticker": ticker,
        "published_price_date": published["date"],
        "target_price_date": target["date"],
        "trading_days": target_index - publish_index,
        "asset_return": asset_return,
        "max_drawdown": max_drawdown,
        "benchmark_return": benchmark_return,
        "relative_return": relative_return,
        "source_url": stooq_daily_csv_url(ticker),
    }


def build_latest_price_outcome(
    *,
    ticker: str,
    history: list[dict[str, Any]],
    benchmark_ticker: str | None,
    benchmark_history: list[dict[str, Any]],
    publish_index: int,
    latest_index: int,
    provider: str,
) -> dict[str, Any]:
    published = history[publish_index]
    latest = history[latest_index]
    return {
        "status": "priced",
        "provider": provider,
        "ticker": ticker,
        "published_price_date": published["date"],
        "latest_price_date": latest["date"],
        "trading_days": latest_index - publish_index,
        "asset_return": percent_change(float(published["close"]), float(latest["close"])),
        "max_drawdown": compute_max_drawdown(history[publish_index : latest_index + 1]),
        "source_url": stooq_daily_csv_url(ticker),
    }


def build_market_data_record(
    *,
    ticker: str | None,
    published_at: datetime | None,
    history: list[dict[str, Any]],
    benchmark_ticker: str | None,
    benchmark_history: list[dict[str, Any]],
    provider: str,
) -> dict[str, Any]:
    if not ticker:
        return {"status": "missing_ticker", "provider": provider}
    if published_at is None:
        return {"status": "missing_published_at", "provider": provider, "ticker": ticker}
    if not history:
        return {"status": "no_price_history", "provider": provider, "ticker": ticker}
    entry = select_price_on_or_before(history, published_at)
    latest = history[-1]
    if not entry:
        return {"status": "no_price_on_or_before_publish_date", "provider": provider, "ticker": ticker}
    benchmark = None
    if benchmark_ticker and benchmark_history:
        benchmark_entry = select_price_on_or_before(benchmark_history, published_at)
        benchmark_latest = benchmark_history[-1]
        if benchmark_entry:
            benchmark_return = percent_change(
                float(benchmark_entry["close"]),
                float(benchmark_latest["close"]),
            )
            benchmark = {
                "ticker": benchmark_ticker,
                "published_close": benchmark_entry["close"],
                "published_price_date": benchmark_entry["date"],
                "latest_close": benchmark_latest["close"],
                "latest_price_date": benchmark_latest["date"],
                "return_pct": benchmark_return,
            }
    asset_return = percent_change(float(entry["close"]), float(latest["close"]))
    return {
        "status": "priced",
        "provider": provider,
        "ticker": ticker,
        "published_at": published_at.isoformat(),
        "published_close": entry["close"],
        "published_price_date": entry["date"],
        "latest_close": latest["close"],
        "latest_price_date": latest["date"],
        "return_pct": asset_return,
        "benchmark": benchmark,
        "relative_return_pct": round(asset_return - benchmark["return_pct"], 4)
        if benchmark
        else None,
        "source_url": stooq_daily_csv_url(ticker),
    }


def published_at_for_recommendation(
    digest: dict[str, Any],
    recommendation: dict[str, Any],
) -> datetime | None:
    title = recommendation.get("video_title")
    for record in digest.get("video_records") or []:
        if record.get("title") == title:
            return parse_datetime(record.get("published_at"))
    return None


def fetch_stooq_daily_history(ticker: str) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        stooq_daily_csv_url(ticker),
        headers={"User-Agent": "seed/0.1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read().decode("utf-8", errors="replace")
    return parse_stooq_daily_csv(content)


def stooq_daily_csv_url(ticker: str) -> str:
    query = urllib.parse.urlencode({"s": ticker.lower(), "i": "d"})
    return f"https://stooq.com/q/d/l/?{query}"


def yahoo_chart_url(ticker: str, *, range_: str = "3y", interval: str = "1d") -> str:
    query = urllib.parse.urlencode({"range": range_, "interval": interval})
    return f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker.upper())}?{query}"


def fetch_yahoo_chart_history(
    ticker: str,
    *,
    range_: str = "3y",
    interval: str = "1d",
) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        yahoo_chart_url(ticker, range_=range_, interval=interval),
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 seed/0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read().decode("utf-8", errors="replace")
    return parse_yahoo_chart_json(content)


def parse_yahoo_chart_json(content: str) -> list[dict[str, Any]]:
    data = json.loads(content)
    result = ((data.get("chart") or {}).get("result") or [None])[0]
    if not isinstance(result, dict):
        return []
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators") or {}
    quote = (indicators.get("quote") or [None])[0]
    if not isinstance(quote, dict):
        return []

    rows: list[dict[str, Any]] = []
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    for index, timestamp in enumerate(timestamps):
        open_price = _optional_float(opens[index] if index < len(opens) else None)
        high_price = _optional_float(highs[index] if index < len(highs) else None)
        low_price = _optional_float(lows[index] if index < len(lows) else None)
        close_price = _optional_float(closes[index] if index < len(closes) else None)
        if open_price is None or high_price is None or low_price is None or close_price is None:
            continue
        row: dict[str, Any] = {
            "date": datetime.fromtimestamp(int(timestamp), UTC).date().isoformat(),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
        }
        volume = _optional_int(volumes[index] if index < len(volumes) else None)
        if volume is not None:
            row["volume"] = volume
        rows.append(row)
    return rows


def parse_stooq_daily_csv(content: str) -> list[dict[str, Any]]:
    rows = []
    for line in content.splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 5 or parts[0].lower() == "no data":
            continue
        try:
            row: dict[str, Any] = {
                "date": parts[0],
                "open": float(parts[1]),
                "high": float(parts[2]),
                "low": float(parts[3]),
                "close": float(parts[4]),
            }
            if len(parts) > 5 and parts[5]:
                row["volume"] = int(float(parts[5]))
            rows.append(row)
        except ValueError:
            continue
    return rows


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def select_price_on_or_before(
    history: list[dict[str, Any]],
    published_at: datetime,
) -> dict[str, Any] | None:
    target = ensure_utc(published_at).date()
    eligible = [
        row
        for row in history
        if datetime.fromisoformat(str(row["date"])).date() <= target
    ]
    return eligible[-1] if eligible else None


def select_price_index_on_or_before(
    history: list[dict[str, Any]],
    published_at: datetime,
) -> int | None:
    target = ensure_utc(published_at).date()
    latest_index: int | None = None
    for index, row in enumerate(history):
        row_date = datetime.fromisoformat(str(row["date"])).date()
        if row_date <= target:
            latest_index = index
        else:
            break
    return latest_index


def select_price_index_or_last(history: list[dict[str, Any]], index: int) -> int | None:
    if not history or index < 0:
        return None
    if index < len(history):
        return index
    return len(history) - 1


def compute_max_drawdown(price_rows: list[dict[str, Any]]) -> float | None:
    if len(price_rows) <= 1:
        return 0.0
    start_price = float(price_rows[0]["close"])
    if start_price == 0:
        return 0.0
    min_price = min(float(row["close"]) for row in price_rows)
    return round(((min_price - start_price) / start_price) * 100, 4)


def percent_change(start: float, end: float) -> float:
    if start == 0:
        return 0.0
    return round(((end - start) / start) * 100, 4)
