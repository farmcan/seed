from __future__ import annotations

import json
from datetime import UTC, datetime
from html import escape
from pathlib import Path

import yaml

from seed.agents.codex import run_codex_prompt
from seed.library import init_library, slugify
from seed.markdown import read_markdown_body

BOOK_METHOD_DISTILLER_SKILL_PATH = Path("skills/book-method-distiller/SKILL.md")


def book_note_output_path(*, library_root: Path, author: str, title: str) -> Path:
    init_library(library_root)
    return library_root / "notes" / f"{slugify(author)}-{slugify(title)}.book-note.md"


def book_semantics_output_path(*, library_root: Path, author: str, title: str) -> Path:
    init_library(library_root)
    return library_root / "semantics" / f"{slugify(author)}-{slugify(title)}.book-semantics.md"


def topic_profile_output_path(*, library_root: Path, topic: str) -> Path:
    init_library(library_root)
    return library_root / "distilled" / f"{slugify(topic)}.topic-profile.md"


def book_methods_output_path(
    *,
    library_root: Path,
    author: str,
    title: str,
    topic: str | None = None,
) -> Path:
    init_library(library_root)
    suffix = f".{slugify(topic)}" if topic else ""
    return library_root / "distilled" / f"{slugify(author)}-{slugify(title)}{suffix}.book-methods.json"


def book_source_output_path(*, library_root: Path, author: str, title: str) -> Path:
    init_library(library_root)
    return library_root / "notes" / f"{slugify(author)}-{slugify(title)}.book-source.json"


def book_methods_report_output_path(
    *,
    library_root: Path,
    author: str,
    title: str,
    topic: str | None = None,
) -> Path:
    init_library(library_root)
    suffix = f".{slugify(topic)}" if topic else ""
    return library_root / "reports" / f"{slugify(author)}-{slugify(title)}{suffix}.book-methods-report.html"


def book_methods_playbook_output_path(
    *,
    library_root: Path,
    author: str,
    title: str,
    topic: str | None = None,
) -> Path:
    init_library(library_root)
    suffix = f".{slugify(topic)}" if topic else ""
    return library_root / "checks" / f"{slugify(author)}-{slugify(title)}{suffix}.book-methods-playbook.md"


def write_book_note(
    output_path: Path,
    *,
    source_path: Path,
    author: str,
    title: str,
    location: str | None = None,
) -> Path:
    text = source_path.read_text(encoding="utf-8")
    metadata = {
        "source_type": "book-note",
        "author": author,
        "title": title,
        "location": location,
        "source_path": str(source_path),
        "created_at": datetime.now(UTC).isoformat(),
    }
    content = [
        "---",
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        text.strip(),
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(content), encoding="utf-8")
    return output_path


def write_book_semantics(
    output_path: Path,
    *,
    note_path: Path,
    author: str,
    title: str,
    topic: str | None = None,
) -> Path:
    body = read_markdown_body(note_path)
    key_points = extract_key_points(body)
    metadata = {
        "source_type": "book-semantics",
        "author": author,
        "title": title,
        "topic": topic,
        "note_path": str(note_path),
        "created_at": datetime.now(UTC).isoformat(),
    }
    content = [
        "---",
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        "# Book Semantics",
        "",
        "## Key Points",
        "",
        *(f"- {point}" for point in key_points),
        "",
        "## Methods And Principles",
        "",
        "- 待从多条笔记或人工 review 中提炼稳定方法论。",
        "",
        "## Agent Checks",
        "",
        "- 这个观点适用的上下文是什么？",
        "- 是否有反例、边界条件或作者没有展开的前提？",
        "- 能否转成可执行步骤或判断规则？",
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(content), encoding="utf-8")
    return output_path


def write_topic_profile(
    output_path: Path,
    *,
    topic: str,
    semantics_paths: list[Path],
) -> Path:
    sections = [
        "---",
        yaml.safe_dump(
            {
                "source_type": "topic-profile",
                "topic": topic,
                "semantics_paths": [str(path) for path in semantics_paths],
                "created_at": datetime.now(UTC).isoformat(),
            },
            allow_unicode=True,
            sort_keys=False,
        ).strip(),
        "---",
        "",
        f"# Topic Profile: {topic}",
        "",
    ]
    for path in semantics_paths:
        sections.extend(
            [
                f"## {path.stem}",
                "",
                read_markdown_body(path)[:1200],
                "",
            ]
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(sections), encoding="utf-8")
    return output_path


