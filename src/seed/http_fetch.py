from __future__ import annotations

import hashlib
import json
import random
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, request

FetchQuality = dict[str, Any]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _cache_file(cache_root: Path, url: str) -> Path:
    cache_root.mkdir(parents=True, exist_ok=True)
    return cache_root / f"{_cache_key(url)}.json"


def _read_cache(cache_path: Path, ttl_seconds: int) -> tuple[Any, int, int] | None:
    if not cache_path.exists():
        return None

    try:
        envelope = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(envelope, dict):
        return None

    payload = envelope.get("payload")
    fetched_at = envelope.get("fetched_at")
    status = int(envelope.get("status", 200) or 200)
    if payload is None or not isinstance(fetched_at, str):
        return None

    try:
        age_seconds = int((datetime.now(UTC) - datetime.fromisoformat(fetched_at)).total_seconds())
    except Exception:
        return None

    if ttl_seconds > 0 and age_seconds > ttl_seconds:
        return None

    return payload, status, age_seconds


def _should_retry(exc: Exception) -> bool:
    if isinstance(exc, error.HTTPError):
        return exc.code in {429, 500, 502, 503, 504, 520, 521, 522, 524}
    return isinstance(exc, (error.URLError, TimeoutError))


def _build_quality(
    *,
    url: str,
    status: int,
    cache_hit: bool,
    retry_count: int,
    fetched_at: str,
    age_seconds: int,
    payload_size: int,
    ttl_seconds: int,
) -> FetchQuality:
    confidence = 0.0
    if 200 <= status < 300:
        confidence += 0.55
    if not cache_hit:
        confidence += 0.20
    if retry_count == 0:
        confidence += 0.15
    else:
        confidence -= min(0.1 * retry_count, 0.25)
    if payload_size > 0:
        confidence += 0.10
    confidence = round(max(0.0, min(1.0, confidence)), 3)

    return {
        "url": url,
        "source": "cache" if cache_hit else "network",
        "cache_hit": cache_hit,
        "http_status": status,
        "status": "ok" if 200 <= status < 300 else f"http_{status}",
        "retry_count": retry_count,
        "fetched_at": fetched_at,
        "payload_age_seconds": age_seconds,
        "payload_size": payload_size,
        "cache_ttl_seconds": ttl_seconds,
        "confidence": confidence,
        "confidence_band": "high" if confidence >= 0.8 else "medium" if confidence >= 0.55 else "low",
    }


def fetch_json_with_cache(
    *,
    url: str,
    headers: dict[str, str] | None = None,
    cache_root: Path | None = None,
    cache_ttl_seconds: int = 3600,
    timeout: int = 30,
    max_retries: int = 3,
    backoff_seconds: float = 0.8,
) -> tuple[Any, FetchQuality]:
    if cache_root is None:
        cache_root = Path("library/.cache/http")

    cache_file = _cache_file(cache_root, url)
    cached = _read_cache(cache_file, ttl_seconds=cache_ttl_seconds)
    if cached is not None:
        payload, status, age_seconds = cached
        quality = _build_quality(
            url=url,
            status=status,
            cache_hit=True,
            retry_count=0,
            fetched_at=_utc_now(),
            age_seconds=age_seconds,
            payload_size=len(json.dumps(payload).encode("utf-8")),
            ttl_seconds=cache_ttl_seconds,
        )
        return payload, quality

    request_headers = {"Accept": "application/json"}
    request_headers.update(headers or {})

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            req = request.Request(url, headers=request_headers)
            with request.urlopen(req, timeout=timeout) as response:
                payload_bytes = response.read()
                payload_size = len(payload_bytes)
                payload = json.loads(payload_bytes.decode("utf-8", errors="replace"))
                status = int(getattr(response, "status", 200) or 200)
            fetched_at = _utc_now()
            payload_age_seconds = 0
            quality = _build_quality(
                url=url,
                status=status,
                cache_hit=False,
                retry_count=attempt,
                fetched_at=fetched_at,
                age_seconds=payload_age_seconds,
                payload_size=payload_size,
                ttl_seconds=cache_ttl_seconds,
            )
            cache_file.write_text(
                json.dumps(
                    {
                        "url": url,
                        "status": status,
                        "fetched_at": fetched_at,
                        "payload": payload,
                        "payload_size": payload_size,
                        "payload_source": "network",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return payload, quality
        except Exception as error:
            last_error = error
            if not _should_retry(error) or attempt >= max_retries:
                break
            sleep_seconds = backoff_seconds * (2**attempt)
            sleep_seconds += random.uniform(0.0, min(0.8, backoff_seconds))
            time.sleep(sleep_seconds)

    if isinstance(last_error, error.HTTPError):
        status = int(last_error.code or 0)
    else:
        status = 0

    quality = _build_quality(
        url=url,
        status=status,
        cache_hit=False,
        retry_count=max_retries,
        fetched_at=_utc_now(),
        age_seconds=0,
        payload_size=0,
        ttl_seconds=cache_ttl_seconds,
    )
    quality["source"] = "failed"
    quality["status"] = "failed"
    quality["error"] = str(last_error) if last_error else "unknown"
    raise RuntimeError(f"failed to fetch {url}: {quality['error']}")
