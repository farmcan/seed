from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from seed.asr.chunked import transcribe_audio_with_optional_chunks
from seed.asr.providers import default_max_upload_mb_for_provider, default_model_for_provider
from seed.costs import (
    build_cost_ledger,
    build_qwen_vl_cost_item,
    cost_ledger_output_path,
    reserved_cost_item,
    reserved_codex_cost_item,
    video_cost_output_path,
    write_cost_ledger,
    write_video_cost_report,
)
from seed.dag_export import (
    export_pipeline_live_dag_html,
    export_video_dag_html,
    pipeline_live_dag_html_output_path,
    relative_asset_base,
    video_dag_html_output_path,
)
from seed.domains.finance import finance_signals_output_path, run_finance_signals_extraction
from seed.factcheck import build_claims_artifact, claims_output_path, write_claims_artifact
from seed.graphs.video_dag import (
    build_video_dag_graph,
    resolve_video_dag_artifacts,
    video_dag_output_path,
    write_video_dag_graph,
)
from seed.library import init_library, save_source_record, slugify
from seed.media import extract_audio
from seed.models import Platform, SourceRecord
from seed.semantics.analyzer import (
    DEFAULT_VIDEO_SEMANTICS_SKILL_PATH,
    run_video_semantics_analysis,
    video_semantics_output_path,
)
from seed.shorts import (
    DEFAULT_SCENE_THRESHOLD,
    DEFAULT_SHORT_MAX_SECONDS,
    build_frame_notes,
    build_motion_relations_artifact,
    build_short_video_profile,
    build_shots_artifact,
    frame_notes_output_path,
    load_frame_notes,
    motion_relations_output_path,
    short_profile_output_path,
    shots_output_path,
    write_frame_notes,
    write_motion_relations_artifact,
    write_short_video_profile,
    write_shots_artifact,
)
from seed.sources.yt_dlp_adapter import download_url
from seed.timeline import build_timeline_artifact, timeline_output_path, write_timeline_artifact
from seed.transcripts import transcript_output_path, write_transcript_markdown
from seed.vision.frames import extract_frames, frame_output_dir, load_frame_paths
from seed.vision.notes import visual_notes_output_path, write_visual_notes_markdown
from seed.vision.qwen_vl_provider import DEFAULT_QWEN_VL_MODEL, analyze_frames_with_qwen_vl_result


StepFn = Callable[[], dict[str, Any]]
ProgressCallback = Callable[[dict[str, Any]], None]


@dataclass
class VideoPipelineOptions:
    source: str
    library_root: Path = Path("library")
    platform: Platform | None = None
    owner: str = "unknown"
    title: str | None = None
    authorized: bool = False
    download: bool = True
    max_height: int = 360
    max_filesize_mb: int | None = 100
    cookies_from_browser: str | None = None
    asr_provider: str = "dashscope"
    asr_model: str | None = None
    language: str | None = None
    asr_prompt: str | None = None
    max_upload_mb: int | None = None
    chunk_audio: bool = True
    chunk_seconds: int | None = None
    every_seconds: int = 5
    max_frames: int = 12
    vision: bool = True
    vision_model: str = DEFAULT_QWEN_VL_MODEL
    vision_prompt: str | None = None
    short_form: bool | None = None
    short_max_seconds: float = DEFAULT_SHORT_MAX_SECONDS
    shot_detection: bool = True
    shot_threshold: float = DEFAULT_SCENE_THRESHOLD
    frame_notes: bool = True
    frame_mode: str = "shot-keyframes"
    frame_notes_fps: float = 1.0
    motion_relations: bool = True
    domain: str | None = None
    semantics_skill_path: Path = DEFAULT_VIDEO_SEMANTICS_SKILL_PATH
    codex_model: str | None = None
    force: bool = False
    export_html: bool = True
    progress_callback: ProgressCallback | None = field(default=None, repr=False, compare=False)