def build_book_methods_prompt(
    *,
    note_path: Path,
    author: str,
    title: str,
    topic: str | None = None,
    focus: str | None = None,
) -> str:
    skill = read_optional_text(BOOK_METHOD_DISTILLER_SKILL_PATH)
    evidence_blocks = build_book_evidence_blocks(note_path)
    generated_at = datetime.now(UTC).isoformat()
    return f"""Distill durable methodology from this book note.

Return only valid JSON. Do not wrap it in Markdown. Do not modify files.

Treat the note as a secondary source unless it contains direct quotes. Extract stable methods, principles, decision rules, boundaries, and anti-patterns. Preserve uncertainty and evidence references. Do not turn book ideas into finance or trading advice unless the text explicitly supports that use case.

Metadata:
- Author: {author}
- Title: {title}
- Topic: {topic or "general methodology"}
- Focus: {focus or "durable methods and reusable agent checks"}
- Generated at: {generated_at}
- Note path: {note_path}

<book_method_distiller_skill>
{skill}
</book_method_distiller_skill>

JSON schema:
{{
  "version": 1,
  "kind": "book_methods",
  "source_type": "book-note",
  "author": string,
  "title": string,
  "topic": string | null,
  "generated_at": string,
  "basis_path": string,
  "focus": string,
  "not_investment_advice": true,
  "stable_principles": [
    {{
      "principle": string,
      "why_it_matters": string,
      "evidence_refs": [string],
      "applicability": string,
      "boundaries": [string],
      "anti_patterns": [string],
      "confidence": "high" | "medium" | "low"
    }}
  ],
  "decision_rules": [
    {{
      "rule": string,
      "when_to_use": string,
      "inputs_needed": [string],
      "steps": [string],
      "failure_modes": [string],
      "evidence_refs": [string]
    }}
  ],
  "mental_models": [
    {{
      "model": string,
      "explanation": string,
      "use_cases": [string],
      "limits": [string],
      "evidence_refs": [string]
    }}
  ],
  "agent_checks": [
    {{
      "check": string,
      "purpose": string,
      "trigger": string | null,
      "evidence_refs": [string]
    }}
  ],
  "cross_source_hooks": [
    {{
      "hook": string,
      "can_compare_with": ["creator_profile" | "video_semantics" | "news_facts" | "earnings_facts" | "finance_digest" | "other"],
      "how_to_use": string,
      "evidence_refs": [string]
    }}
  ],
  "source_gaps": [string],
  "open_questions": [string],
  "summary": string
}}

<book_note_evidence_blocks>
{json.dumps(evidence_blocks, ensure_ascii=False, indent=2)}
</book_note_evidence_blocks>
"""


