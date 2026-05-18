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
    ai_practice_signals_path: Path | None = None,
    finance_signals_path: Path | None = None,
    news_facts_path: Path | None = None,
    earnings_analysis_path: Path | None = None,
    timeline_path: Path | None = None,
    claims_path: Path | None = None,
    cost_path: Path | None = None,
    creator_profile_path: Path | None = None,
    short_profile_path: Path | None = None,
    shots_path: Path | None = None,
    frame_notes_path: Path | None = None,
    motion_relations_path: Path | None = None,
) -> dict[str, Any]:
    inferred_owner = owner or infer_owner(semantics_path) or "unknown"
    inferred_platform = platform or infer_platform(semantics_path) or "unknown"
    frame_count = count_frames(frame_dir)
    transcript_chunks = count_transcript_chunks(transcript_path)
    resolved_audio_path = audio_path or infer_audio_path(source_path)
    frame_paths = list_frame_paths(frame_dir)
    semantics_text = semantics_path.read_text(encoding="utf-8") if semantics_path and semantics_path.exists() else ""
    ai_practice_signals = load_json_artifact(ai_practice_signals_path)
    finance_signals = load_json_artifact(finance_signals_path)
    news_facts = load_json_artifact(news_facts_path)
    earnings_analysis = load_json_artifact(earnings_analysis_path)
    timeline = load_timeline(timeline_path)
    timeline_events = timeline.get("events", []) if timeline else []
    claims = load_claims(claims_path)
    cost_report = load_cost_report(cost_path)
    short_profile = load_json_artifact(short_profile_path)
    shots_artifact = load_json_artifact(shots_path)
    shots = shots_artifact.get("shots", []) if shots_artifact else []
    frame_notes = load_jsonl_artifact(frame_notes_path)
    motion_relations = load_json_artifact(motion_relations_path)
    relations = motion_relations.get("relations", []) if motion_relations else []

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
            "short-profile",
            "timeline",
            "Short Video Profile",
            short_profile_summary(short_profile),
            170,
            380,
            [
                path_metric(short_profile_path),
                "short" if short_profile.get("is_short_form") else "long",
                aspect_metric(short_profile),
            ],
            short_profile_path,
        ),
        node(
            "shots",
            "frame",
            "Shot Strip",
            shots_summary(shots_artifact),
            500,
            520,
            [
                path_metric(shots_path),
                f"{len(shots)} shots" if shots else "no shots",
            ],
            shots_path,
            preview=shot_strip_preview(shots),
        ),
        node(
            "frame-notes",
            "frame",
            "Frame Evidence Notes",
            frame_notes_summary(frame_notes),
            500,
            760,
            [
                path_metric(frame_notes_path),
                f"{len(frame_notes)} frames" if frame_notes else "no frame notes",
            ],
            frame_notes_path,
            preview=frame_notes_preview(frame_notes),
        ),
        node(
            "motion-relations",
            "timeline",
            "Motion Relations",
            motion_relations_summary(motion_relations),
            850,
            760,
            [
                path_metric(motion_relations_path),
                f"{len(relations)} relations" if relations else "no relations",
                str(motion_relations.get("provider") or "provider pending"),
            ],
            motion_relations_path,
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
            factcheck_summary(claims),
            850,
            150,
            [path_metric(claims_path), f"{len(claims)} claims" if claims else "no claims"],
            claims_path,
        ),
        node(
            "costs",
            "asset",
            "Cost Report",
            cost_summary(cost_report),
            850,
            390,
            [path_metric(cost_path), cost_metric(cost_report)],
            cost_path,
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

    timeline_nodes = build_timeline_event_nodes(
        timeline_events,
        timeline_path,
        source_path=source_path,
        audio_path=resolved_audio_path,
    )
    nodes.extend(timeline_nodes)
    claim_nodes = build_claim_nodes(claims, claims_path)
    nodes.extend(claim_nodes)
    shot_nodes = build_shot_nodes(
        shots,
        shots_path,
        source_path=source_path,
    )
    nodes.extend(shot_nodes)
    frame_note_nodes = build_frame_note_nodes(
        frame_notes,
        frame_notes_path,
        source_path=source_path,
    )
    nodes.extend(frame_note_nodes)
    motion_relation_nodes = build_motion_relation_nodes(
        relations,
        motion_relations_path,
        source_path=source_path,
    )
    nodes.extend(motion_relation_nodes)
    if finance_signals:
        nodes.append(
            node(
                "finance-signals",
                "asset",
                "Finance Signals",
                finance_signals_summary(finance_signals),
                850,
                -360,
                [
                    path_metric(finance_signals_path),
                    f"{len(finance_signals.get('recommendations') or [])} recs",
                    "not advice",
                ],
                finance_signals_path,
            )
        )
    if ai_practice_signals:
        nodes.append(
            node(
                "ai-practice-signals",
                "asset",
                "AI Practice Signals",
                ai_practice_signals_summary(ai_practice_signals),
                850,
                -560,
                [
                    path_metric(ai_practice_signals_path),
                    f"{len(ai_practice_signals.get('practice_events') or [])} practices",
                    f"{len(ai_practice_signals.get('capability_signals') or [])} capabilities",
                ],
                ai_practice_signals_path,
            )
        )
    if news_facts:
        nodes.append(
            node(
                "news-facts",
                "asset",
                "News Facts",
                news_facts_summary(news_facts),
                1180 if ai_practice_signals else 850,
                -560,
                [
                    path_metric(news_facts_path),
                    f"{len(news_facts.get('facts') or [])} facts",
                    f"{len(news_facts.get('open_questions') or [])} open questions",
                ],
                news_facts_path,
            )
        )
    if earnings_analysis:
        nodes.append(
            node(
                "earnings-analysis",
                "asset",
                "Earnings Analysis",
                earnings_analysis_summary(earnings_analysis),
                1180,
                -360,
                [
                    path_metric(earnings_analysis_path),
                    f"{len(earnings_analysis.get('companies') or [])} companies",
                    f"{len(earnings_analysis.get('earnings_claims') or [])} claims",
                ],
                earnings_analysis_path,
            )
        )

    edges = [
        ["source", "video-media"],
        ["video-media", "audio-media"],
        ["video-media", "frames"],
        ["audio-media", "transcript"],
        ["frames", "visual"],
        ["video-media", "short-profile"],
        ["short-profile", "shots"],
        ["shots", "frame-notes"],
        ["frame-notes", "motion-relations"],
        ["shots", "visual"],
        ["transcript", "timeline"],
        ["frames", "timeline"],
        ["transcript", "semantics"],
        ["visual", "semantics"],
        ["timeline", "semantics"],
        ["motion-relations", "semantics"],
        ["semantics", "claims"],
        ["semantics", "structure"],
        ["semantics", "methods"],
        ["claims", "creator-signals"],
        ["structure", "creator-signals"],
        ["methods", "creator-signals"],
        ["creator-signals", "creator"],
        ["claims", "factcheck"],
        ["visual", "costs"],
        ["costs", "skills"],
        ["creator", "skills"],
        ["factcheck", "skills"],
    ]
    edges.extend(["timeline", event_node["id"]] for event_node in timeline_nodes)
    edges.extend(["factcheck", claim_node["id"]] for claim_node in claim_nodes)
    edges.extend(["shots", shot_node["id"]] for shot_node in shot_nodes)
    edges.extend(["frame-notes", frame_node["id"]] for frame_node in frame_note_nodes)
    edges.extend(["motion-relations", relation_node["id"]] for relation_node in motion_relation_nodes)
    if finance_signals:
        edges.extend(
            [
                ["semantics", "finance-signals"],
                ["finance-signals", "creator-signals"],
            ]
        )
    if ai_practice_signals:
        edges.extend(
            [
                ["semantics", "ai-practice-signals"],
                ["ai-practice-signals", "methods"],
                ["ai-practice-signals", "creator-signals"],
            ]
        )
    if news_facts:
        edges.extend(
            [
                ["semantics", "news-facts"],
                ["news-facts", "factcheck"],
                ["news-facts", "creator-signals"],
            ]
        )
    if earnings_analysis:
        edges.extend(
            [
                ["semantics", "earnings-analysis"],
                ["earnings-analysis", "factcheck"],
                ["earnings-analysis", "creator-signals"],
            ]
        )

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
    ai_practice_signals_path: Path | None = None,
    finance_signals_path: Path | None = None,
    news_facts_path: Path | None = None,
    earnings_analysis_path: Path | None = None,
    timeline_path: Path | None = None,
    claims_path: Path | None = None,
    cost_path: Path | None = None,
    creator_profile_path: Path | None = None,
    short_profile_path: Path | None = None,
    shots_path: Path | None = None,
    frame_notes_path: Path | None = None,
    motion_relations_path: Path | None = None,
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
        "ai_practice_signals_path": ai_practice_signals_path
        or find_matching_file(
            library_root / "semantics",
            title_slug=title_slug,
            suffixes={".json"},
            preferred_suffix=".ai-practice-signals",
            require_preferred=True,
        ),
        "finance_signals_path": finance_signals_path
        or find_matching_file(
            library_root / "semantics",
            title_slug=title_slug,
            suffixes={".json"},
            preferred_suffix=".finance-signals",
            require_preferred=True,
        ),
        "news_facts_path": news_facts_path
        or find_matching_file(
            library_root / "semantics",
            title_slug=title_slug,
            suffixes={".json"},
            preferred_suffix=".news-facts",
            require_preferred=True,
        ),
        "earnings_analysis_path": earnings_analysis_path
        or find_matching_file(
            library_root / "semantics",
            title_slug=title_slug,
            suffixes={".json"},
            preferred_suffix=".earnings-analysis",
            require_preferred=True,
        ),
        "timeline_path": timeline_path
        or find_matching_file(library_root / "timelines", title_slug=title_slug, suffixes={".json"}),
        "claims_path": claims_path
        or find_matching_file(
            library_root / "claims",
            title_slug=title_slug,
            suffixes={".json"},
            preferred_suffix=".verified",
        ),
        "cost_path": cost_path
        or find_matching_file(
            library_root / "costs",
            title_slug=title_slug,
            suffixes={".json"},
            preferred_suffix=".ledger",
        ),
        "creator_profile_path": creator_profile_path,
        "short_profile_path": short_profile_path
        or find_matching_file(
            library_root / "shorts",
            title_slug=title_slug,
            suffixes={".json"},
            preferred_suffix=".short-video-profile",
            require_preferred=True,
        ),
        "shots_path": shots_path
        or find_matching_file(
            library_root / "shots",
            title_slug=title_slug,
            suffixes={".json"},
            preferred_suffix=".shots",
            require_preferred=True,
        ),
        "frame_notes_path": frame_notes_path
        or find_matching_file(library_root / "frames", title_slug=title_slug, suffixes={".jsonl"}),
        "motion_relations_path": motion_relations_path
        or find_matching_file(
            library_root / "shots",
            title_slug=title_slug,
            suffixes={".json"},
            preferred_suffix=".motion-relations",
            require_preferred=True,
        ),
    }


