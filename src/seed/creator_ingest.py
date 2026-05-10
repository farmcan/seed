from __future__ import annotations

from pathlib import Path

from seed.library import load_creator_video_list, load_source_records, save_source_record
from seed.models import CreatorVideo, CreatorVideoIngestItem, CreatorVideoIngestResult, SourceRecord
from seed.sources.yt_dlp_adapter import download_url


def ingest_creator_videos(
    list_path: Path,
    *,
    library_root: Path,
    authorized: bool,
    limit: int | None = None,
    start_index: int = 1,
    skip_existing: bool = True,
    download: bool = True,
    max_height: int = 360,
    max_filesize_mb: int | None = 100,
    cookies_from_browser: str | None = None,
    keep_going: bool = True,
) -> CreatorVideoIngestResult:
    if download and not authorized:
        raise ValueError("download requires authorized=True")
    if start_index < 1:
        raise ValueError("start_index must be greater than or equal to 1")

    video_list = load_creator_video_list(list_path)
    existing_urls = {
        _normalize_url(str(record.url))
        for record in load_source_records(library_root)
        if record.platform == video_list.platform and record.url is not None
    }
    selected = _select_videos(video_list.videos, start_index=start_index, limit=limit)
    result = CreatorVideoIngestResult(selected=len(selected))

    for video in selected:
        normalized_url = _normalize_url(video.url)
        if skip_existing and normalized_url in existing_urls:
            result.skipped += 1
            result.items.append(
                CreatorVideoIngestItem(url=video.url, title=video.title, status="skipped")
            )
            continue

        try:
            download_result = None
            if download:
                download_result = download_url(
                    video.url,
                    platform=video.platform,
                    library_root=library_root,
                    max_height=max_height,
                    max_filesize_mb=max_filesize_mb,
                    cookies_from_browser=cookies_from_browser,
                )

            owner = download_result.owner if download_result and download_result.owner else video.owner
            title = download_result.title if download_result and download_result.title else video.title
            record = SourceRecord(
                url=video.url,
                platform=video.platform,
                owner=owner,
                title=title,
                authorized=authorized,
                raw_path=download_result.raw_path if download_result else None,
                metadata_path=download_result.metadata_path if download_result else None,
            )
            source_record_path = save_source_record(library_root, record)
            existing_urls.add(normalized_url)
            result.recorded += 1
            if download_result and download_result.raw_path:
                result.downloaded += 1
            result.items.append(
                CreatorVideoIngestItem(
                    url=video.url,
                    title=title,
                    status="downloaded" if download else "recorded",
                    source_record_path=source_record_path,
                    raw_path=download_result.raw_path if download_result else None,
                    metadata_path=download_result.metadata_path if download_result else None,
                )
            )
        except Exception as error:
            result.failed += 1
            result.items.append(
                CreatorVideoIngestItem(
                    url=video.url,
                    title=video.title,
                    status="failed",
                    error=str(error),
                )
            )
            if not keep_going:
                raise

    return result


def _select_videos(
    videos: list[CreatorVideo],
    *,
    start_index: int,
    limit: int | None,
) -> list[CreatorVideo]:
    start = start_index - 1
    selected = videos[start:]
    if limit is None:
        return selected
    return selected[:limit]


def _normalize_url(url: str) -> str:
    return url.rstrip("/")