def run_book_methods_distillation(
    *,
    note_path: Path,
    output_path: Path,
    author: str,
    title: str,
    topic: str | None = None,
    focus: str | None = None,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    prompt = build_book_methods_prompt(
        note_path=note_path,
        author=author,
        title=title,
        topic=topic,
        focus=focus,
    )
    return run_codex_prompt(
        prompt=prompt,
        output_path=output_path,
        model=model,
        cwd=cwd or Path.cwd(),
        dry_run=dry_run,
    )


def build_book_evidence_blocks(
    note_path: Path,
    *,
    max_blocks: int = 80,
    max_chars: int = 9000,
) -> list[dict[str, str]]:
    body = read_markdown_body(note_path)
    blocks: list[dict[str, str]] = []
    chars_used = 0
    for block in extract_markdown_blocks(body):
        if chars_used >= max_chars or len(blocks) >= max_blocks:
            break
        clipped = block[:800]
        chars_used += len(clipped)
        blocks.append({"ref": f"B{len(blocks) + 1}", "text": clipped})
    return blocks or [{"ref": "B1", "text": "待补充读书笔记内容。"}]


def extract_markdown_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                blocks.append(" ".join(current).strip())
                current = []
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith(("- ", "* ")):
            if current:
                blocks.append(" ".join(current).strip())
                current = []
            blocks.append(stripped[2:].strip())
            continue
        current.append(stripped)
    if current:
        blocks.append(" ".join(current).strip())
    return [block for block in blocks if block]


def extract_key_points(text: str, *, limit: int = 8) -> list[str]:
    points = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ")):
            points.append(stripped[2:].strip())
        elif stripped.startswith("#"):
            continue
        else:
            points.append(stripped)
        if len(points) >= limit:
            break
    return points or ["待补充可提炼观点。"]


def read_optional_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_book_source_artifact(
    output_path: Path,
    *,
    note_path: Path,
    author: str,
    title: str,
    provider: str = "markdown",
    source_url: str | None = None,
    location: str | None = None,
    tags: list[str] | None = None,
) -> Path:
    evidence_blocks = build_book_evidence_blocks(note_path)
    entries = []
    for index, block in enumerate(evidence_blocks, start=1):
        evidence_id = str(block.get("ref") or block.get("id") or block.get("evidence_id") or f"B{index}")
        entries.append(
            {
                "evidence_id": evidence_id,
                "kind": "note_block",
                "chapter": None,
                "page": None,
                "location": location,
                "highlight": block.get("text") or block.get("content") or "",
                "note": None,
                "tags": tags or [],
                "source_url": source_url,
            }
        )

    artifact = {
        "version": 1,
        "kind": "book_source",
        "source_type": "book-note",
        "provider": provider,
        "author": author,
        "title": title,
        "source_path": str(note_path),
        "source_url": source_url,
        "location": location,
        "tags": tags or [],
        "imported_at": datetime.now(UTC).isoformat(),
        "entries": entries,
        "source_gaps": [
            "Chapter, page, and exact location are optional for markdown imports; add them when available.",
            "Direct quotes and secondary notes are not automatically distinguished in markdown imports.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def write_book_methods_report_html(output_path: Path, *, methods_path: Path) -> Path:
    methods = json.loads(methods_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_book_methods_report_html(methods, methods_path=methods_path), encoding="utf-8")
    return output_path


def write_book_methods_playbook_md(output_path: Path, *, methods_path: Path) -> Path:
    methods = json.loads(methods_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_book_methods_playbook_markdown(methods, methods_path=methods_path), encoding="utf-8")
    return output_path


def build_book_methods_report_html(methods: dict, *, methods_path: Path) -> str:
    title = str(methods.get("title") or "Untitled")
    author = str(methods.get("author") or "Unknown author")
    topic = methods.get("topic") or "general methodology"
    generated_at = methods.get("generated_at") or ""
    focus = methods.get("focus") or ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)} book methods</title>
  <style>
    :root {{
      --ink: #17211b;
      --muted: #69746d;
      --paper: #f7f1df;
      --panel: rgba(255, 252, 241, 0.92);
      --line: rgba(44, 66, 50, 0.18);
      --accent: #be5a2c;
      --accent-2: #1f7a6b;
      --shadow: 0 24px 80px rgba(41, 54, 43, 0.18);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 8% 10%, rgba(190, 90, 44, 0.22), transparent 28rem),
        radial-gradient(circle at 92% 4%, rgba(31, 122, 107, 0.2), transparent 24rem),
        linear-gradient(135deg, #f8efd9, #edf0dc 52%, #f6e2c9);
      font-family: Charter, "Iowan Old Style", "Palatino Linotype", serif;
    }}
    main {{ width: min(1180px, calc(100vw - 32px)); margin: 0 auto; padding: 42px 0 64px; }}
    .hero {{
      padding: 34px;
      border: 1px solid var(--line);
      border-radius: 30px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }}
    .eyebrow {{ color: var(--accent); font-size: 13px; letter-spacing: 0.14em; text-transform: uppercase; }}
    h1 {{ margin: 12px 0 8px; font-size: clamp(34px, 6vw, 76px); line-height: 0.92; max-width: 900px; }}
    h2 {{ margin: 36px 0 16px; font-size: 26px; }}
    h3 {{ margin: 0 0 10px; font-size: 20px; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
    .pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 12px;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.42);
      font-size: 14px;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }}
    .card {{
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 20px;
      background: rgba(255, 252, 241, 0.78);
      box-shadow: 0 14px 40px rgba(41, 54, 43, 0.08);
    }}
    .card p {{ margin: 8px 0; color: var(--muted); line-height: 1.55; }}
    .refs {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }}
    .ref {{ color: #fff; background: var(--accent-2); border-radius: 999px; padding: 4px 8px; font-size: 12px; }}
    ul {{ padding-left: 20px; }}
    li {{ margin: 6px 0; line-height: 1.45; }}
    .summary {{
      margin-top: 18px;
      padding: 18px 20px;
      border-left: 5px solid var(--accent);
      background: rgba(255, 255, 255, 0.38);
      border-radius: 18px;
      line-height: 1.65;
    }}
    @media (max-width: 720px) {{
      main {{ width: min(100vw - 20px, 1180px); padding-top: 18px; }}
      .hero {{ padding: 22px; border-radius: 22px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="eyebrow">Book method distillation</div>
      <h1>{escape(title)}</h1>
      <div class="meta">
        <span class="pill">Author: {escape(author)}</span>
        <span class="pill">Topic: {escape(str(topic))}</span>
        <span class="pill">Generated: {escape(str(generated_at))}</span>
        <span class="pill">Source: {escape(str(methods_path))}</span>
      </div>
      <div class="summary">{escape(str(methods.get("summary") or "No summary provided."))}</div>
      {_paragraph("Focus", focus)}
    </section>
    {_cards_section("Stable Principles", methods.get("stable_principles"), "principle", "why_it_matters")}
    {_cards_section("Decision Rules", methods.get("decision_rules"), "rule", "when_to_use")}
    {_cards_section("Mental Models", methods.get("mental_models"), "model", "explanation")}
    {_cards_section("Agent Checks", methods.get("agent_checks"), "check", "purpose")}
    {_cards_section("Cross-source Hooks", methods.get("cross_source_hooks"), "hook", "how_to_use")}
    {_list_section("Source Gaps", methods.get("source_gaps"))}
    {_list_section("Open Questions", methods.get("open_questions"))}
  </main>
</body>
</html>
"""


def build_book_methods_playbook_markdown(methods: dict, *, methods_path: Path) -> str:
    title = str(methods.get("title") or "Untitled")
    author = str(methods.get("author") or "Unknown author")
    lines = [
        f"# Book Methods Playbook: {title}",
        "",
        f"- Author: {author}",
        f"- Topic: {methods.get('topic') or 'general methodology'}",
        f"- Source: `{methods_path}`",
        "- Use status: draft until reviewed against source notes.",
        "",
        "## Before using this method",
        "",
        "- Check whether the task matches the book context.",
        "- Check whether the relevant method has evidence refs.",
        "- Check source gaps before applying the method to a high-stakes decision.",
        "- Do not convert general methods into investment, medical, legal, or safety advice.",
        "",
        "## Agent checks",
        "",
    ]
    for item in _as_list(methods.get("agent_checks")):
        lines.extend(
            [
                f"- {item.get('check') or 'Unnamed check'}",
                f"  - Purpose: {item.get('purpose') or 'not specified'}",
                f"  - Trigger: {item.get('trigger') or 'manual review'}",
                f"  - Evidence: {', '.join(_string_list(item.get('evidence_refs'))) or 'missing'}",
            ]
        )
    lines.extend(["", "## Decision rules", ""])
    for item in _as_list(methods.get("decision_rules")):
        lines.extend(
            [
                f"- {item.get('rule') or 'Unnamed rule'}",
                f"  - When to use: {item.get('when_to_use') or 'not specified'}",
                f"  - Inputs needed: {', '.join(_string_list(item.get('inputs_needed'))) or 'not specified'}",
                f"  - Evidence: {', '.join(_string_list(item.get('evidence_refs'))) or 'missing'}",
            ]
        )
    lines.extend(["", "## Cross-source hooks", ""])
    for item in _as_list(methods.get("cross_source_hooks")):
        lines.extend(
            [
                f"- {item.get('hook') or 'Unnamed hook'}",
                f"  - Compare with: {', '.join(_string_list(item.get('can_compare_with'))) or 'not specified'}",
                f"  - How to use: {item.get('how_to_use') or 'not specified'}",
                f"  - Evidence: {', '.join(_string_list(item.get('evidence_refs'))) or 'missing'}",
            ]
        )
    lines.extend(["", "## Source gaps", ""])
    lines.extend(f"- {gap}" for gap in _string_list(methods.get("source_gaps")) or ["No source gaps listed."])
    lines.extend(["", "## Open questions", ""])
    lines.extend(f"- {question}" for question in _string_list(methods.get("open_questions")) or ["No open questions listed."])
    return "\n".join(lines) + "\n"


def _cards_section(title: str, items: object, title_key: str, body_key: str) -> str:
    values = _as_list(items)
    if not values:
        return ""
    cards = []
    for item in values:
        heading = escape(str(item.get(title_key) or "Untitled"))
        body = escape(str(item.get(body_key) or ""))
        details = _detail_list(item)
        refs = "".join(f'<span class="ref">{escape(ref)}</span>' for ref in _string_list(item.get("evidence_refs")))
        cards.append(f'<article class="card"><h3>{heading}</h3><p>{body}</p>{details}<div class="refs">{refs}</div></article>')
    return f'<section><h2>{escape(title)}</h2><div class="grid">{"".join(cards)}</div></section>'


def _detail_list(item: dict) -> str:
    skip_keys = {
        "principle",
        "why_it_matters",
        "rule",
        "when_to_use",
        "model",
        "explanation",
        "check",
        "purpose",
        "hook",
        "how_to_use",
        "evidence_refs",
    }
    rows = []
    for key, value in item.items():
        if key in skip_keys or value in (None, "", []):
            continue
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            text = ", ".join(_string_list(value))
        else:
            text = str(value)
        rows.append(f"<li><strong>{escape(label)}:</strong> {escape(text)}</li>")
    return f"<ul>{''.join(rows)}</ul>" if rows else ""


def _list_section(title: str, items: object) -> str:
    values = _string_list(items)
    if not values:
        return ""
    rows = "".join(f"<li>{escape(value)}</li>" for value in values)
    return f'<section><h2>{escape(title)}</h2><article class="card"><ul>{rows}</ul></article></section>'


def _paragraph(label: str, value: object) -> str:
    if value in (None, ""):
        return ""
    return f'<p><strong>{escape(label)}:</strong> {escape(str(value))}</p>'


def _as_list(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item not in (None, "")]