def write_video_dag_graph(path: Path, graph: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def find_matching_file(
    directory: Path,
    *,
    title_slug: str,
    suffixes: set[str],
    preferred_suffix: str | None = None,
    require_preferred: bool = False,
) -> Path | None:
    if not directory.exists():
        return None
    candidates = [
        path
        for path in directory.glob("*")
        if path.is_file()
        and path.suffix.lower() in suffixes
        and title_slug in slugify(path.stem)
    ]
    if preferred_suffix:
        preferred = [path for path in candidates if path.stem.endswith(preferred_suffix)]
        if preferred:
            return max(preferred, key=lambda path: path.stat().st_mtime)
        if require_preferred:
            return None
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
    media_anchor: dict[str, Any] | None = None,
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
    if media_anchor:
        result["media_anchor"] = media_anchor
    return result


def load_timeline(timeline_path: Path | None) -> dict[str, Any]:
    if not timeline_path or not timeline_path.exists():
        return {}
    return json.loads(timeline_path.read_text(encoding="utf-8"))


def load_claims(claims_path: Path | None) -> list[dict[str, Any]]:
    if not claims_path or not claims_path.exists():
        return []
    artifact = json.loads(claims_path.read_text(encoding="utf-8"))
    return artifact.get("claims") or []


def load_cost_report(cost_path: Path | None) -> dict[str, Any]:
    if not cost_path or not cost_path.exists():
        return {}
    return json.loads(cost_path.read_text(encoding="utf-8"))


def load_json_artifact(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl_artifact(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def short_profile_summary(profile: dict[str, Any]) -> str:
    if not profile:
        return "判断视频是否进入 60s 短视频强分析链路：duration、fps、宽高比、竖屏和音轨。当前没有找到 short profile artifact。"
    duration = profile.get("duration_seconds")
    fps = profile.get("fps")
    width = profile.get("width")
    height = profile.get("height")
    is_short = "短视频" if profile.get("is_short_form") else "长视频"
    return (
        f"已生成 short profile：{is_short}，"
        f"duration={duration}s，fps={fps}，resolution={width}x{height}，"
        f"vertical={profile.get('is_vertical')}。"
    )


def aspect_metric(profile: dict[str, Any]) -> str:
    if not profile:
        return "aspect unknown"
    width = profile.get("width")
    height = profile.get("height")
    if not width or not height:
        return "aspect unknown"
    return f"{width}x{height}"


def shots_summary(artifact: dict[str, Any]) -> str:
    shots = artifact.get("shots") or []
    if not shots:
        return "shot boundary artifact 用来展示短视频镜头切分、代表帧、转场和节奏密度。当前没有找到 shots artifact。"
    durations = [shot.get("duration_seconds") for shot in shots if shot.get("duration_seconds") is not None]
    avg_duration = round(sum(durations) / len(durations), 2) if durations else None
    return (
        f"已生成 {len(shots)} 个 shot。"
        f"平均 shot 时长 {avg_duration}s。"
        f"provider={artifact.get('provider')}，threshold={artifact.get('threshold')}。"
    )


def shot_strip_preview(shots: list[dict[str, Any]]) -> dict[str, Any] | None:
    items = [
        str(shot["representative_frame_path"])
        for shot in shots[:8]
        if shot.get("representative_frame_path")
    ]
    return {"type": "gallery", "items": items} if items else None


def frame_notes_summary(notes: list[dict[str, Any]]) -> str:
    if not notes:
        return "短视频逐帧/密集帧证据索引。默认先记录 timestamp、shot、frame path 和图像尺寸；VL/OCR 字段可后续补强。"
    modes = ", ".join(sorted({str(note.get("frame_mode")) for note in notes if note.get("frame_mode")}))
    pending = sum(1 for note in notes if note.get("status") == "pending_vl")
    return f"已生成 {len(notes)} 条 frame evidence。frame mode: {modes or 'unknown'}；待 VL/OCR 补强 {pending} 条。"


def frame_notes_preview(notes: list[dict[str, Any]]) -> dict[str, Any] | None:
    items = [str(note["frame_path"]) for note in notes[:8] if note.get("frame_path")]
    return {"type": "gallery", "items": items} if items else None


def motion_relations_summary(artifact: dict[str, Any]) -> str:
    if not artifact:
        return "人物/物体运动关系 artifact 尚未生成。这个节点用于承接 pose、tracking、optical flow 或 VL provider 输出，避免只靠文本猜测动作关系。"
    relations = artifact.get("relations") or []
    pending = sum(1 for relation in relations if relation.get("status") == "needs_pose_or_vl")
    capabilities = artifact.get("capabilities") or {}
    enabled = ", ".join(sorted(key for key, value in capabilities.items() if value))
    return (
        f"已生成 {len(relations)} 条运动关系候选。"
        f"provider={artifact.get('provider')}；"
        f"待 pose/tracking/VL 补强 {pending} 条；"
        f"已启用能力：{enabled or 'baseline only'}。"
    )


def timeline_summary(events: list[dict[str, Any]]) -> str:
    if not events:
        return "对齐 transcript chunk、关键帧、广告段、论证阶段和 CTA。当前没有找到 timeline artifact。"
    kinds = ", ".join(sorted({str(event.get("kind")) for event in events if event.get("kind")}))
    return f"已生成真实 timeline artifact，包含 {len(events)} 个事件。事件类型：{kinds}。"


def factcheck_summary(claims: list[dict[str, Any]]) -> str:
    if not claims:
        return "需要外部来源核验的日期、预算、人物表态、合同和政策声明。当前没有找到 claims artifact。"
    statuses = ", ".join(sorted({str(claim.get("status")) for claim in claims if claim.get("status")}))
    return f"已抽取 {len(claims)} 条待核验 claim。状态集合：{statuses}。"


def finance_signals_summary(signals: dict[str, Any]) -> str:
    if not signals:
        return "财经领域信号 artifact 尚未生成。它用于结构化记录标的、方向、动作、时间窗口、风险控制和证据引用；所有内容都是创作者观点，不是投资建议。"
    instruments = signals.get("instruments") or []
    viewpoint_events = signals.get("viewpoint_events") or []
    recommendations = signals.get("recommendations") or []
    methods = signals.get("methodology_signals") or []
    stance = signals.get("stance_summary") or "no stance summary"
    return (
        f"已提取 {len(instruments)} 个标的、{len(viewpoint_events) or len(recommendations)} 条观点事件、"
        f"{len(recommendations)} 条兼容推荐信号、"
        f"{len(methods)} 条方法论信号。立场摘要：{stance}"
    )


def ai_practice_signals_summary(signals: dict[str, Any]) -> str:
    if not signals:
        return "AI practices artifact 尚未生成。它用于结构化记录真实 AI 使用流程、时代判断、能力信号和可落地实验。"
    practices = signals.get("practice_events") or []
    beliefs = signals.get("belief_events") or []
    capabilities = signals.get("capability_signals") or []
    personal = signals.get("personal_application_candidates") or []
    project = signals.get("project_application_candidates") or []
    summary = signals.get("ai_usage_summary") or "no usage summary"
    return (
        f"已提取 {len(practices)} 个实践事件、{len(beliefs)} 个观点事件、"
        f"{len(capabilities)} 个能力信号、{len(personal)} 个个人实验候选、"
        f"{len(project)} 个 Seed 项目候选。摘要：{summary}"
    )


def news_facts_summary(artifact: dict[str, Any]) -> str:
    if not artifact:
        return "新闻事实 artifact 尚未生成。它用于把事实、reported claims、解释和来源缺口分开。"
    facts = artifact.get("facts") or []
    claims = artifact.get("reported_claims") or []
    impacts = artifact.get("industry_impacts") or []
    summary = artifact.get("summary") or "no summary"
    return (
        f"已提取 {len(facts)} 条事实、{len(claims)} 条 attributed claims、"
        f"{len(impacts)} 条行业影响机制。摘要：{summary}"
    )


def earnings_analysis_summary(artifact: dict[str, Any]) -> str:
    if not artifact:
        return "财报分析 artifact 尚未生成。它用于把公司、财报 claim、驱动因素和待 SEC 核验缺口分开。"
    companies = artifact.get("companies") or []
    claims = artifact.get("earnings_claims") or []
    drivers = artifact.get("drivers") or []
    risks = artifact.get("risks") or []
    return (
        f"已提取 {len(companies)} 家公司、{len(claims)} 条财报 claim、"
        f"{len(drivers)} 个驱动因素、{len(risks)} 个风险。"
    )


def cost_summary(report: dict[str, Any]) -> str:
    if not report:
        return "按单条视频记录 Qwen-VL token 用量、估算单价和总费用；Codex 费用先预留字段。当前没有找到 cost artifact。"
    if report.get("kind") == "cost_ledger":
        qwen_items = [item for item in report.get("items", []) if item.get("kind") == "qwen_vl"]
        reserved_items = [item for item in report.get("items", []) if item.get("status") == "reserved"]
        return (
            "已生成 pipeline 级成本 ledger："
            f"{len(qwen_items)} 条 Qwen-VL 明细，"
            f"{len(reserved_items)} 个预留项，"
            f"总计 {cost_metric(report)}。"
        )
    qwen_items = [item for item in report.get("items", []) if item.get("kind") == "qwen_vl"]
    if not qwen_items:
        return "已生成成本 artifact，但未找到 Qwen-VL 明细。"
    item = qwen_items[0]
    usage = item.get("usage") or {}
    estimate = item.get("estimated_cost") or {}
    return (
        "已记录 Qwen-VL 成本明细："
        f"input {usage.get('input_tokens', 0)} tokens，"
        f"output {usage.get('output_tokens', 0)} tokens，"
        f"估算 {estimate.get('amount', 0)} {estimate.get('currency', '')}。"
    )


def cost_metric(report: dict[str, Any]) -> str:
    totals = report.get("totals") if report else None
    if not totals:
        return "cost pending"
    return ", ".join(f"{amount} {currency}" for currency, amount in totals.items())


def build_timeline_event_nodes(
    events: list[dict[str, Any]],
    timeline_path: Path | None,
    *,
    source_path: Path | None = None,
    audio_path: Path | None = None,
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
                media_anchor=media_anchor_for_event(
                    event,
                    source_path=source_path,
                    audio_path=audio_path,
                ),
            )
        )
    return nodes


def media_anchor_for_event(
    event: dict[str, Any],
    *,
    source_path: Path | None,
    audio_path: Path | None,
) -> dict[str, Any] | None:
    start_seconds = optional_seconds(event.get("start_seconds"))
    if start_seconds is None:
        return None
    anchor: dict[str, Any] = {
        "start_seconds": start_seconds,
        "label": format_event_timestamp(start_seconds),
    }
    if source_path:
        anchor["video_src"] = str(source_path)
    if audio_path:
        anchor["audio_src"] = str(audio_path)
    return anchor


def optional_seconds(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_claim_nodes(
    claims: list[dict[str, Any]],
    claims_path: Path | None,
    *,
    max_claims: int = 8,
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for index, claim in enumerate(claims[:max_claims]):
        text = str(claim.get("text") or "")
        status = str(claim.get("status") or "unknown")
        source_section = str(claim.get("source_section") or "unknown")
        evidence_path = claim.get("evidence_path")
        nodes.append(
            node(
                f"claim-{index + 1}",
                "asset",
                f"Claim {index + 1}: {status}",
                text,
                1180,
                360 + index * 110,
                [status, source_section],
                Path(str(evidence_path)) if evidence_path else claims_path,
            )
        )
    return nodes


def build_shot_nodes(
    shots: list[dict[str, Any]],
    shots_path: Path | None,
    *,
    source_path: Path | None = None,
    max_shots: int = 10,
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for index, shot in enumerate(shots[:max_shots]):
        start_seconds = optional_seconds(shot.get("start_seconds"))
        title = f"Shot {index + 1}: {format_event_timestamp(start_seconds)}"
        frame_path = Path(str(shot["representative_frame_path"])) if shot.get("representative_frame_path") else None
        body = (
            f"{format_event_timestamp(shot.get('start_seconds'))} -> "
            f"{format_event_timestamp(shot.get('end_seconds'))}；"
            f"transition={shot.get('transition_type')}；"
            f"代表帧用于检查主体、构图、字幕/OCR 和剪辑目的。"
        )
        nodes.append(
            node(
                f"shot-{index + 1}",
                "frame",
                title,
                body,
                850,
                560 + index * 110,
                [
                    str(shot.get("transition_type") or "shot"),
                    f"{shot.get('duration_seconds')}s" if shot.get("duration_seconds") is not None else "",
                    str(shot.get("confidence") or ""),
                ],
                frame_path or shots_path,
                preview={"type": "image", "src": str(frame_path)} if frame_path else None,
                media_anchor=media_anchor_for_event(
                    {"start_seconds": shot.get("start_seconds")},
                    source_path=source_path,
                    audio_path=None,
                ),
            )
        )
    return nodes


def build_frame_note_nodes(
    notes: list[dict[str, Any]],
    frame_notes_path: Path | None,
    *,
    source_path: Path | None = None,
    max_frames: int = 10,
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for index, note in enumerate(notes[:max_frames]):
        frame_path = Path(str(note["frame_path"])) if note.get("frame_path") else None
        start_seconds = optional_seconds(note.get("timestamp_seconds"))
        image = note.get("image") or {}
        body = (
            f"timestamp={format_event_timestamp(note.get('timestamp_seconds'))}；"
            f"shot={note.get('shot_id') or 'unknown'}；"
            f"image={image.get('width')}x{image.get('height')}；"
            f"subtitle={field_presence(note.get('subtitle'))}；"
            f"effects={effects_presence(note.get('visual_effects'))}；"
            f"editing={field_presence(note.get('editing'))}；"
            f"status={note.get('status')}。"
        )
        nodes.append(
            node(
                f"frame-note-{index + 1}",
                "frame",
                f"Frame {index + 1}: {format_event_timestamp(start_seconds)}",
                body,
                1180,
                560 + index * 110,
                [
                    str(note.get("frame_mode") or "frame"),
                    str(note.get("status") or ""),
                ],
                frame_path or frame_notes_path,
                preview={"type": "image", "src": str(frame_path)} if frame_path else None,
                media_anchor=media_anchor_for_event(
                    {"start_seconds": note.get("timestamp_seconds")},
                    source_path=source_path,
                    audio_path=None,
                ),
            )
        )
    return nodes


def build_motion_relation_nodes(
    relations: list[dict[str, Any]],
    relations_path: Path | None,
    *,
    source_path: Path | None = None,
    max_relations: int = 10,
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for index, relation in enumerate(relations[:max_relations]):
        start_seconds = optional_seconds(relation.get("start_seconds"))
        status = str(relation.get("status") or "unknown")
        label = str(relation.get("label") or relation.get("kind") or f"Relation {index + 1}")
        providers = relation.get("needs_provider") or []
        if isinstance(providers, list):
            providers_text = ",".join(str(provider) for provider in providers)
        else:
            providers_text = str(providers)
        frame_indices = relation.get("source_frame_indices") or []
        body = (
            f"{relation.get('summary') or 'Motion relation candidate.'} "
            f"frames={frame_indices}；"
            f"shot_ids={relation.get('shot_ids') or []}；"
            f"needs={providers_text or 'none'}。"
        )
        nodes.append(
            node(
                f"motion-relation-{index + 1}",
                "timeline",
                f"Motion {index + 1}: {label}",
                body,
                1180,
                760 + index * 110,
                [
                    status,
                    str(relation.get("kind") or "relation"),
                    format_event_timestamp(start_seconds),
                ],
                relations_path,
                media_anchor=media_anchor_for_event(
                    {"start_seconds": relation.get("start_seconds")},
                    source_path=source_path,
                    audio_path=None,
                ),
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


def field_presence(value: Any) -> str:
    if not isinstance(value, dict):
        return "pending"
    known = [key for key, item in value.items() if has_value(item)]
    return ",".join(known) if known else "pending"


def effects_presence(value: Any) -> str:
    if not isinstance(value, dict):
        return "pending"
    enabled = [key for key, item in value.items() if has_value(item)]
    return ",".join(enabled) if enabled else "pending"


def has_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str) and not value:
        return False
    if isinstance(value, (list, tuple, set, dict)) and not value:
        return False
    return True


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
