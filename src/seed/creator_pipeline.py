from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from seed.costs import (
    DEFAULT_QWEN_VL_CURRENCY,
    build_cost_ledger,
    cost_ledger_output_path,
    ledger_total,
    write_cost_ledger,
)
from seed.agent_assets import (
    agent_asset_review_output_path,
    build_agent_assets_from_creator_profile,
    write_agent_assets,
)
from seed.creator_ingest import ingest_creator_videos
from seed.dag_export import export_video_dag_html, relative_asset_base
from seed.graphs.creator_dag import (
    build_creator_dag_graph,
    creator_dag_html_output_path,
    creator_dag_output_path,
    find_creator_asset_paths,
    write_creator_dag_graph,
)
from seed.library import init_library, save_creator_video_list, slugify
from seed.models import CreatorVideoList, Platform
from seed.pipeline import VideoPipelineOptions, run_video_pipeline
from seed.semantics.aggregator import (
    DEFAULT_CREATOR_PROFILE_SKILL_PATH,
    DEFAULT_MIN_CREATOR_PROFILE_VIDEOS,
    creator_profile_output_path,
    find_video_semantics_files,
    run_creator_profile_aggregation,
    validate_creator_profile_video_count,
)
from seed.semantics.validation import (
    creator_profile_validation_output_path,
    validate_creator_profile,
    write_creator_profile_validation,
)
from seed.sources.creator_videos import fetch_creator_video_list


@dataclass
class CreatorPipelineOptions:
    owner_name: str
    platform: Platform
    library_root: Path = Path("library")
    owner_id: str | None = None
    limit: int = 5
    start_index: int = 1
    published_after: datetime | None = None
    published_before: datetime | None = None
    authorized: bool = False
    download: bool = True
    skip_existing: bool = True
    keep_going: bool = True
    max_height: int = 360
    max_filesize_mb: int | None = 100
    cookies_from_browser: str | None = None
    vision: bool = True
    domain: str | None = None
    force: bool = False
    max_estimated_cost: float | None = None
    cost_currency: str = DEFAULT_QWEN_VL_CURRENCY
    aggregate_profile: bool = True
    min_profile_videos: int = DEFAULT_MIN_CREATOR_PROFILE_VIDEOS
    creator_profile_skill_path: Path = DEFAULT_CREATOR_PROFILE_SKILL_PATH
    codex_model: str | None = None
    generate_assets: bool = True
    build_creator_dag: bool = True
    export_creator_dag_html: bool = True


def creator_pipeline_manifest_path(*, library_root: Path, owner: str) -> Path:
    init_library(library_root)
    return library_root / "runs" / f"{slugify(owner)}.creator-pipeline.yaml"


def run_creator_pipeline(options: CreatorPipelineOptions) -> tuple[dict[str, Any], Path]:
    init_library(options.library_root)
    video_list = fetch_creator_video_list(
        platform=options.platform,
        owner_name=options.owner_name,
        limit=options.limit,
        owner_id=options.owner_id,
        cookies_from_browser=options.cookies_from_browser,
    )
    video_list = filter_creator_video_list_by_date(video_list, options)
    list_path = save_creator_video_list(options.library_root, video_list)
    ingest_result = ingest_creator_videos(
        list_path,
        library_root=options.library_root,
        authorized=options.authorized,
        limit=options.limit,
        start_index=options.start_index,
        skip_existing=options.skip_existing,
        download=options.download,
        max_height=options.max_height,
        max_filesize_mb=options.max_filesize_mb,
        cookies_from_browser=options.cookies_from_browser,
        keep_going=options.keep_going,
    )

    video_runs = []
    cost_paths: list[Path] = []
    current_ledger = build_cost_ledger(
        title=video_list.owner,
        cost_report_paths=[],
        scope="creator",
    )
    for item in ingest_result.items:
        if budget_exceeded(current_ledger, options):
            video_runs.append(
                {
                    "url": item.url,
                    "title": item.title,
                    "status": "skipped",
                    "reason": "budget_exceeded",
                    "budget": budget_record(current_ledger, options),
                }
            )
            continue
        if not item.raw_path:
            video_runs.append(
                {
                    "url": item.url,
                    "title": item.title,
                    "status": "skipped",
                    "reason": "no raw_path",
                }
            )
            continue
        try:
            context, manifest_path = run_video_pipeline(
                VideoPipelineOptions(
                    source=str(item.raw_path),
                    library_root=options.library_root,
                    platform=options.platform,
                    owner=video_list.owner,
                    title=item.title,
                    authorized=True,
                    download=False,
                    vision=options.vision,
                    domain=options.domain,
                    force=options.force,
                )
            )
            cost_path = getattr(context, "cost_ledger_path", None) or getattr(context, "cost_path", None)
            if cost_path:
                cost_paths.append(Path(cost_path))
                current_ledger = build_cost_ledger(
                    title=video_list.owner,
                    cost_report_paths=cost_paths,
                    scope="creator",
                )
            video_runs.append(
                {
                    "url": item.url,
                    "title": item.title,
                    "status": "completed",
                    "manifest_path": str(manifest_path),
                    "html_path": str(context.html_path) if context.html_path else None,
                    "cost_path": str(cost_path) if cost_path else None,
                    "budget": budget_record(current_ledger, options),
                }
            )
        except Exception as error:
            video_runs.append(
                {
                    "url": item.url,
                    "title": item.title,
                    "status": "failed",
                    "error": str(error),
                }
            )
            if not options.keep_going:
                raise

    ledger_path = cost_ledger_output_path(library_root=options.library_root, title=f"{video_list.owner}-creator")
    write_cost_ledger(ledger_path, current_ledger)
    creator_steps = run_creator_post_processing(
        owner=video_list.owner,
        platform=options.platform,
        ledger_path=ledger_path,
        options=options,
    )
    manifest = {
        "version": 1,
        "owner_query": options.owner_name,
        "owner": video_list.owner,
        "platform": str(options.platform),
        "domain": options.domain,
        "updated_at": datetime.now(UTC).isoformat(),
        "creator_video_list_path": str(list_path),
        "ingest": ingest_result.model_dump(mode="json"),
        "budget": budget_record(current_ledger, options),
        "video_runs": video_runs,
        "creator_steps": creator_steps,
    }
    manifest["cost_ledger_path"] = str(ledger_path)
    manifest_path = creator_pipeline_manifest_path(
        library_root=options.library_root,
        owner=video_list.owner,
    )
    manifest_path.write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return manifest, manifest_path


