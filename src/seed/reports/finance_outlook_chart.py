from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from html import escape
from typing import Any

MIN_KLINE_HISTORY_DAYS = 365 * 3 - 14
MIN_KLINE_HISTORY_POINTS = 600


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}%"


def _format_price(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"


def _normalize_text_line(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text if text else ""


def _historical_price_coverage(history: list[Any]) -> dict[str, Any]:
    dates = sorted(
        date
        for date in (
            _parse_chart_exact_date(_as_dict(row).get("date") or _as_dict(row).get("time"))
            for row in history
            if isinstance(row, dict)
        )
        if date is not None
    )
    if not dates:
        return {
            "status": "missing",
            "points": len(history),
            "first_date": None,
            "last_date": None,
            "calendar_days": 0,
            "meets_three_year_minimum": False,
        }
    calendar_days = (dates[-1].date() - dates[0].date()).days
    return {
        "status": "ok",
        "points": len(history),
        "first_date": dates[0].date().isoformat(),
        "last_date": dates[-1].date().isoformat(),
        "calendar_days": calendar_days,
        "meets_three_year_minimum": (
            calendar_days >= MIN_KLINE_HISTORY_DAYS
            and len(history) >= MIN_KLINE_HISTORY_POINTS
        ),
    }


def _parse_chart_reference_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text[:10])
    except ValueError:
        return None


def _normalize_chart_time(
    value: Any,
    index: int,
    *,
    reference_date: datetime | None,
) -> str:
    text = str(value or "").strip()
    if text:
        candidate = text[:10]
        try:
            datetime.fromisoformat(candidate)
            return candidate
        except ValueError:
            pass
        if reference_date is None:
            return (datetime(2000, 1, 3) + timedelta(days=index)).date().isoformat()
        for fmt in ("%b %d", "%B %d"):
            try:
                parsed = datetime.strptime(f"{reference_date.year} {text}", f"%Y {fmt}")
            except ValueError:
                continue
            if parsed.date() > (reference_date + timedelta(days=7)).date():
                parsed = parsed.replace(year=reference_date.year - 1)
            return parsed.date().isoformat()
    return (datetime(2000, 1, 3) + timedelta(days=index)).date().isoformat()


def _chart_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def _parse_chart_exact_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if not match:
        return None
    try:
        return datetime.fromisoformat(match.group(1))
    except ValueError:
        return None


def _chart_date_text(value: datetime) -> str:
    return value.date().isoformat()


def _chart_pct(
    value: datetime,
    *,
    start: datetime,
    end: datetime,
) -> float:
    total = max((end.date() - start.date()).days, 1)
    offset = (value.date() - start.date()).days
    return round(min(max(offset / total * 100, 0), 100), 3)


def _pick_chart_trigger(event_text: str, triggers: list[Any]) -> str:
    normalized_event = event_text.lower()
    best_trigger = ""
    best_score = 0
    keywords = [
        "q1",
        "q2",
        "q3",
        "q4",
        "ev",
        "ai",
        "aigc",
        "财报",
        "业绩",
        "报告",
        "半年度",
        "补贴",
        "政策",
        "手机",
        "毛利",
        "利润",
        "订阅",
        "credits",
        "海外",
        "算力",
        "api",
        "竞争",
        "价格战",
        "模型",
        "交付",
    ]
    for trigger in triggers:
        trigger_text = _normalize_text_line(trigger)
        if not trigger_text:
            continue
        normalized_trigger = trigger_text.lower()
        score = sum(
            1 for keyword in keywords
            if keyword in normalized_event and keyword in normalized_trigger
        )
        if score > best_score:
            best_trigger = trigger_text
            best_score = score
    if best_trigger:
        return best_trigger
    for trigger in triggers:
        trigger_text = _normalize_text_line(trigger)
        if trigger_text:
            return trigger_text
    return ""


def _chart_event_label(event_text: str) -> str:
    normalized = event_text.lower()
    if any(term in normalized for term in ("财报", "earnings", "q1", "q2", "q3", "q4")):
        return "财报"
    if any(term in normalized for term in ("政策", "补贴", "regulation")):
        return "政策"
    if any(term in normalized for term in ("ai", "aigc", "模型", "算力")):
        return "AI"
    if any(term in normalized for term in ("产品", "发布", "交付", "delivery")):
        return "产品"
    return "事件"


def _chart_event_category(event: dict[str, Any]) -> str:
    raw_category = _normalize_text_line(
        event.get("category") or event.get("type") or event.get("kind")
    ).lower()
    explicit_categories = {
        "earnings": "earnings",
        "financial": "earnings",
        "财报": "earnings",
        "业绩": "earnings",
        "product": "product",
        "产品": "product",
        "policy": "policy",
        "政策": "policy",
        "macro": "macro",
        "geopolitical": "macro",
        "宏观": "macro",
        "ai": "ai",
        "aigc": "ai",
        "research": "research",
        "研报": "research",
        "rating": "research",
        "news": "news",
        "新闻": "news",
    }
    if raw_category in explicit_categories:
        return explicit_categories[raw_category]
    text = " ".join(
        _normalize_text_line(event.get(key)).lower()
        for key in ("event", "title", "name", "label", "relevance", "note", "impact")
    )
    haystack = f"{raw_category} {text}"
    if any(term in haystack for term in ("earnings", "result", "financial", "财报", "业绩", "annual", "q1", "q2", "q3", "q4")):
        return "earnings"
    if any(term in haystack for term in ("product", "launch", "delivery", "ev", "su7", "yu7", "产品", "发布", "交付")):
        return "product"
    if any(term in haystack for term in ("policy", "regulation", "tariff", "subsidy", "政策", "监管", "补贴", "关税")):
        return "policy"
    if any(term in haystack for term in ("war", "iran", "israel", "oil", "geopolitical", "战争", "冲突", "油价", "地缘")):
        return "macro"
    if any(term in haystack for term in ("ai", "aigc", "model", "claude", "gpt", "模型", "算力")):
        return "ai"
    if any(term in haystack for term in ("research", "target", "rating", "研报", "目标价", "评级")):
        return "research"
    return "news"


def _chart_event_style(category: str) -> dict[str, str]:
    styles = {
        "earnings": {"color": "#255f9e", "text": "E", "label": "财报"},
        "product": {"color": "#8a5a28", "text": "P", "label": "产品"},
        "policy": {"color": "#7b4aa0", "text": "政", "label": "政策"},
        "macro": {"color": "#9b6b1f", "text": "宏", "label": "宏观"},
        "ai": {"color": "#b4443f", "text": "AI", "label": "AI"},
        "research": {"color": "#5f6f7a", "text": "研", "label": "研报"},
        "news": {"color": "#5d6970", "text": "N", "label": "新闻"},
    }
    return styles.get(category, styles["news"])


def _nearest_candle_time(event_date: datetime, candle_dates: list[datetime]) -> str | None:
    if not candle_dates:
        return None
    for candle_date in candle_dates:
        if candle_date.date() >= event_date.date():
            return _chart_date_text(candle_date)
    return _chart_date_text(candle_dates[-1])


def _source_link_html(event: dict[str, Any]) -> str:
    source_urls = event.get("source_urls")
    first_source_url = source_urls[0] if isinstance(source_urls, list) and source_urls else None
    source_url = _normalize_text_line(
        event.get("source_url")
        or event.get("url")
        or first_source_url
    )
    source_title = _normalize_text_line(
        event.get("source_title") or event.get("source") or event.get("title_source")
    )
    if source_url:
        label = source_title or "source"
        return f'<a href="{escape(source_url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>'
    if source_title:
        return escape(source_title)
    return "source pending"


def _parse_chart_event_window(
    date_text: str,
    *,
    last_date: datetime,
    projection_end: datetime,
) -> tuple[datetime | None, datetime | None, str]:
    normalized = date_text.strip()
    if not normalized:
        return None, None, "待跟踪"

    exact_date = _parse_chart_exact_date(normalized)
    is_ongoing = any(term in normalized.lower() for term in ("起", "ongoing", "持续", "through", "以后"))
    if exact_date is not None:
        if exact_date.date() > projection_end.date():
            return projection_end, projection_end, "超出当前预测窗"
        if exact_date.date() > last_date.date():
            return exact_date, exact_date, "未来时间点"
        if is_ongoing:
            return last_date, projection_end, "持续影响窗口"
        return None, None, "已进入价格"

    year_range = re.search(r"\b(20\d{2})\D+(20\d{2})\b", normalized)
    if year_range:
        start = datetime(int(year_range.group(1)), 1, 1)
        end = datetime(int(year_range.group(2)), 12, 31)
        if end.date() < last_date.date() or start.date() > projection_end.date():
            return None, None, "窗口外"
        return max(start, last_date), min(end, projection_end), "未来窗口"

    half_match = re.search(r"\b(20\d{2})[-\s]*(H[12])\b", normalized, re.IGNORECASE)
    if half_match:
        year = int(half_match.group(1))
        month = 6 if half_match.group(2).upper() == "H1" else 12
        day = 30 if month == 6 else 31
        candidate = datetime(year, month, day)
        if candidate.date() > projection_end.date():
            return projection_end, projection_end, "超出当前预测窗"
        if candidate.date() > last_date.date():
            return candidate, candidate, "预计窗口"
        return None, None, "已进入价格"

    return None, None, "窗口事件"


def _build_historical_chart_events(
    *,
    market_context: dict[str, Any],
    candles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candle_dates = [
        parsed for parsed in (
            _parse_chart_exact_date(candle.get("time"))
            for candle in candles
            if isinstance(candle, dict)
        )
        if parsed is not None
    ]
    if not candle_dates:
        return []
    first_date = candle_dates[0]
    last_date = candle_dates[-1]
    raw_events = (
        _as_list(market_context.get("chart_events"))
        + _as_list(market_context.get("historical_events"))
        + _as_list(market_context.get("timeline_events"))
    )
    events: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for raw_event in raw_events:
        event = _as_dict(raw_event)
        if not event:
            continue
        parsed_date = _parse_chart_exact_date(event.get("date") or event.get("published_at") or event.get("as_of"))
        if parsed_date is None or parsed_date.date() < first_date.date() or parsed_date.date() > last_date.date():
            continue
        title = _normalize_text_line(
            event.get("event") or event.get("title") or event.get("name") or event.get("label")
        )
        if not title:
            continue
        snapped_time = _nearest_candle_time(parsed_date, candle_dates)
        if not snapped_time:
            continue
        dedupe_key = (parsed_date.date().isoformat(), title.casefold())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        category = _chart_event_category(event)
        style = _chart_event_style(category)
        relevance = _normalize_text_line(
            event.get("relevance")
            or event.get("impact")
            or event.get("note")
            or event.get("summary")
        )
        events.append(
            {
                "time": snapped_time,
                "dateLabel": parsed_date.date().isoformat(),
                "label": title,
                "category": category,
                "categoryLabel": style["label"],
                "markerText": _normalize_text_line(event.get("marker")) or style["text"],
                "color": _normalize_text_line(event.get("color")) or style["color"],
                "position": "aboveBar" if category in {"earnings", "product", "ai", "research"} else "belowBar",
                "relevance": relevance,
                "sourceHtml": _source_link_html(event),
            }
        )
    return sorted(events, key=lambda item: (str(item.get("time") or ""), str(item.get("label") or "")))[:30]


def _build_chart_event_annotations(
    *,
    market_context: dict[str, Any],
    scenarios: dict[str, Any],
    last_date: datetime,
    current_price: float,
    projection_end: datetime,
) -> list[dict[str, Any]]:
    base_case = _as_dict(scenarios.get("base_case"))
    upside_case = _as_dict(scenarios.get("upside_case"))
    downside_case = _as_dict(scenarios.get("downside_case"))
    events: list[dict[str, Any]] = []
    for index, event in enumerate(_as_list(market_context.get("next_events"))[:6]):
        if not isinstance(event, dict):
            continue
        title = _normalize_text_line(
            event.get("event") or event.get("title") or event.get("name")
        ) or "关键事件"
        date_text = _normalize_text_line(event.get("date")) or "时间待定"
        relevance = _normalize_text_line(event.get("relevance") or event.get("note"))
        event_text = " ".join(item for item in (title, date_text, relevance) if item)
        window_start, window_end, window_status = _parse_chart_event_window(
            date_text,
            last_date=last_date,
            projection_end=projection_end,
        )
        plot_time = ""
        status = window_status
        if window_start is not None and window_end is not None and window_start.date() == window_end.date():
            plot_time = _chart_date_text(window_start)

        upside_hint = _pick_chart_trigger(event_text, _as_list(upside_case.get("triggers")))
        downside_hint = _pick_chart_trigger(event_text, _as_list(downside_case.get("triggers")))
        base_hint = _pick_chart_trigger(event_text, _as_list(base_case.get("triggers")))
        marker_label = _chart_event_label(event_text)
        category = _chart_event_category(
            {
                **event,
                "event": title,
                "relevance": relevance,
            }
        )
        style = _chart_event_style(category)
        events.append(
            {
                "time": plot_time,
                "dateLabel": date_text,
                "railStart": _chart_date_text(window_start) if window_start is not None else "",
                "railEnd": _chart_date_text(window_end) if window_end is not None else "",
                "sortDate": (
                    _chart_date_text(window_start)
                    if window_start is not None
                    else f"9999-{index:02d}-{index:02d}"
                ),
                "label": title,
                "markerText": marker_label,
                "category": category,
                "categoryLabel": style["label"],
                "status": status,
                "relevance": relevance,
                "baseHint": base_hint,
                "upsideHint": upside_hint,
                "downsideHint": downside_hint,
                "price": round(current_price, 4),
                "color": style["color"] if plot_time else "#7a858b",
                "withinProjection": bool(window_start is not None),
            }
        )
    return sorted(events, key=lambda item: str(item.get("sortDate") or "9999"))


def _build_chart_projection_end(
    *,
    scenarios: dict[str, Any],
    last_date: datetime,
    event_dates: list[datetime],
) -> datetime:
    explicit_date = (
        _parse_chart_exact_date(scenarios.get("target_date"))
        or _parse_chart_exact_date(scenarios.get("forecast_date"))
        or _parse_chart_exact_date(scenarios.get("horizon_end_date"))
    )
    if explicit_date is not None and explicit_date.date() > last_date.date():
        return explicit_date
    one_year = last_date + timedelta(days=365)
    future_events = [item for item in event_dates if item.date() > last_date.date()]
    if future_events:
        return max(one_year, max(future_events) + timedelta(days=30))
    return one_year


def _build_chart_projection_dates(
    *,
    last_date: datetime,
    projection_end: datetime,
    event_dates: list[datetime],
) -> list[datetime]:
    dates: dict[str, datetime] = {}
    cursor = last_date + timedelta(days=1)
    while cursor.date() < projection_end.date():
        dates[_chart_date_text(cursor)] = cursor
        cursor += timedelta(days=1)
    for event_date in event_dates:
        if last_date.date() < event_date.date() < projection_end.date():
            dates[_chart_date_text(event_date)] = event_date
    dates[_chart_date_text(projection_end)] = projection_end
    return [dates[key] for key in sorted(dates)]


def _build_chart_scenario_paths(
    *,
    current_price: float,
    scenarios: dict[str, Any],
    last_date: datetime,
    projection_end: datetime,
    event_dates: list[datetime],
) -> list[dict[str, Any]]:
    case_specs = [
        ("base", "基准情景路径", "#255f9e", _as_dict(scenarios.get("base_case"))),
        ("upside", "上行情景路径", "#b4443f", _as_dict(scenarios.get("upside_case"))),
        ("downside", "下行情景路径", "#16745b", _as_dict(scenarios.get("downside_case"))),
    ]
    total_days = max((projection_end.date() - last_date.date()).days, 1)
    projection_dates = _build_chart_projection_dates(
        last_date=last_date,
        projection_end=projection_end,
        event_dates=event_dates,
    )
    paths: list[dict[str, Any]] = []
    for key, label, color, scenario in case_specs:
        target = _safe_float(scenario.get("target_price"))
        if target is None:
            continue
        points = [{"time": _chart_date_text(last_date), "value": round(current_price, 4)}]
        for event_date in projection_dates:
            progress = (event_date.date() - last_date.date()).days / total_days
            event_price = current_price + (target - current_price) * progress
            points.append({"time": _chart_date_text(event_date), "value": round(event_price, 4)})
        returns = _safe_float(scenario.get("returns"))
        paths.append(
            {
                "key": key,
                "label": label,
                "color": color,
                "lineStyle": "dashed",
                "description": (
                    f"{label}：当前价 -> {_format_price(target)}"
                    + (f"（{_format_pct(returns)}）" if returns is not None else "")
                ),
                "data": points,
            }
        )
    return paths


def _build_chart_time_rail_html(
    *,
    historical_events: list[dict[str, Any]],
    future_events: list[dict[str, Any]],
    first_date: datetime,
    current_date: datetime,
    projection_end: datetime,
) -> str:
    now_pct = _chart_pct(current_date, start=first_date, end=projection_end)
    future_width = max(100 - now_pct, 0)
    historical_points = "".join(
        "<span class='rail-point rail-history-point' "
        f"style='left:{_chart_pct(_parse_chart_exact_date(item.get('time')) or current_date, start=first_date, end=projection_end)}%; "
        f"background:{escape(str(item.get('color') or '#5d6970'))};' "
        f"title='{escape(str(item.get('dateLabel') or item.get('time') or ''), quote=True)} · "
        f"{escape(str(item.get('label') or '历史事件'), quote=True)}'>"
        f"{escape(str(item.get('markerText') or ''))}</span>"
        for item in historical_events[:18]
        if item.get("time")
    )

    future_points: list[str] = []
    for index, item in enumerate(future_events[:8]):
        start_date = _parse_chart_exact_date(item.get("railStart") or item.get("time"))
        end_date = _parse_chart_exact_date(item.get("railEnd") or item.get("time"))
        if start_date is None or end_date is None:
            continue
        start_pct = _chart_pct(start_date, start=first_date, end=projection_end)
        end_pct = _chart_pct(end_date, start=first_date, end=projection_end)
        width_pct = max(end_pct - start_pct, 0.55)
        lane = index % 3
        color = escape(str(item.get("color") or "#255f9e"))
        label = escape(str(item.get("label") or "未来事件"))
        date_label = escape(str(item.get("dateLabel") or item.get("railStart") or ""))
        relevance = escape(str(item.get("relevance") or "待补充潜在影响"))
        base_hint = escape(str(item.get("baseHint") or "等待事件验证"))
        upside_hint = escape(str(item.get("upsideHint") or "等待事件验证"))
        downside_hint = escape(str(item.get("downsideHint") or "等待事件验证"))
        if end_date.date() > start_date.date():
            future_points.append(
                "<div class='rail-window' "
                f"style='left:{start_pct}%; width:{width_pct}%; --rail-color:{color}; --lane:{lane};'>"
                f"<span>{date_label}</span><strong>{label}</strong></div>"
            )
        else:
            future_points.append(
                "<div class='rail-future-event' "
                f"style='left:{start_pct}%; --rail-color:{color}; --lane:{lane};'>"
                f"<span class='rail-event-date'>{date_label}</span>"
                f"<strong>{label}</strong>"
                f"<em>{relevance}</em>"
                f"<small>基准：{base_hint}</small>"
                f"<small class='upside'>上行：{upside_hint}</small>"
                f"<small class='downside'>下行：{downside_hint}</small>"
                "</div>"
            )

    if not historical_points and not future_points:
        return ""

    return f"""
      <div class="chart-time-rail" style="--now:{now_pct}%; --future-width:{future_width}%;">
        <div class="rail-heading">
          <strong>同轴事件时间线</strong>
          <span>横坐标从历史 K 线起点延伸到未来 12 个月；右侧浅色区域是无真实 K 线的未来观察窗。</span>
        </div>
        <div class="rail-canvas">
          <div class="rail-axis"></div>
          <div class="rail-history-zone"></div>
          <div class="rail-future-zone"></div>
          <div class="rail-now"><span>当前 / 最后一根真实K线<br>{escape(_chart_date_text(current_date))}</span></div>
          {historical_points}
          {''.join(future_points)}
        </div>
        <div class="rail-labels">
          <span>{escape(_chart_date_text(first_date))}</span>
          <span>{escape(_chart_date_text(current_date))}</span>
          <span>{escape(_chart_date_text(projection_end))}</span>
        </div>
      </div>
    """


def _build_price_target_lines(
    *,
    current_price: float,
    scenarios: dict[str, Any],
    market_context: dict[str, Any],
) -> list[dict[str, Any]]:
    base_case = _as_dict(scenarios.get("base_case"))
    upside_case = _as_dict(scenarios.get("upside_case"))
    downside_case = _as_dict(scenarios.get("downside_case"))
    line_specs = [
        ("base", "基准", "#255f9e", base_case),
        ("upside", "上行", "#b4443f", upside_case),
        ("downside", "下行", "#16745b", downside_case),
    ]
    lines: list[dict[str, Any]] = []
    for key, label, color, scenario in line_specs:
        target = _safe_float(scenario.get("target_price"))
        if target is None:
            continue
        returns = _safe_float(scenario.get("returns"))
        pct_text = f" {_format_pct(returns)}" if returns is not None else ""
        lines.append(
            {
                "key": key,
                "label": label,
                "price": round(target, 4),
                "color": color,
                "title": f"{label}{pct_text}",
                "description": f"{label}目标 {_format_price(target)}{pct_text}",
                "isAboveAnchor": target >= current_price,
            }
        )

    support = _safe_float(market_context.get("fifty_two_week_low"))
    if support is not None and not any(item.get("key") == "downside" for item in lines):
        downside_pct = (support / current_price - 1) * 100 if current_price else None
        lines.append(
            {
                "key": "support",
                "label": "52周低位",
                "price": round(support, 4),
                "color": "#16745b",
                "title": f"52周低位 {_format_pct(downside_pct)}",
                "description": f"52周低位 {_format_price(support)}（{_format_pct(downside_pct)}）",
                "isAboveAnchor": support >= current_price,
            }
        )
    resistance = _safe_float(market_context.get("fifty_two_week_high"))
    if resistance is not None and not any(item.get("key") == "upside" for item in lines):
        upside_pct = (resistance / current_price - 1) * 100 if current_price else None
        lines.append(
            {
                "key": "resistance",
                "label": "52周高位",
                "price": round(resistance, 4),
                "color": "#b4443f",
                "title": f"52周高位 {_format_pct(upside_pct)}",
                "description": f"52周高位 {_format_price(resistance)}（{_format_pct(upside_pct)}）",
                "isAboveAnchor": resistance >= current_price,
            }
        )
    return lines


def build_kline_chart_html(market_context: dict[str, Any], scenarios: dict[str, Any]) -> str:
    history = [
        item for item in _as_list(market_context.get("historical_prices"))
        if isinstance(item, dict)
        and _safe_float(item.get("open")) is not None
        and _safe_float(item.get("high")) is not None
        and _safe_float(item.get("low")) is not None
        and _safe_float(item.get("close")) is not None
    ]
    current_price = _safe_float(
        market_context.get("current_price")
        or market_context.get("latest_close")
        or scenarios.get("anchor_price")
    )
    if not history or current_price is None:
        return ""

    candles: list[dict[str, Any]] = []
    reference_date = _parse_chart_reference_date(
        market_context.get("as_of")
        or market_context.get("current_price_date")
        or market_context.get("latest_price_date")
    )
    for index, row in enumerate(history):
        candles.append(
            {
                "time": _normalize_chart_time(
                    row.get("date") or row.get("time") or row.get("as_of"),
                    index,
                    reference_date=reference_date,
                ),
                "open": round(_safe_float(row.get("open")) or 0.0, 4),
                "high": round(_safe_float(row.get("high")) or 0.0, 4),
                "low": round(_safe_float(row.get("low")) or 0.0, 4),
                "close": round(_safe_float(row.get("close")) or 0.0, 4),
            }
        )

    target_lines = _build_price_target_lines(
        current_price=current_price,
        scenarios=scenarios,
        market_context=market_context,
    )
    if not candles:
        return ""
    try:
        last_chart_date = datetime.fromisoformat(str(candles[-1]["time"]))
    except (KeyError, TypeError, ValueError):
        last_chart_date = reference_date or datetime.now(tz=UTC).replace(tzinfo=None)
    try:
        first_chart_date = datetime.fromisoformat(str(candles[0]["time"]))
    except (KeyError, TypeError, ValueError):
        first_chart_date = last_chart_date - timedelta(days=max(len(candles), 1))
    event_exact_dates = [
        event_date for event_date in (
            _parse_chart_exact_date(_as_dict(event).get("date"))
            for event in _as_list(market_context.get("next_events"))
        )
        if event_date is not None and event_date.date() > last_chart_date.date()
    ]
    projection_end = _build_chart_projection_end(
        scenarios=scenarios,
        last_date=last_chart_date,
        event_dates=event_exact_dates,
    )
    scenario_paths = _build_chart_scenario_paths(
        current_price=current_price,
        scenarios=scenarios,
        last_date=last_chart_date,
        projection_end=projection_end,
        event_dates=event_exact_dates,
    )
    event_annotations = _build_chart_event_annotations(
        market_context=market_context,
        scenarios=scenarios,
        last_date=last_chart_date,
        current_price=current_price,
        projection_end=projection_end,
    )
    historical_events = _build_historical_chart_events(
        market_context=market_context,
        candles=candles,
    )
    if not target_lines and not scenario_paths and not event_annotations and not historical_events:
        return ""

    chart_prices = [
        price
        for candle in candles
        for price in (
            _safe_float(candle.get("open")),
            _safe_float(candle.get("high")),
            _safe_float(candle.get("low")),
            _safe_float(candle.get("close")),
        )
        if price is not None
    ]
    chart_prices.extend(
        _safe_float(line.get("price"))
        for line in target_lines
        if _safe_float(line.get("price")) is not None
    )
    for path in scenario_paths:
        chart_prices.extend(
            _safe_float(point.get("value"))
            for point in _as_list(path.get("data"))
            if _safe_float(point.get("value")) is not None
        )
    min_price = min(chart_prices)
    max_price = max(chart_prices)
    padding = max((max_price - min_price) * 0.08, 0.5)

    coverage = _as_dict(market_context.get("historical_price_coverage")) or _historical_price_coverage(history)
    coverage_days = int(_safe_float(coverage.get("calendar_days")) or 0)
    coverage_years = coverage_days / 365 if coverage_days else 0
    coverage_points = int(_safe_float(coverage.get("points")) or len(candles))
    coverage_first = str(coverage.get("first_date") or candles[0].get("time") or "")
    coverage_last = str(coverage.get("last_date") or candles[-1].get("time") or "")
    coverage_ok = bool(coverage.get("meets_three_year_minimum"))
    first_date = escape(coverage_first)
    last_date = escape(coverage_last)
    coverage_text = (
        f"历史 K 线覆盖 {first_date} - {last_date}，"
        f"{coverage_points} 个交易日，约 {coverage_years:.1f} 年。"
    )
    coverage_warning = ""
    if not coverage_ok:
        coverage_warning = (
            "<div class='small warn'>历史 K 线不足 3 年：当前图只能反映已取得的历史数据，"
            "需要补齐交易所、券商终端或付费行情源后再做客户级展示。</div>"
        )
    target_legend = "".join(
        "<span>"
        f"<i class='legend-line' style='border-color:{escape(str(line['color']))}'></i>"
        f"{escape(str(line['description']))}"
        "</span>"
        for line in target_lines
    )
    path_legend = "".join(
        "<span>"
        f"<i class='legend-path' style='border-color:{escape(str(path['color']))}'></i>"
        f"{escape(str(path['description']))}"
        "</span>"
        for path in scenario_paths
    )
    event_markers = [
        {
            "time": item.get("time"),
            "position": "atPriceMiddle",
            "shape": "circle",
            "color": item.get("color") or "#255f9e",
            "text": item.get("markerText") or "事件",
            "price": item.get("price"),
            "size": 1,
        }
        for item in event_annotations
        if item.get("time")
    ]
    historical_event_markers = [
        {
            "time": item.get("time"),
            "position": item.get("position") or "aboveBar",
            "shape": "circle",
            "color": item.get("color") or "#5d6970",
            "text": item.get("markerText") or "E",
            "size": 1,
        }
        for item in historical_events
        if item.get("time")
    ]
    event_lane = [
        {"time": _chart_date_text(last_chart_date), "value": round(current_price, 4)},
        *[
            {"time": marker["time"], "value": round(current_price, 4)}
            for marker in event_markers
        ],
        {"time": _chart_date_text(projection_end), "value": round(current_price, 4)},
    ]
    event_cards_html = ""
    if event_annotations:
        event_cards = "".join(
            "<div class='event-impact-card'>"
            f"<div class='event-date'>{escape(str(item.get('dateLabel') or '时间待定'))}"
            f" · {escape(str(item.get('status') or '待跟踪'))}</div>"
            f"<strong>{escape(str(item.get('label') or '关键事件'))}</strong>"
            f"<div class='small'>{escape(str(item.get('relevance') or '待补充事件影响'))}</div>"
            f"<div class='small scenario-hint'><span>基准：</span>{escape(str(item.get('baseHint') or '等待事件验证'))}</div>"
            f"<div class='small scenario-hint upside'><span>上行：</span>{escape(str(item.get('upsideHint') or '等待事件验证'))}</div>"
            f"<div class='small scenario-hint downside'><span>下行：</span>{escape(str(item.get('downsideHint') or '等待事件验证'))}</div>"
            "</div>"
            for item in event_annotations
        )
        event_cards_html = f"""
        <div class="finance-event-timeline">
          {event_cards}
        </div>
        """
    historical_events_html = ""
    if historical_events:
        historical_cards = "".join(
            "<div class='chart-event-row'>"
            f"<span class='chart-event-dot' style='background:{escape(str(item.get('color') or '#5d6970'))}'></span>"
            f"<span class='event-date'>{escape(str(item.get('dateLabel') or ''))}</span>"
            f"<strong>{escape(str(item.get('label') or '历史事件'))}</strong>"
            f"<span class='tag'>{escape(str(item.get('categoryLabel') or item.get('category') or '事件'))}</span>"
            f"<span class='small'>{escape(str(item.get('relevance') or '待补充影响机制'))}</span>"
            f"<span class='small source-ref'>来源：{item.get('sourceHtml') or 'source pending'}</span>"
            "</div>"
            for item in historical_events
        )
        historical_events_html = f"""
        <div class="chart-event-history">
          <div class="small muted">历史事件标注：事件点按事件发生日期对齐到最近交易日；宏观/战争/政策类事件只表示可能的解释变量，不等于因果证明。</div>
          {historical_cards}
        </div>
        """
    event_rail_html = _build_chart_time_rail_html(
        historical_events=historical_events,
        future_events=event_annotations,
        first_date=first_chart_date,
        current_date=last_chart_date,
        projection_end=projection_end,
    )
    chart_payload = {
        "library": "TradingView Lightweight Charts",
        "history": candles,
        "targets": target_lines,
        "scenarioPaths": scenario_paths,
        "eventMarkers": event_markers,
        "historicalEventMarkers": historical_event_markers,
        "historicalEvents": [
            {
                "time": item.get("time"),
                "date": item.get("dateLabel"),
                "label": item.get("label"),
                "category": item.get("category"),
                "relevance": item.get("relevance"),
            }
            for item in historical_events
        ],
        "eventLane": event_lane,
        "autoscale": {
            "min": round(min_price - padding, 4),
            "max": round(max_price + padding, 4),
        },
        "currentPrice": round(current_price, 4),
        "currentPriceLabel": f"当前 {_format_price(current_price)}",
        "firstDate": first_date,
        "lastDate": last_date,
        "projectionEndDate": _chart_date_text(projection_end),
        "futureProjectionPointCount": sum(len(_as_list(path.get("data"))) for path in scenario_paths),
    }
    return f"""
    <section class="section">
      <h2>历史 K 线 + 关键时间点 + 情景路径</h2>
      <div class="small muted">{coverage_text}</div>
      {coverage_warning}
      <div class="finance-kline-chart" data-chart-library="TradingView Lightweight Charts">
        <div class="chart-wrap">
          <div class="finance-chart-root" role="img" aria-label="真实历史K线、未来事件标记和情景路径"></div>
          <div class="chart-fallback small muted">图表脚本未加载：历史区间 {first_date} - {last_date}；目标价区（非K线）和关键时间点见下方说明。</div>
        </div>
        <script type="application/json" class="finance-chart-data">{_chart_json(chart_payload)}</script>
      </div>
      <div class="chart-legend target-legend">
        <span><i class="legend-candle up"></i>历史上涨K线</span>
        <span><i class="legend-candle down"></i>历史下跌K线</span>
        {target_legend}
        {path_legend}
        <span><i class="legend-historical-event"></i>历史事件</span>
        <span><i class="legend-event"></i>关键时间点</span>
      </div>
      {event_rail_html}
      {historical_events_html}
      {event_cards_html}
      <div class="small muted chart-path-note">情景路径（非K线）把当前价连接到外部目标价/支撑锚点，并把财报、产品、政策、AI 竞争等关键时间点放到同一时间轴上；它只说明“哪些事件可能让价格向哪个锚点靠拢”，不是未来每日K线、不是确定预测或交易建议。</div>
      <div class="small muted">图表由本地 vendored TradingView Lightweight Charts 渲染：K 线只来自真实历史 OHLC；目标价区（非K线）参考 TradingView Price Target 的目标价水平范式；未来事件需要继续用公司公告、财报、政策原文和行情源复核。</div>
    </section>
    """

