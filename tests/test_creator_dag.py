import json

from seed.graphs.creator_dag import (
    build_creator_dag_graph,
    creator_dag_html_output_path,
    creator_dag_output_path,
    write_creator_dag_graph,
)


def test_creator_dag_output_paths(tmp_path):
    graph_path = creator_dag_output_path(library_root=tmp_path, owner="某 UP")

    assert graph_path == tmp_path / "graphs" / "某-up.creator-dag.json"
    assert creator_dag_html_output_path(graph_path=graph_path) == (
        tmp_path / "graphs" / "某-up.creator-dag.html"
    )


def test_build_creator_dag_graph(tmp_path):
    semantics = tmp_path / "demo.video-semantics.md"
    semantics.write_text(
        "---\ntitle: Demo Video\n---\n\n## Verbal Language\n\n- Main claims:\n  - Claim A.",
        encoding="utf-8",
    )
    profile = tmp_path / "demo.creator-profile.md"
    profile.write_text("# Profile", encoding="utf-8")
    skill = tmp_path / "SKILL.md"
    skill.write_text("# Skill", encoding="utf-8")

    graph = build_creator_dag_graph(
        owner="demo",
        semantics_paths=[semantics],
        creator_profile_path=profile,
        skill_paths=[skill],
    )

    assert graph["kind"] == "creator-dag"
    assert any(node["id"] == "video-001" and node["title"] == "Demo Video" for node in graph["nodes"])
    assert ["video-001", "creator"] in graph["edges"]
    assert ["profile", "agent-assets"] in graph["edges"]


def test_write_creator_dag_graph(tmp_path):
    path = write_creator_dag_graph(tmp_path / "creator.json", {"nodes": [], "edges": []})

    assert json.loads(path.read_text(encoding="utf-8")) == {"nodes": [], "edges": []}
