from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify
from seed.markdown import find_markdown_field


def video_dag_output_path(
    *,
    library_root: Path,
    title: str,
) -> Path:
    init_library(library_root)
    return library_root / "graphs" / f"{slugify(title)}.video-dag.json"


def build_video_dag_graph(
    *,
    title: str,
    owner: str | None = None,
    platform: str | None = None,
    source_path: Path | None = None,
    audio_path: Path | None = None,
    transcript_path: Path | None = None,
    frame_dir: Path | None = None,
    visual_notes_path: Path | None = None,
    semantics_path: Path | None = None,
    timeline_path: Path | None = None,
    creator_profile_path: Path | None = None,
) -> dict[str, Any]:
    inferred_owner = owner or infer_owner(semantics_path) or "unknown"
    inferred_platform = platform or infer_platform(semantics_path) or "unknown"
    frame_count = count_frames(frame_dir)
    transcript_chunks = count_transcript_chunks(transcript_path)
    resolved_audio_path = audio_path or infer_audio_path(source_path)
    frame_paths = list_frame_paths(frame_dir)
    semantics_text = semantics_path.read_text(encoding="utf-8") if semantics_path and semantics_path.exists() else ""
    timeline = load_timeline(timeline_path)
    timeline_events = timeline.get("events", []) if timeline else []

    nodes = [
        node(
            "source",
            "source",
            "Source Metadata",
            f"{inferred_platform} / {inferred_owner} / {title}",
            -880,
            -120,
            [path_metric(source_path), inferred_platform, inferred_owner],
            source_path,
        ),
        node(
            "video-media",
            "source",
            "Video File",
            "本地下载的视频文件，可在画布侧栏预览，用来确认画面风格、素材类型和内容形态。",
            -560,
            -260,
            [path_metric(source_path), "video"],
            source_path,
            preview={"type": "video", "src": str(source_path)} if source_path else None,
        ),
        node(
            "audio-media",
            "transcript",
            "Audio Track",
            "从视频抽取的 ASR 音频，可用于回听语气、广告段和口播节奏。",
            -560,
            -20,
            [path_metric(resolved_audio_path), "audio"],
            resolved_audio_path,
            preview={"type": "audio", "src": str(resolved_audio_path)} if resolved_audio_path else None,
        ),
        node(
            "transcript",
            "transcript",
            "Transcript",
            "ASR 或人工整理后的文字语言，用于提取口播观点、论证和广告段。",
            -210,
            -250,
            [path_metric(transcript_path), f"{transcript_chunks} chunks" if transcript_chunks else "text"],
            transcript_path,
        ),
        node(
            "frames",
            "frame",
            "Frame Gallery",
            "抽样关键帧截图，可直接在画布侧栏查看，用作视觉证据、封面候选和 timeline 锚点。",
            -210,
            260,
            [path_metric(frame_dir), f"{frame_count} frames" if frame_count else "no frames"],
            frame_dir,
            preview={"type": "gallery", "items": [str(path) for path in frame_paths[:8]]} if frame_paths else None,
        ),
        node(
            "visual",
            "visual",
            "Visual Notes",
            "由 VL 模型分析关键帧得到的画面、屏幕文字、符号素材和剪辑节奏。",
            -210,
            10,
            [path_metric(visual_notes_path), "visual language"],
            visual_notes_path,
        ),
        node(
            "timeline",
            "timeline",
            "Timeline",
            timeline_summary(timeline_events),
            170,
            120,
            [
                path_metric(timeline_path),
                f"{len(timeline_events)} events" if timeline_events else "no events",
            ],
            timeline_path,
        ),
        node(
            "semantics",
            "semantics",
            "Video Semantics",
            "融合口播与视觉证据，沉淀核心观点、结构、方法论和可复用 prompt fragments。",
            170,
            -120,
            [path_metric(semantics_path), "claims", "methods"],
            semantics_path,
        ),
        node(
            "claims",
            "semantics",
            "Main Claims",
            section_summary(semantics_text, "Verbal Language", "主张：美国撤军背景下欧洲防务领导权重分配；法德围绕 FCAS、军工份额和战略自主竞争。"),
            500,
            -360,
            ["derived", "verbal evidence"],
            semantics_path,
        ),
        node(
            "structure",
            "timeline",
            "Video Structure",
            section_summary(semantics_text, "Video Structure", "结构：外部压力开场 -> 法德冲突 -> 项目份额争夺 -> 第三方介入 -> 趋势判断 -> CTA。"),
            500,
            -120,
            ["hook", "proof", "cta"],
            semantics_path,
        ),
        node(
            "methods",
            "asset",
            "Methods / Principles",
            section_summary(semantics_text, "Methods And Principles", "方法：用军工合作项目、采购流向、预算和核心研发权分析联盟内部主导权。"),
            500,
            120,
            ["decision rules", "failure modes"],
            semantics_path,
        ),
        node(
            "creator-signals",
            "creator",
            "Creator Signals",
            section_summary(semantics_text, "Creator Signals", "创作者信号：高密度国际政治信息 + 口语化吐槽 + 拟人化大国关系 + 军工项目解释权力结构。"),
            850,
            -120,
            ["style", "worldview", "evidence"],
            semantics_path,
        ),
        node(
            "creator",
            "creator",
            "Creator Profile",
            "跨视频聚合表达风格、叙事框架、视觉语言习惯和常用分析方法；单条视频时只是 provisional signal。",
            1180,
            -120,
            [path_metric(creator_profile_path), inferred_owner],
            creator_profile_path,
        ),
        node(
            "factcheck",
            "asset",
            "Fact-check Queue",
            "需要外部来源核验的日期、预算、人物表态、合同和政策声明。",
            850,
            150,
            ["claims", "sources", "risk"],
            None,
        ),
        node(
            "skills",
            "asset",
            "Agent Skills / Checks",
            "输出给 agent 使用的技能、事前检查、事实核验问题和复盘问题。",
            1180,
            150,
            ["SKILL.md", "pre-check", "reflection"],
            None,
        ),
    ]

    timeline_nodes = build_timeline_event_nodes(timeline_events, timeline_path)
    nodes.extend(timeline_nodes)

    edges = [
        ["source", "video-media"],
        ["video-media", "audio-media"],
        ["video-media", "frames"],
        ["audio-media", "transcript"],
        ["frames", "visual"],
        ["transcript", "timeline"],
        ["frames", "timeline"],
        ["transcript", "semantics"],
        ["visual", "semantics"],
        ["timeline", "semantics"],
        ["semantics", "claims"],
        ["semantics", "structure"],
        ["semantics", "methods"],
        ["claims", "creator-signals"],
        ["structure", "creator-signals"],
        ["methods", "creator-signals"],
        ["creator-signals", "creator"],
        ["claims", "factcheck"],
        ["creator", "skills"],
        ["factcheck", "skills"],
    ]
    edges.extend(["timeline", event_node["id"]] for event_node in timeline_nodes)

    return {
        "version": 1,
        "title": title,
        "owner": inferred_owner,
        "platform": inferred_platform,
        "nodes": nodes,
        "edges": edges,
    }


