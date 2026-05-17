from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify


def finance_news_report_output_path(*, library_root: Path, digest_path: Path) -> Path:
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
    return library_root / "reports" / f"{slugify(name)}.finance-news-report.html"


def build_finance_news_report_html(
    digest: dict[str, Any],
    *,
    digest_path: Path | None = None,
) -> str:
    owner = text(digest.get("owner") or "Unknown")
    platform = text(digest.get("platform") or "unknown")
    generated_at = datetime.now(UTC).isoformat()
    events = [event for event in digest.get("viewpoint_events") or [] if isinstance(event, dict)]
    events_with_context = [event for event in events if event.get("news_context")]
    topic_rows = build_topic_rows(events)
    video_groups = group_events_by_video(events)
    source_gaps = aggregate_context_values(events, "source_gaps")
    open_questions = aggregate_context_values(events, "open_questions")
    totals = digest.get("totals") if isinstance(digest.get("totals"), dict) else {}
    window = digest.get("window") if isinstance(digest.get("window"), dict) else {}

    topic_table = "\n".join(topic_row_html(row) for row in topic_rows)
    video_html = "\n".join(video_section_html(title, grouped_events) for title, grouped_events in video_groups)
    gap_items = "".join(f"<li>{escape(item)}</li>" for item in source_gaps[:16])
    question_items = "".join(f"<li>{escape(item)}</li>" for item in open_questions[:16])
    digest_link = (
        f"<a href='{escape(str(digest_path))}'>{escape(digest_path.name)}</a>"
        if digest_path
        else "inline digest"
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(owner)} - 财经观点新闻事实报告</title>
  <style>
    :root {{
      --bg: #f5f7f8;
      --panel: #ffffff;
      --ink: #17201c;
      --muted: #62706a;
      --line: #d8ded9;
      --teal: #0d6f68;
      --rust: #b74d32;
      --olive: #52642a;
      --amber: #a46a13;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Avenir Next", "Noto Sans SC", "Segoe UI", sans-serif;
      line-height: 1.55;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: linear-gradient(135deg, #ffffff 0%, #edf3f2 52%, #f7ece8 100%);
    }}
    main, .hero-inner {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
    }}
    .hero-inner {{ padding: 34px 0 28px; }}
    .eyebrow {{
      color: var(--teal);
      font-weight: 800;
      font-size: 13px;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 8px 0 10px;
      font-size: 42px;
      line-height: 1.08;
      letter-spacing: 0;
    }}
    h2 {{ margin: 0 0 14px; font-size: 22px; letter-spacing: 0; }}
    h3 {{ margin: 0; font-size: 18px; letter-spacing: 0; }}
    a {{ color: var(--teal); text-decoration-thickness: 1px; }}
    .muted {{ color: var(--muted); }}
    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      align-items: end;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(2, minmax(130px, 1fr));
      gap: 10px;
      min-width: 310px;
    }}
    .stat {{
      background: rgba(255,255,255,.78);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 14px;
    }}
    .stat strong {{ display: block; font-size: 24px; }}
    main {{ padding: 26px 0 42px; }}
    section {{
      margin-top: 28px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      background: var(--panel);
      border: 1px solid var(--line);
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }}
    th {{ color: var(--muted); font-size: 13px; font-weight: 800; }}
    tr:last-child td {{ border-bottom: 0; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 2px 9px;
      border: 1px solid var(--line);
      background: #f8faf9;
      font-size: 12px;
      font-weight: 700;
      margin: 2px 4px 2px 0;
      white-space: nowrap;
    }}
    .support-high {{ color: var(--teal); }}
    .support-medium {{ color: var(--amber); }}
    .support-low {{ color: var(--rust); }}
    .video-card {{
      margin-top: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    .video-head {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 16px;
      background: #f9fbfa;
      border-bottom: 1px solid var(--line);
    }}
    .event {{
      padding: 16px;
      border-bottom: 1px solid var(--line);
    }}
    .event:last-child {{ border-bottom: 0; }}
    .event-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      margin-top: 12px;
    }}
    .fact-list {{
      margin: 8px 0 0;
      padding-left: 20px;
    }}
    .fact-list li {{ margin: 6px 0; }}
    .context-block {{
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px dashed var(--line);
    }}
    .context-title {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin-bottom: 8px;
    }}
    .empty {{
      padding: 18px;
      border: 1px dashed var(--line);
      border-radius: 8px;
      color: var(--muted);
      background: #fbfcfc;
    }}
    footer {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto 34px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 760px) {{
      .hero-grid, .event-grid {{ grid-template-columns: 1fr; }}
      .stats {{ min-width: 0; grid-template-columns: repeat(2, 1fr); }}
      h1 {{ font-size: 30px; }}
      th:nth-child(4), td:nth-child(4) {{ display: none; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="hero-inner">
      <div class="hero-grid">
        <div>
          <div class="eyebrow">Finance Views × News Facts</div>
          <h1>{escape(owner)} 财经观点新闻事实报告</h1>
          <div class="muted">
            平台：{escape(platform)} ｜ 生成时间：{escape(generated_at)} ｜ Digest：{digest_link}
          </div>
          <div class="muted">
            窗口：{escape(text(window.get("published_after") or "start"))}
            到 {escape(text(window.get("published_before") or "now"))}
          </div>
        </div>
        <div class="stats" aria-label="summary">
          {stat_html("视频数", totals.get("videos_analyzed") or digest.get("videos_analyzed") or 0)}
          {stat_html("观点事件", len(events))}
          {stat_html("有事实上下文", len(events_with_context))}
          {stat_html("新闻匹配", totals.get("news_context_matches") or 0)}
        </div>
      </div>
    </div>
  </header>
  <main>
    <section>
      <h2>热点概览</h2>
      <table>
        <thead>
          <tr>
            <th>热点/标的</th><th>UP 提及次数</th><th>涉及行业</th><th>Facts 支撑度</th><th>主要风险</th>
          </tr>
        </thead>
        <tbody>
          {topic_table or "<tr><td colspan='5'>暂无可汇总的观点事件。</td></tr>"}
        </tbody>
      </table>
    </section>
    <section>
      <h2>UP 观点卡</h2>
      <div class="event-grid">
        <div>
          <div class="badge">Owner</div>
          <h3>{escape(owner)}</h3>
          <p class="muted">系统只记录创作者观点与事实引用，不把任何结论升级成投资建议。</p>
        </div>
        <div>
          <div class="badge">Signal Policy</div>
          <p>观点保持为 creator claim；新闻内容只进入 facts/context/source gaps。</p>
        </div>
      </div>
    </section>
    <section>
      <h2>视频与观点事件</h2>
      {video_html or "<div class='empty'>暂无观点事件。</div>"}
    </section>
    <section>
      <h2>Source Gaps 与 Open Questions</h2>
      <div class="event-grid">
        <div>
          <h3>Source Gaps</h3>
          <ul>{gap_items or "<li>暂无。</li>"}</ul>
        </div>
        <div>
          <h3>Open Questions</h3>
          <ul>{question_items or "<li>暂无。</li>"}</ul>
        </div>
      </div>
    </section>
  </main>
  <footer>
    Not investment advice. This report separates creator viewpoints from external facts and source gaps.
  </footer>
</body>
</html>"""


def write_finance_news_report_html(path: Path, html: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def build_topic_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for event in events:
        topic = text(event.get("instrument") or event.get("ticker") or "unknown")
        row = grouped.setdefault(
            topic.casefold(),
            {
                "topic": topic,
                "mentions": 0,
                "industries": Counter(),
                "source_urls": set(),
                "risk_flags": Counter(),
                "contexts": 0,
            },
        )
        row["mentions"] += 1
        for risk in event.get("risk_flags") or []:
            row["risk_flags"][text(risk)] += 1
        for context in event.get("news_context") or []:
            row["contexts"] += 1
            for url in context.get("source_urls") or []:
                row["source_urls"].add(text(url))
            for impact in context.get("industry_impacts") or []:
                industry = text(impact.get("industry") or "")
                if industry:
                    row["industries"][industry] += 1
            for relevance in context.get("market_relevance") or []:
                sector = text(relevance.get("asset_or_sector") or "")
                if sector:
                    row["industries"][sector] += 1
    return sorted(grouped.values(), key=lambda row: (-row["mentions"], row["topic"]))


def topic_row_html(row: dict[str, Any]) -> str:
    industries = ", ".join(name for name, _ in row["industries"].most_common(4)) or "unknown"
    risks = ", ".join(name for name, _ in row["risk_flags"].most_common(3)) or "待继续观察"
    support, support_class = support_label(
        context_count=int(row["contexts"]),
        source_count=len(row["source_urls"]),
    )
    return f"""<tr>
  <td><strong>{escape(text(row["topic"]))}</strong></td>
  <td>{escape(str(row["mentions"]))}</td>
  <td>{escape(industries)}</td>
  <td><span class="{support_class}">{escape(support)}</span></td>
  <td>{escape(risks)}</td>
</tr>"""


def support_label(*, context_count: int, source_count: int) -> tuple[str, str]:
    if context_count >= 2 and source_count >= 2:
        return "高", "support-high"
    if context_count >= 1 and source_count >= 1:
        return "中", "support-medium"
    return "低/待补", "support-low"


def group_events_by_video(events: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[text(event.get("video_title") or "Untitled video")].append(event)
    return sorted(grouped.items(), key=lambda item: item[0])


def video_section_html(title: str, events: list[dict[str, Any]]) -> str:
    event_html = "\n".join(event_html_block(event) for event in events)
    published = first_non_empty(event.get("published_at") for event in events)
    return f"""<div class="video-card">
  <div class="video-head">
    <div>
      <h3>{escape(title)}</h3>
      <div class="muted">发布时间：{escape(text(published or "unknown"))}</div>
    </div>
    <div><span class="badge">{len(events)} events</span></div>
  </div>
  {event_html}
</div>"""


def event_html_block(event: dict[str, Any]) -> str:
    evidence = ", ".join(text(value) for value in event.get("evidence_refs") or []) or "none"
    risks = event.get("risk_flags") or []
    risk_badges = "".join(f"<span class='badge'>{escape(text(risk))}</span>" for risk in risks)
    contexts = event.get("news_context") or []
    context_html = "\n".join(context_html_block(context) for context in contexts)
    if not context_html:
        context_html = "<div class='empty'>暂无匹配新闻 facts。需要补充 news digest 或改进 ticker/entity mapping。</div>"
    return f"""<div class="event">
  <h3>{escape(text(event.get("instrument") or "unknown"))}</h3>
  <div>
    {badge("动作", event.get("action"))}
    {badge("方向", event.get("direction"))}
    {badge("周期", event.get("horizon"))}
    {badge("置信度", event.get("conviction"))}
  </div>
  <div class="event-grid">
    <div>
      <strong>UP 原始观点</strong>
      <p>{escape(text(event.get("entry_condition") or event.get("rationale") or "未记录明确入场条件。"))}</p>
      <p class="muted">失效/退出：{escape(text(event.get("exit_or_invalidation") or "未记录"))}</p>
    </div>
    <div>
      <strong>证据与风险</strong>
      <p class="muted">证据锚点：{escape(evidence)}</p>
      <div>{risk_badges or "<span class='badge'>no risk flags</span>"}</div>
    </div>
  </div>
  {context_html}
</div>"""


def context_html_block(context: dict[str, Any]) -> str:
    facts = context.get("facts") or []
    impacts = context.get("industry_impacts") or []
    relevance = context.get("market_relevance") or []
    source_links = " ".join(source_link(url) for url in context.get("source_urls") or [])
    facts_html = "".join(fact_item_html(fact) for fact in facts[:6])
    impacts_html = "".join(impact_row_html(impact) for impact in impacts[:6])
    relevance_html = "".join(relevance_row_html(item) for item in relevance[:6])
    return f"""<div class="context-block">
  <div class="context-title">
    <strong>新闻 Facts 对照：{escape(text(context.get("topic") or "unknown"))}</strong>
    <span class="badge">score {escape(str(context.get("match_score") or 0))}</span>
    <span class="badge">{escape(", ".join(context.get("matched_terms") or []) or "no terms")}</span>
  </div>
  <ul class="fact-list">{facts_html or "<li>暂无 fact 引用。</li>"}</ul>
  <table>
    <thead><tr><th>行业影响</th><th>机制</th><th>方向</th></tr></thead>
    <tbody>{impacts_html or "<tr><td colspan='3'>暂无行业影响。</td></tr>"}</tbody>
  </table>
  <table>
    <thead><tr><th>市场相关</th><th>说明</th><th>Fact refs</th></tr></thead>
    <tbody>{relevance_html or "<tr><td colspan='3'>暂无市场相关项。</td></tr>"}</tbody>
  </table>
  <p class="muted">来源：{source_links or "暂无 URL"} ｜ 用途：事实引用，不是交易建议。</p>
</div>"""


def fact_item_html(fact: dict[str, Any]) -> str:
    status = text(fact.get("status") or "unknown")
    statement = text(fact.get("statement") or "")
    fact_id = text(fact.get("fact_id") or "fact")
    return f"<li><strong>{escape(fact_id)}</strong> [{escape(status)}] {escape(statement)}</li>"


def impact_row_html(impact: dict[str, Any]) -> str:
    return f"""<tr>
  <td>{escape(text(impact.get("industry") or "unknown"))}</td>
  <td>{escape(text(impact.get("mechanism") or ""))}</td>
  <td>{escape(text(impact.get("possible_direction") or "unclear"))}</td>
</tr>"""


def relevance_row_html(item: dict[str, Any]) -> str:
    refs = ", ".join(text(ref) for ref in item.get("fact_refs") or [])
    return f"""<tr>
  <td>{escape(text(item.get("asset_or_sector") or "unknown"))}</td>
  <td>{escape(text(item.get("relevance") or ""))}</td>
  <td>{escape(refs)}</td>
</tr>"""


def aggregate_context_values(events: list[dict[str, Any]], key: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for event in events:
        for context in event.get("news_context") or []:
            for value in context.get(key) or []:
                item = text(value)
                if not item or item in seen:
                    continue
                seen.add(item)
                values.append(item)
    return values


def stat_html(label: str, value: Any) -> str:
    return f"<div class='stat'><span class='muted'>{escape(label)}</span><strong>{escape(str(value))}</strong></div>"


def badge(label: str, value: Any) -> str:
    resolved = text(value or "unknown")
    return f"<span class='badge'>{escape(label)}：{escape(resolved)}</span>"


def source_link(url: str) -> str:
    safe = escape(text(url))
    return f"<a href='{safe}' target='_blank' rel='noreferrer'>{safe}</a>"


def text(value: Any) -> str:
    return str(value).strip()


def first_non_empty(values: Any) -> Any:
    for value in values:
        if value:
            return value
    return None
