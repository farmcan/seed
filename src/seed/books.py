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


def book_homepage_output_path(
    *,
    library_root: Path,
    author: str,
    title: str,
    topic: str | None = None,
) -> Path:
    init_library(library_root)
    suffix = f".{slugify(topic)}" if topic else ""
    return library_root / "reports" / f"{slugify(author)}-{slugify(title)}{suffix}.book-homepage.html"


def book_author_profile_output_path(
    *,
    library_root: Path,
    author: str,
    topic: str | None = None,
) -> Path:
    init_library(library_root)
    suffix = f".{slugify(topic)}" if topic else ""
    return library_root / "distilled" / f"{slugify(author)}{suffix}.book-author-profile.json"


def book_author_homepage_output_path(
    *,
    library_root: Path,
    author: str,
    topic: str | None = None,
) -> Path:
    init_library(library_root)
    suffix = f".{slugify(topic)}" if topic else ""
    return library_root / "reports" / f"{slugify(author)}{suffix}.book-author-homepage.html"


def book_layers_output_path(
    *,
    library_root: Path,
    author: str,
    title: str,
    topic: str | None = None,
) -> Path:
    init_library(library_root)
    suffix = f".{slugify(topic)}" if topic else ""
    return library_root / "distilled" / f"{slugify(author)}-{slugify(title)}{suffix}.book-layers.json"


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
    layer_plan = build_book_layer_artifact(
        note_path=note_path,
        author=author,
        title=title,
        topic=topic,
    )
    evidence_blocks = [
        {"ref": block["ref"], "text": block["text"], "section_id": block.get("section_id")}
        for block in layer_plan["blocks"]
    ]
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

<book_layer_plan>
{json.dumps(layer_plan, ensure_ascii=False, indent=2)}
</book_layer_plan>
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
    blocks = [
        {"ref": block["ref"], "text": block["text"]}
        for block in build_layered_book_blocks(note_path, max_blocks=max_blocks, max_chars=max_chars)
    ]
    return blocks or [{"ref": "B1", "text": "待补充读书笔记内容。"}]


def build_book_layer_artifact(
    *,
    note_path: Path,
    author: str,
    title: str,
    topic: str | None = None,
    max_blocks: int = 120,
    max_chars: int = 20000,
) -> dict[str, object]:
    blocks = build_layered_book_blocks(note_path, max_blocks=max_blocks, max_chars=max_chars)
    sections = build_book_sections(blocks)
    return {
        "version": 1,
        "kind": "book_layers",
        "source_type": "book-note",
        "author": author,
        "title": title,
        "topic": topic,
        "basis_path": str(note_path),
        "generated_at": datetime.now(UTC).isoformat(),
        "layers": ["block", "section", "book"],
        "blocks": blocks or [{"ref": "B1", "text": "待补充读书笔记内容。", "section_id": "section-001"}],
        "sections": sections,
        "book_layer": {
            "evidence_refs": [block["ref"] for block in blocks],
            "section_ids": [section["section_id"] for section in sections],
            "distillation_strategy": "section methods -> book methods -> topic profile",
        },
        "source_gaps": book_layer_source_gaps(blocks, sections),
    }


def write_book_layer_artifact(output_path: Path, artifact: dict[str, object]) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def build_layered_book_blocks(
    note_path: Path,
    *,
    max_blocks: int,
    max_chars: int,
) -> list[dict[str, object]]:
    body = read_markdown_body(note_path)
    raw_blocks = extract_markdown_blocks_with_headings(body)
    blocks: list[dict[str, object]] = []
    chars_used = 0
    for raw in raw_blocks:
        if chars_used >= max_chars or len(blocks) >= max_blocks:
            break
        clipped = str(raw["text"])[:800]
        chars_used += len(clipped)
        ref = f"B{len(blocks) + 1}"
        section_title = str(raw.get("section_title") or "Unsectioned")
        blocks.append(
            {
                "ref": ref,
                "text": clipped,
                "section_id": section_id(section_title),
                "section_title": section_title,
                "heading_path": raw.get("heading_path") or [],
                "char_count": len(clipped),
                "layer": "block",
            }
        )
    return blocks


