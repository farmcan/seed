import json

from seed.agent_assets import (
    agent_asset_review_output_path,
    build_agent_asset_review,
    update_agent_asset_review,
    write_agent_asset_review,
)


def test_agent_asset_review_output_path(tmp_path):
    assert agent_asset_review_output_path(library_root=tmp_path, owner="Demo UP") == (
        tmp_path / "checks" / "demo-up.agent-assets.review.json"
    )


def test_build_and_update_agent_asset_review(tmp_path):
    skill = tmp_path / "skills" / "demo" / "SKILL.md"
    check = tmp_path / "checks" / "demo.pre-check.md"
    skill.parent.mkdir(parents=True)
    check.parent.mkdir(parents=True)
    skill.write_text("skill", encoding="utf-8")
    check.write_text("check", encoding="utf-8")
    review_path = tmp_path / "checks" / "demo.agent-assets.review.json"

    review = build_agent_asset_review(
        owner="demo",
        asset_paths={"skill": skill, "pre_check": check},
    )
    write_agent_asset_review(review_path, review)
    updated = update_agent_asset_review(
        review_path=review_path,
        status="reviewed",
        asset_paths=[skill],
        reviewer="levi",
        notes=["looks usable"],
    )

    assert updated["status"] == "mixed"
    assert updated["assets"][0]["status"] == "reviewed"
    assert updated["assets"][0]["reviewer"] == "levi"
    assert updated["assets"][1]["status"] == "draft"

    write_agent_asset_review(review_path, updated)
    assert json.loads(review_path.read_text(encoding="utf-8"))["status"] == "mixed"
