from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any

from seed.library import init_library, slugify

AIGC_KEYWORDS = [
    "aigc",
    "ai",
    "llm",
    "大模型",
    "生成式",
    "生成模型",
    "agent",
    "自动化",
    "算力",
    "saa",
    "sasa",
    "云计算",
    "软件",
    "gpu",
    "芯片",
    "推理",
    "content",
    "多模态",
]

SOFTWARE_KEYWORDS = [
    "软件",
    "software",
    "saas",
    "enterprise",
    "crm",
    "erp",
    "平台",
    "SaaS",
]

AIGC_PRODUCTION_KEYWORDS = [
    "算力",
    "训练",
    "finetune",
    "推理",
    "token",
    "模型",
    "模型参数",
    "部署",
    "gpu",
    "api",
    "框架",
]

AIGC_USAGE_KEYWORDS = [
    "内容生产",
    "内容生成",
    "自动化",
    "生产率",
    "效率",
    "工作流",
    "运营",
    "客服",
    "研发",
    "创作",
]

AICODING_KEYWORDS = [
    "aicoding",
    "ai coding",
    "coding agent",
    "代码",
    "编程",
    "代码生成",
    "代码助手",
    "开发工具",
    "开发壁垒",
    "claude",
    "cursor",
    "copilot",
    "swe-agent",
    "自动编程",
]


def _collect_event_text(event: dict[str, Any]) -> str:
    fields: list[Any] = [
        event.get("action"),
        event.get("direction"),
        event.get("entry_condition"),
        event.get("uncertainty"),
        event.get("thesis"),
        event.get("summary"),
        event.get("analysis"),
        event.get("notes"),
        event.get("title"),
        event.get("description"),
        event.get("observation"),
        event.get("content"),
        event.get("insight"),
    ]
    risk_flags = event.get("risk_flags")
    if isinstance(risk_flags, list):
        fields.extend(str(flag) for flag in risk_flags if isinstance(flag, str))
    for key in ("event_outcomes", "news_context"):
        nested = event.get(key)
        if isinstance(nested, dict):
            for item in nested.values():
                if isinstance(item, str):
                    fields.append(item)
                elif isinstance(item, dict):
                    fields.append(_collect_event_text(item))
        elif isinstance(nested, list):
            for item in nested:
                if isinstance(item, dict):
                    for value in item.values():
                        if isinstance(value, str):
                            fields.append(value)
                        elif isinstance(value, list):
                            fields.extend(str(v) for v in value if isinstance(v, str))
    return " ".join(str(item) for item in fields if isinstance(item, str))


def _build_aicoding_impact_signals(
    events: list[dict[str, Any]],
    *,
    has_software_context: bool,
    has_aicoding_context: bool,
) -> list[str]:
    event_text = " ".join(_collect_event_text(event) for event in events).casefold()
    if (
        not has_software_context
        and not has_aicoding_context
    ) or not _contains_any_keyword(event_text, AICODING_KEYWORDS):
        return []

    statements = [
        "AI Coding（如 Claude Code、Cursor、Copilot 等）使部分软件开发工时和交付壁垒下降，倾向削弱传统“人力服务型”软件增速与毛利。",
        "结构上更可能是从“交付效率提升”转向“产品化能力差异化”竞争，受益者往往是平台化、订阅化和生态闭环强的公司。",
        "该变量需要与财报证据联动验证：人均毛利变化、项目工时占比、自动化后的人力替代率、定价与续费是否同步改善。",
    ]
    return statements


def _contains_software_context(
    events: list[dict[str, Any]],
    digest: dict[str, Any],
    peer_context: dict[str, Any],
) -> bool:
    chunks: list[Any] = []
    chunks.append(peer_context.get("industry"))
    chunks.append(digest.get("industry"))
    chunks.append(digest.get("sector"))
    chunks.extend(str(item) for item in peer_context.get("peers") or [])
    for thesis in digest.get("macro_theses") or []:
        if isinstance(thesis, dict):
            chunks.append(thesis.get("industry"))
            chunks.append(thesis.get("thesis"))
            chunks.extend(thesis.get("variables") or [])
        elif isinstance(thesis, str):
            chunks.append(thesis)
    for event in events:
        chunks.extend(event.get(key) for key in ("industry", "sector", "aigc_sector", "analysis"))
    context_text = " ".join(str(item) for item in chunks if isinstance(item, str))
    if not context_text:
        context_text = " ".join(_collect_event_text(event) for event in events)
    return _contains_any_keyword(context_text, SOFTWARE_KEYWORDS)


def _contains_aicoding_context(digest: dict[str, Any]) -> bool:
    digest_text = " ".join(
        str(item)
        for item in [
            digest.get("owner"),
            digest.get("industry"),
            digest.get("sector"),
            str(digest.get("peer_context") or ""),
            str(digest.get("methodology_signals") or ""),
        ]
        if isinstance(item, str)
    )
    return _contains_any_keyword(digest_text, AICODING_KEYWORDS)


def finance_outlook_output_path(*, library_root: Path, digest_path: Path) -> Path:
    init_library(library_root)
    name = digest_path.name
    for suffix in (
        ".finance-digest.priced.news-context.json",
        ".finance-digest.news-context.json",
        ".finance-digest.priced.json",
        ".finance-digest.json",
        ".json",
    ):
        if name.endswith(suffix):
            name = name.removesuffix(suffix)
            break
    return library_root / "reports" / f"{slugify(name)}.finance-outlook-report.html"


