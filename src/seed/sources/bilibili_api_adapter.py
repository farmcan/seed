from __future__ import annotations

import json
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify
from seed.models import DownloadResult


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
}


def download_bilibili_via_api(
    url: str,
    *,
    library_root: Path,
    max_height: int = 360,
    max_filesize_mb: int | None = 100,
) -> DownloadResult:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("Bilibili API fallback requires ffmpeg on PATH")

    init_library(library_root)
    raw_dir = library_root / "raw"
    bvid = _extract_bvid(url)
    view = _get_json(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}")
    data = view["data"]
    cid = data["cid"]
    title = data.get("title") or bvid
    owner = (data.get("owner") or {}).get("name")
    page_url = f"https://www.bilibili.com/video/{bvid}/"

    play = _get_json(
        "https://api.bilibili.com/x/player/playurl?"
        + urllib.parse.urlencode(
            {
                "bvid": bvid,
                "cid": cid,
                "qn": 16,
                "fnval": 16,
                "fourk": 0,
            }
        ),
        referer=page_url,
    )
    dash = play["data"]["dash"]
    video = _select_video(dash["video"], max_height=max_height)
    audio = _select_audio(dash.get("audio") or [])

    safe_name = slugify(f"bilibili-{bvid}-{title}")[:120]
    video_part = raw_dir / f"{safe_name}.video.m4s"
    audio_part = raw_dir / f"{safe_name}.audio.m4s"
    media_path = raw_dir / f"{safe_name}.mp4"
    metadata_path = raw_dir / f"{safe_name}.info.json"

    metadata = {
        "bvid": bvid,
        "cid": cid,
        "title": title,
        "owner": owner,
        "webpage_url": page_url,
        "view": data,
        "selected_streams": {
            "video": _stream_summary(video),
            "audio": _stream_summary(audio) if audio else None,
        },
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    _download_file(_stream_url(video), video_part, referer=page_url, max_filesize_mb=max_filesize_mb)
    if audio:
        _download_file(_stream_url(audio), audio_part, referer=page_url, max_filesize_mb=max_filesize_mb)
        _merge_av(video_part, audio_part, media_path)
        _remove_file(audio_part)
    else:
        _remux_video(video_part, media_path)
    _remove_file(video_part)

    return DownloadResult(
        title=title,
        owner=owner,
        webpage_url=page_url,
        raw_path=media_path,
        metadata_path=metadata_path,
    )


def _extract_bvid(url: str) -> str:
    parts = urllib.parse.urlparse(url)
    for part in parts.path.split("/"):
        if part.startswith("BV"):
            return part
    raise ValueError(f"Could not find BVID in URL: {url}")


def _get_json(url: str, *, referer: str | None = None) -> dict[str, Any]:
    headers = dict(HEADERS)
    if referer:
        headers["Referer"] = referer
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("code") != 0:
        raise RuntimeError(f"Bilibili API returned {payload.get('code')}: {payload.get('message')}")
    return payload


def _select_video(streams: list[dict[str, Any]], *, max_height: int) -> dict[str, Any]:
    eligible = [stream for stream in streams if int(stream.get("height") or 0) <= max_height]
    if not eligible:
        eligible = streams
    return min(eligible, key=lambda stream: (int(stream.get("height") or 0), int(stream.get("bandwidth") or 0)))


def _select_audio(streams: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not streams:
        return None
    return min(streams, key=lambda stream: int(stream.get("bandwidth") or 0))


def _stream_url(stream: dict[str, Any]) -> str:
    return stream.get("baseUrl") or stream["base_url"]


def _stream_summary(stream: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": stream.get("id"),
        "height": stream.get("height"),
        "width": stream.get("width"),
        "bandwidth": stream.get("bandwidth"),
        "codecs": stream.get("codecs"),
    }


def _download_file(
    url: str,
    path: Path,
    *,
    referer: str,
    max_filesize_mb: int | None,
) -> None:
    request = urllib.request.Request(url, headers={**HEADERS, "Referer": referer})
    with urllib.request.urlopen(request, timeout=60) as response:
        content_length = response.headers.get("Content-Length")
        if content_length and max_filesize_mb is not None:
            max_bytes = max_filesize_mb * 1024 * 1024
            if int(content_length) > max_bytes:
                raise RuntimeError(f"Remote file is larger than {max_filesize_mb} MB")

        with path.open("wb") as output:
            shutil.copyfileobj(response, output)


def _merge_av(video_path: Path, audio_path: Path, output_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-c",
            "copy",
            str(output_path),
        ],
        check=True,
    )


def _remux_video(video_path: Path, output_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video_path),
            "-c",
            "copy",
            str(output_path),
        ],
        check=True,
    )


def _remove_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
