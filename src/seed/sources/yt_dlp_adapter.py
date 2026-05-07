from __future__ import annotations

import os
from pathlib import Path

from yt_dlp import DownloadError, YoutubeDL

from seed.library import init_library
from seed.models import DownloadResult, Platform
from seed.sources.bilibili_api_adapter import download_bilibili_via_api


COOKIES_ENV_BY_PLATFORM = {
    Platform.bilibili: "BILIBILI_COOKIES_FILE",
    Platform.xiaohongshu: "XIAOHONGSHU_COOKIES_FILE",
}


def download_url(
    url: str,
    *,
    platform: Platform,
    library_root: Path,
    max_height: int = 360,
    max_filesize_mb: int | None = 100,
) -> DownloadResult:
    init_library(library_root)
    raw_dir = library_root / "raw"
    downloaded_files: list[Path] = []

    def capture_download(download: dict) -> None:
        if download.get("status") == "finished" and download.get("filename"):
            downloaded_files.append(Path(download["filename"]))

    options = {
        "format": f"bv*[height<={max_height}]+ba/b[height<={max_height}]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": str(raw_dir / "%(extractor_key)s-%(id)s-%(title).80B.%(ext)s"),
        "paths": {"home": str(raw_dir)},
        "progress_hooks": [capture_download],
        "quiet": False,
        "restrictfilenames": True,
        "writeinfojson": True,
    }
    if max_filesize_mb is not None:
        options["max_filesize"] = max_filesize_mb * 1024 * 1024

    cookies_env = COOKIES_ENV_BY_PLATFORM.get(platform)
    if cookies_env and os.getenv(cookies_env):
        options["cookiefile"] = os.environ[cookies_env]

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
    except DownloadError:
        if platform != Platform.bilibili:
            raise
        return download_bilibili_via_api(
            url,
            library_root=library_root,
            max_height=max_height,
            max_filesize_mb=max_filesize_mb,
        )

    raw_path = _select_media_path(downloaded_files, raw_dir)
    metadata_path = _select_metadata_path(raw_path, raw_dir)

    return DownloadResult(
        title=info.get("title"),
        owner=info.get("uploader") or info.get("channel"),
        webpage_url=info.get("webpage_url") or url,
        raw_path=raw_path,
        metadata_path=metadata_path,
    )


def _select_media_path(downloaded_files: list[Path], raw_dir: Path) -> Path | None:
    media_suffixes = {".mp4", ".m4a", ".webm", ".flv", ".mkv"}
    for path in reversed(downloaded_files):
        if path.exists() and path.suffix.lower() in media_suffixes:
            return path

    candidates = [
        path
        for path in raw_dir.glob("*")
        if path.is_file() and path.suffix.lower() in media_suffixes
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def _select_metadata_path(raw_path: Path | None, raw_dir: Path) -> Path | None:
    if raw_path is not None:
        metadata_path = raw_path.with_suffix(".info.json")
        if metadata_path.exists():
            return metadata_path

    candidates = list(raw_dir.glob("*.info.json"))
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)