def finance_outlook_payload_output_path(
    *, library_root: Path, digest_path: Path
) -> Path:
    init_library(library_root)
    name = digest_path.name
    for suffix in (
        ".finance-digest.priced.news-context.json",
        ".finance-digest.news-context.json",
        ".finance-digest.priced.json",
        ".finance-digest.json",
        ".json",
    ):
        if name.endswith(suffix):
            name = name.removesuffix(suffix)
            break
    return library_root / "distilled" / f"{slugify(name)}.finance-outlook.json"


def find_owner_finance_outlook_report_paths(
    *,
    library_root: Path,
    owner: str,
) -> list[Path]:
    reports = library_root / "reports"
    if not reports.exists():
        return []
    prefix = slugify(owner)
    return sorted(reports.glob(f"{prefix}*.finance-outlook-report.html"))


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _conviction_weight(value: Any) -> float:
    if not isinstance(value, str):
        return 0.5
    text = value.strip().casefold()
    if text in {"high", "强", "strong"}:
        return 1.0
    if text in {"medium", "中"}:
        return 0.7
    if text in {"low", "低", "weak"}:
        return 0.4
    return 0.5


def _extract_event_outcome_metrics(event: dict[str, Any]) -> dict[str, Any]:
    outcome = event.get("event_outcomes") or {}
    latest = outcome.get("latest") if isinstance(outcome, dict) else None
    horizons = outcome.get("horizons") if isinstance(outcome, dict) else None

    latest_return = _to_float(latest.get("asset_return") if isinstance(latest, dict) else None)
    latest_drawdown = _to_float(latest.get("max_drawdown") if isinstance(latest, dict) else None)

    horizon_values: dict[str, float | None] = {}
    if isinstance(horizons, dict):
        for key, item in horizons.items():
            if not isinstance(item, dict):
                continue
            horizon_values[key] = _to_float(item.get("asset_return"))

    up_candidates: list[float] = [
        value for value in horizon_values.values() if value is not None and value > 0
    ]
    down_candidates: list[float] = [
        value for value in horizon_values.values() if value is not None and value < 0
    ]

    upside = max(up_candidates) if up_candidates else None
    downside = min(down_candidates) if down_candidates else None

    risk_reward = None
    if upside is not None and downside is not None and downside < 0:
        risk_reward = round(upside / abs(downside), 2)

    status = outcome.get("status") if isinstance(outcome, dict) else None
    return {
        "status": status,
        "horizon_returns": horizon_values,
        "latest_return": latest_return,
        "latest_drawdown": latest_drawdown,
        "upside": upside,
        "downside": downside,
        "risk_reward": risk_reward,
    }


def _collect_text_tokens(event: dict[str, Any]) -> list[str]:
    fields = [
        event.get("action"),
        event.get("direction"),
        event.get("entry_condition"),
        event.get("risk_flags"),
        event.get("uncertainty"),
    ]
    texts: list[str] = []
    for item in fields:
        if isinstance(item, str):
            texts.append(item)
    risk_flags = event.get("risk_flags")
    if isinstance(risk_flags, list):
        texts.extend(str(flag) for flag in risk_flags if isinstance(flag, str))
    return texts


def _contains_aigc_signal(text: str) -> bool:
    normalized = text.casefold()
    return any(term in normalized for term in AIGC_KEYWORDS)


def _contains_any_keyword(text: str, keywords: list[str]) -> bool:
    normalized = text.casefold()
    return any(term in normalized for term in keywords)


def _extract_matching_terms(text: str, keywords: list[str]) -> list[str]:
    normalized = text.casefold()
    return sorted({term for term in keywords if term in normalized})


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _peer_context_from_digest(digest: dict[str, Any]) -> dict[str, Any]:
    peer_context_block = digest.get("peer_context")
    if isinstance(peer_context_block, dict):
        raw_peers = (
            peer_context_block.get("peers")
            or peer_context_block.get("peer_assets")
            or peer_context_block.get("comparable_assets")
            or []
        )
        target_asset = peer_context_block.get("target_asset")
        target_ticker = peer_context_block.get("target_ticker")
        industry = peer_context_block.get("industry")
        notes = peer_context_block.get("peer_notes")
    else:
        raw_peers = (
            digest.get("peer_assets")
            or digest.get("peers")
            or digest.get("comparable_assets")
            or []
        )
        target_asset = digest.get("target_asset") or digest.get("asset") or digest.get("instrument")
        target_ticker = digest.get("target_ticker")
        industry = digest.get("industry")
        notes = digest.get("peer_notes")

    peers: list[dict[str, Any]] = []
    if isinstance(raw_peers, list):
        for item in raw_peers:
            if isinstance(item, str):
                peers.append({"name": item.strip()})
            elif isinstance(item, dict):
                name = item.get("name") or item.get("ticker") or item.get("symbol")
                if isinstance(name, str) and name.strip():
                    peers.append(
                        {
                            "name": name.strip(),
                            "ticker": str(item.get("ticker") or "").strip() or None,
                            "relation": item.get("relation") or item.get("type"),
                            "note": item.get("note") or item.get("rationale"),
                        }
                    )

    if not isinstance(notes, list):
        notes = None

    return {
        "target_asset": target_asset,
        "target_ticker": target_ticker,
        "industry": industry,
        "peers": peers,
        "notes": notes,
    }