def run_creator_post_processing(
    *,
    owner: str,
    platform: Platform,
    ledger_path: Path,
    options: CreatorPipelineOptions,
) -> list[dict[str, Any]]:
    semantics_paths = find_video_semantics_files(
        library_root=options.library_root,
        owner=owner,
    )
    steps: list[dict[str, Any]] = []
    expected_profile_path = creator_profile_output_path(library_root=options.library_root, owner=owner)

    profile_step = maybe_aggregate_creator_profile(
        owner=owner,
        platform=platform,
        semantics_paths=semantics_paths,
        profile_path=expected_profile_path,
        options=options,
    )
    steps.append(profile_step)
    profile_path = resolved_creator_profile_path(
        expected_profile_path=expected_profile_path,
        profile_step=profile_step,
        options=options,
    )

    steps.append(
        maybe_generate_creator_assets(
            owner=owner,
            profile_path=profile_path,
            options=options,
        )
    )
    steps.append(
        maybe_build_creator_dag(
            owner=owner,
            semantics_paths=semantics_paths,
            profile_path=profile_path,
            ledger_path=ledger_path,
            options=options,
        )
    )
    return steps


def filter_creator_video_list_by_date(
    video_list: CreatorVideoList,
    options: CreatorPipelineOptions,
) -> CreatorVideoList:
    if options.published_after is None and options.published_before is None:
        return video_list

    after = normalize_datetime(options.published_after)
    before = normalize_datetime(options.published_before)
    kept = []
    missing_dates = 0
    for video in video_list.videos:
        published_at = normalize_datetime(video.published_at)
        if published_at is None:
            missing_dates += 1
            continue
        if after and published_at < after:
            continue
        if before and published_at >= before:
            continue
        kept.append(video)

    notes = list(video_list.notes)
    notes.append(
        "Filtered creator videos by published_at window: "
        f"after={after.isoformat() if after else 'none'}, "
        f"before={before.isoformat() if before else 'none'}, "
        f"kept={len(kept)}, missing_dates_excluded={missing_dates}."
    )
    return video_list.model_copy(update={"videos": kept, "notes": notes})


def normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def resolved_creator_profile_path(
    *,
    expected_profile_path: Path,
    profile_step: dict[str, Any],
    options: CreatorPipelineOptions,
) -> Path | None:
    if profile_step["status"] == "completed" and expected_profile_path.exists():
        return expected_profile_path
    if not options.aggregate_profile and expected_profile_path.exists():
        return expected_profile_path
    return None


