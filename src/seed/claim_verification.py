from __future__ import annotations

import json
import re
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify


DEFAULT_VERIFICATION_STATUS_WITH_SOURCES = "unclear"
DEFAULT_VERIFICATION_STATUS_WITHOUT_SOURCES = "unverified"
CONTRADICTION_MARKERS = {
    "false",
    "incorrect",
    "not true",
    "contradict",
    "contradicted",
    "misleading",
    "辟谣",
    "不实",
    "错误",
    "并非",
    "没有证据",
}


def verified_claims_output_path(
    *,
    library_root: Path,
    claims_path: Path,
    title: str | None = None,
) -> Path:
    init_library(library_root)
    name = slugify(title or claims_path.stem.removesuffix(".claims"))
    return library_root / "claims" / f"{name}.verified.json"


def build_verified_claims_artifact(
    *,
    claims_path: Path,
    evidence_urls: list[str] | None = None,
    fetch_sources: bool = True,
) -> dict[str, Any]:
    claims_artifact = json.loads(claims_path.read_text(encoding="utf-8"))
    claims = claims_artifact.get("claims", [])
    sources = [
        fetch_evidence_source(url) if fetch_sources else evidence_source_stub(url)
        for url in evidence_urls or []
    ]
    stages = build_verification_stages(claims=claims, sources=sources)
    verdicts_by_id = {verdict["claim_id"]: verdict for verdict in stages["verdicts"]}
    return {
        "title": claims_artifact.get("title") or claims_path.stem,
        "created_at": datetime.now(UTC).isoformat(),
        "claims_path": str(claims_path),
        "verification_method": "staged-source-heuristic",
        "sources": sources,
        "stages": stages,
        "claims": [
            verified_claim_record(claim, verdicts_by_id.get(claim_id(claim)), sources)
            for claim in claims
        ],
    }