def _build_time_coverage(events: list[dict[str, Any]]) -> dict[str, Any]:
    times: list[datetime] = []
    for event in events:
        published = _parse_datetime(event.get("published_at"))
        if published is not None:
            times.append(published)
    if not times:
        return {"status": "missing", "earliest": None, "latest": None}
    times.sort()
    return {
        "status": "available",
        "earliest": times[0].isoformat(),
        "latest": times[-1].isoformat(),
        "events_with_time": len(times),
    }


def _asset_price_context(rows: list[dict[str, Any]]) -> dict[str, Any]:
    context_rows: list[dict[str, Any]] = []
    for row in rows:
        outcome = row.get("event_outcomes")
        if not isinstance(outcome, dict) or outcome.get("status") != "priced":
            continue

        latest = outcome.get("latest")
        if not isinstance(latest, dict) or latest.get("status") != "priced":
            continue

        published_price_date = latest.get("published_price_date")
        latest_price_date = latest.get("latest_price_date")
        published_close = _safe_float(latest.get("published_close"))
        latest_close = _safe_float(latest.get("latest_close"))
        if (
            not isinstance(published_price_date, str)
            or not isinstance(latest_price_date, str)
            or published_close is None
            or latest_close is None
        ):
            continue

        context_rows.append(
            {
                "published_price_date": published_price_date,
                "latest_price_date": latest_price_date,
                "published_close": published_close,
                "latest_close": latest_close,
                "published_asset_return": _safe_float(latest.get("asset_return")),
                "max_drawdown": _safe_float(latest.get("max_drawdown")),
            }
        )

    if not context_rows:
        return {"status": "insufficient_price_context"}

    context_rows.sort(key=lambda item: item["latest_price_date"])
    anchor = context_rows[-1]
    return {
        "status": "priced",
        "published_price_date": anchor["published_price_date"],
        "latest_price_date": anchor["latest_price_date"],
        "published_close": anchor["published_close"],
        "latest_close": anchor["latest_close"],
        "published_asset_return": anchor["published_asset_return"],
        "max_drawdown": anchor["max_drawdown"],
    }


