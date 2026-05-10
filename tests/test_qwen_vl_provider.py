from pathlib import Path

from seed.vision.qwen_vl_provider import (
    build_visual_analysis_messages,
    image_data_url,
    mime_type_for_image,
    token_usage_from_response,
)


def test_mime_type_for_image():
    assert mime_type_for_image(Path("a.jpg")) == "image/jpeg"
    assert mime_type_for_image(Path("a.jpeg")) == "image/jpeg"
    assert mime_type_for_image(Path("a.png")) == "image/png"
    assert mime_type_for_image(Path("a.webp")) == "image/webp"


def test_image_data_url(tmp_path):
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"abc")

    assert image_data_url(image) == "data:image/jpeg;base64,YWJj"


def test_build_visual_analysis_messages(tmp_path):
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"abc")

    messages = build_visual_analysis_messages([image], prompt="describe")

    assert messages[0]["role"] == "user"
    assert messages[0]["content"][0] == {"type": "text", "text": "describe"}
    assert messages[0]["content"][1]["type"] == "image_url"


def test_token_usage_from_response_supports_openai_compatible_usage():
    response = type(
        "Response",
        (),
        {"usage": {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150}},
    )()

    usage = token_usage_from_response(response)

    assert usage.input_tokens == 120
    assert usage.output_tokens == 30
    assert usage.total_tokens == 150
