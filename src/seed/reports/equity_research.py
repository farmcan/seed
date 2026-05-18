from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify


def equity_research_report_output_path(*, library_root: Path, ledger_path: Path) -> Path:
    init_library(library_root)
    name = ledger_path.name
    for suffix in (
        ".equity-research.json",
        ".financial-statement-review.json",
        ".json",
    ):
        if name.endswith(suffix):
            name = name.removesuffix(suffix)
            break
    return library_root / "reports" / f"{slugify(name)}.equity-research-report.html"


def text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _as_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item.strip()]


def _list_html(values: list[str], *, limit: int = 12) -> str:
    if not values:
        return "<li>暂无</li>"
    return "".join(f"<li>{escape(item)}</li>" for item in values[:limit])


def build_equity_research_report_html(
    payload: dict[str, Any],
    *,
    ledger_path: Path | None = None,
) -> str:
    report_info = payload.get("report") if isinstance(payload.get("report"), dict) else {}
    report_id = text(report_info.get("report_id") or ledger_path.stem if ledger_path else "equity-research")
    issuer = text(report_info.get("issuer") or "unknown")
    ticker = text(report_info.get("ticker") or "unknown")
    rating = text(report_info.get("rating") or "未披露")
    target_price_range = text(report_info.get("target_price_range") or "未披露")
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    events = payload.get("viewpoint_events")
    if not isinstance(events, list):
        events = []

    not_investment_advice = bool(payload.get("not_investment_advice", False))
    notes_summary = text(payload.get("notes_summary") or "未填写")
    source_gaps = _as_list(payload.get("source_gaps"))
    open_questions = _as_list(payload.get("open_questions"))

    events_html_rows = []
    total_risk_flags = 0
    for event in events:
        if not isinstance(event, dict):
            continue
        claim = escape(text(event.get("claim") or ""))
        support = escape(text("; ".join(_as_list(event.get("support")))))
        confidence = escape(text(event.get("conviction") or "unknown"))
        evidence_level = escape(text(event.get("evidence_level") or "reported"))
        horizon = escape(text(event.get("horizon") or "unknown"))
        exit_condition = escape(text(event.get("exit_or_invalidation") or "未披露"))
        uncertainty = escape(text(event.get("uncertainty") or ""))
        risk_flags = _as_list(event.get("risk_flags"))
        risk_display = escape("；".join(risk_flags) if risk_flags else "无")
        total_risk_flags += len(risk_flags)
        support_refs = _as_list(event.get("support_refs"))
        support_refs_html = _list_html(support_refs)
        open_questions_html = _list_html(_as_list(event.get("open_questions")))
        open_questions_block = (
            f'<ul class="items">{open_questions_html}</ul>' if open_questions_html != "<li>暂无</li>" else ""
        )
        events_html_rows.append(
            f"""
            <article class='event'>
              <h3>{claim}</h3>
              <div class='meta'>证据强度：{evidence_level} ｜ 置信度：{confidence} ｜ 时间窗：{horizon}</div>
              <p><strong>失效条件：</strong>{exit_condition}</p>
              <p><strong>支持依据：</strong>{support or "未提供"}</p>
              <div class='grid'>
                <div>
                  <h4>来源引用</h4>
                  <ul class='items'>{support_refs_html}</ul>
                </div>
                <div>
                  <h4>风险信号</h4>
                  <p>{risk_display}</p>
                </div>
              </div>
              {f'<p><strong>不确定性：</strong>{uncertainty}</p>' if uncertainty else ''}
              {open_questions_block}
            </article>
            """
        )

    if not events_html_rows:
        events_html_rows = ["<p>未识别到有效观点事件。</p>"]

    digest_link = (
        f"<a href='{escape(str(ledger_path))}'>{escape(ledger_path.name)}</a>"
        if ledger_path
        else "inline payload"
    )

    return f"""<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Equity Research Report - {escape(report_id)}</title>
    <style>
      :root {{
        --bg: #f4f7f9;
        --panel: #fff;
        --ink: #17211d;
        --muted: #65716b;
        --line: #dce2dd;
        --teal: #0d6f68;
        --red: #b74d32;
        --amber: #a46a13;
      }}
      body {{
        margin: 0;
        background: var(--bg);
        color: var(--ink);
        font-family: "PingFang SC", "Noto Sans SC", "Segoe UI", sans-serif;
        line-height: 1.55;
      }}
      .container {{
        width: min(1100px, calc(100% - 30px));
        margin: 18px auto 30px;
      }}
      .card {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
      }}
      h1 {{ margin: 0 0 6px; font-size: 30px; }}
      .muted {{ color: var(--muted); }}
      .summary {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
      }}
      .stat {{
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 10px;
        background: #fafcfc;
      }}
      .stat strong {{ font-size: 22px; display: block; color: var(--teal); }}
      .tag {{
        display: inline-block;
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 2px 8px;
        font-size: 12px;
        margin-right: 5px;
        background: #f8faf9;
      }}
      .items {{ margin: 8px 0 0; padding-left: 20px; }}
      .meta {{ color: var(--muted); font-size: 13px; margin-bottom: 10px; }}
      .event {{ border: 1px solid var(--line); border-radius: 8px; padding: 14px; margin-bottom: 10px; background: #fff; }}
      .grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-top: 8px;
      }}
      h3 {{ margin: 0 0 8px; font-size: 18px; }}
      h4 {{ margin: 0 0 6px; font-size: 14px; }}
      .disclaimer {{ color: var(--amber); font-size: 13px; }}
      @media (max-width: 820px) {{
        .summary {{ grid-template-columns: 1fr 1fr; }}
        .grid {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="card">
        <h1>研报观点蒸馏报告</h1>
        <div class="muted">标的：{escape(issuer)}（{escape(ticker)}） ｜ 报告 ID：{escape(report_id)}</div>
        <div class="muted">发行/目标：{escape(rating)} ｜ 目标价区间：{escape(target_price_range)} ｜ 生成时间：{escape(generated_at)}</div>
        <p class="disclaimer">说明：此报告仅展示公开研报观点与证据映射，非投资建议。最终判断请以主文档和原始报告为准。</p>
        <div class="summary">
          <div class="stat"><strong>{len(events)}</strong>观点事件</div>
          <div class="stat"><strong>{total_risk_flags}</strong>风险信号</div>
          <div class="stat"><strong>{len(_as_list(payload.get('open_questions')))}</strong>未决问题</div>
          <div class="stat"><strong>{'是' if not_investment_advice else '否'}</strong>输出约束</div>
        </div>
      </div>

      <div class="card">
        <h2>观点事件</h2>
        {"".join(events_html_rows)}
      </div>

      <div class="card">
        <h2>证据缺口与未决问题</h2>
        <p><span class="tag">Source Gaps</span></p>
        <ul class="items">{_list_html(source_gaps)}</ul>
        <p><span class="tag">Open Questions</span></p>
        <ul class="items">{_list_html(open_questions)}</ul>
      </div>

      <div class="card">
        <h2>摘要</h2>
        <p>{escape(notes_summary)}</p>
        <p class="muted">源对象：{digest_link}</p>
      </div>
    </div>
  </body>
</html>
"""


def write_equity_research_report_html(path: Path, html: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path
