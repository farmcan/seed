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
    sources = [
        fetch_evidence_source(url) if fetch_sources else evidence_source_stub(url)
        for url in evidence_urls or []
    ]
    status = (
        DEFAULT_VERIFICATION_STATUS_WITH_SOURCES
        if sources
        else DEFAULT_VERIFICATION_STATUS_WITHOUT_SOURCES
    )
    return {
        "title": claims_artifact.get("title") or claims_path.stem,
        "created_at": datetime.now(UTC).isoformat(),
        "claims_path": str(claims_path),
        "verification_method": "source-recording",
        "sources": sources,
        "claims": [
            {
                **claim,
                "status": status,
                "verification": {
                    "status": status,
                    "sources": [source["url"] for source in sources],
                    "checked_at": datetime.now(UTC).isoformat(),
                    "rationale": verification_rationale(sources),
                },
            }
            for claim in claims_artifact.get("claims", [])
        ],
    }


def write_verified_claims_artifact(path: Path, artifact: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


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
        "Automatic contradiction/support judgment is not implemented yet, so status remains unclear."
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