def maybe_aggregate_creator_profile(
    *,
    owner: str,
    platform: Platform,
    semantics_paths: list[Path],
    profile_path: Path,
    options: CreatorPipelineOptions,
) -> dict[str, Any]:
    step: dict[str, Any] = {
        "name": "aggregate_creator_profile",
        "status": "pending",
        "inputs": {"semantics_count": len(semantics_paths)},
    }
    if not options.aggregate_profile:
        return skipped_step(step, "disabled")
    try:
        validate_creator_profile_video_count(semantics_paths, min_videos=options.min_profile_videos)
    except ValueError as error:
        step["min_profile_videos"] = options.min_profile_videos
        return skipped_step(step, str(error))

    try:
        run_creator_profile_aggregation(
            semantics_paths=semantics_paths,
            output_path=profile_path,
            skill_path=options.creator_profile_skill_path,
            owner=owner,
            platform=str(platform),
            domain=options.domain,
            model=options.codex_model,
            cwd=Path.cwd(),
        )
        validation = validate_creator_profile(profile_path, owner=owner)
        validation_path = creator_profile_validation_output_path(library_root=options.library_root, owner=owner)
        write_creator_profile_validation(validation_path, validation)
    except Exception as error:
        if not options.keep_going:
            raise
        return failed_step(step, error)

    step.update(
        {
            "status": "completed",
            "profile_path": str(profile_path),
            "validation_path": str(validation_path),
            "validation_status": validation["status"],
        }
    )
    return step


def maybe_generate_creator_assets(
    *,
    owner: str,
    profile_path: Path | None,
    options: CreatorPipelineOptions,
) -> dict[str, Any]:
    step: dict[str, Any] = {"name": "generate_agent_assets", "status": "pending"}
    if not options.generate_assets:
        return skipped_step(step, "disabled")
    if profile_path is None or not profile_path.exists():
        return skipped_step(step, "missing creator profile")
    try:
        assets = build_agent_assets_from_creator_profile(
            profile_path=profile_path,
            owner=owner,
        )
        paths = write_agent_assets(
            library_root=options.library_root,
            owner=owner,
            assets=assets,
        )
        review_path = agent_asset_review_output_path(library_root=options.library_root, owner=owner)
    except Exception as error:
        if not options.keep_going:
            raise
        return failed_step(step, error)

    step.update(
        {
            "status": "completed",
            "paths": {name: str(path) for name, path in paths.items()},
            "review_path": str(review_path),
        }
    )
    return step


def maybe_build_creator_dag(
    *,
    owner: str,
    semantics_paths: list[Path],
    profile_path: Path | None,
    ledger_path: Path,
    options: CreatorPipelineOptions,
) -> dict[str, Any]:
    step: dict[str, Any] = {
        "name": "build_creator_dag",
        "status": "pending",
        "inputs": {"semantics_count": len(semantics_paths)},
    }
    if not options.build_creator_dag:
        return skipped_step(step, "disabled")
    if not semantics_paths:
        return skipped_step(step, "no video semantics files")

    try:
        assets = find_creator_asset_paths(library_root=options.library_root, owner=owner)
        graph = build_creator_dag_graph(
            owner=owner,
            semantics_paths=semantics_paths,
            library_root=options.library_root,
            creator_profile_path=profile_path,
            skill_paths=assets["skill_paths"] if profile_path else [],
            check_paths=assets["check_paths"] if profile_path else [],
            validation_path=assets["validation_path"] if profile_path else None,
            cost_ledger_path=ledger_path if ledger_path.exists() else assets["cost_ledger_path"],
        )
        graph_path = creator_dag_output_path(library_root=options.library_root, owner=owner)
        write_creator_dag_graph(graph_path, graph)
        html_path = None
        if options.export_creator_dag_html:
            html_path = creator_dag_html_output_path(graph_path=graph_path)
            export_video_dag_html(
                graph_path=graph_path,
                output_path=html_path,
                asset_base=relative_asset_base(output_path=html_path, repo_root=Path.cwd()),
            )
    except Exception as error:
        if not options.keep_going:
            raise
        return failed_step(step, error)

    step.update(
        {
            "status": "completed",
            "graph_path": str(graph_path),
            "html_path": str(html_path) if html_path else None,
        }
    )
    return step


def skipped_step(step: dict[str, Any], reason: str) -> dict[str, Any]:
    step["status"] = "skipped"
    step["reason"] = reason
    return step


def failed_step(step: dict[str, Any], error: Exception) -> dict[str, Any]:
    step["status"] = "failed"
    step["error"] = str(error)
    return step


def budget_exceeded(ledger: dict[str, Any], options: CreatorPipelineOptions) -> bool:
    if options.max_estimated_cost is None:
        return False
    return ledger_total(ledger, currency=options.cost_currency) >= options.max_estimated_cost


def budget_record(ledger: dict[str, Any], options: CreatorPipelineOptions) -> dict[str, Any]:
    return {
        "currency": options.cost_currency,
        "max_estimated_cost": options.max_estimated_cost,
        "current_estimated_cost": ledger_total(ledger, currency=options.cost_currency),
        "exceeded": budget_exceeded(ledger, options),
    }
