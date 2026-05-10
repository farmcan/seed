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
    transcript_path: Path | None = None,
    frame_dir: Path | None = None,
    visual_notes_path: Path | None = None,
    semantics_path: Path | None = None,
    creator_profile_path: Path | None = None,
) -> dict[str, Any]:
    inferred_owner = owner or infer_owner(semantics_path) or "unknown"
    inferred_platform = platform or infer_platform(semantics_path) or "unknown"
    frame_count = count_frames(frame_dir)
    transcript_chunks = count_transcript_chunks(transcript_path)

    nodes = [
        node(
            "source",
            "source",
            "Source",
            f"{inferred_platform} / {inferred_owner} / {title}",
            -560,
            -140,
            [path_metric(source_path), inferred_platform, inferred_owner],
            source_path,
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
            "Frames",
            "抽样关键帧截图，可作为视觉证据、封面候选和 timeline 锚点。",
            -210,
            260,
            [path_metric(frame_dir), f"{frame_count} frames" if frame_count else "no frames"],
            frame_dir,
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
            "对齐 transcript chunk、关键帧、广告段、论证阶段和 CTA。当前作为待生成 artifact 的结构占位。",
            170,
            120,
            ["planned", "chunks + frames", "beats"],
            None,
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
            "creator",
            "creator",
            "Creator Profile",
            "跨视频聚合表达风格、叙事框架、视觉语言习惯和常用分析方法。",
            540,
            -120,
            [path_metric(creator_profile_path), inferred_owner],
            creator_profile_path,
        ),
        node(
            "factcheck",
            "asset",
            "Fact-check Queue",
            "需要外部来源核验的日期、预算、人物表态、合同和政策声明。",
            520,
            150,
            ["claims", "sources", "risk"],
            None,
        ),
        node(
            "skills",
            "asset",
            "Agent Skills / Checks",
            "输出给 agent 使用的技能、事前检查、事实核验问题和复盘问题。",
            900,
            -120,
            ["SKILL.md", "pre-check", "reflection"],
            None,
        ),
    ]

    return {
        "version": 1,
        "title": title,
        "owner": inferred_owner,
        "platform": inferred_platform,
        "nodes": nodes,
        "edges": [
            ["source", "transcript"],
            ["source", "frames"],
            ["frames", "visual"],
            ["transcript", "timeline"],
            ["frames", "timeline"],
            ["transcript", "semantics"],
            ["visual", "semantics"],
            ["timeline", "semantics"],
            ["semantics", "creator"],
            ["semantics", "factcheck"],
            ["creator", "skills"],
            ["factcheck", "skills"],
        ],
    }


def write_video_dag_graph(path: Path, graph: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def node(
    node_id: str,
    node_type: str,
    title: str,
    body: str,
    x: int,
    y: int,
    metrics: list[str],
    path: Path | None,
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
    return result


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


def count_transcript_chunks(transcript_path: Path | None) -> int:
    if not transcript_path or not transcript_path.exists():
        return 0
    text = transcript_path.read_text(encoding="utf-8")
    return sum(1 for line in text.splitlines() if line.startswith("## Chunk "))