def _build_asset_rollup(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        instrument = str(event.get("instrument") or "unknown").strip() or "unknown"
        ticker = str(event.get("ticker") or "").strip()
        key = ticker.upper() if ticker else instrument
        grouped[key].append(event)

    rollups: list[dict[str, Any]] = []
    for key, rows in sorted(grouped.items(), key=lambda item: item[0].casefold()):
        names = [
            str(event.get("instrument") or "unknown")
            for event in rows
            if isinstance(event.get("instrument"), str)
        ]
        name = names[0] if names else key
        direction_counter = Counter(str(event.get("direction") or "unknown") for event in rows)
        action_counter = Counter(str(event.get("action") or "unknown") for event in rows)
        risk_counter = Counter(
            str(flag)
            for event in rows
            if isinstance(event.get("risk_flags"), list)
            for flag in event["risk_flags"]
            if isinstance(flag, str)
        )

        outcome_rows = [_extract_event_outcome_metrics(event) for event in rows]
        latest_returns = [
            item["latest_return"] for item in outcome_rows if item["latest_return"] is not None
        ]
        upside_vals = [item["upside"] for item in outcome_rows if item["upside"] is not None]
        downside_vals = [item["downside"] for item in outcome_rows if item["downside"] is not None]

        confidence = mean(_conviction_weight(event.get("conviction")) for event in rows) if rows else 0.5
        rr_candidates: list[float] = [
            item["risk_reward"] for item in outcome_rows if item["risk_reward"] is not None
        ]

        evidence_flags = [
            bool(event.get("evidence_refs")) for event in rows
            if isinstance(event.get("evidence_refs"), list)
        ]
        evidence_ratio = (
            sum(1 for has_evidence in evidence_flags if has_evidence) / len(evidence_flags)
            if evidence_flags
            else 0.0
        )

        event_text = " ".join(
            text for item in rows for text in _collect_text_tokens(item)
        ).casefold()
        aigc_terms = _extract_matching_terms(event_text, AIGC_KEYWORDS)
        production_terms = _extract_matching_terms(event_text, AIGC_PRODUCTION_KEYWORDS)
        usage_terms = _extract_matching_terms(event_text, AIGC_USAGE_KEYWORDS)
        software_terms = _extract_matching_terms(event_text, SOFTWARE_KEYWORDS)
        bearish_direction = direction_counter.get("bearish", 0) + direction_counter.get("mixed", 0)
        bullish_direction = direction_counter.get("bullish", 0)
        bearish_actions = (
            action_counter.get("sell", 0)
            + action_counter.get("avoid", 0)
            + action_counter.get("short sell", 0)
            + action_counter.get("reduce", 0)
        )
        bullish_actions = action_counter.get("add", 0) + action_counter.get("buy", 0) + action_counter.get("allocate", 0)
        downside_pressure = round((bearish_direction + bearish_actions) / max(len(rows), 1), 2)
        upside_support = round((bullish_direction + bullish_actions) / max(len(rows), 1), 2)
        is_software_sector = bool(software_terms)

        latest_return = mean(latest_returns) if latest_returns else None
        max_return = max(upside_vals) if upside_vals else None
        min_return = min(downside_vals) if downside_vals else None
        drawdowns = [item["latest_drawdown"] for item in outcome_rows if item["latest_drawdown"] is not None]
        max_drawdown = min(drawdowns) if drawdowns else None
        direction_bias = "bearish" if bearish_direction > bullish_direction else "bullish" if bullish_direction > bearish_direction else "mixed"
        price_context = _asset_price_context(rows)
        upside_target = None
        downside_target = None
        if price_context.get("status") == "priced":
            current_price = _safe_float(price_context.get("latest_close"))
            if current_price is not None:
                if max_return is not None:
                    upside_target = round(current_price * (1 + max_return / 100), 4)
                if min_return is not None and min_return < 0:
                    downside_target = round(current_price * (1 + min_return / 100), 4)
        price_context["target_prices"] = {
            "upside_pct": max_return,
            "upside_target": upside_target,
            "downside_pct": min_return,
            "downside_target": downside_target,
        }

        rollup = {
            "asset_id": key,
            "instrument": name,
            "event_count": len(rows),
            "action_distribution": action_counter,
            "direction_distribution": direction_counter,
            "confidence": round(confidence, 3),
            "evidence_ratio": round(evidence_ratio, 3),
            "risk_flags": risk_counter,
            "risk_reward_ratio": round(mean(rr_candidates), 2) if rr_candidates else None,
            "latest_return": latest_return,
            "upside": max_return,
            "downside": min_return,
            "target_prices": price_context.get("target_prices"),
            "max_drawdown": max_drawdown,
            "price_context": price_context,
            "downside_pressure": downside_pressure,
            "upside_support": upside_support,
            "aigc_relevance": bool(aigc_terms),
            "aigc_production_terms": production_terms,
            "aigc_usage_terms": usage_terms,
            "aigc_terms": aigc_terms,
            "is_software_sector": is_software_sector,
            "software_terms": software_terms,
            "top_risks": [name for name, _ in risk_counter.most_common(4)],
            "direction_bias": direction_bias,
        }
        rollups.append(rollup)

    return rollups


def build_finance_outlook_outputs_for_owner(
    *,
    library_root: Path,
    owner: str,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> list[Path]:
    from seed.domains.finance import finance_digest_output_path
    from seed.domains.finance import finance_window_slug

    expected = finance_digest_output_path(
        library_root=library_root,
        owner=owner,
        published_after=published_after,
        published_before=published_before,
    )
    candidates = [expected]
    if not expected.exists():
        candidates = sorted((library_root / "distilled").glob(f"{slugify(owner)}*.finance-digest*.json"))

    if not candidates:
        return []

    window = finance_window_slug(
        published_after=published_after,
        published_before=published_before,
    ) if (published_after or published_before) else None
    if window is not None:
        windowed = [
            path
            for path in candidates
            if path.name.find(f".{window}.") != -1
        ]
        if windowed:
            candidates = windowed

    digest_path = sorted(
        candidates,
        key=lambda path: (
            path.name.endswith(".finance-digest.news-context.json"),
            path.name.endswith(".finance-digest.priced.json"),
            path.stat().st_mtime,
            path.name,
        ),
        reverse=True,
    )[0]
    if not digest_path.exists():
        return []

    digest = json.loads(digest_path.read_text(encoding="utf-8"))
    payload = build_finance_outlook_payload(digest, digest_path=digest_path)

    payload_path = finance_outlook_payload_output_path(
        library_root=library_root,
        digest_path=digest_path,
    )
    payload_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report_path = finance_outlook_output_path(
        library_root=library_root,
        digest_path=digest_path,
    )
    write_finance_outlook_report(report_path, build_finance_outlook_report_html(payload))
    return [payload_path, report_path]


def build_finance_outlook_payload(
    digest: dict[str, Any],
    *,
    digest_path: Path | None = None,
) -> dict[str, Any]:
    events = [event for event in digest.get("viewpoint_events") or [] if isinstance(event, dict)]
    rollups = _build_asset_rollup(events)
    time_coverage = _build_time_coverage(events)
    peer_context = _peer_context_from_digest(digest)
    has_software_context = bool([item for item in rollups if item.get("is_software_sector")])
    has_aicoding_context = _contains_aicoding_context(digest) or _contains_software_context(
        events,
        digest=digest,
        peer_context=peer_context,
    )
    aicoding_signals = _build_aicoding_impact_signals(
        events,
        has_software_context=has_software_context,
        has_aicoding_context=has_aicoding_context,
    )

    macro_signals: list[str] = []
    for thesis in digest.get("macro_theses") or []:
        if isinstance(thesis, dict):
            text = thesis.get("thesis")
            if isinstance(text, str) and text.strip():
                macro_signals.append(text.strip())
            for variable in thesis.get("variables") or []:
                if isinstance(variable, str) and variable.strip():
                    macro_signals.append(variable.strip())
        elif isinstance(thesis, str) and thesis.strip():
            macro_signals.append(thesis.strip())
    if aicoding_signals:
        macro_signals.extend(aicoding_signals)

    news_context_events = sum(1 for event in events if event.get("news_context"))
    priced_events = [
        event
        for event in events
        if isinstance(event.get("event_outcomes"), dict)
        and event["event_outcomes"].get("status") == "priced"
    ]
    software_rollups = [item for item in rollups if item.get("is_software_sector")]
    aigc_rollups = [item for item in rollups if item.get("aigc_relevance")]
    direction_bias_counts = Counter(item.get("direction_bias", "mixed") for item in rollups)
    upside_list = [item["upside"] for item in rollups if item["upside"] is not None]
    downside_list = [item["downside"] for item in rollups if item["downside"] is not None]
    overall_upside = max(upside_list) if upside_list else None
    overall_downside = min(downside_list) if downside_list else None
    overall_rr = None
    if overall_upside is not None and overall_downside is not None and overall_downside < 0:
        overall_rr = round(overall_upside / abs(overall_downside), 2)

    software_headwinds: list[str] = []
    for item in software_rollups:
        asset = str(item.get("instrument") or item.get("asset_id"))
        for risk in item.get("top_risks", []):
            software_headwinds.append(f"{asset}：{risk}")

    industry_outlook: list[str] = []
    news_context_signals: list[str] = []
    open_questions: list[str] = []
    source_gaps: list[str] = []
    for question in digest.get("open_questions") or digest.get("open_questions", []):
        if isinstance(question, str) and question.strip():
            open_questions.append(question.strip())
    for gap in digest.get("source_gaps") or digest.get("evidence_gaps") or []:
        if isinstance(gap, str) and gap.strip():
            source_gaps.append(gap.strip())

    for event in events:
        for question in event.get("open_questions") or []:
            if isinstance(question, str) and question.strip():
                open_questions.append(question.strip())
        for gap in event.get("source_gaps") or []:
            if isinstance(gap, str) and gap.strip():
                source_gaps.append(gap.strip())
        for event_context in event.get("news_context") or []:
            if not isinstance(event_context, dict):
                continue
            for impact in event_context.get("industry_impacts") or []:
                if not isinstance(impact, dict):
                    continue
                industry = str(impact.get("industry") or "").strip()
                mechanism = str(impact.get("mechanism") or "").strip()
                direction = str(impact.get("possible_direction") or "中性").strip()
                if industry and mechanism:
                    industry_outlook.append(f"{industry}: {mechanism}（{direction}）")
            for gap in event_context.get("source_gaps") or []:
                if isinstance(gap, str) and gap.strip():
                    source_gaps.append(gap.strip())
            for question in event_context.get("open_questions") or []:
                if isinstance(question, str) and question.strip():
                    open_questions.append(question.strip())
            for note in event_context.get("market_relevance") or []:
                if not isinstance(note, dict):
                    continue
                relevance = str(note.get("relevance") or "").strip()
                asset = str(note.get("asset_or_sector") or "").strip()
                if relevance and asset:
                    news_context_signals.append(f"{asset}: {relevance}")

    action_counter = Counter(str(event.get("action") or "unknown") for event in events)
    direction_counter = Counter(str(event.get("direction") or "unknown") for event in events)
    risk_flags = Counter(
        flag
        for event in events
        if isinstance(event.get("risk_flags"), list)
        for flag in event["risk_flags"]
        if isinstance(flag, str)
    )
    if aicoding_signals:
        risk_flags["AI 代码工具替代压力"] += 1

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "kind": "finance_outlook",
        "owner": digest.get("owner"),
        "platform": digest.get("platform"),
        "source_digest_path": str(digest_path) if digest_path is not None else None,
        "window": digest.get("window"),
        "not_investment_advice": True,
        "time_coverage": time_coverage,
        "peer_context": peer_context,
        "totals": {
            "events": len(events),
            "priced_events": len(priced_events),
            "news_context_events": news_context_events,
            "assets": len(rollups),
            "software_assets": len(software_rollups),
            "aigc_assets": len(aigc_rollups),
            "overall_upside": overall_upside,
            "overall_downside": overall_downside,
            "overall_risk_reward": overall_rr,
            "direction_bias": dict(direction_bias_counts),
        },
        "macro_signals": macro_signals,
        "actions": dict(action_counter),
        "directions": dict(direction_counter),
        "risk_flags": dict(risk_flags),
        "software_headwinds": sorted(set(software_headwinds)),
        "aicoding_signals": aicoding_signals,
        "industry_outlook": sorted(set(industry_outlook)),
        "aigc": {
            "assets": [item.get("instrument") for item in aigc_rollups],
            "production_terms": sorted(
                {term for item in aigc_rollups for term in item.get("aigc_production_terms", [])}
            ),
            "usage_terms": sorted({term for item in aigc_rollups for term in item.get("aigc_usage_terms", [])}),
        },
        "news_context_signals": sorted(set(news_context_signals)),
        "source_gaps": sorted(set(source_gaps)),
        "open_questions": sorted(set(open_questions)),
        "asset_rollups": rollups,
        "methodology_signals": digest.get("methodology_signals") or [],
    }


def _format_pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}%"