def extract_markdown_blocks_with_headings(text: str) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    current: list[str] = []
    heading_stack: list[tuple[int, str]] = []

    def flush() -> None:
        if not current:
            return
        heading_path = [title for _, title in heading_stack]
        section_title = heading_path[-1] if heading_path else "Unsectioned"
        blocks.append(
            {
                "text": " ".join(current).strip(),
                "heading_path": heading_path,
                "section_title": section_title,
            }
        )
        current.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("#"):
            flush()
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped.lstrip("#").strip()
            heading_stack = [(item_level, item_title) for item_level, item_title in heading_stack if item_level < level]
            heading_stack.append((level, title))
            continue
        if stripped.startswith(("- ", "* ")):
            flush()
            current.append(stripped[2:].strip())
            flush()
            continue
        current.append(stripped)
    flush()
    return [block for block in blocks if str(block.get("text") or "").strip()]


def build_book_sections(blocks: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    order: list[str] = []
    for block in blocks:
        section = str(block.get("section_id") or "section-001")
        if section not in grouped:
            grouped[section] = []
            order.append(section)
        grouped[section].append(block)

    sections = []
    for section in order:
        section_blocks = grouped[section]
        title = str(section_blocks[0].get("section_title") or "Unsectioned")
        refs = [str(block["ref"]) for block in section_blocks]
        sections.append(
            {
                "section_id": section,
                "title": title,
                "heading_path": section_blocks[0].get("heading_path") or [],
                "evidence_refs": refs,
                "block_count": len(section_blocks),
                "summary_candidate": summarize_section_candidate(section_blocks),
                "method_candidates": method_candidates_from_blocks(section_blocks),
                "source_gaps": section_source_gaps(section_blocks),
            }
        )
    return sections


def section_id(title: str) -> str:
    slug = slugify(title)
    return f"section-{slug}" if slug else "section-001"


def summarize_section_candidate(blocks: list[dict[str, object]]) -> str:
    text = " ".join(str(block.get("text") or "") for block in blocks)
    return text[:360] + ("..." if len(text) > 360 else "")


def method_candidates_from_blocks(blocks: list[dict[str, object]], *, limit: int = 5) -> list[dict[str, object]]:
    candidates = []
    for block in blocks:
        text = str(block.get("text") or "")
        if looks_method_like(text):
            candidates.append(
                {
                    "evidence_ref": block.get("ref"),
                    "candidate": text[:280],
                    "status": "candidate_needs_distillation",
                }
            )
        if len(candidates) >= limit:
            break
    return candidates


def looks_method_like(text: str) -> bool:
    lower = text.lower()
    keywords = [
        "should",
        "must",
        "rule",
        "principle",
        "method",
        "avoid",
        "check",
        "步骤",
        "原则",
        "方法",
        "避免",
        "检查",
        "边界",
    ]
    return any(keyword in lower for keyword in keywords)


def section_source_gaps(blocks: list[dict[str, object]]) -> list[str]:
    gaps = []
    if not any(block.get("heading_path") for block in blocks):
        gaps.append("No Markdown heading was available for this section.")
    if len(blocks) == 1:
        gaps.append("Only one evidence block is available; section-level conclusion should remain provisional.")
    return gaps


def book_layer_source_gaps(blocks: list[dict[str, object]], sections: list[dict[str, object]]) -> list[str]:
    gaps = []
    if not blocks:
        gaps.append("No usable evidence blocks were found in the note.")
    if not sections:
        gaps.append("No section/chapter layer could be inferred.")
    if len(sections) <= 1:
        gaps.append("The note has one or zero inferred sections; chapter-level distillation is limited.")
    if any(not block.get("heading_path") for block in blocks):
        gaps.append("Some blocks have no heading path; add chapter/section headings for better layering.")
    return gaps


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
    evidence_blocks = build_layered_book_blocks(note_path, max_blocks=80, max_chars=9000) or [
        {
            "ref": "B1",
            "text": "待补充读书笔记内容。",
            "section_title": "Unsectioned",
            "heading_path": [],
        }
    ]
    entries = []
    for index, block in enumerate(evidence_blocks, start=1):
        evidence_id = str(block.get("ref") or block.get("id") or block.get("evidence_id") or f"B{index}")
        entries.append(
            {
                "evidence_id": evidence_id,
                "kind": "note_block",
                "chapter": block.get("section_title"),
                "heading_path": block.get("heading_path") or [],
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


def write_book_homepage_html(
    output_path: Path,
    *,
    author: str,
    title: str,
    topic: str | None = None,
    source_path: Path | None = None,
    layers_path: Path | None = None,
    methods_path: Path | None = None,
    report_path: Path | None = None,
    playbook_path: Path | None = None,
) -> Path:
    source = read_json_artifact(source_path)
    layers = read_json_artifact(layers_path)
    methods = read_json_artifact(methods_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_book_homepage_html(
            author=author,
            title=title,
            topic=topic or methods.get("topic"),
            source=source,
            layers=layers,
            methods=methods,
            asset_paths={
                "book-source": source_path,
                "book-layers": layers_path,
                "book-methods": methods_path,
                "methods-report": report_path,
                "agent-playbook": playbook_path,
            },
        ),
        encoding="utf-8",
    )
    return output_path


def build_book_homepage_html(
    *,
    author: str,
    title: str,
    topic: object,
    source: dict,
    layers: dict,
    methods: dict,
    asset_paths: dict[str, Path | None],
) -> str:
    entries = source.get("entries") if isinstance(source.get("entries"), list) else []
    blocks = layers.get("blocks") if isinstance(layers.get("blocks"), list) else []
    sections = layers.get("sections") if isinstance(layers.get("sections"), list) else []
    source_gaps = _string_list(source.get("source_gaps")) + _string_list(layers.get("source_gaps")) + _string_list(methods.get("source_gaps"))
    metrics = [
        ("B* blocks", len(blocks) or len(entries)),
        ("Sections", len(sections)),
        ("Principles", len(_as_list(methods.get("stable_principles")))),
        ("Rules", len(_as_list(methods.get("decision_rules")))),
        ("Agent checks", len(_as_list(methods.get("agent_checks")))),
        ("Hooks", len(_as_list(methods.get("cross_source_hooks")))),
    ]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)} book homepage</title>
  {book_homepage_styles()}
</head>
<body>
  <main>
    <section class="topline">
      <div>
        <div class="eyebrow">Book Homepage</div>
        <h1>{escape(title)}</h1>
        <p class="lede">{escape(str(methods.get("summary") or "Source-grounded methods, section evidence, and agent-ready checks for this book."))}</p>
      </div>
      <div class="meta">
        <span>{escape(author)}</span>
        <span>{escape(str(topic or "general methodology"))}</span>
        <span>{escape(str(methods.get("generated_at") or layers.get("generated_at") or ""))}</span>
      </div>
    </section>
    {metric_grid(metrics)}
    <section class="band">
      <h2>Asset Links</h2>
      <div class="link-grid">{asset_links(asset_paths)}</div>
    </section>
    <section class="band">
      <h2>Layer Map</h2>
      <div class="grid">{section_cards(sections)}</div>
    </section>
    {_cards_section("Stable Principles", methods.get("stable_principles"), "principle", "why_it_matters")}
    {_cards_section("Decision Rules", methods.get("decision_rules"), "rule", "when_to_use")}
    {_cards_section("Agent Checks", methods.get("agent_checks"), "check", "purpose")}
    {_cards_section("Cross-source Hooks", methods.get("cross_source_hooks"), "hook", "how_to_use")}
    {_list_section("Source Gaps", source_gaps)}
    {_list_section("Open Questions", methods.get("open_questions"))}
  </main>
</body>
</html>
"""


def build_book_author_profile_artifact(
    *,
    author: str,
    methods_paths: list[Path],
    topic: str | None = None,
) -> dict[str, object]:
    books = []
    principles = []
    rules = []
    models = []
    hooks = []
    source_gaps = []
    open_questions = []
    topics: dict[str, int] = {}
    for path in methods_paths:
        methods = read_json_artifact(path)
        if not methods:
            continue
        book_topic = methods.get("topic") or "general methodology"
        topics[str(book_topic)] = topics.get(str(book_topic), 0) + 1
        book = {
            "title": methods.get("title") or path.stem,
            "author": methods.get("author") or author,
            "topic": methods.get("topic"),
            "book_methods_path": str(path),
            "book_layers_path": str(infer_book_layers_path(path)) if infer_book_layers_path(path).exists() else None,
            "stable_principles_count": len(_as_list(methods.get("stable_principles"))),
            "decision_rules_count": len(_as_list(methods.get("decision_rules"))),
            "agent_checks_count": len(_as_list(methods.get("agent_checks"))),
            "cross_source_hooks_count": len(_as_list(methods.get("cross_source_hooks"))),
            "summary": methods.get("summary"),
        }
        books.append(book)
        principles.extend(with_book_context(methods.get("stable_principles"), book, "principle"))
        rules.extend(with_book_context(methods.get("decision_rules"), book, "rule"))
        models.extend(with_book_context(methods.get("mental_models"), book, "model"))
        hooks.extend(with_book_context(methods.get("cross_source_hooks"), book, "hook"))
        source_gaps.extend(prefixed_items(_string_list(methods.get("source_gaps")), book))
        open_questions.extend(prefixed_items(_string_list(methods.get("open_questions")), book))

    return {
        "version": 1,
        "kind": "book_author_profile",
        "author": author,
        "topic": topic,
        "generated_at": datetime.now(UTC).isoformat(),
        "books": books,
        "topic_map": [{"topic": name, "book_count": count} for name, count in sorted(topics.items())],
        "recurring_principles": recurring_items(principles, "principle"),
        "principles": principles,
        "decision_rules": rules,
        "mental_models": models,
        "cross_source_hooks": hooks,
        "source_gaps": source_gaps,
        "open_questions": open_questions,
        "profile_status": "deterministic_aggregation",
        "source_gaps_note": "This profile aggregates existing book-methods artifacts; it is not yet an LLM-synthesized author interpretation.",
    }


def write_book_author_profile_artifact(output_path: Path, artifact: dict[str, object]) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def write_book_author_homepage_html(output_path: Path, *, profile_path: Path) -> Path:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_book_author_homepage_html(profile, profile_path=profile_path), encoding="utf-8")
    return output_path


def build_book_author_homepage_html(profile: dict, *, profile_path: Path) -> str:
    author = str(profile.get("author") or "Unknown author")
    topic = profile.get("topic") or "all topics"
    books = _as_list(profile.get("books"))
    metrics = [
        ("Books", len(books)),
        ("Principles", len(_as_list(profile.get("principles")))),
        ("Rules", len(_as_list(profile.get("decision_rules")))),
        ("Models", len(_as_list(profile.get("mental_models")))),
        ("Hooks", len(_as_list(profile.get("cross_source_hooks")))),
        ("Recurring", len(_as_list(profile.get("recurring_principles")))),
    ]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(author)} book author homepage</title>
  {book_homepage_styles()}
</head>
<body>
  <main>
    <section class="topline">
      <div>
        <div class="eyebrow">Book Author Homepage</div>
        <h1>{escape(author)}</h1>
        <p class="lede">多本书/笔记的确定性聚合视图，用来观察作者反复出现的方法、规则、模型和跨来源对照钩子。</p>
      </div>
      <div class="meta">
        <span>{escape(str(topic))}</span>
        <span>{escape(str(profile.get("profile_status") or "deterministic"))}</span>
        <span>{escape(str(profile_path))}</span>
      </div>
    </section>
    {metric_grid(metrics)}
    <section class="band">
      <h2>Books</h2>
      <div class="grid">{author_book_cards(books)}</div>
    </section>
    {_cards_section("Recurring Principles", profile.get("recurring_principles"), "principle", "summary")}
    {_cards_section("Decision Rules", profile.get("decision_rules"), "rule", "when_to_use")}
    {_cards_section("Mental Models", profile.get("mental_models"), "model", "explanation")}
    {_cards_section("Cross-source Hooks", profile.get("cross_source_hooks"), "hook", "how_to_use")}
    {_list_section("Source Gaps", profile.get("source_gaps"))}
    {_list_section("Open Questions", profile.get("open_questions"))}
  </main>
</body>
</html>
"""


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


def read_json_artifact(path: Path | None) -> dict:
    if not path or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def infer_book_layers_path(methods_path: Path) -> Path:
    return methods_path.with_name(methods_path.name.replace(".book-methods.json", ".book-layers.json"))


def find_author_book_method_paths(*, library_root: Path, author: str, topic: str | None = None) -> list[Path]:
    init_library(library_root)
    paths = sorted((library_root / "distilled").glob(f"{slugify(author)}-*.book-methods.json"))
    matched = []
    for path in paths:
        data = read_json_artifact(path)
        if data.get("author") and str(data.get("author")) != author:
            continue
        if topic is not None and data.get("topic") != topic:
            continue
        matched.append(path)
    return matched


def with_book_context(items: object, book: dict[str, object], label_key: str) -> list[dict[str, object]]:
    values = []
    for item in _as_list(items):
        updated = dict(item)
        updated["book_title"] = book.get("title")
        updated["book_topic"] = book.get("topic")
        updated["book_methods_path"] = book.get("book_methods_path")
        if label_key in updated and "summary" not in updated:
            updated["summary"] = updated.get(label_key)
        values.append(updated)
    return values


def prefixed_items(items: list[str], book: dict[str, object]) -> list[str]:
    title = str(book.get("title") or "Untitled")
    return [f"{title}: {item}" for item in items]


def recurring_items(items: list[dict[str, object]], key: str) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for item in items:
        label = str(item.get(key) or "").strip()
        if not label:
            continue
        normalized = " ".join(label.lower().split())
        grouped.setdefault(normalized, []).append(item)
    recurring = []
    for group in grouped.values():
        if len(group) < 2:
            continue
        first = group[0]
        recurring.append(
            {
                key: first.get(key),
                "summary": f"Appears in {len(group)} book-method entries.",
                "book_titles": sorted({str(item.get("book_title")) for item in group if item.get("book_title")}),
                "evidence_refs": sorted(
                    {
                        ref
                        for item in group
                        for ref in _string_list(item.get("evidence_refs"))
                    }
                ),
            }
        )
    return recurring


def metric_grid(metrics: list[tuple[str, object]]) -> str:
    cards = "".join(
        f'<div class="metric"><strong>{escape(str(value))}</strong><span>{escape(label)}</span></div>'
        for label, value in metrics
    )
    return f'<section class="metrics">{cards}</section>'


def asset_links(paths: dict[str, Path | None]) -> str:
    links = []
    for label, path in paths.items():
        if path and path.exists():
            links.append(f'<a class="asset" href="{escape(str(path))}"><strong>{escape(label)}</strong><span>{escape(path.name)}</span></a>')
        else:
            links.append(f'<div class="asset missing"><strong>{escape(label)}</strong><span>missing</span></div>')
    return "".join(links)


def section_cards(sections: object) -> str:
    values = _as_list(sections)
    if not values:
        return '<article class="card"><h3>No section layer</h3><p>Add Markdown headings to improve book layering.</p></article>'
    cards = []
    for section in values:
        refs = "".join(f'<span class="ref">{escape(ref)}</span>' for ref in _string_list(section.get("evidence_refs"))[:8])
        candidates = _as_list(section.get("method_candidates"))
        cards.append(
            "<article class=\"card\">"
            f"<h3>{escape(str(section.get('title') or section.get('section_id') or 'Section'))}</h3>"
            f"<p>{escape(str(section.get('summary_candidate') or ''))}</p>"
            f"<p class=\"muted\">{len(candidates)} method candidates · {section.get('block_count') or 0} blocks</p>"
            f"<div class=\"refs\">{refs}</div>"
            "</article>"
        )
    return "".join(cards)


def author_book_cards(books: object) -> str:
    values = _as_list(books)
    if not values:
        return '<article class="card"><h3>No books found</h3><p>Run book pipelines or pass book-methods paths first.</p></article>'
    cards = []
    for book in values:
        methods_path = book.get("book_methods_path")
        layers_path = book.get("book_layers_path")
        cards.append(
            "<article class=\"card\">"
            f"<h3>{escape(str(book.get('title') or 'Untitled'))}</h3>"
            f"<p>{escape(str(book.get('summary') or 'No summary provided.'))}</p>"
            "<ul>"
            f"<li>Topic: {escape(str(book.get('topic') or 'general methodology'))}</li>"
            f"<li>Principles: {escape(str(book.get('stable_principles_count') or 0))}</li>"
            f"<li>Rules: {escape(str(book.get('decision_rules_count') or 0))}</li>"
            f"<li>Hooks: {escape(str(book.get('cross_source_hooks_count') or 0))}</li>"
            "</ul>"
            f"{path_link('methods', methods_path)}{path_link('layers', layers_path)}"
            "</article>"
        )
    return "".join(cards)


def path_link(label: str, path: object) -> str:
    if not path:
        return ""
    text = str(path)
    return f'<p><a href="{escape(text)}">{escape(label)}: {escape(Path(text).name)}</a></p>'


def book_homepage_styles() -> str:
    return """<style>
    :root {
      --ink: #17211f;
      --muted: #62706a;
      --line: #d7e0dc;
      --panel: #ffffff;
      --soft: #eef5f2;
      --accent: #1e6b68;
      --accent-2: #9a4f2d;
      --bg: #f6f8f7;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    main { width: min(1180px, calc(100vw - 32px)); margin: 0 auto; padding: 32px 0 56px; }
    .topline {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(240px, 340px);
      gap: 22px;
      align-items: end;
      padding-bottom: 22px;
      border-bottom: 1px solid var(--line);
    }
    .eyebrow { color: var(--accent); font-size: 12px; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; }
    h1 { margin: 8px 0; font-size: clamp(34px, 5vw, 64px); line-height: 0.96; letter-spacing: 0; }
    h2 { margin: 0 0 14px; font-size: 22px; }
    h3 { margin: 0 0 8px; font-size: 17px; }
    .lede { color: var(--muted); max-width: 780px; line-height: 1.6; }
    .meta { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
    .meta span, .pill {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 999px;
      padding: 7px 10px;
      color: var(--muted);
      font-size: 13px;
    }
    .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 20px 0; }
    .metric, .card, .asset {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: 0 12px 32px rgba(33, 45, 42, 0.06);
    }
    .metric { padding: 16px; }
    .metric strong { display: block; font-size: 28px; color: var(--accent); }
    .metric span, .muted { color: var(--muted); }
    .band, section { margin-top: 24px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }
    .card { padding: 18px; }
    .card p { color: var(--muted); line-height: 1.55; }
    .link-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; }
    .asset { display: block; padding: 14px; text-decoration: none; color: var(--ink); }
    .asset span { display: block; margin-top: 4px; color: var(--muted); font-size: 13px; word-break: break-word; }
    .asset.missing { opacity: 0.55; }
    .refs { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
    .ref { background: var(--soft); color: var(--accent); border-radius: 999px; padding: 4px 8px; font-size: 12px; }
    a { color: var(--accent); }
    li { margin: 5px 0; }
    @media (max-width: 760px) {
      main { width: min(100vw - 20px, 1180px); padding-top: 20px; }
      .topline { grid-template-columns: 1fr; }
      .meta { justify-content: flex-start; }
    }
  </style>"""


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