def resolve_video_dag_artifacts(
    *,
    library_root: Path,
    title: str,
    source_path: Path | None = None,
    audio_path: Path | None = None,
    transcript_path: Path | None = None,
    frame_dir: Path | None = None,
    visual_notes_path: Path | None = None,
    semantics_path: Path | None = None,
    timeline_path: Path | None = None,
    creator_profile_path: Path | None = None,
) -> dict[str, Path | None]:
    title_slug = slugify(title)
    resolved_source = source_path or find_matching_file(
        library_root / "raw",
        title_slug=title_slug,
        suffixes={".mp4", ".mkv", ".webm", ".mov", ".flv"},
    )
    return {
        "source_path": resolved_source,
        "audio_path": audio_path or infer_audio_path(resolved_source),
        "transcript_path": transcript_path
        or find_matching_file(library_root / "transcripts", title_slug=title_slug, suffixes={".md"}),
        "frame_dir": frame_dir or find_matching_dir(library_root / "frames", title_slug=title_slug),
        "visual_notes_path": visual_notes_path
        or find_matching_file(library_root / "notes", title_slug=title_slug, suffixes={".md"}),
        "semantics_path": semantics_path
        or find_matching_file(library_root / "semantics", title_slug=title_slug, suffixes={".md"}),
        "timeline_path": timeline_path
        or find_matching_file(library_root / "timelines", title_slug=title_slug, suffixes={".json"}),
        "creator_profile_path": creator_profile_path,
    }


