from seed.models import Platform
from seed.sources.yt_dlp_adapter import _build_download_options, cookies_help_for_platform


def test_yt_dlp_outtmpl_is_relative_to_raw_dir(tmp_path):
    options = _build_download_options(
        platform=Platform.xiaohongshu,
        raw_dir=tmp_path / "raw",
        max_height=720,
        max_filesize_mb=80,
        cookies_from_browser=None,
    )

    assert options["paths"]["home"] == str(tmp_path / "raw")
    assert not options["outtmpl"].startswith(str(tmp_path))


def test_cookies_help_for_platform_mentions_env_and_browser():
    help_text = cookies_help_for_platform(Platform.bilibili)

    assert help_text is not None
    assert "BILIBILI_COOKIES_FILE" in help_text
    assert "--cookies-from-browser" in help_text