@dataclass
class VideoPipelineContext:
    title: str
    owner: str
    platform: str
    media_path: Path | None = None
    source_record_path: Path | None = None
    transcript_path: Path | None = None
    audio_path: Path | None = None
    frame_dir: Path | None = None
    short_profile_path: Path | None = None
    shots_path: Path | None = None
    frame_notes_path: Path | None = None
    motion_relations_path: Path | None = None
    visual_notes_path: Path | None = None
    cost_path: Path | None = None
    cost_ledger_path: Path | None = None
    semantics_path: Path | None = None
    finance_signals_path: Path | None = None
    timeline_path: Path | None = None
    claims_path: Path | None = None
    graph_path: Path | None = None
    html_path: Path | None = None
    live_html_path: Path | None = None


@dataclass
class PipelineStepRecord:
    step: str
    status: str
    started_at: str
    finished_at: str | None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float | None = None
    artifact_paths: list[str] = field(default_factory=list)
    cost_delta: dict[str, Any] | None = None
    provider: str | None = None
    model: str | None = None
    error: str | None = None


def run_manifest_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "runs" / f"{slugify(title)}.video-pipeline.yaml"


def run_status_output_path(*, library_root: Path, title: str) -> Path:
    return run_manifest_output_path(library_root=library_root, title=title).with_suffix(".status.json")


def planned_video_pipeline_steps(options: VideoPipelineOptions) -> list[str]:
    steps = [
        "source",
        "short_profile",
        "transcribe",
        "extract_frames",
        "detect_shots",
        "build_frame_notes",
        "build_motion_relations",
    ]
    if options.vision:
        steps.append("analyze_frames")
    steps.append("analyze_video_semantics")
    if options.domain == "finance":
        steps.append("extract_finance_signals")
    steps.extend(
        [
            "build_cost_ledger",
            "build_timeline",
            "extract_claims",
            "build_video_dag",
        ]
    )
    if options.export_html:
        steps.append("export_video_dag_html")
    return steps


