from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seed.agents.codex import run_codex_prompt
from seed.library import init_library, slugify
from seed.skill_refs import read_video_analysis_lenses


GDELT_DOC_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
FACTS_DISTILLER_SKILL_PATH = Path("skills/facts-distiller/SKILL.md")


def news_search_output_path(
    *,
    library_root: Path,
    query: str,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> Path:
    init_library(library_root)
    return library_root / "news" / f"{slugify(query)}.{news_window_slug(published_after=published_after, published_before=published_before)}.news-search.json"


def news_digest_output_path(
    *,
    library_root: Path,
    topic: str,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> Path:
    init_library(library_root)
    return library_root / "distilled" / f"{slugify(topic)}.{news_window_slug(published_after=published_after, published_before=published_before)}.news-digest.json"


def news_facts_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "semantics" / f"{slugify(title)}.news-facts.json"


def news_window_slug(
    *,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> str:
    if not published_after and not published_before:
        return "recent"
    after = date_slug(published_after) if published_after else "start"
    before = date_slug(published_before) if published_before else "now"
    return f"{after}-to-{before}"


def date_slug(value: datetime | None) -> str:
    if value is None:
        return "none"
    resolved = value if value.tzinfo else value.replace(tzinfo=UTC)
    return resolved.astimezone(UTC).strftime("%Y%m%d")


def build_gdelt_doc_url(
    *,
    query: str,
    max_records: int = 25,
    timespan: str | None = "1week",
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    sort: str = "datedesc",
) -> str:
    params: dict[str, str] = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": str(max(1, min(max_records, 250))),
        "sort": sort,
    }
    if published_after:
        params["startdatetime"] = gdelt_datetime(published_after)
    if published_before:
        params["enddatetime"] = gdelt_datetime(published_before)
    if timespan and not (published_after or published_before):
        params["timespan"] = timespan
    return f"{GDELT_DOC_API_URL}?{urllib.parse.urlencode(params)}"


def gdelt_datetime(value: datetime) -> str:
    resolved = value if value.tzinfo else value.replace(tzinfo=UTC)
    return resolved.astimezone(UTC).strftime("%Y%m%d%H%M%S")


def fetch_gdelt_news(
    *,
    query: str,
    max_records: int = 25,
    timespan: str | None = "1week",
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    sort: str = "datedesc",
) -> dict[str, Any]:
    source_url = build_gdelt_doc_url(
        query=query,
        max_records=max_records,
        timespan=timespan,
        published_after=published_after,
        published_before=published_before,
        sort=sort,
    )
    request = urllib.request.Request(source_url, headers={"User-Agent": "seed/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    articles = payload.get("articles") if isinstance(payload, dict) else []
    return {
        "source_url": source_url,
        "articles": normalize_gdelt_articles(articles if isinstance(articles, list) else []),
    }


def normalize_gdelt_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for article in articles:
        normalized.append(
            {
                "title": article.get("title"),
                "url": article.get("url"),
                "mobile_url": article.get("url_mobile") or article.get("mobileurl"),
                "domain": article.get("domain"),
                "language": article.get("language"),
                "source_country": article.get("sourcecountry"),
                "published_at": article.get("seendate"),
                "social_image": article.get("socialimage"),
                "provider": "gdelt-doc-2.0",
            }
        )
    return normalized


def build_news_search_artifact(
    *,
    query: str,
    articles: list[dict[str, Any]],
    source_url: str,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    provider: str = "gdelt-doc-2.0",
) -> dict[str, Any]:
    return {
        "version": 1,
        "kind": "news_search",
        "provider": provider,
        "query": query,
        "source_url": source_url,
        "generated_at": datetime.now(UTC).isoformat(),
        "window": {
            "published_after": normalize_datetime(published_after),
            "published_before": normalize_datetime(published_before),
        },
        "article_count": len(articles),
        "articles": articles,
    }


def build_news_facts_prompt(
    *,
    news_artifact_path: Path,
    topic: str | None = None,
    focus: str | None = None,
) -> str:
    artifact = json.loads(news_artifact_path.read_text(encoding="utf-8"))
    skill = read_optional_text(FACTS_DISTILLER_SKILL_PATH)
    resolved_topic = topic or str(artifact.get("query") or news_artifact_path.stem)
    return f"""Distill factual news coverage into a source-grounded facts ledger.

Return only valid JSON. Do not wrap it in Markdown. Do not modify files.

The output must summarize facts, reported claims, uncertainty, and source coverage. Keep analysis separate from facts. Do not write recommendations, political opinions, or trading advice.

Topic: {resolved_topic}
Focus: {focus or "general factual summary"}
Input artifact path: {news_artifact_path}

<facts_distiller_skill>
{skill}
</facts_distiller_skill>

JSON schema:
{{
  "version": 1,
  "kind": "news_facts_digest",
  "topic": string,
  "generated_at": string,
  "basis_path": string,
  "source_count": number,
  "facts": [
    {{
      "fact_id": string,
      "statement": string,
      "status": "confirmed" | "reported" | "disputed" | "unclear",
      "source_urls": [string],
      "source_titles": [string],
      "first_seen": string | null,
      "latest_seen": string | null,
      "entities": [string],
      "evidence_notes": string,
      "uncertainty": string | null
    }}
  ],
  "reported_claims": [
    {{
      "claim": string,
      "attributed_to": string | null,
      "source_urls": [string],
      "status": "reported" | "disputed" | "unclear",
      "uncertainty": string | null
    }}
  ],
  "industry_impacts": [
    {{
      "industry": string,
      "mechanism": string,
      "possible_direction": "positive" | "negative" | "mixed" | "unclear",
      "affected_entities": [string],
      "fact_refs": [string],
      "uncertainty": string | null
    }}
  ],
  "market_relevance": [
    {{
      "asset_or_sector": string,
      "relevance": string,
      "fact_refs": [string],
      "uncertainty": string | null
    }}
  ],
  "source_gaps": [string],
  "open_questions": [string],
  "summary": string
}}

<news_search_artifact>
{json.dumps(artifact, ensure_ascii=False, indent=2)}
</news_search_artifact>
"""


def run_news_facts_distillation(
    *,
    news_artifact_path: Path,
    output_path: Path,
    topic: str | None = None,
    focus: str | None = None,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    prompt = build_news_facts_prompt(news_artifact_path=news_artifact_path, topic=topic, focus=focus)
    return run_codex_prompt(
        prompt=prompt,
        output_path=output_path,
        model=model,
        cwd=cwd or Path.cwd(),
        dry_run=dry_run,
    )


def build_news_semantics_prompt(
    *,
    semantics_path: Path,
    title: str | None = None,
    owner: str | None = None,
    platform: str | None = None,
) -> str:
    semantics = semantics_path.read_text(encoding="utf-8")
    lenses = read_video_analysis_lenses(domains=["news"])
    generated_at = datetime.now(UTC).isoformat()
    return f"""Extract factual news claims from this video semantics artifact.

Return only valid JSON. Do not wrap it in Markdown. Do not modify files.

Separate factual claims, reported claims, creator interpretation, and evidence gaps. The output is a facts queue, not an opinion essay.

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
  "kind": "video_news_facts",
  "domain": "news",
  "title": string,
  "owner": string,
  "platform": string,
  "generated_at": string,
  "basis_path": string,
  "facts": [
    {{
      "fact_id": string,
      "statement": string,
      "status": "stated_in_video" | "reported" | "unclear",
      "entities": [string],
      "evidence_refs": [string],
      "needs_external_verification": true,
      "uncertainty": string | null
    }}
  ],
  "interpretations": [
    {{
      "interpretation": string,
      "creator_attribution": string,
      "evidence_refs": [string],
      "uncertainty": string | null
    }}
  ],
  "industry_impacts": [
    {{
      "industry": string,
      "mechanism": string,
      "possible_direction": "positive" | "negative" | "mixed" | "unclear",
      "evidence_refs": [string],
      "uncertainty": string | null
    }}
  ],
  "source_gaps": [string],
  "open_questions": [string]
}}

<video_semantics>
{semantics}
</video_semantics>
"""


def run_news_facts_extraction(
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
    prompt = build_news_semantics_prompt(
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


def write_news_artifact(path: Path, artifact: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def normalize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    resolved = value if value.tzinfo else value.replace(tzinfo=UTC)
    return resolved.astimezone(UTC).isoformat()


def read_optional_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
