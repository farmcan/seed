from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify


def finance_daily_brief_output_path(
    *,
    library_root: Path,
    report_date: str | None = None,
    title: str = "finance-creator-daily-brief",
) -> Path:
    init_library(library_root)
    date = slugify(report_date or datetime.now(UTC).date().isoformat())
    return library_root / "reports" / f"{date}.{slugify(title)}.html"


def finance_daily_brief_artifact_output_path(
    *,
    library_root: Path,
    report_date: str | None = None,
    title: str = "finance-creator-daily-brief",
) -> Path:
    init_library(library_root)
    date = slugify(report_date or datetime.now(UTC).date().isoformat())
    return library_root / "distilled" / f"{date}.{slugify(title)}.json"


def write_finance_daily_brief_html(path: Path, html: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def write_finance_daily_brief_artifact(path: Path, artifact: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_finance_daily_brief_artifact(
    digests: list[dict[str, Any]],
    *,
    digest_paths: list[Path] | None = None,
    title: str = "财经 UP 每日观点简报",
    report_date: str | None = None,
) -> dict[str, Any]:
    paths = digest_paths or []
    creator_sections = [
        build_creator_section(digest, digest_path=paths[index] if index < len(paths) else None)
        for index, digest in enumerate(digests)
        if isinstance(digest, dict)
    ]
    consensus_rows = build_consensus_rows(creator_sections)
    methodology_rows = build_methodology_rows(creator_sections)
    return {
        "version": 1,
        "kind": "finance_creator_daily_brief",
        "title": title,
        "report_date": report_date or datetime.now(UTC).date().isoformat(),
        "generated_at": datetime.now(UTC).isoformat(),
        "not_investment_advice": True,
        "input_digest_paths": [str(path) for path in paths],
        "totals": {
            "creators": len(creator_sections),
            "videos": sum(int(section["totals"]["videos"]) for section in creator_sections),
            "viewpoint_events": sum(int(section["totals"]["viewpoint_events"]) for section in creator_sections),
            "instruments": len(consensus_rows),
            "methodology_signals": len(methodology_rows),
        },
        "creator_sections": creator_sections,
        "consensus_rows": consensus_rows,
        "methodology_rows": methodology_rows,
        "product_notes": [
            "每个创作者单独成章，便于快速扫过当天/窗口内各 UP 的核心观点。",
            "跨创作者表只表达一致、分歧和样本不足，不生成 Seed 自己的买卖建议。",
            "方法论信号来自 creator digest 的 methodology_signals，默认仍需人工复核。",
        ],
    }


def build_creator_section(digest: dict[str, Any], *, digest_path: Path | None = None) -> dict[str, Any]:
    owner = _text(digest.get("owner") or "Unknown")
    platform = _text(digest.get("platform") or "unknown")
    events = [_normalize_event(event) for event in _as_dict_list(digest.get("viewpoint_events"))]
    videos = _as_dict_list(digest.get("video_records"))
    methodologies = _as_dict_list(digest.get("methodology_signals"))
    window = digest.get("window") if isinstance(digest.get("window"), dict) else {}
    core_events = sorted(
        events,
        key=lambda event: (
            _conviction_rank(event.get("conviction")),
            len(event.get("evidence_refs") or []),
            _has_text(event.get("entry_condition")),
            _text(event.get("instrument")),
        ),
        reverse=True,
    )[:5]
    return {
        "owner": owner,
        "platform": platform,
        "digest_path": str(digest_path) if digest_path else None,
        "window": {
            "published_after": window.get("published_after"),
            "published_before": window.get("published_before"),
        },
        "totals": {
            "videos": int(digest.get("videos_analyzed") or len(videos)),
            "viewpoint_events": len(events),
            "recommendations": int((digest.get("totals") or {}).get("recommendations") or 0),
            "events_with_news_context": sum(1 for event in events if event.get("news_context")),
            "priced_events": sum(1 for event in events if isinstance(event.get("event_outcomes"), dict)),
            "methodology_signals": len(methodologies),
        },
        "core_viewpoints": core_events,
        "all_events": events,
        "methodology_signals": methodologies[:8],
        "risk_flags": _string_list(digest.get("risk_flags"))[:12],
        "evidence_gaps": _string_list(digest.get("evidence_gaps"))[:12],
        "video_titles": [_text(video.get("title")) for video in videos if video.get("title")][:8],
    }


def build_consensus_rows(creator_sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for section in creator_sections:
        for event in section.get("all_events") or []:
            key = _instrument_key(event)
            if key:
                grouped[key].append({"owner": section["owner"], **event})

    rows = []
    for key, events in grouped.items():
        owners = sorted({str(event.get("owner")) for event in events if event.get("owner")})
        directions = Counter(_text(event.get("direction") or "unknown") for event in events)
        actions = Counter(_text(event.get("action") or "unknown") for event in events)
        tickers = sorted({_text(event.get("ticker")) for event in events if event.get("ticker")})
        rows.append(
            {
                "instrument": _text(events[0].get("instrument") or key),
                "tickers": tickers,
                "owners": owners,
                "event_count": len(events),
                "direction_distribution": dict(directions),
                "action_distribution": dict(actions),
                "consensus": consensus_label(directions),
                "sample_note": "multi_creator" if len(owners) > 1 else "single_creator_only",
                "example_claims": [
                    {
                        "owner": event.get("owner"),
                        "video_title": event.get("video_title"),
                        "action": event.get("action"),
                        "direction": event.get("direction"),
                        "horizon": event.get("horizon"),
                        "thesis": event.get("entry_condition") or event.get("uncertainty"),
                    }
                    for event in events[:4]
                ],
            }
        )
    return sorted(rows, key=lambda row: (-int(row["event_count"]), row["instrument"]))


def build_methodology_rows(creator_sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section in creator_sections:
        for method in section.get("methodology_signals") or []:
            rows.append(
                {
                    "owner": section["owner"],
                    "method": method.get("method") or "unknown",
                    "decision_rule": method.get("decision_rule"),
                    "when_it_applies": method.get("when_it_applies"),
                    "failure_modes": _string_list(method.get("failure_modes")),
                    "evidence_refs": _string_list(method.get("evidence_refs")),
                }
            )
    return rows


def build_finance_daily_brief_html(artifact: dict[str, Any]) -> str:
    title = _text(artifact.get("title") or "财经 UP 每日观点简报")
    totals = artifact.get("totals") if isinstance(artifact.get("totals"), dict) else {}
    creator_sections = _as_dict_list(artifact.get("creator_sections"))
    consensus_rows = _as_dict_list(artifact.get("consensus_rows"))
    methodology_rows = _as_dict_list(artifact.get("methodology_rows"))
    creator_html = "\n".join(render_creator_section(section) for section in creator_sections)
    consensus_html = "\n".join(render_consensus_row(row) for row in consensus_rows[:24])
    methodology_html = "\n".join(render_methodology_row(row) for row in methodology_rows[:24])
    notes_html = "".join(f"<li>{escape(_text(note))}</li>" for note in artifact.get("product_notes") or [])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)}</title>
  <style>
    :root {{
      --bg: #f6f7f4;
      --panel: #ffffff;
      --ink: #17201c;
      --muted: #66736d;
      --line: #d8ded9;
      --teal: #0d6f68;
      --rust: #a9432d;
      --amber: #9f6b16;
      --blue: #315c8a;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: "Avenir Next", "Noto Sans SC", "Segoe UI", sans-serif; line-height: 1.55; }}
    header {{ background: #fff; border-bottom: 1px solid var(--line); }}
    .wrap {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; }}
    .hero {{ padding: 34px 0 28px; }}
    .eyebrow {{ color: var(--teal); font-size: 13px; font-weight: 800; letter-spacing: 0; text-transform: uppercase; }}
    h1 {{ margin: 8px 0 10px; font-size: 38px; line-height: 1.12; letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 22px; letter-spacing: 0; }}
    h3 {{ margin: 0; font-size: 18px; letter-spacing: 0; }}
    a {{ color: var(--teal); }}
    .muted {{ color: var(--muted); }}
    .stats {{ display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 10px; margin-top: 18px; }}
    .stat {{ border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #fbfcfb; }}
    .stat strong {{ display: block; font-size: 23px; }}
    main {{ padding: 26px 0 44px; }}
    section {{ margin-top: 28px; }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }}
    .creator {{ margin-top: 18px; }}
    .creator-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: start; border-bottom: 1px solid var(--line); padding-bottom: 12px; margin-bottom: 12px; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .badge {{ display: inline-flex; border: 1px solid var(--line); border-radius: 999px; padding: 2px 9px; font-size: 12px; font-weight: 700; background: #f8faf9; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 9px 8px; vertical-align: top; text-align: left; overflow-wrap: anywhere; }}
    th {{ color: var(--muted); font-size: 13px; }}
    tr:last-child td {{ border-bottom: 0; }}
    .grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(260px, .42fr); gap: 16px; }}
    .positive {{ color: var(--teal); font-weight: 800; }}
    .negative {{ color: var(--rust); font-weight: 800; }}
    .mixed {{ color: var(--amber); font-weight: 800; }}
    .unknown {{ color: var(--muted); font-weight: 800; }}
    ul {{ margin: 8px 0 0; padding-left: 20px; }}
    footer {{ padding: 0 0 34px; color: var(--muted); font-size: 13px; }}
    @media (max-width: 860px) {{ .stats, .grid {{ grid-template-columns: 1fr; }} h1 {{ font-size: 30px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="wrap hero">
      <div class="eyebrow">Finance Creator Daily Brief</div>
      <h1>{escape(title)}</h1>
      <p class="muted">报告日期：{escape(_text(artifact.get("report_date")))} ｜ 生成时间：{escape(_text(artifact.get("generated_at")))} ｜ 非投资建议</p>
      <div class="stats">
        {stat_html("创作者", totals.get("creators"))}
        {stat_html("视频", totals.get("videos"))}
        {stat_html("观点事件", totals.get("viewpoint_events"))}
        {stat_html("标的/主题", totals.get("instruments"))}
        {stat_html("方法论信号", totals.get("methodology_signals"))}
      </div>
    </div>
  </header>
  <main class="wrap">
    <section class="panel">
      <h2>怎么读这份简报</h2>
      <ul>{notes_html}</ul>
    </section>
    <section>
      <h2>跨 UP 共识与分歧</h2>
      <div class="panel">
        <table>
          <thead><tr><th>标的/主题</th><th>UP</th><th>方向分布</th><th>动作分布</th><th>判断</th></tr></thead>
          <tbody>{consensus_html or "<tr><td colspan='5'>暂无可聚合观点。</td></tr>"}</tbody>
        </table>
      </div>
    </section>
    <section>
      <h2>每位 UP 今日/窗口观点</h2>
      {creator_html or "<div class='panel muted'>暂无创作者章节。</div>"}
    </section>
    <section>
      <h2>方法论蒸馏候选</h2>
      <div class="panel">
        <table>
          <thead><tr><th>UP</th><th>方法</th><th>决策规则</th><th>失效条件</th><th>证据</th></tr></thead>
          <tbody>{methodology_html or "<tr><td colspan='5'>暂无方法论信号；需要补更多视频或改进 finance signals 抽取。</td></tr>"}</tbody>
        </table>
      </div>
    </section>
  </main>
  <footer class="wrap">Seed 只汇总创作者观点、事实引用和证据缺口；不提供买入、卖出或持有建议。</footer>
</body>
</html>
"""


def render_creator_section(section: dict[str, Any]) -> str:
    viewpoints = "\n".join(render_viewpoint_row(event) for event in _as_dict_list(section.get("core_viewpoints")))
    gaps = "".join(f"<li>{escape(item)}</li>" for item in _string_list(section.get("evidence_gaps"))[:8])
    risks = "".join(f"<span class='badge'>{escape(item)}</span>" for item in _string_list(section.get("risk_flags"))[:8])
    videos = "".join(f"<li>{escape(item)}</li>" for item in section.get("video_titles") or [])
    totals = section.get("totals") if isinstance(section.get("totals"), dict) else {}
    digest_link = (
        f"<a href='{escape(_text(section.get('digest_path')))}'>digest</a>"
        if section.get("digest_path")
        else "<span class='muted'>inline digest</span>"
    )
    return f"""<div class="panel creator">
  <div class="creator-head">
    <div>
      <h3>{escape(_text(section.get("owner")))}</h3>
      <div class="muted">{escape(_text(section.get("platform")))} ｜ {digest_link}</div>
    </div>
    <div class="badges">
      <span class="badge">视频 {escape(str(totals.get("videos") or 0))}</span>
      <span class="badge">观点 {escape(str(totals.get("viewpoint_events") or 0))}</span>
      <span class="badge">新闻上下文 {escape(str(totals.get("events_with_news_context") or 0))}</span>
      <span class="badge">方法 {escape(str(totals.get("methodology_signals") or 0))}</span>
    </div>
  </div>
  <div class="grid">
    <div>
      <table>
        <thead><tr><th>标的</th><th>动作/方向</th><th>核心观点</th><th>风险/证据</th></tr></thead>
        <tbody>{viewpoints or "<tr><td colspan='4'>暂无核心观点事件。</td></tr>"}</tbody>
      </table>
    </div>
    <div>
      <h3>风险与证据缺口</h3>
      <div>{risks or "<span class='muted'>暂无汇总风险标签。</span>"}</div>
      <ul>{gaps or "<li>暂无证据缺口；仍需人工复核样本覆盖。</li>"}</ul>
      <h3 style="margin-top:14px;">视频样本</h3>
      <ul>{videos or "<li>暂无视频标题。</li>"}</ul>
    </div>
  </div>
</div>"""


def render_viewpoint_row(event: dict[str, Any]) -> str:
    direction = _text(event.get("direction") or "unknown")
    direction_class = {
        "bullish": "positive",
        "bearish": "negative",
        "mixed": "mixed",
        "neutral": "unknown",
    }.get(direction, "unknown")
    evidence = ", ".join(_string_list(event.get("evidence_refs"))[:5]) or "缺 evidence refs"
    risk = ", ".join(_string_list(event.get("risk_flags"))[:4])
    return f"""<tr>
  <td>{escape(_text(event.get("instrument") or "unknown"))}<br><span class="muted">{escape(_text(event.get("ticker") or ""))}</span></td>
  <td>{escape(_text(event.get("action") or "unknown"))}<br><span class="{direction_class}">{escape(direction)}</span><br><span class="muted">{escape(_text(event.get("horizon") or ""))}</span></td>
  <td>{escape(_text(event.get("entry_condition") or event.get("uncertainty") or "未提取核心观点。"))}<br><span class="muted">{escape(_text(event.get("video_title") or ""))}</span></td>
  <td>{escape(risk or "未提取风险")}<br><span class="muted">{escape(evidence)}</span></td>
</tr>"""


def render_consensus_row(row: dict[str, Any]) -> str:
    consensus = _text(row.get("consensus") or "unknown")
    klass = "positive" if consensus == "bullish_consensus" else "negative" if consensus == "bearish_consensus" else "mixed" if consensus == "conflict" else "unknown"
    return f"""<tr>
  <td>{escape(_text(row.get("instrument")))}<br><span class="muted">{escape(", ".join(row.get("tickers") or []))}</span></td>
  <td>{escape(", ".join(row.get("owners") or []))}</td>
  <td>{escape(_format_distribution(row.get("direction_distribution")))}</td>
  <td>{escape(_format_distribution(row.get("action_distribution")))}</td>
  <td><span class="{klass}">{escape(consensus)}</span><br><span class="muted">{escape(_text(row.get("sample_note")))}</span></td>
</tr>"""


def render_methodology_row(row: dict[str, Any]) -> str:
    return f"""<tr>
  <td>{escape(_text(row.get("owner")))}</td>
  <td>{escape(_text(row.get("method")))}</td>
  <td>{escape(_text(row.get("decision_rule") or "待补充"))}</td>
  <td>{escape("; ".join(_string_list(row.get("failure_modes"))[:3]) or "待补充")}</td>
  <td>{escape(", ".join(_string_list(row.get("evidence_refs"))[:5]) or "缺 evidence refs")}</td>
</tr>"""


def stat_html(label: str, value: Any) -> str:
    return f"<div class='stat'><strong>{escape(str(value or 0))}</strong><span>{escape(label)}</span></div>"


def consensus_label(directions: Counter[str]) -> str:
    positive = directions.get("bullish", 0)
    negative = directions.get("bearish", 0)
    mixed = directions.get("mixed", 0)
    if positive and negative:
        return "conflict"
    if positive and positive >= max(negative, mixed, 1):
        return "bullish_consensus"
    if negative and negative >= max(positive, mixed, 1):
        return "bearish_consensus"
    if mixed:
        return "mixed_or_unclear"
    return "insufficient_signal"


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event.get("event_id"),
        "video_title": event.get("video_title"),
        "published_at": event.get("published_at"),
        "instrument": event.get("instrument") or "unknown",
        "ticker": event.get("ticker"),
        "action": event.get("action") or "unknown",
        "direction": event.get("direction") or "unknown",
        "horizon": event.get("horizon"),
        "conviction": event.get("conviction") or "unknown",
        "entry_condition": event.get("entry_condition"),
        "exit_or_invalidation": event.get("exit_or_invalidation"),
        "risk_flags": _string_list(event.get("risk_flags")),
        "evidence_refs": _string_list(event.get("evidence_refs")),
        "uncertainty": event.get("uncertainty"),
        "news_context": event.get("news_context") or [],
        "event_outcomes": event.get("event_outcomes"),
    }


def _instrument_key(event: dict[str, Any]) -> str:
    ticker = _text(event.get("ticker")).casefold()
    if ticker and ticker not in {"none", "unknown", "null"}:
        return ticker
    instrument = _text(event.get("instrument")).casefold()
    return instrument if instrument and instrument != "unknown" else ""


def _conviction_rank(value: Any) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(_text(value).casefold(), 0)


def _has_text(value: Any) -> int:
    return 1 if isinstance(value, str) and value.strip() else 0


def _format_distribution(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    return ", ".join(f"{key}:{count}" for key, count in sorted(value.items()))


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value or [] if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item.strip()]


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