def _format_rr(value: float | None) -> str:
    if value is None:
        return "待补充"
    if value > 20:
        return ">20"
    return str(value)


def _format_time(value: Any) -> str:
    parsed = _parse_datetime(value)
    return parsed.strftime("%Y-%m-%d %H:%M") if parsed else "-"


def _format_price(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"


def build_finance_outlook_report_html(payload: dict[str, Any]) -> str:
    owner = escape(str(payload.get("owner") or "Unknown"))
    platform = escape(str(payload.get("platform") or "unknown"))
    generated_at = escape(str(payload.get("generated_at") or ""))
    totals = payload.get("totals") if isinstance(payload.get("totals"), dict) else {}
    industry_outlook = payload.get("industry_outlook") or []
    software_headwinds = payload.get("software_headwinds") or []
    news_context_signals = payload.get("news_context_signals") or []
    aigc = payload.get("aigc") or {}
    aicoding_signals = payload.get("aicoding_signals") or []
    direction_bias = totals.get("direction_bias") or {}
    time_coverage = payload.get("time_coverage") or {}
    peer_context = payload.get("peer_context") or {}

    actions = payload.get("actions") or {}
    directions = payload.get("directions") or {}
    rollups = payload.get("asset_rollups") or []

    peer_rows: list[str] = []
    peers = peer_context.get("peers")
    if isinstance(peers, list):
        for peer in peers:
            if not isinstance(peer, dict):
                continue
            name = str(peer.get("name") or "").strip()
            if not name:
                continue
            parts = [name]
            if ticker := str(peer.get("ticker") or "").strip():
                parts.append(f"ticker={ticker}")
            if relation := str(peer.get("relation") or "").strip():
                parts.append(relation)
            if note := str(peer.get("note") or "").strip():
                parts.append(note)
            peer_rows.append("｜".join(parts))

    asset_rows = []
    for item in rollups:
        evidence_ratio = item.get("evidence_ratio")
        evidence_text = (
            "完整" if (isinstance(evidence_ratio, (int, float)) and evidence_ratio >= 0.6) else "不完整"
        )
        action_dist = "，".join(
            f"{escape(str(action))}: {count}" for action, count in item.get("action_distribution", {}).items()
        )
        direction_dist = "，".join(
            f"{escape(str(direction))}: {count}"
            for direction, count in item.get("direction_distribution", {}).items()
        )
        bias = str(item.get("direction_bias", "mixed"))
        direction_bias_tag = (
            "偏空"
            if bias == "bearish"
            else "偏多" if bias == "bullish" else "中性"
        )

        risks = item.get("top_risks")
        risk_text = ", ".join(escape(str(risk)) for risk in risks) if risks else "待补充"
        aigc_flag = "是" if item.get("aigc_relevance") else "否"
        price_context = item.get("price_context") if isinstance(item.get("price_context"), dict) else {}
        target_prices = item.get("target_prices") if isinstance(item.get("target_prices"), dict) else {}
        scenario_parts = [
            f"基准：{_format_pct(item.get('latest_return'))}",
            f"上行空间：{_format_pct(item.get('upside'))}",
            f"下行空间：{_format_pct(item.get('downside'))}",
            f"回撤：{_format_pct(item.get('max_drawdown'))}",
        ]
        latest_price = price_context.get("latest_close")
        latest_price_date = price_context.get("latest_price_date")
        if latest_price is not None and latest_price_date is not None:
            scenario_parts.append(f"最新价：{_format_price(_safe_float(latest_price))}（{_format_time(latest_price_date)}）")
        if target_prices.get("upside_target") is not None:
            scenario_parts.append(
                f"上行目标：{_format_price(_safe_float(target_prices.get('upside_target')))}（{_format_pct(target_prices.get('upside_pct'))}）"
            )
        if target_prices.get("downside_target") is not None:
            scenario_parts.append(
                f"下行目标：{_format_price(_safe_float(target_prices.get('downside_target')))}（{_format_pct(target_prices.get('downside_pct'))}）"
            )
        scenario = "；".join(scenario_parts)
        event_count = str(item.get("event_count") or 0)
        rr = _format_rr(item.get("risk_reward_ratio"))
        rr_tag = (
            "<span class='tag warn'>下行压力高</span>"
            if (
                isinstance(item.get("risk_reward_ratio"), float)
                and item.get("risk_reward_ratio") < 1.0
            )
            else ""
        )
        tags = "".join(
            f"<span class='tag'>{escape(term)}</span>" for term in item.get("aigc_terms") or []
        )
        software_tags = ", ".join(escape(str(term)) for term in item.get("software_terms") or [])
        row = f"""
      <tr>
        <td><strong>{escape(str(item.get('instrument') or item.get('asset_id')))}</strong>
          <div class='muted'>({escape(str(item.get('asset_id')))})</div>
        </td>
        <td>{escape(direction_bias_tag)} ({escape(str(item.get('direction_bias') or 'mixed') )})</td>
        <td>{len(item.get('aigc_terms') or [])} 类</td>
        <td>{rr}{rr_tag}</td>
        <td>{escape(event_count)}</td>
        <td>{_format_pct(item.get('upside'))}</td>
        <td>{_format_pct(item.get('downside'))}</td>
        <td>{_format_pct(item.get('latest_return'))}</td>
        <td>{escape(software_tags or '否')}</td>
        <td>{evidence_text} ({round(float(evidence_ratio or 0) * 100)}%)</td>
        <td>{escape(action_dist or 'unknown')} / {escape(direction_dist or 'unknown')}</td>
        <td>{escape(aigc_flag)}<br>{tags}</td>
        <td>{escape(risk_text)}</td>
        <td><div class='small'>{escape(scenario)}</div></td>
        </tr>
            """
        asset_rows.append(row)

    peer_list_html = "".join(
        f"<li>{escape(item)}</li>" for item in (peer_rows or ["未提供可比较同类样本"])
    )
    software_headwind_rows = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (software_headwinds or ["暂无明显软件方向利空信号"])
    )
    asset_rows_html = (
        "".join(asset_rows)
        if asset_rows
        else "<tr><td colspan=\"13\" class='muted'>当前 digest 无可对齐标的</td></tr>"
    )
    target_price_rows: list[str] = []
    for item in rollups:
        if not isinstance(item, dict):
            continue
        price_context = item.get("price_context")
        if not isinstance(price_context, dict) or price_context.get("status") != "priced":
            continue
        target_prices = item.get("target_prices")
        if not isinstance(target_prices, dict):
            continue
        target_price_rows.append(
            f"<li>{escape(str(item.get('instrument') or item.get('asset_id')))}："
            f"基准价 {_format_price(_safe_float((price_context or {}).get('latest_close')))}"
            f"（{_format_time((price_context or {}).get('latest_price_date'))}）；"
            f"上行目标 {_format_price(_safe_float((target_prices or {}).get('upside_target')))} "
            f"（{_format_pct((target_prices or {}).get('upside_pct'))}）；"
            f"下行目标 {_format_price(_safe_float((target_prices or {}).get('downside_target')))} "
            f"（{_format_pct((target_prices or {}).get('downside_pct'))}）</li>"
        )
    target_price_rows_html = (
        "".join(target_price_rows)
        if target_price_rows
        else "<li>暂无可估算目标价位（缺少价格锚点）</li>"
    )

    macro_rows_html = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (payload.get("macro_signals") or ["暂无明确行业变量"])
    )
    aicoding_rows_html = "".join(
        f"<li>{escape(str(item))}</li>" for item in (aicoding_signals or ["暂无AI Coding结构性信号（当前证据不足）"])
    )
    industry_rows_html = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (industry_outlook or ["暂无行业机制对齐"])
    )
    risk_flags_summary = (
        ", ".join(escape(str(flag)) for flag in list(payload.get("risk_flags", {}).keys())[:4])
        or "待补充"
    )
    aigc_production = ", ".join(
        escape(str(item)) for item in aigc.get("production_terms", [])
    ) or "待补充"
    aigc_usage = ", ".join(
        escape(str(item)) for item in aigc.get("usage_terms", [])
    ) or "待补充"
    aigc_assets = ", ".join(escape(str(item)) for item in aigc.get("assets", [])) or "无"
    news_context_snippets = "; ".join(escape(str(item)) for item in news_context_signals[:8]) or "无"
    aicoding_guardrails = [
        "1）优先核验：AI Coding 相关事件是否已落入已披露财报/公告（新增研发效率、外包与人力占比变化）。",
        "2）若出现“人均毛利下滑+新增人力成本下降未提升续费率”，说明替代压力真实。",
        "3）如可见“平台订阅化粘性提升+生态应用扩张”，再评估是否为受益而非受损。",
    ]
    aicoding_guardrail_html = "".join(f"<li>{item}</li>" for item in aicoding_guardrails)

    return f"""<!doctype html>
<html lang='zh-CN'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>{owner} - 财经观点前瞻研判</title>
    <style>
    :root {{
      --bg: #f5f7f8;
      --panel: #ffffff;
      --ink: #182022;
      --muted: #637074;
      --line: #d7dee0;
      --warn: #b15b29;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: 'Noto Sans SC', 'Segoe UI', sans-serif;
      line-height: 1.45;
    }}
    .shell {{
      width: min(1240px, calc(100% - 36px));
      margin: 0 auto;
      padding: 26px 0;
    }}
    header {{
      background: linear-gradient(140deg, #ffffff 0%, #edf2f1 55%, #f9ece7 100%);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 18px;
      margin-bottom: 16px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    .muted {{ color: var(--muted); }}
    .meta {{ color: #445; margin-top: 4px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }}
    ul {{
      margin: 8px 0 0;
      padding-left: 20px;
    }}
    li {{
      margin: 6px 0;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
    }}
    .card strong {{ font-size: 20px; display: block; }}
    .section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      margin-top: 12px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      background: white;
      border: 1px solid var(--line);
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 9px 8px;
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }}
    th {{ background: #f8fbfc; color: #445; position: sticky; top: 0; }}
    .small {{ font-size: 12px; color: var(--muted); }}
    .tag {{
      display: inline-block;
      border: 1px solid #d2e2e0;
      background: #f4faf8;
      border-radius: 999px;
      padding: 2px 8px;
      margin: 0 4px 4px 0;
      font-size: 12px;
    }}
    .warn {{ color: var(--warn); }}
    .footer {{ margin-top: 20px; color: var(--muted); font-size: 12px; }}
    @media (max-width: 1080px) {{
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 700px) {{
      .grid {{ grid-template-columns: 1fr; }}
      th:nth-child(9), td:nth-child(9), th:nth-child(10), td:nth-child(10), th:nth-child(11), td:nth-child(11) {{
        display: none;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div class="muted">Finance Forward View (scenario draft)</div>
      <h1>{owner} 财经观点前瞻研判</h1>
      <div class="meta">
        平台：{platform} ｜ 生成时间：{generated_at}
      </div>
      <div class="meta">
        事件数：{totals.get('events', 0)} ｜ 有价格后验：{totals.get('priced_events', 0)}
        ｜ 新闻事实对齐：{totals.get('news_context_events', 0)} ｜ 标的：{totals.get('assets', 0)}
        ｜ 整体上行：{_format_pct(totals.get('overall_upside'))} ｜ 整体下行：{_format_pct(totals.get('overall_downside'))} ｜ R/R：{_format_rr(totals.get('overall_risk_reward'))}
      </div>
      <div class="meta">
        时间覆盖：{_format_time(time_coverage.get("earliest"))} 到 {_format_time(time_coverage.get("latest"))}
        （{time_coverage.get("events_with_time", 0)}/{totals.get("events", 0)} 条）
      </div>
      <div class="meta">
        标的偏向：多空={escape(str(direction_bias.get('bullish', 0)))} ｜ 空头={escape(str(direction_bias.get('bearish', 0)))} ｜ 混合={escape(str(direction_bias.get('mixed', 0)))}
      </div>
    </header>

    <section class="section">
      <h2>全局情景</h2>
      <div class="grid">
        <div class="card">
          <span class="muted">动作分布</span>
          <strong>{', '.join(f'{escape(str(action))}:{count}' for action, count in actions.items()) or '待补充'}</strong>
        </div>
        <div class="card">
          <span class="muted">方向分布</span>
          <strong>{', '.join(f'{escape(str(direction))}:{count}' for direction, count in directions.items()) or '待补充'}</strong>
        </div>
        <div class="card">
          <span class="muted">风险因素 Top</span>
          <strong>{risk_flags_summary}</strong>
        </div>
        <div class="card">
          <span class="muted">证据边界状态</span>
          <strong>{len(payload.get('source_gaps', []))} 个证据缺口</strong>
          <div class='small'>{'; '.join(escape(str(item)) for item in payload.get('open_questions', [])[:2]) or '无明显 open questions'}</div>
        </div>
        <div class="card">
          <span class="muted">同类公司对照</span>
          <strong>{escape(str(peer_context.get("target_asset") or peer_context.get("target_ticker") or peer_context.get("asset") or "未标注"))}</strong>
          <div class='small'>行业：{escape(str(peer_context.get("industry") or "待补充"))}</div>
          <div class='small'>同业样本：{len(peer_rows)} 家</div>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>同类公司（事实输入）</h2>
      <ul>
        {peer_list_html}
      </ul>
      <div class='small muted'>来源于 digest.peer_context，仅用于事实汇总，不作投资建议比较。</div>
    </section>

    <section class="section">
      <h2>当前利空与下行压力</h2>
      <ul>
        {software_headwind_rows}
      </ul>
      <div class="small muted">核验项：估值、增速、现金流、商业化路径与监管变化。</div>
    </section>

    <section class="section">
      <h2>标的级风险收益（观点级草案）</h2>
      <table>
        <thead>
          <tr>
            <th>标的</th>
            <th>方向偏好</th>
            <th>AIGC信号</th>
            <th>R/R</th>
            <th>事件数</th>
            <th>上行空间</th>
            <th>下行空间</th>
            <th>基准收益</th>
            <th>软件标签</th>
            <th>证据完整度</th>
            <th>AIGC相关</th>
            <th>关键风险</th>
            <th>情景</th>
          </tr>
        </thead>
        <tbody>
          {asset_rows_html}
        </tbody>
      </table>
      <div class="small muted" style="margin-top:8px;">
        R/R 是基于有价格后验事件的上行/下行估计比例；
        仅用于风险收益场景比较，不构成投资建议。
      </div>
    </section>

    <section class="section">
      <h2>目标价位草案（基于价格后验）</h2>
      <ul>
        {target_price_rows_html}
      </ul>
      <div class='small muted'>目标仅为草案：采用 latest close 与事件极值收益做场景映射；仅作风险收益讨论输入。</div>
    </section>

    <section class="section">
      <h2>AIGC / 软件行业变量</h2>
      <div class="small muted" style="margin-bottom: 8px;">
        AIGC 生产侧：{aigc_production}
      </div>
      <div class="small muted" style="margin-bottom: 8px;">
        AIGC 使用侧：{aigc_usage}
      </div>
      <ul>
        {macro_rows_html}
      </ul>
      <div class="small muted" style="margin-top: 8px;">
        AIGC 相关标的：{aigc_assets}
      </div>
    </section>

    <section class="section">
      <h2>AI Coding 结构性变量（软件护城河）</h2>
      <div class="small muted" style="margin-bottom: 6px;">
        该模块覆盖“编程智能体 / 自动编程”对软件行业供给结构的影响，重点看交付壁垒是否下降和公司商业化是否被替代。
      </div>
      <ul>
        {aicoding_rows_html}
      </ul>
      <div class="small muted" style="margin-top: 8px;">复核指引（避免漏判）：</div>
      <ul>
        {aicoding_guardrail_html}
      </ul>
    </section>

    <section class="section">
      <h2>行业影响与新闻机制</h2>
      <ul>
        {industry_rows_html}
      </ul>
      <div class="small muted" style="margin-top: 8px;">
        新闻事实补充：{news_context_snippets}
      </div>
      <div class="small muted" style="font-size:12px;">
        对照观察项（非投资建议）：
        工具侧可替代性、算力/带宽成本、商业模式随使用弹性变化。
      </div>
    </section>

    <div class="footer">
      仅展示创作者观点、事件证据与风险收益场景；不构成投资建议。
      请结合公司公告/财报与独立核验后做最终判断。
    </div>
  </div>
</body>
</html>
"""


def write_finance_outlook_report(path: Path, html: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path
