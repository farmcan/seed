from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from seed.creator_ingest import ingest_creator_videos
from seed.library import init_library, save_creator_video_list, slugify
from seed.models import Platform
from seed.pipeline import VideoPipelineOptions, run_video_pipeline
from seed.sources.creator_videos import fetch_creator_video_list


@dataclass
class CreatorPipelineOptions:
    owner_name: str
    platform: Platform
    library_root: Path = Path("library")
    limit: int = 5
    start_index: int = 1
    authorized: bool = False
    download: bool = True
    skip_existing: bool = True
    keep_going: bool = True
    max_height: int = 360
    max_filesize_mb: int | None = 100
    cookies_from_browser: str | None = None
    vision: bool = True
    force: bool = False


def creator_pipeline_manifest_path(*, library_root: Path, owner: str) -> Path:
    init_library(library_root)
    return library_root / "runs" / f"{slugify(owner)}.creator-pipeline.yaml"


def run_creator_pipeline(options: CreatorPipelineOptions) -> tuple[dict[str, Any], Path]:
    init_library(options.library_root)
    video_list = fetch_creator_video_list(
        platform=options.platform,
        owner_name=options.owner_name,
        limit=options.limit,
        cookies_from_browser=options.cookies_from_browser,
    )
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
    for item in ingest_result.items:
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
                    force=options.force,
                )
            )
            video_runs.append(
                {
                    "url": item.url,
                    "title": item.title,
                    "status": "completed",
                    "manifest_path": str(manifest_path),
                    "html_path": str(context.html_path) if context.html_path else None,
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

    manifest = {
        "version": 1,
        "owner_query": options.owner_name,
        "owner": video_list.owner,
        "platform": str(options.platform),
        "updated_at": datetime.now(UTC).isoformat(),
        "creator_video_list_path": str(list_path),
        "ingest": ingest_result.model_dump(mode="json"),
        "video_runs": video_runs,
    }
    manifest_path = creator_pipeline_manifest_path(
        library_root=options.library_root,
        owner=video_list.owner,
    )
    manifest_path.write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return manifest, manifest_path
