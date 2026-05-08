from pathlib import Path

from seed.asr.dashscope_provider import audio_data_url, mime_type_for_audio
from seed.asr.providers import default_max_upload_mb_for_provider, default_model_for_provider


def test_default_model_for_provider():
    assert default_model_for_provider("dashscope") == "qwen3-asr-flash"
    assert default_model_for_provider("qwen") == "qwen3-asr-flash"
    assert default_model_for_provider("openai") == "gpt-4o-mini-transcribe"


def test_default_max_upload_mb_for_provider():
    assert default_max_upload_mb_for_provider("dashscope") == 9
    assert default_max_upload_mb_for_provider("qwen") == 9
    assert default_max_upload_mb_for_provider("openai") == 24


def test_mime_type_for_audio():
    assert mime_type_for_audio(Path("a.m4a")) == "audio/mp4"
    assert mime_type_for_audio(Path("a.mp3")) == "audio/mpeg"
    assert mime_type_for_audio(Path("a.wav")) == "audio/wav"


def test_audio_data_url(tmp_path):
    audio = tmp_path / "demo.m4a"
    audio.write_bytes(b"abc")

    assert audio_data_url(audio) == "data:audio/mp4;base64,YWJj"


def test_dashscope_system_context_uses_official_text_shape():
    from seed.asr.dashscope_provider import build_messages

    messages = build_messages(audio_data="data:audio/mp4;base64,YWJj", prompt="中文术语")

    assert messages[0] == {"role": "system", "content": [{"text": "中文术语"}]}
    assert messages[1]["content"][0]["type"] == "input_audio"
