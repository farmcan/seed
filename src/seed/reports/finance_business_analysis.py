from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify


BUSINESS_ANALYSIS_SUFFIXES: tuple[str, ...] = (
    ".finance-digest.priced.news-context.json",
    ".finance-digest.news-context.json",
    ".finance-digest.priced.json",
    ".finance-digest.json",
    ".finance-outlook.json",
    ".json",
)


def finance_business_analysis_md_output_path(*, library_root: Path, source_path: Path) -> Path:
    init_library(library_root)
    return library_root / "reports" / f"{_source_stem(source_path)}.business-analysis.md"


def finance_business_analysis_html_output_path(*, library_root: Path, source_path: Path) -> Path:
    init_library(library_root)
    return library_root / "reports" / f"{_source_stem(source_path)}.business-analysis.html"


def write_finance_business_analysis_markdown(path: Path, markdown: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return path


def write_finance_business_analysis_html(path: Path, html: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def build_finance_business_analysis_markdown(
    outlook: dict[str, Any],
    *,
    source: dict[str, Any] | None = None,
    source_path: Path | None = None,
    outlook_report_path: Path | None = None,
) -> str:
    source = source if isinstance(source, dict) else {}
    business = _business_analysis(source, outlook)
    peer_context = _as_dict(outlook.get("peer_context") or source.get("peer_context"))
    first_principles = _as_dict(outlook.get("first_principles") or source.get("first_principles"))
    market_context = _as_dict(outlook.get("market_context") or source.get("market_context"))
    scenarios = _as_dict(outlook.get("scenarios") or source.get("market_scenarios"))
    target_asset = _text(
        peer_context.get("target_asset")
        or outlook.get("owner")
        or source.get("owner")
        or "unknown"
    )
    ticker = _text(peer_context.get("target_ticker") or market_context.get("ticker") or "unknown")
    generated_at = datetime.now(UTC).date().isoformat()
    lines: list[str] = [
        f"# {target_asset} {ticker} 主营业务、市场与股价情景分析",
        "",
        f"生成时间：{generated_at}",
        "说明：本报告只做公开资料研究和情景拆解，不提供买入、卖出或持有建议。",
    ]
    if outlook_report_path:
        lines.append(f"配套报告：`{outlook_report_path}`")
    if source_path:
        lines.append(f"源对象：`{source_path}`")
    lines.extend(
        [
            "",
            "## 1. 主营业务到底是什么",
            "",
            _text(
                business.get("business_model")
                or first_principles.get("business_model")
                or "待补充主营业务描述。"
            ),
            "",
        ]
    )
    revenue_segments = _as_list_of_dicts(business.get("revenue_segments"))
    if revenue_segments:
        lines.extend(
            _markdown_table(
                ["收入口径", "金额", "同比", "占比", "解释"],
                [
                    [
                        item.get("segment") or item.get("name"),
                        item.get("revenue") or item.get("amount"),
                        item.get("yoy") or item.get("yoy_pct"),
                        item.get("share") or item.get("share_pct"),
                        item.get("explanation") or item.get("note"),
                    ]
                    for item in revenue_segments
                ],
            )
        )
        lines.append("")
    revenue_logic = _text(business.get("revenue_logic") or first_principles.get("revenue_logic"))
    if revenue_logic:
        lines.extend([revenue_logic, ""])

    lines.extend(["## 2. 营收主要来自谁", ""])
    customer_sources = _as_string_list(business.get("customer_sources"))
    if customer_sources:
        lines.extend(f"- {item}" for item in customer_sources)
    else:
        customer_dependency = _text(first_principles.get("customer_dependency"))
        single_customer_risk = _text(first_principles.get("single_customer_risk"))
        if customer_dependency:
            lines.append(f"- 客户集中度：{customer_dependency}")
        if single_customer_risk:
            lines.append(f"- 大客户风险：{single_customer_risk}")
        if not customer_dependency and not single_customer_risk:
            lines.append("- 待补充客户类型、区域收入和集中度披露。")
    lines.append("")

    lines.extend(["## 3. 市场有多大", ""])
    market_layers = _as_list_of_dicts(business.get("market_size_layers"))
    if market_layers:
        lines.extend(
            _markdown_table(
                ["层级", "对公司的意义", "外部规模信号"],
                [
                    [
                        item.get("layer") or item.get("name"),
                        item.get("relevance") or item.get("meaning"),
                        item.get("signal") or item.get("market_size") or item.get("note"),
                    ]
                    for item in market_layers
                ],
            )
        )
    else:
        industry = _text(peer_context.get("industry"))
        lines.append(industry or "待补充市场规模、CAGR 和可服务市场边界。")
    lines.append("")

    lines.extend(["## 4. 竞争有多大", ""])
    competition_layers = _as_list_of_dicts(business.get("competition_layers"))
    if competition_layers:
        lines.extend(
            _markdown_table(
                ["竞争层", "代表", "对公司的压力"],
                [
                    [
                        item.get("layer") or item.get("name"),
                        item.get("representatives") or item.get("competitors"),
                        item.get("pressure") or item.get("note"),
                    ]
                    for item in competition_layers
                ],
            )
        )
    else:
        competitors = _as_string_list(first_principles.get("competitors"))
        peer_names = [
            _text(peer.get("name") or peer.get("ticker"))
            for peer in _as_list_of_dicts(peer_context.get("peers"))
        ]
        names = [item for item in competitors + peer_names if item]
        pressure = _text(first_principles.get("competitive_pressure"))
        lines.append(f"- 主要竞争者：{'; '.join(sorted(set(names))) or '待补充'}")
        lines.append(f"- 竞争压力：{pressure or '待补充'}")
    lines.append("")

    lines.extend(["## 4.1 AI 创作工具竞争现状", ""])
    competitive_watch = _as_list_of_dicts(
        business.get("competitive_watch")
        or market_context.get("competitive_watch")
        or source.get("competitive_watch")
    )
    if competitive_watch:
        lines.extend(
            _markdown_table(
                ["竞争者", "当前动作", "影响业务线", "压力", "不确定性"],
                [
                    [
                        item.get("competitor") or item.get("name"),
                        item.get("move") or item.get("current_state"),
                        item.get("affected_business_line") or item.get("business_line"),
                        item.get("pressure_level") or item.get("pressure"),
                        item.get("uncertainty") or item.get("note"),
                    ]
                    for item in competitive_watch
                ],
            )
        )
    else:
        ai_risk = _text(first_principles.get("aicoding_or_automation_risk"))
        lines.append(ai_risk or "待补充 Adobe、Canva、CapCut、基础模型和垂直应用的当前竞争动作。")
    lines.append("")

    lines.extend(["## 5. 未来股价可能的几种走势", ""])
    stock_paths = _as_list_of_dicts(business.get("stock_paths"))
    if not stock_paths:
        stock_paths = _stock_paths_from_scenarios(scenarios)
    if stock_paths:
        lines.extend(
            _markdown_table(
                ["情景", "股价路径/目标", "触发条件", "需要验证什么"],
                [
                    [
                        item.get("scenario") or item.get("name"),
                        item.get("path") or _target_line(item),
                        item.get("triggers") or item.get("trigger"),
                        item.get("validation_points") or item.get("validation"),
                    ]
                    for item in stock_paths
                ],
            )
        )
    else:
        lines.append("待补充基准、上行、下行情景。")
    lines.append("")

    lines.extend(["## 6. 接下来最该盯的指标", ""])
    metrics = _as_string_list(business.get("metrics_to_watch"))
    if not metrics:
        metrics = _metrics_from_scenarios(scenarios)
    if metrics:
        lines.extend(f"- {item}" for item in metrics)
    else:
        lines.append("- 待补充下一次财报、产品、竞争和市场指标。")
    lines.append("")

    source_gaps = _as_string_list(outlook.get("source_gaps") or source.get("source_gaps"))
    open_questions = _as_string_list(outlook.get("open_questions") or source.get("open_questions"))
    if source_gaps or open_questions:
        lines.extend(["## 7. 证据缺口与未决问题", ""])
        if source_gaps:
            lines.append("Source gaps：")
            lines.extend(f"- {item}" for item in source_gaps[:12])
            lines.append("")
        if open_questions:
            lines.append("Open questions：")
            lines.extend(f"- {item}" for item in open_questions[:12])
            lines.append("")

    lines.extend(["## 来源", ""])
    sources = _collect_sources(business, source, outlook)
    if sources:
        lines.extend(f"- {item}" for item in sources)
    else:
        lines.append("- 待补充来源。")
    lines.append("")
    return "\n".join(lines)


def build_finance_business_analysis_html(
    outlook: dict[str, Any],
    *,
    source: dict[str, Any] | None = None,
    source_path: Path | None = None,
    outlook_report_path: Path | None = None,
) -> str:
    markdown = build_finance_business_analysis_markdown(
        outlook,
        source=source,
        source_path=source_path,
        outlook_report_path=outlook_report_path,
    )
    body = _markdown_to_html(markdown)
    title = escape(_first_heading(markdown) or "财经业务分析报告")
    outlook_link = ""
    if outlook_report_path:
        outlook_link = (
            f'<a href="{escape(outlook_report_path.name)}">'
            "打开 Finance Outlook HTML</a>"
        )
    source_link = ""
    if source_path:
        source_link = f'<a href="{escape(source_path.name)}">查看源对象</a>'
    nav_links = "".join(link for link in (outlook_link, source_link) if link)
    if nav_links:
        nav_links = f'<div class="nav">{nav_links}</div>'
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    :root {{
      --bg: #f5f7f8;
      --panel: #ffffff;
      --ink: #16201d;
      --muted: #64706a;
      --line: #dbe3df;
      --accent: #0d6f68;
      --accent2: #8a5a28;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "PingFang SC", "Noto Sans SC", "Segoe UI", Arial, sans-serif;
      line-height: 1.62;
    }}
    .wrap {{ width: min(1120px, calc(100% - 32px)); margin: 22px auto 40px; }}
    .hero, .content {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }}
    .hero {{ padding: 22px 24px; margin-bottom: 14px; }}
    .content {{ padding: 18px 22px; }}
    .hero h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.25; }}
    .meta {{ color: var(--muted); font-size: 14px; }}
    .nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
    .nav a {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      text-decoration: none;
      color: var(--accent);
      background: #fafcfc;
      font-size: 13px;
    }}
    h1 {{ font-size: 28px; }}
    h2 {{ margin-top: 28px; border-top: 1px solid var(--line); padding-top: 18px; font-size: 22px; }}
    p {{ margin: 10px 0; }}
    ul {{ padding-left: 22px; }}
    li {{ margin: 6px 0; }}
    .table-wrap {{ overflow: auto; margin: 12px 0 18px; border: 1px solid var(--line); border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 10px 11px; text-align: left; vertical-align: top; }}
    th {{ background: #eef4f2; color: #24332f; font-weight: 700; }}
    tr:last-child td {{ border-bottom: 0; }}
    code {{ background: #eef4f2; border: 1px solid var(--line); border-radius: 5px; padding: 1px 5px; }}
    a {{ color: var(--accent); }}
    .callout {{
      border-left: 4px solid var(--accent2);
      background: #fff8ec;
      padding: 10px 12px;
      border-radius: 6px;
      margin: 12px 0;
      color: #46341d;
    }}
    .footer {{ color: var(--muted); font-size: 13px; margin-top: 14px; }}
    @media (max-width: 760px) {{
      .wrap {{ width: min(100% - 20px, 1120px); }}
      .hero, .content {{ padding: 16px; }}
      .hero h1 {{ font-size: 24px; }}
      h2 {{ font-size: 19px; }}
      th, td {{ min-width: 160px; }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <h1>{title}</h1>
      <div class="meta">非投资建议 ｜ Seed 本地产物</div>
      {nav_links}
    </section>
    <section class="content">
      <div class="callout">这份 HTML 是对业务、收入来源、市场空间、竞争格局和股价情景的可阅读补充；K 线图和目标价情景请看配套 Finance Outlook HTML。</div>
      {body}
    </section>
    <div class="footer">Generated by Seed local report chain. Sources are listed inside the report.</div>
  </main>
</body>
</html>"""


def _source_stem(path: Path) -> str:
    name = path.name
    for suffix in BUSINESS_ANALYSIS_SUFFIXES:
        if name.endswith(suffix):
            name = name.removesuffix(suffix)
            break
    return slugify(name)


def _business_analysis(source: dict[str, Any], outlook: dict[str, Any]) -> dict[str, Any]:
    value = source.get("business_analysis") or outlook.get("business_analysis")
    return value if isinstance(value, dict) else {}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
        elif isinstance(item, dict):
            text = item.get("text") or item.get("name") or item.get("metric") or item.get("note")
            if text:
                result.append(_text(text))
    return result


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "；".join(_text(item) for item in value if _text(item))
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if item not in (None, "", []):
                parts.append(f"{key}: {_text(item)}")
        return "；".join(parts)
    return str(value).strip()


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        normalized = list(row[: len(headers)])
        while len(normalized) < len(headers):
            normalized.append("")
        lines.append("| " + " | ".join(_cell(value) for value in normalized) + " |")
    return lines


def _cell(value: Any) -> str:
    text = _text(value) or "-"
    return text.replace("|", "\\|").replace("\n", " ")


def _stock_paths_from_scenarios(scenarios: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = [
        ("base_case", "基准"),
        ("upside_case", "上行"),
        ("downside_case", "下行"),
    ]
    result: list[dict[str, Any]] = []
    for key, label in mapping:
        item = _as_dict(scenarios.get(key))
        if not item:
            continue
        result.append(
            {
                "scenario": label,
                "path": _target_line(item),
                "triggers": item.get("triggers"),
                "validation_points": item.get("validation_points"),
            }
        )
    return result


def _target_line(item: dict[str, Any]) -> str:
    target = item.get("target_price")
    returns = item.get("returns")
    if target is None and returns is None:
        return "-"
    if returns is None:
        return f"目标价 {target}"
    if target is None:
        return f"{returns}%"
    return f"目标价 {target}（{returns}%）"


def _metrics_from_scenarios(scenarios: dict[str, Any]) -> list[str]:
    metrics: list[str] = []
    for key in ("base_case", "upside_case", "downside_case"):
        item = _as_dict(scenarios.get(key))
        for metric in _as_string_list(item.get("validation_points")):
            if metric and not metric.startswith("method:") and metric not in metrics:
                metrics.append(metric)
    return metrics


def _collect_sources(
    business: dict[str, Any],
    source: dict[str, Any],
    outlook: dict[str, Any],
) -> list[str]:
    sources: list[str] = []
    seen: set[str] = set()

    def add_ref(ref: Any) -> None:
        if isinstance(ref, str):
            text = ref.strip()
            key = text
        elif isinstance(ref, dict):
            title = _text(ref.get("title") or ref.get("source_title") or ref.get("name"))
            url = _text(ref.get("url") or ref.get("source_url"))
            note = _text(ref.get("note"))
            if title and url:
                text = f"{title}: {url}"
            else:
                text = title or url
            if note:
                text = f"{text}；{note}" if text else note
            key = url or text
        else:
            return
        if text and key not in seen:
            seen.add(key)
            sources.append(text)

    for ref in business.get("sources") or []:
        add_ref(ref)
    for block in (
        outlook.get("market_context"),
        source.get("market_context"),
        outlook.get("scenarios"),
        source.get("market_scenarios"),
    ):
        block_dict = _as_dict(block)
        for ref in block_dict.get("source_refs") or []:
            add_ref(ref)
    for item in _as_list_of_dicts(business.get("competitive_watch")):
        for ref in item.get("source_refs") or []:
            add_ref(ref)
    return sources


def _markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    html: list[str] = []
    table: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            html.append("</ul>")
            in_list = False

    def flush_table() -> None:
        nonlocal table
        if not table:
            return
        if len(table) >= 2:
            headers = _split_table_row(table[0])
            body = [_split_table_row(row) for row in table[2:]]
            html.append("<div class=\"table-wrap\"><table><thead><tr>")
            html.append("".join(f"<th>{_inline_html(item)}</th>" for item in headers))
            html.append("</tr></thead><tbody>")
            for row in body:
                html.append("<tr>" + "".join(f"<td>{_inline_html(item)}</td>" for item in row) + "</tr>")
            html.append("</tbody></table></div>")
        table = []

    for line in lines:
        if line.startswith("|") and line.rstrip().endswith("|"):
            close_list()
            table.append(line)
            continue
        flush_table()
        stripped = line.strip()
        if not stripped:
            close_list()
            continue
        if stripped.startswith("# "):
            close_list()
            html.append(f"<h1>{_inline_html(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            close_list()
            html.append(f"<h2>{_inline_html(stripped[3:])}</h2>")
        elif stripped.startswith("- "):
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{_inline_html(stripped[2:])}</li>")
        else:
            close_list()
            html.append(f"<p>{_inline_html(stripped)}</p>")
    close_list()
    flush_table()
    return "\n".join(html)


def _split_table_row(line: str) -> list[str]:
    return [item.strip().replace("\\|", "|") for item in line.strip().strip("|").split("|")]


def _inline_html(text: str) -> str:
    escaped = escape(text)
    escaped = escaped.replace("`", "")
    parts = []
    for token in escaped.split():
        if token.startswith(("https://", "http://")):
            token = f'<a href="{token}" target="_blank" rel="noopener noreferrer">{token}</a>'
        parts.append(token)
    return " ".join(parts)


def _first_heading(markdown: str) -> str | None:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None