def build_verification_stages(
    *,
    claims: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    source_scores = [score_source(source) for source in sources]
    evidence_snippets = [
        snippet
        for claim in claims
        for snippet in evidence_snippets_for_claim(claim=claim, sources=sources)
    ]
    return {
        "claim_decomposition": [decompose_claim(claim) for claim in claims],
        "query_plan": [query_plan_for_claim(claim) for claim in claims],
        "evidence_snippets": evidence_snippets,
        "source_scores": source_scores,
        "verdicts": [
            verdict_for_claim(
                claim=claim,
                snippets=[snippet for snippet in evidence_snippets if snippet["claim_id"] == claim_id(claim)],
                source_scores=source_scores,
                has_sources=bool(sources),
            )
            for claim in claims
        ],
    }


def verified_claim_record(
    claim: dict[str, Any],
    verdict: dict[str, Any] | None,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    status = verdict["status"] if verdict else DEFAULT_VERIFICATION_STATUS_WITHOUT_SOURCES
    return {
        **claim,
        "status": status,
        "verification": {
            "status": status,
            "sources": [source["url"] for source in sources],
            "checked_at": datetime.now(UTC).isoformat(),
            "confidence": verdict.get("confidence", "none") if verdict else "none",
            "rationale": verdict.get("rationale", verification_rationale(sources)) if verdict else verification_rationale(sources),
            "evidence_refs": verdict.get("evidence_refs", []) if verdict else [],
        },
    }


def decompose_claim(claim: dict[str, Any]) -> dict[str, Any]:
    text = claim_text(claim)
    terms = important_terms(text)
    return {
        "claim_id": claim_id(claim),
        "text": text,
        "terms": terms,
        "source_section": claim.get("source_section"),
    }


def query_plan_for_claim(claim: dict[str, Any]) -> dict[str, Any]:
    text = claim_text(claim)
    terms = important_terms(text)
    queries = [text]
    if terms:
        queries.append(" ".join(terms[:8]))
    if claim.get("source_section"):
        queries.append(f"{claim['source_section']} {text}")
    return {
        "claim_id": claim_id(claim),
        "queries": dedupe_preserve_order(queries),
        "required_evidence": ["external source", "source excerpt", "uncertainty note"],
    }


def evidence_snippets_for_claim(
    *,
    claim: dict[str, Any],
    sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    text = claim_text(claim)
    terms = important_terms(text)
    snippets = []
    for source in sources:
        source_text = compact_text(" ".join([str(source.get("title") or ""), str(source.get("summary") or "")]))
        if not source_text:
            continue
        matched = [term for term in terms if term.lower() in source_text.lower()]
        overlap = len(matched) / max(len(terms), 1)
        exact = normalize_text(text) in normalize_text(source_text)
        if not exact and overlap < 0.2:
            continue
        snippets.append(
            {
                "claim_id": claim_id(claim),
                "source_url": source["url"],
                "snippet": best_snippet(source_text, matched or terms),
                "matched_terms": matched,
                "overlap_score": round(overlap, 3),
                "exact_match": exact,
                "contradiction_marker": contains_contradiction_marker(source_text),
            }
        )
    return snippets


def score_source(source: dict[str, Any]) -> dict[str, Any]:
    url = str(source.get("url") or "")
    score = 0.2
    reasons = []
    if source.get("fetch_status") == "ok":
        score += 0.3
        reasons.append("fetched")
    if url.startswith("https://"):
        score += 0.1
        reasons.append("https")
    if re.search(r"\.(gov|edu|mil)(/|$)", url):
        score += 0.2
        reasons.append("institutional-domain")
    if source.get("title"):
        score += 0.1
        reasons.append("title")
    if source.get("summary"):
        score += 0.1
        reasons.append("summary")
    return {
        "source_url": url,
        "score": round(min(score, 1.0), 3),
        "reasons": reasons or ["stub"],
    }


def verdict_for_claim(
    *,
    claim: dict[str, Any],
    snippets: list[dict[str, Any]],
    source_scores: list[dict[str, Any]],
    has_sources: bool,
) -> dict[str, Any]:
    if not has_sources:
        return {
            "claim_id": claim_id(claim),
            "status": DEFAULT_VERIFICATION_STATUS_WITHOUT_SOURCES,
            "confidence": "none",
            "evidence_refs": [],
            "rationale": "No external evidence source was provided; claim remains unverified.",
        }
    if not snippets:
        return {
            "claim_id": claim_id(claim),
            "status": DEFAULT_VERIFICATION_STATUS_WITH_SOURCES,
            "confidence": "low",
            "evidence_refs": [],
            "rationale": "External sources were recorded, but no relevant evidence snippet was extracted.",
        }

    score_by_url = {item["source_url"]: item["score"] for item in source_scores}
    best = max(snippets, key=lambda item: (item["exact_match"], item["overlap_score"], score_by_url.get(item["source_url"], 0)))
    evidence_refs = [f"{snippet['source_url']}#snippet-{index + 1}" for index, snippet in enumerate(snippets[:3])]
    if best["contradiction_marker"] and best["overlap_score"] >= 0.4:
        return {
            "claim_id": claim_id(claim),
            "status": "contradicted",
            "confidence": "medium",
            "evidence_refs": evidence_refs,
            "rationale": "A relevant source snippet contains contradiction markers near matched claim terms.",
        }
    if best["exact_match"] or (best["overlap_score"] >= 0.6 and score_by_url.get(best["source_url"], 0) >= 0.6):
        return {
            "claim_id": claim_id(claim),
            "status": "supported",
            "confidence": "medium",
            "evidence_refs": evidence_refs,
            "rationale": "A relevant external source snippet substantially overlaps with the claim.",
        }
    return {
        "claim_id": claim_id(claim),
        "status": DEFAULT_VERIFICATION_STATUS_WITH_SOURCES,
        "confidence": "low",
        "evidence_refs": evidence_refs,
        "rationale": "Some relevant evidence was found, but it is insufficient for supported or contradicted.",
    }


def write_verified_claims_artifact(path: Path, artifact: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def claim_id(claim: dict[str, Any]) -> str:
    return str(claim.get("id") or slugify(claim_text(claim)) or "claim")


def claim_text(claim: dict[str, Any]) -> str:
    return str(claim.get("text") or claim.get("claim") or "")


def important_terms(text: str) -> list[str]:
    terms = re.findall(r"[\w\u4e00-\u9fff]{2,}", text.lower())
    stopwords = {
        "the",
        "and",
        "that",
        "with",
        "from",
        "this",
        "claim",
        "因为",
        "所以",
        "一个",
        "这个",
        "以及",
        "可以",
    }
    return dedupe_preserve_order([term for term in terms if term not in stopwords])[:16]


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def best_snippet(text: str, terms: list[str], *, max_length: int = 500) -> str:
    if not text:
        return ""
    lower = text.lower()
    positions = [lower.find(term.lower()) for term in terms if term and lower.find(term.lower()) >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - max_length // 3)
    return text[start : start + max_length].strip()


def contains_contradiction_marker(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in CONTRADICTION_MARKERS)


def fetch_evidence_source(url: str) -> dict[str, Any]:
    accessed_at = datetime.now(UTC).isoformat()
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "seed-claim-verifier/0.1"})
        with urllib.request.urlopen(request, timeout=10) as response:
            content_type = response.headers.get("content-type", "")
            raw = response.read(200_000)
        text = raw.decode("utf-8", errors="ignore")
        return {
            "url": url,
            "accessed_at": accessed_at,
            "content_type": content_type,
            "title": extract_html_title(text),
            "summary": compact_text(strip_html(text))[:1200],
            "fetch_status": "ok",
        }
    except Exception as error:
        source = evidence_source_stub(url)
        source["accessed_at"] = accessed_at
        source["fetch_status"] = "failed"
        source["error"] = str(error)
        return source


def evidence_source_stub(url: str) -> dict[str, Any]:
    return {
        "url": url,
        "accessed_at": datetime.now(UTC).isoformat(),
        "content_type": None,
        "title": None,
        "summary": "",
        "fetch_status": "not_fetched",
    }


def verification_rationale(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "No external evidence source was provided; claim remains unverified."
    fetched = sum(1 for source in sources if source.get("fetch_status") == "ok")
    return (
        f"Recorded {len(sources)} external evidence source(s), {fetched} fetched successfully. "
        "Staged verification requires relevant snippets before upgrading a claim status."
    )


def extract_html_title(text: str) -> str | None:
    match = re.search(r"<title[^>]*>(?P<title>.*?)</title>", text, flags=re.I | re.S)
    if not match:
        return None
    return compact_text(strip_html(match.group("title"))) or None


def strip_html(text: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?</style>", " ", text)
    return re.sub(r"(?s)<[^>]+>", " ", text)


def compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
