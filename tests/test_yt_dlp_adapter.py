from seed.models import Platform
from seed.sources.yt_dlp_adapter import _build_download_options


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
