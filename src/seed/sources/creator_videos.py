from __future__ import annotations

import hashlib
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from http.cookiejar import CookieJar
from typing import Any

from yt_dlp import DownloadError, YoutubeDL

from seed.models import CreatorVideo, CreatorVideoList, Platform
from seed.sources.yt_dlp_adapter import COOKIES_ENV_BY_PLATFORM


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

BILIBILI_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Referer": "https://www.bilibili.com/",
}

WBI_MIXIN_KEY_TABLE = [
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
]


def fetch_creator_video_list(
    *,
    platform: Platform,
    owner_name: str,
    limit: int = 20,
    cookies_from_browser: str | None = None,
) -> CreatorVideoList:
    if platform == Platform.bilibili:
        return fetch_bilibili_creator_video_list(
            owner_name=owner_name,
            limit=limit,
            cookies_from_browser=cookies_from_browser,
        )
    if platform == Platform.xiaohongshu:
        return fetch_xiaohongshu_creator_video_list(owner_name=owner_name, limit=limit)
    raise ValueError(f"Creator video discovery is not supported for platform: {platform}")


def fetch_bilibili_creator_video_list(
    *,
    owner_name: str,
    limit: int = 20,
    cookies_from_browser: str | None = None,
) -> CreatorVideoList:
    try:
        candidate = _find_bilibili_user(owner_name)
    except Exception as error:
        return CreatorVideoList(
            platform=Platform.bilibili,
            owner_query=owner_name,
            owner=owner_name,
            provider="bilibili-user-search-blocked",
            notes=[
                f"Bilibili user search failed: {error}",
                "Try --cookies-from-browser or BILIBILI_COOKIES_FILE if the request is blocked.",
            ],
        )
    owner = candidate.get("uname") or owner_name
    owner_id = str(candidate["mid"])
    owner_url = f"https://space.bilibili.com/{owner_id}/video"
    notes: list[str] = []

    try:
        videos = _fetch_bilibili_space_videos_with_ytdlp(
            owner=owner,
            owner_id=owner_id,
            owner_url=owner_url,
            limit=limit,
            cookies_from_browser=cookies_from_browser,
        )
        provider = "yt-dlp:bilibili-space"
    except DownloadError as error:
        notes.append(f"yt-dlp space extractor failed: {error}")
        try:
            videos = _fetch_bilibili_space_videos_with_api(
                owner=owner,
                owner_id=owner_id,
                limit=limit,
            )
            provider = "bilibili-wbi-api"
        except Exception as fallback_error:
            notes.append(f"Bilibili WBI API fallback failed: {fallback_error}")
            notes.append("Try --cookies-from-browser or BILIBILI_COOKIES_FILE if the request is blocked.")
            videos = []
            provider = "bilibili-discovery-blocked"

    return CreatorVideoList(
        platform=Platform.bilibili,
        owner_query=owner_name,
        owner=owner,
        owner_id=owner_id,
        owner_url=owner_url,
        provider=provider,
        videos=videos[:limit],
        notes=notes,
    )


def fetch_xiaohongshu_creator_video_list(*, owner_name: str, limit: int = 20) -> CreatorVideoList:
    profile_links = _search_web_links(
        f"site:xiaohongshu.com/user/profile {owner_name} 小红书",
        limit=5,
    )
    note_links = _search_web_links(
        f"site:xiaohongshu.com/explore {owner_name} 小红书 视频",
        limit=limit,
    )
    owner_url = _first_matching_link(profile_links, "/user/profile/")
    videos = [
        CreatorVideo(
            platform=Platform.xiaohongshu,
            owner=owner_name,
            video_id=_extract_xiaohongshu_note_id(url),
            title=None,
            url=url,
            metadata={"discovery": "web-search-candidate"},
        )
        for url in note_links
        if "/explore/" in url
    ][:limit]
    notes = [
        "Xiaohongshu does not expose a stable unauthenticated creator note list on the web.",
        "These entries are search candidates, not an authoritative creator timeline.",
        "Use a cookie-backed xiaohongshu provider later for reliable profile note pagination.",
    ]
    if profile_links:
        notes.append("Profile candidates: " + ", ".join(profile_links[:3]))

    return CreatorVideoList(
        platform=Platform.xiaohongshu,
        owner_query=owner_name,
        owner=owner_name,
        owner_id=_extract_xiaohongshu_user_id(owner_url) if owner_url else None,
        owner_url=owner_url,
        provider="web-search:xiaohongshu-candidates",
        videos=videos,
        notes=notes,
    )