def write_video_dag_graph(path: Path, graph: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def find_matching_file(directory: Path, *, title_slug: str, suffixes: set[str]) -> Path | None:
    if not directory.exists():
        return None
    candidates = [
        path
        for path in directory.glob("*")
        if path.is_file()
        and path.suffix.lower() in suffixes
        and title_slug in slugify(path.stem)
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def find_matching_dir(directory: Path, *, title_slug: str) -> Path | None:
    if not directory.exists():
        return None
    candidates = [
        path
        for path in directory.glob("*")
        if path.is_dir() and title_slug in slugify(path.name)
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def node(
    node_id: str,
    node_type: str,
    title: str,
    body: str,
    x: int,
    y: int,
    metrics: list[str],
    path: Path | None,
    preview: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean_metrics = [metric for metric in metrics if metric and metric != "missing"]
    result: dict[str, Any] = {
        "id": node_id,
        "type": node_type,
        "title": title,
        "body": body,
        "x": x,
        "y": y,
        "metrics": clean_metrics,
    }
    if path:
        result["path"] = str(path)
    if preview:
        result["preview"] = preview
    return result


def load_timeline(timeline_path: Path | None) -> dict[str, Any]:
    if not timeline_path or not timeline_path.exists():
        return {}
    return json.loads(timeline_path.read_text(encoding="utf-8"))


def timeline_summary(events: list[dict[str, Any]]) -> str:
    if not events:
        return "对齐 transcript chunk、关键帧、广告段、论证阶段和 CTA。当前没有找到 timeline artifact。"
    kinds = ", ".join(sorted({str(event.get("kind")) for event in events if event.get("kind")}))
    return f"已生成真实 timeline artifact，包含 {len(events)} 个事件。事件类型：{kinds}。"


def build_timeline_event_nodes(
    events: list[dict[str, Any]],
    timeline_path: Path | None,
    *,
    max_events: int = 8,
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for index, event in enumerate(events[:max_events]):
        timestamp = format_event_timestamp(event.get("start_seconds"))
        label = str(event.get("label") or event.get("kind") or f"Event {index + 1}")
        description = str(event.get("description") or event.get("evidence_path") or "")
        metrics = [
            str(event.get("kind") or "event"),
            timestamp,
            str(event.get("confidence") or "unknown"),
        ]
        nodes.append(
            node(
                f"timeline-event-{index + 1}",
                "timeline",
                label,
                description,
                500,
                280 + index * 110,
                metrics,
                Path(str(event["evidence_path"])) if event.get("evidence_path") else timeline_path,
            )
        )
    return nodes


def format_event_timestamp(value: Any) -> str:
    if value is None:
        return "time unknown"
    seconds = int(value)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"


def path_metric(path: Path | None) -> str:
    if not path:
        return "missing"
    if path.exists():
        return path.name
    return f"missing: {path.name}"


def infer_owner(semantics_path: Path | None) -> str | None:
    return infer_semantics_field(semantics_path, "owner")


def infer_platform(semantics_path: Path | None) -> str | None:
    return infer_semantics_field(semantics_path, "platform")


def infer_semantics_field(path: Path | None, field: str) -> str | None:
    if not path or not path.exists():
        return None
    return find_markdown_field(path.read_text(encoding="utf-8"), field)


def count_frames(frame_dir: Path | None) -> int:
    if not frame_dir or not frame_dir.exists():
        return 0
    return len(sorted(frame_dir.glob("frame_*.jpg")))


def list_frame_paths(frame_dir: Path | None) -> list[Path]:
    if not frame_dir or not frame_dir.exists():
        return []
    return sorted(frame_dir.glob("frame_*.jpg"))


def count_transcript_chunks(transcript_path: Path | None) -> int:
    if not transcript_path or not transcript_path.exists():
        return 0
    text = transcript_path.read_text(encoding="utf-8")
    return sum(1 for line in text.splitlines() if line.startswith("## Chunk "))


def infer_audio_path(source_path: Path | None) -> Path | None:
    if not source_path:
        return None
    candidate = source_path.with_suffix(".asr.mp3")
    return candidate if candidate.exists() else None


def section_summary(markdown_text: str, heading: str, fallback: str) -> str:
    section = extract_markdown_section(strip_frontmatter(markdown_text), heading)
    if not section:
        return fallback
    compact = " ".join(line.strip(" -") for line in section.splitlines() if line.strip())
    return compact[:520] + ("..." if len(compact) > 520 else "")


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    return parts[2] if len(parts) == 3 else text


def extract_markdown_section(markdown_text: str, heading: str) -> str:
    lines = markdown_text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().casefold() == f"## {heading}".casefold():
            start = index + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end]).strip()
