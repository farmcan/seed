import json
from pathlib import Path

from seed.costs import (
    TokenRate,
    TokenUsage,
    build_qwen_vl_cost_item,
    estimate_token_cost,
    qwen_vl_token_rate,
    reserved_codex_cost_item,
    video_cost_output_path,
    write_video_cost_report,
)


def test_video_cost_output_path_uses_title(tmp_path):
    path = video_cost_output_path(library_root=tmp_path, title="法德 欧洲")

    assert path == tmp_path / "costs" / "法德-欧洲.cost.json"


def test_estimate_token_cost():
    estimate = estimate_token_cost(
        TokenUsage(input_tokens=1_000_000, output_tokens=500_000, total_tokens=1_500_000),
        TokenRate(
            currency="USD",
            input_per_million=0.23,
            output_per_million=0.574,
            region="china-mainland",
            source_url="https://example.com",
        ),
    )

    assert estimate.amount == 0.517
    assert estimate.currency == "USD"


def test_qwen_vl_rate_allows_env_override(monkeypatch):
    monkeypatch.setenv("SEED_QWEN_VL_INPUT_PRICE_PER_M", "1.5")
    monkeypatch.setenv("SEED_QWEN_VL_OUTPUT_PRICE_PER_M", "2.5")
    monkeypatch.setenv("SEED_QWEN_VL_PRICE_CURRENCY", "CNY")

    rate = qwen_vl_token_rate("qwen-vl-max")

    assert rate.input_per_million == 1.5
    assert rate.output_per_million == 2.5
    assert rate.currency == "CNY"


def test_write_video_cost_report(tmp_path):
    note_path = Path("library/notes/demo.visual.md")
    item = build_qwen_vl_cost_item(
        title="demo",
        model="qwen-vl-max",
        usage=TokenUsage(input_tokens=1000, output_tokens=2000, total_tokens=3000),
        artifact_path=note_path,
        frame_count=3,
    )

    path = write_video_cost_report(
        tmp_path / "demo.cost.json",
        title="demo",
        items=[item, reserved_codex_cost_item()],
    )

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["title"] == "demo"
    assert data["items"][0]["usage"]["total_tokens"] == 3000
    assert data["items"][1]["status"] == "reserved"
    assert data["totals"]["USD"] > 0