def _find_bilibili_user(owner_name: str) -> dict[str, Any]:
    payload = _get_json(
        "https://api.bilibili.com/x/web-interface/search/type",
        params={
            "search_type": "bili_user",
            "keyword": owner_name,
            "page": 1,
        },
        headers={**BILIBILI_HEADERS, "Referer": "https://search.bilibili.com/"},
    )
    candidates = (payload.get("data") or {}).get("result") or []
    if not candidates:
        raise ValueError(f"No Bilibili user found for: {owner_name}")

    normalized = _normalize_name(owner_name)
    exact = [item for item in candidates if _normalize_name(item.get("uname") or "") == normalized]
    ranked = exact or candidates
    return max(ranked, key=lambda item: int(item.get("fans") or 0))


def _fetch_bilibili_space_videos_with_ytdlp(
    *,
    owner: str,
    owner_id: str,
    owner_url: str,
    limit: int,
    cookies_from_browser: str | None,
) -> list[CreatorVideo]:
    options: dict[str, Any] = {
        "extract_flat": True,
        "noplaylist": False,
        "playlist_items": f"1-{limit}",
        "quiet": True,
        "skip_download": True,
    }
    cookies_env = COOKIES_ENV_BY_PLATFORM.get(Platform.bilibili)
    if cookies_env and os.getenv(cookies_env):
        options["cookiefile"] = os.environ[cookies_env]
    if cookies_from_browser:
        options["cookiesfrombrowser"] = (cookies_from_browser.lower(), None, None, None)

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(owner_url, download=False)

    videos: list[CreatorVideo] = []
    for entry in info.get("entries") or []:
        url = entry.get("webpage_url") or entry.get("url")
        video_id = entry.get("id")
        if url and not url.startswith("http") and video_id:
            url = f"https://www.bilibili.com/video/{video_id}"
        if not url:
            continue
        videos.append(
            CreatorVideo(
                platform=Platform.bilibili,
                owner=owner,
                owner_id=owner_id,
                video_id=video_id,
                title=entry.get("title"),
                url=url,
                duration_seconds=_optional_int(entry.get("duration")),
                metrics=_entry_metrics(entry),
                metadata={"extractor": entry.get("extractor_key")},
            )
        )
    return _enrich_missing_bilibili_titles(videos)


def _fetch_bilibili_space_videos_with_api(
    *,
    owner: str,
    owner_id: str,
    limit: int,
) -> list[CreatorVideo]:
    opener = _bilibili_opener()
    _prime_bilibili_cookies(opener)
    params = _sign_bilibili_wbi_params(
        {
            "mid": owner_id,
            "ps": min(max(limit, 1), 50),
            "tid": 0,
            "pn": 1,
            "order": "pubdate",
        },
        opener=opener,
    )
    payload = _get_json(
        "https://api.bilibili.com/x/space/wbi/arc/search",
        params=params,
        headers={**BILIBILI_HEADERS, "Referer": f"https://space.bilibili.com/{owner_id}/video"},
        opener=opener,
    )
    items = (((payload.get("data") or {}).get("list") or {}).get("vlist")) or []
    return [_bilibili_arc_item_to_video(item, owner=owner, owner_id=owner_id) for item in items]


def _bilibili_arc_item_to_video(
    item: dict[str, Any],
    *,
    owner: str,
    owner_id: str,
) -> CreatorVideo:
    bvid = item.get("bvid")
    return CreatorVideo(
        platform=Platform.bilibili,
        owner=owner,
        owner_id=owner_id,
        video_id=bvid or str(item.get("aid") or ""),
        title=item.get("title"),
        url=f"https://www.bilibili.com/video/{bvid}" if bvid else str(item.get("pic") or ""),
        published_at=_timestamp_to_datetime(item.get("created")),
        duration_seconds=_duration_to_seconds(item.get("length")),
        metrics={
            "play": _optional_int(item.get("play")),
            "comment": _optional_int(item.get("comment")),
        },
        metadata={
            "aid": _optional_int(item.get("aid")),
            "description": item.get("description"),
            "pic": item.get("pic"),
        },
    )


