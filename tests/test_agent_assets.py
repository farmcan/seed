from seed.agent_assets import (
    build_agent_assets_from_creator_profile,
    precheck_output_path,
    reflection_check_output_path,
    skill_output_path,
    write_agent_assets,
)


def test_agent_asset_paths(tmp_path):
    assert skill_output_path(library_root=tmp_path, owner="某 UP") == (
        tmp_path / "skills" / "某-up" / "SKILL.md"
    )
    assert precheck_output_path(library_root=tmp_path, owner="某 UP") == (
        tmp_path / "checks" / "某-up.pre-check.md"
    )
    assert reflection_check_output_path(library_root=tmp_path, owner="某 UP") == (
        tmp_path / "checks" / "某-up.post-task-reflection.md"
    )


def test_build_agent_assets_from_creator_profile(tmp_path):
    profile = tmp_path / "demo.creator-profile.md"
    profile.write_text(
        """## Metadata

- Owner: Demo Creator

## Creator Summary

Use conflict-led explanations.

## Agent Skills

- Skill name: Conflict Analysis
- Trigger: Need to explain a strategic conflict.
- Procedure: Identify actors, incentives, leverage, and failure modes.
- Inputs: Topic and sources.
- Outputs: Structured analysis.

## Pre-Checks

- Is the source evidence enough?
- Are claims separated from jokes?

## Post-Task Reflection

- Did the method clarify the tradeoff?
""",
        encoding="utf-8",
    )

    assets = build_agent_assets_from_creator_profile(profile_path=profile)

    assert "name: conflict-analysis" in assets["skill"]
    assert "Use conflict-led explanations." in assets["skill"]
    assert "Identify actors, incentives, leverage" in assets["skill"]
    assert "- [ ] Is the source evidence enough?" in assets["pre_check"]
    assert "- [ ] Did the method clarify the tradeoff?" in assets["post_task_reflection"]


def test_write_agent_assets(tmp_path):
    paths = write_agent_assets(
        library_root=tmp_path,
        owner="Demo",
        assets={
            "skill": "skill",
            "pre_check": "pre",
            "post_task_reflection": "post",
        },
    )

    assert paths["skill"].read_text(encoding="utf-8") == "skill"
    assert paths["pre_check"].read_text(encoding="utf-8") == "pre"
    assert paths["post_task_reflection"].read_text(encoding="utf-8") == "post"