def run_video_pipeline(options: VideoPipelineOptions) -> tuple[VideoPipelineContext, Path]:
    init_library(options.library_root)
    source_path = Path(options.source)
    initial_title = options.title or (source_path.stem if source_path.exists() else "video")
    context = VideoPipelineContext(
        title=initial_title,
        owner=options.owner,
        platform=str(options.platform or Platform.manual),
    )
    manifest_path = run_manifest_output_path(library_root=options.library_root, title=initial_title)
    status_path = run_status_output_path(library_root=options.library_root, title=initial_title)
    planned_steps = planned_video_pipeline_steps(options)
    steps: list[PipelineStepRecord] = []

    emit_progress(
        options,
        {
            "event": "run_started",
            "manifest_path": str(manifest_path),
            "status_path": str(status_path),
            "planned_steps": planned_steps,
        },
    )
    write_pipeline_status(
        status_path,
        options=options,
        context=context,
        steps=steps,
        planned_steps=planned_steps,
        run_status="running",
    )
    context.live_html_path = export_pipeline_live_dag(
        status_path=status_path,
        options=options,
    )

    def run_step(
        name: str,
        fn: StepFn,
        *,
        inputs: dict[str, Any] | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        started = datetime.now(UTC)
        started_at = started.isoformat()
        running_step = PipelineStepRecord(
            step=name,
            status="running",
            started_at=started_at,
            finished_at=None,
            inputs=_stringify_mapping(inputs or {}),
            provider=provider,
            model=model,
        )
        write_pipeline_status(
            status_path,
            options=options,
            context=context,
            steps=steps,
            planned_steps=planned_steps,
            run_status="running",
            current_step=running_step,
        )
        emit_progress(options, {"event": "step_started", "step": step_record_dict(running_step)})
        try:
            outputs = fn()
            status = str(outputs.pop("status", "completed"))
            finished = datetime.now(UTC)
            record = PipelineStepRecord(
                step=name,
                status=status,
                started_at=started_at,
                finished_at=finished.isoformat(),
                inputs=_stringify_mapping(inputs or {}),
                outputs=_stringify_mapping(outputs),
                duration_seconds=round((finished - started).total_seconds(), 3),
                artifact_paths=artifact_paths_from_outputs(outputs),
                cost_delta=cost_delta_from_outputs(outputs),
                provider=provider,
                model=model,
            )
            steps.append(record)
        except Exception as error:
            finished = datetime.now(UTC)
            record = PipelineStepRecord(
                step=name,
                status="failed",
                started_at=started_at,
                finished_at=finished.isoformat(),
                inputs=_stringify_mapping(inputs or {}),
                duration_seconds=round((finished - started).total_seconds(), 3),
                provider=provider,
                model=model,
                error=str(error),
            )
            steps.append(record)
            write_pipeline_manifest(manifest_path, options=options, context=context, steps=steps)
            write_pipeline_status(
                status_path,
                options=options,
                context=context,
                steps=steps,
                planned_steps=planned_steps,
                run_status="failed",
            )
            context.live_html_path = export_pipeline_live_dag(
                status_path=status_path,
                options=options,
            )
            emit_progress(options, {"event": "step_finished", "step": step_record_dict(record)})
            raise
        write_pipeline_manifest(manifest_path, options=options, context=context, steps=steps)
        write_pipeline_status(
            status_path,
            options=options,
            context=context,
            steps=steps,
            planned_steps=planned_steps,
            run_status="running",
        )
        emit_progress(options, {"event": "step_finished", "step": step_record_dict(record)})

    run_step("source", lambda: _source_step(options, context), inputs={"source": options.source})
    run_step("short_profile", lambda: _short_profile_step(options, context), inputs={"media_path": context.media_path})
    run_step(
        "transcribe",
        lambda: _transcribe_step(options, context),
        inputs={"media_path": context.media_path},
        provider=options.asr_provider,
        model=options.asr_model or default_model_for_provider(options.asr_provider),
    )
    run_step("extract_frames", lambda: _frames_step(options, context), inputs={"media_path": context.media_path})
    run_step(
        "detect_shots",
        lambda: _shots_step(options, context),
        inputs={
            "media_path": context.media_path,
            "short_profile_path": context.short_profile_path,
        },
        provider="ffmpeg-scene",
    )
    run_step(
        "build_frame_notes",
        lambda: _frame_notes_step(options, context),
        inputs={
            "media_path": context.media_path,
            "short_profile_path": context.short_profile_path,
            "shots_path": context.shots_path,
        },
    )
    run_step(
        "build_motion_relations",
        lambda: _motion_relations_step(options, context),
        inputs={
            "short_profile_path": context.short_profile_path,
            "shots_path": context.shots_path,
            "frame_notes_path": context.frame_notes_path,
        },
    )
    if options.vision:
        run_step(
            "analyze_frames",
            lambda: _visual_step(options, context),
            inputs={"frame_dir": context.frame_dir},
            provider="dashscope",
            model=options.vision_model,
        )
    run_step(
        "analyze_video_semantics",
        lambda: _semantics_step(options, context),
        inputs={
            "transcript_path": context.transcript_path,
            "visual_notes_path": context.visual_notes_path,
        },
        provider="codex",
        model=options.codex_model,
    )
    if options.domain == "finance":
        run_step(
            "extract_finance_signals",
            lambda: _finance_signals_step(options, context),
            inputs={"semantics_path": context.semantics_path},
            provider="codex",
            model=options.codex_model,
        )
    run_step("build_cost_ledger", lambda: _cost_ledger_step(options, context), inputs={"title": context.title})
    run_step("build_timeline", lambda: _timeline_step(options, context), inputs={"title": context.title})
    run_step("extract_claims", lambda: _claims_step(options, context), inputs={"semantics_path": context.semantics_path})
    run_step("build_video_dag", lambda: _dag_step(options, context), inputs={"title": context.title})
    if options.export_html:
        run_step("export_video_dag_html", lambda: _html_step(options, context), inputs={"graph_path": context.graph_path})

    write_pipeline_manifest(manifest_path, options=options, context=context, steps=steps)
    write_pipeline_status(
        status_path,
        options=options,
        context=context,
        steps=steps,
        planned_steps=planned_steps,
        run_status="completed",
    )
    context.live_html_path = export_pipeline_live_dag(
        status_path=status_path,
        options=options,
    )
    emit_progress(
        options,
        {
            "event": "run_finished",
            "manifest_path": str(manifest_path),
            "status_path": str(status_path),
            "live_html_path": str(context.live_html_path) if context.live_html_path else None,
            "steps": [step_record_dict(step) for step in steps],
        },
    )
    return context, manifest_path


def export_pipeline_live_dag(*, status_path: Path, options: VideoPipelineOptions) -> Path | None:
    if not options.export_html:
        return None
    output_path = pipeline_live_dag_html_output_path(status_path=status_path)
    return export_pipeline_live_dag_html(
        status_path=status_path,
        output_path=output_path,
        asset_base=relative_asset_base(output_path=output_path, repo_root=Path.cwd()),
        status_url=status_path.name,
        live_status=True,
    )


def write_pipeline_manifest(
    path: Path,
    *,
    options: VideoPipelineOptions,
    context: VideoPipelineContext,
    steps: list[PipelineStepRecord],
) -> Path:
    data = {
        "version": 1,
        "source": options.source,
        "title": context.title,
        "owner": context.owner,
        "platform": context.platform,
        "domain": options.domain,
        "updated_at": datetime.now(UTC).isoformat(),
        "force": options.force,
        "outputs": _stringify_mapping(context.__dict__),
        "steps": [step.__dict__ for step in steps],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def write_pipeline_status(
    path: Path,
    *,
    options: VideoPipelineOptions,
    context: VideoPipelineContext,
    steps: list[PipelineStepRecord],
    planned_steps: list[str],
    run_status: str,
    current_step: PipelineStepRecord | None = None,
) -> Path:
    completed_by_name = {step.step: step_record_dict(step) for step in steps}
    rendered_steps: list[dict[str, Any]] = []
    for name in planned_steps:
        if name in completed_by_name:
            rendered_steps.append(completed_by_name[name])
        elif current_step and current_step.step == name:
            rendered_steps.append(step_record_dict(current_step))
        else:
            rendered_steps.append(
                {
                    "step": name,
                    "status": "pending",
                    "started_at": None,
                    "finished_at": None,
                    "duration_seconds": None,
                    "inputs": {},
                    "outputs": {},
                    "artifact_paths": [],
                    "cost_delta": None,
                    "provider": None,
                    "model": None,
                    "error": None,
                }
            )
    data = {
        "version": 1,
        "kind": "video_pipeline_status",
        "status": run_status,
        "source": options.source,
        "title": context.title,
        "owner": context.owner,
        "platform": context.platform,
        "domain": options.domain,
        "updated_at": datetime.now(UTC).isoformat(),
        "current_step": current_step.step if current_step else None,
        "outputs": _stringify_mapping(context.__dict__),
        "steps": rendered_steps,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def step_record_dict(record: PipelineStepRecord) -> dict[str, Any]:
    return {
        "step": record.step,
        "status": record.status,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "inputs": record.inputs,
        "outputs": record.outputs,
        "duration_seconds": record.duration_seconds,
        "artifact_paths": record.artifact_paths,
        "cost_delta": record.cost_delta,
        "provider": record.provider,
        "model": record.model,
        "error": record.error,
    }


def emit_progress(options: VideoPipelineOptions, event: dict[str, Any]) -> None:
    if options.progress_callback:
        options.progress_callback(event)


def artifact_paths_from_outputs(outputs: dict[str, Any]) -> list[str]:
    paths: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, Path):
            paths.append(str(value))
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                visit(item)

    visit(outputs)
    return sorted(set(paths))


def cost_delta_from_outputs(outputs: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("cost_ledger_path", "cost_path"):
        path = outputs.get(key)
        if isinstance(path, Path) and path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
            return {
                "path": str(path),
                "totals": data.get("totals", {}),
            }
    return None


def _source_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    source_path = Path(options.source)
    if source_path.exists():
        context.media_path = source_path
        context.title = options.title or source_path.stem
        context.platform = str(options.platform or Platform.manual)
        return {"status": "completed", "media_path": context.media_path}

    if not options.platform:
        raise ValueError("--platform is required when source is a URL")
    if options.download and not options.authorized:
        raise ValueError("--download requires --authorized")

    result = None
    if options.download:
        result = download_url(
            options.source,
            platform=options.platform,
            library_root=options.library_root,
            max_height=options.max_height,
            max_filesize_mb=options.max_filesize_mb,
            cookies_from_browser=options.cookies_from_browser,
        )
        context.media_path = result.raw_path
        if result.title and options.title is None:
            context.title = result.title
        if result.owner and options.owner == "unknown":
            context.owner = result.owner

    context.platform = str(options.platform)
    record = SourceRecord(
        url=options.source,
        platform=options.platform,
        owner=context.owner,
        title=context.title,
        authorized=options.authorized,
        raw_path=result.raw_path if result else None,
        metadata_path=result.metadata_path if result else None,
        download_provider=result.provider if result else None,
        fallback_used=result.fallback_used if result else False,
        download_notes=result.notes if result else [],
    )
    context.source_record_path = save_source_record(options.library_root, record)
    return {
        "status": "completed",
        "source_record_path": context.source_record_path,
        "media_path": context.media_path,
    }


def _transcribe_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    media_path = _require_path(context.media_path, "media_path")
    output_path = transcript_output_path(
        library_root=options.library_root,
        media_path=media_path,
        title=context.title,
    )
    if output_path.exists() and not options.force:
        context.transcript_path = output_path
        context.audio_path = media_path.with_suffix(".asr.mp3")
        return {"status": "skipped", "transcript_path": output_path}

    resolved_model = options.asr_model or default_model_for_provider(options.asr_provider)
    resolved_max_upload_mb = options.max_upload_mb or default_max_upload_mb_for_provider(options.asr_provider)
    audio_path = extract_audio(media_path, options.library_root)
    text, chunks = transcribe_audio_with_optional_chunks(
        audio_path,
        provider=options.asr_provider,
        model=resolved_model,
        language=options.language,
        prompt=options.asr_prompt,
        max_upload_mb=resolved_max_upload_mb,
        chunk_audio=options.chunk_audio,
        chunk_seconds=options.chunk_seconds,
    )
    write_transcript_markdown(
        output_path,
        text=text,
        media_path=media_path,
        audio_path=audio_path,
        provider=options.asr_provider,
        model=resolved_model,
        title=context.title,
        language=options.language,
        chunks=chunks,
    )
    context.audio_path = audio_path
    context.transcript_path = output_path
    return {"transcript_path": output_path, "audio_path": audio_path, "chunks": len(chunks)}


def _frames_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    media_path = _require_path(context.media_path, "media_path")
    output_dir = frame_output_dir(media_path, options.library_root)
    if load_frame_paths(output_dir) and not options.force:
        context.frame_dir = output_dir
        return {"status": "skipped", "frame_dir": output_dir, "frames": len(load_frame_paths(output_dir))}
    context.frame_dir = extract_frames(
        media_path,
        options.library_root,
        every_seconds=options.every_seconds,
        max_frames=options.max_frames,
    )
    return {"frame_dir": context.frame_dir, "frames": len(load_frame_paths(context.frame_dir))}


def _short_profile_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    media_path = _require_path(context.media_path, "media_path")
    output_path = short_profile_output_path(library_root=options.library_root, title=context.title)
    if output_path.exists() and not options.force:
        context.short_profile_path = output_path
        return {"status": "skipped", "short_profile_path": output_path}

    profile = build_short_video_profile(
        media_path=media_path,
        title=context.title,
        platform=context.platform,
        short_max_seconds=options.short_max_seconds,
    )
    if options.short_form is not None:
        profile["is_short_form"] = options.short_form
        profile["short_form_override"] = True
    write_short_video_profile(output_path, profile)
    context.short_profile_path = output_path
    return {
        "short_profile_path": output_path,
        "duration_seconds": profile.get("duration_seconds"),
        "is_short_form": profile.get("is_short_form"),
    }


def _shots_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    if not options.shot_detection:
        return {"status": "skipped", "reason": "shot detection disabled"}
    media_path = _require_path(context.media_path, "media_path")
    profile_path = _require_path(context.short_profile_path, "short_profile_path")
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    if not profile.get("is_short_form"):
        return {"status": "skipped", "reason": "not short form", "short_profile_path": profile_path}

    output_path = shots_output_path(library_root=options.library_root, title=context.title)
    if output_path.exists() and not options.force:
        context.shots_path = output_path
        return {"status": "skipped", "shots_path": output_path}

    artifact = build_shots_artifact(
        media_path=media_path,
        title=context.title,
        profile=profile,
        library_root=options.library_root,
        threshold=options.shot_threshold,
    )
    write_shots_artifact(output_path, artifact)
    context.shots_path = output_path
    return {"shots_path": output_path, "shots": len(artifact["shots"])}


def _frame_notes_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    if not options.frame_notes:
        return {"status": "skipped", "reason": "frame notes disabled"}
    media_path = _require_path(context.media_path, "media_path")
    profile_path = _require_path(context.short_profile_path, "short_profile_path")
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    if not profile.get("is_short_form"):
        return {"status": "skipped", "reason": "not short form", "short_profile_path": profile_path}

    output_path = frame_notes_output_path(library_root=options.library_root, title=context.title)
    if output_path.exists() and not options.force:
        context.frame_notes_path = output_path
        return {"status": "skipped", "frame_notes_path": output_path}

    shots_artifact = {}
    if context.shots_path and context.shots_path.exists():
        shots_artifact = yaml.safe_load(context.shots_path.read_text(encoding="utf-8")) or {}
    notes = build_frame_notes(
        media_path=media_path,
        title=context.title,
        profile=profile,
        shots_artifact=shots_artifact,
        library_root=options.library_root,
        frame_mode=options.frame_mode,
        fps=options.frame_notes_fps,
    )
    write_frame_notes(output_path, notes)
    context.frame_notes_path = output_path
    return {"frame_notes_path": output_path, "frames": len(notes), "frame_mode": options.frame_mode}


def _motion_relations_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    if not options.motion_relations:
        return {"status": "skipped", "reason": "motion relations disabled"}
    profile_path = _require_path(context.short_profile_path, "short_profile_path")
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    if not profile.get("is_short_form"):
        return {"status": "skipped", "reason": "not short form", "short_profile_path": profile_path}

    output_path = motion_relations_output_path(library_root=options.library_root, title=context.title)
    if output_path.exists() and not options.force:
        context.motion_relations_path = output_path
        return {"status": "skipped", "motion_relations_path": output_path}

    shots_artifact = {}
    if context.shots_path and context.shots_path.exists():
        shots_artifact = yaml.safe_load(context.shots_path.read_text(encoding="utf-8")) or {}
    notes = load_frame_notes(context.frame_notes_path)
    artifact = build_motion_relations_artifact(
        title=context.title,
        profile=profile,
        shots_artifact=shots_artifact,
        frame_notes=notes,
    )
    write_motion_relations_artifact(output_path, artifact)
    context.motion_relations_path = output_path
    return {
        "motion_relations_path": output_path,
        "relations": len(artifact["relations"]),
        "provider": artifact["provider"],
    }


def _visual_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    frame_dir = _require_path(context.frame_dir, "frame_dir")
    frame_paths = load_frame_paths(frame_dir)
    output_path = visual_notes_output_path(
        library_root=options.library_root,
        source_path=frame_dir,
        title=context.title,
    )
    cost_path = video_cost_output_path(library_root=options.library_root, title=context.title)
    if output_path.exists() and cost_path.exists() and not options.force:
        context.visual_notes_path = output_path
        context.cost_path = cost_path
        return {"status": "skipped", "visual_notes_path": output_path, "cost_path": cost_path}

    result = analyze_frames_with_qwen_vl_result(
        frame_paths,
        model=options.vision_model,
        prompt=options.vision_prompt,
    )
    write_visual_notes_markdown(
        output_path,
        analysis=result.analysis,
        frame_dir=frame_dir,
        frame_paths=frame_paths,
        provider="dashscope",
        model=options.vision_model,
        title=context.title,
    )
    cost_item = build_qwen_vl_cost_item(
        title=context.title,
        model=options.vision_model,
        usage=result.usage,
        artifact_path=output_path,
        frame_count=len(frame_paths),
    )
    write_video_cost_report(
        cost_path,
        title=context.title,
        items=[cost_item, reserved_codex_cost_item()],
    )
    context.visual_notes_path = output_path
    context.cost_path = cost_path
    return {
        "visual_notes_path": output_path,
        "cost_path": cost_path,
        "input_tokens": result.usage.input_tokens,
        "output_tokens": result.usage.output_tokens,
    }


def _cost_ledger_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    output_path = cost_ledger_output_path(library_root=options.library_root, title=context.title)
    if output_path.exists() and not options.force:
        context.cost_ledger_path = output_path
        return {"status": "skipped", "cost_ledger_path": output_path}
    cost_report_paths = [context.cost_path] if context.cost_path else []
    ledger = build_cost_ledger(
        title=context.title,
        cost_report_paths=[path for path in cost_report_paths if path],
        scope="video",
        reserved_items=[
            reserved_cost_item(kind="asr", provider=options.asr_provider, operation="transcribe-media"),
            reserved_codex_cost_item(),
            reserved_cost_item(kind="search", provider="unknown", operation="verify-claims"),
        ],
    )
    write_cost_ledger(output_path, ledger)
    context.cost_ledger_path = output_path
    return {"cost_ledger_path": output_path, "totals": ledger["totals"]}


def _semantics_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    transcript_path = _require_path(context.transcript_path, "transcript_path")
    output_path = video_semantics_output_path(
        library_root=options.library_root,
        transcript_path=transcript_path,
        title=context.title,
    )
    if output_path.exists() and not options.force:
        context.semantics_path = output_path
        return {"status": "skipped", "semantics_path": output_path}
    run_video_semantics_analysis(
        transcript_path=transcript_path,
        output_path=output_path,
        skill_path=options.semantics_skill_path,
        visual_notes_path=context.visual_notes_path,
        title=context.title,
        owner=context.owner,
        platform=context.platform,
        domain=options.domain,
        model=options.codex_model,
        cwd=Path.cwd(),
    )
    context.semantics_path = output_path
    return {"semantics_path": output_path}


def _finance_signals_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    semantics_path = _require_path(context.semantics_path, "semantics_path")
    output_path = finance_signals_output_path(library_root=options.library_root, title=context.title)
    if output_path.exists() and not options.force:
        context.finance_signals_path = output_path
        return {"status": "skipped", "finance_signals_path": output_path}
    run_finance_signals_extraction(
        semantics_path=semantics_path,
        output_path=output_path,
        title=context.title,
        owner=context.owner,
        platform=context.platform,
        model=options.codex_model,
        cwd=Path.cwd(),
    )
    context.finance_signals_path = output_path
    return {"finance_signals_path": output_path}


def _timeline_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    output_path = timeline_output_path(
        library_root=options.library_root,
        title=context.title,
        transcript_path=context.transcript_path,
    )
    if output_path.exists() and not options.force:
        context.timeline_path = output_path
        return {"status": "skipped", "timeline_path": output_path}
    artifact = build_timeline_artifact(
        title=context.title,
        transcript_path=context.transcript_path,
        frame_dir=context.frame_dir,
        visual_notes_path=context.visual_notes_path,
        semantics_path=context.semantics_path,
    )
    write_timeline_artifact(output_path, artifact)
    context.timeline_path = output_path
    return {"timeline_path": output_path, "events": len(artifact["events"])}


def _claims_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    semantics_path = _require_path(context.semantics_path, "semantics_path")
    output_path = claims_output_path(
        library_root=options.library_root,
        title=context.title,
        semantics_path=semantics_path,
    )
    if output_path.exists() and not options.force:
        context.claims_path = output_path
        return {"status": "skipped", "claims_path": output_path}
    artifact = build_claims_artifact(semantics_path=semantics_path, title=context.title)
    write_claims_artifact(output_path, artifact)
    context.claims_path = output_path
    return {"claims_path": output_path, "claims": len(artifact["claims"])}


def _dag_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    artifacts = resolve_video_dag_artifacts(
        library_root=options.library_root,
        title=context.title,
        source_path=context.media_path,
        audio_path=context.audio_path,
        transcript_path=context.transcript_path,
        frame_dir=context.frame_dir,
        visual_notes_path=context.visual_notes_path,
        semantics_path=context.semantics_path,
        finance_signals_path=context.finance_signals_path,
        timeline_path=context.timeline_path,
        claims_path=context.claims_path,
        cost_path=context.cost_ledger_path or context.cost_path,
        short_profile_path=context.short_profile_path,
        shots_path=context.shots_path,
        frame_notes_path=context.frame_notes_path,
        motion_relations_path=context.motion_relations_path,
    )
    graph = build_video_dag_graph(
        title=context.title,
        owner=context.owner,
        platform=context.platform,
        source_path=artifacts["source_path"],
        audio_path=artifacts["audio_path"],
        transcript_path=artifacts["transcript_path"],
        frame_dir=artifacts["frame_dir"],
        visual_notes_path=artifacts["visual_notes_path"],
        semantics_path=artifacts["semantics_path"],
        finance_signals_path=artifacts["finance_signals_path"],
        timeline_path=artifacts["timeline_path"],
        claims_path=artifacts["claims_path"],
        cost_path=artifacts["cost_path"],
        creator_profile_path=artifacts["creator_profile_path"],
        short_profile_path=artifacts["short_profile_path"],
        shots_path=artifacts["shots_path"],
        frame_notes_path=artifacts["frame_notes_path"],
        motion_relations_path=artifacts["motion_relations_path"],
    )
    output_path = video_dag_output_path(library_root=options.library_root, title=context.title)
    write_video_dag_graph(output_path, graph)
    context.graph_path = output_path
    return {"graph_path": output_path, "nodes": len(graph["nodes"]), "edges": len(graph["edges"])}


def _html_step(options: VideoPipelineOptions, context: VideoPipelineContext) -> dict[str, Any]:
    graph_path = _require_path(context.graph_path, "graph_path")
    output_path = video_dag_html_output_path(graph_path=graph_path)
    export_video_dag_html(
        graph_path=graph_path,
        output_path=output_path,
        asset_base=relative_asset_base(output_path=output_path, repo_root=Path.cwd()),
    )
    context.html_path = output_path
    return {"html_path": output_path}


def _require_path(path: Path | None, name: str) -> Path:
    if path is None:
        raise ValueError(f"{name} is required")
    return path


def _stringify_mapping(value: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, item in value.items():
        if isinstance(item, Path):
            result[key] = str(item)
        elif isinstance(item, dict):
            result[key] = _stringify_mapping(item)
        else:
            result[key] = item
    return result