def _enrich_missing_bilibili_titles(videos: list[CreatorVideo]) -> list[CreatorVideo]:
    enriched: list[CreatorVideo] = []
    for video in videos:
        if video.title or not video.video_id:
            enriched.append(video)
            continue
        try:
            detail = _get_json(
                "https://api.bilibili.com/x/web-interface/view",
                params={"bvid": video.video_id},
                headers=BILIBILI_HEADERS,
            )
            data = detail.get("data") or {}
            enriched.append(
                video.model_copy(
                    update={
                        "title": data.get("title"),
                        "published_at": _timestamp_to_datetime(data.get("pubdate")),
                        "duration_seconds": _optional_int(data.get("duration")),
                        "metrics": {
                            **video.metrics,
                            "view": _optional_int((data.get("stat") or {}).get("view")),
                            "like": _optional_int((data.get("stat") or {}).get("like")),
                            "reply": _optional_int((data.get("stat") or {}).get("reply")),
                        },
                    }
                )
            )
        except Exception:
            enriched.append(video)
    return enriched


def _get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    opener: urllib.request.OpenerDirector | None = None,
    allowed_codes: tuple[int | None, ...] = (0, None),
) -> dict[str, Any]:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers=headers or {"User-Agent": DEFAULT_USER_AGENT})
    open_url = opener.open if opener else urllib.request.urlopen
    with open_url(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("code") not in allowed_codes:
        raise RuntimeError(f"API returned {payload.get('code')}: {payload.get('message')}")
    return payload


def _bilibili_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))


def _prime_bilibili_cookies(opener: urllib.request.OpenerDirector) -> None:
    request = urllib.request.Request("https://www.bilibili.com/", headers=BILIBILI_HEADERS)
    try:
        with opener.open(request, timeout=30) as response:
            response.read(1)
    except urllib.error.HTTPError:
        pass


def _sign_bilibili_wbi_params(
    params: dict[str, Any],
    *,
    opener: urllib.request.OpenerDirector,
) -> dict[str, Any]:
    nav = _get_json(
        "https://api.bilibili.com/x/web-interface/nav",
        headers=BILIBILI_HEADERS,
        opener=opener,
        allowed_codes=(0, -101, None),
    )
    wbi_img = (nav.get("data") or {}).get("wbi_img") or {}
    img_key = _wbi_key_from_url(wbi_img["img_url"])
    sub_key = _wbi_key_from_url(wbi_img["sub_url"])
    mixin_key = _wbi_mixin_key(img_key + sub_key)
    signed = {**params, "wts": int(time.time())}
    signed = {
        key: "".join(char for char in str(value) if char not in "!'()*")
        for key, value in sorted(signed.items())
    }
    query = urllib.parse.urlencode(signed)
    signed["w_rid"] = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
    return signed


def _wbi_key_from_url(url: str) -> str:
    return url.rsplit("/", 1)[1].split(".", 1)[0]


def _wbi_mixin_key(raw: str) -> str:
    return "".join(raw[index] for index in WBI_MIXIN_KEY_TABLE)[:32]


def _search_web_links(query: str, *, limit: int) -> list[str]:
    params = urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(
        f"https://duckduckgo.com/html/?{params}",
        headers={"User-Agent": DEFAULT_USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            content = response.read().decode("utf-8", errors="replace")
    except Exception:
        return []
    return _parse_duckduckgo_links(content)[:limit]


def _parse_duckduckgo_links(content: str) -> list[str]:
    links: list[str] = []
    for match in re.finditer(r'href="(?P<href>[^"]+)"', content):
        href = html.unescape(match.group("href"))
        parsed = urllib.parse.urlparse(href)
        if parsed.path == "/l/":
            query = urllib.parse.parse_qs(parsed.query)
            href = query.get("uddg", [href])[0]
        if "xiaohongshu.com" not in href:
            continue
        clean = _clean_result_url(href)
        if clean not in links:
            links.append(clean)
    return links


def _clean_result_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _first_matching_link(links: list[str], marker: str) -> str | None:
    return next((link for link in links if marker in link), None)


def _extract_xiaohongshu_user_id(url: str | None) -> str | None:
    if not url:
        return None
    match = re.search(r"/user/profile/([^/?#]+)", url)
    return match.group(1) if match else None


def _extract_xiaohongshu_note_id(url: str) -> str | None:
    match = re.search(r"/explore/([^/?#]+)", url)
    return match.group(1) if match else None


def _entry_metrics(entry: dict[str, Any]) -> dict[str, int | float | str | None]:
    return {
        "view": _optional_int(entry.get("view_count")),
        "like": _optional_int(entry.get("like_count")),
        "comment": _optional_int(entry.get("comment_count")),
    }


def _timestamp_to_datetime(value: Any) -> datetime | None:
    timestamp = _optional_int(value)
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=UTC)


def _duration_to_seconds(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value)
    parts = text.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return int(text)
    except ValueError:
        return None


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()
