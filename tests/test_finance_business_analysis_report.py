import json

from seed.cli import build_finance_business_analysis_report
from seed.reports.finance_business_analysis import (
    build_finance_business_analysis_html,
    build_finance_business_analysis_markdown,
    finance_business_analysis_html_output_path,
    finance_business_analysis_md_output_path,
)
from seed.reports.finance_outlook import build_finance_outlook_payload


def test_build_finance_business_analysis_markdown_and_html(tmp_path, monkeypatch):
    monkeypatch.setattr("seed.reports.finance_outlook.fetch_yahoo_chart_history", lambda *args, **kwargs: [])
    digest_path = tmp_path / "demo.finance-digest.news-context.json"
    digest = _demo_digest()
    digest_path.write_text(json.dumps(digest, ensure_ascii=False), encoding="utf-8")

    outlook = build_finance_outlook_payload(digest, digest_path=digest_path)
    markdown = build_finance_business_analysis_markdown(
        outlook,
        source=digest,
        source_path=digest_path,
    )
    html = build_finance_business_analysis_html(
        outlook,
        source=digest,
        source_path=digest_path,
    )

    assert "主营业务到底是什么" in markdown
    assert "营收主要来自谁" in markdown
    assert "AI 创作工具竞争现状" in markdown
    assert "Adobe" in markdown
    assert "Canva" in markdown
    assert "目标价 30.0（50.0%）" in markdown
    assert "不提供买入、卖出或持有建议" in markdown
    assert "https://example.test/annual-results" in markdown
    assert "财经业务分析报告" not in html
    assert "Seed 本地产物" in html
    assert "Adobe" in html


def test_finance_business_analysis_paths_and_cli(tmp_path, monkeypatch):
    monkeypatch.setattr("seed.reports.finance_outlook.fetch_yahoo_chart_history", lambda *args, **kwargs: [])
    digest_path = tmp_path / "demo.finance-digest.news-context.json"
    digest_path.write_text(json.dumps(_demo_digest(), ensure_ascii=False), encoding="utf-8")

    root = tmp_path / "library"
    markdown_path = finance_business_analysis_md_output_path(
        library_root=root,
        source_path=digest_path,
    )
    html_path = finance_business_analysis_html_output_path(
        library_root=root,
        source_path=digest_path,
    )

    assert markdown_path.name == "demo.business-analysis.md"
    assert html_path.name == "demo.business-analysis.html"

    build_finance_business_analysis_report(
        source_path=digest_path,
        output=html_path,
        markdown_output=markdown_path,
        root=root,
    )

    assert markdown_path.exists()
    assert html_path.exists()
    assert "主营业务到底是什么" in markdown_path.read_text(encoding="utf-8")
    assert "打开 Finance Outlook HTML" in html_path.read_text(encoding="utf-8")


def _demo_digest():
    return {
        "kind": "finance_digest_with_news_context",
        "owner": "demo",
        "platform": "bilibili",
        "peer_context": {
            "target_asset": "Demo Co",
            "target_ticker": "DEMO",
            "industry": "AI 创作软件",
            "peers": [{"name": "Canva", "relation": "设计工具替代品"}],
        },
        "first_principles": {
            "business_model": "Demo Co 通过订阅、AI 点数和广告服务变现。",
            "revenue_logic": "收入增长取决于付费用户、AI 用量和企业客户渗透。",
            "competitors": ["Adobe", "Canva", "CapCut"],
            "competitive_pressure": "基础模型和设计平台会压缩单点功能溢价。",
            "customer_dependency": "未披露单一大客户集中度。",
        },
        "business_analysis": {
            "business_model": "Demo Co 是 AI 影像和创作工具公司，核心收入来自订阅和增值点数。",
            "revenue_segments": [
                {
                    "segment": "影像与设计产品",
                    "revenue": "12.0 亿",
                    "yoy": "+20%",
                    "share": "70%",
                    "explanation": "订阅与 AI credits 是主要增长来源。",
                }
            ],
            "customer_sources": [
                "个人创作者和移动端用户贡献订阅。",
                "商家和企业用户贡献设计与营销工具收入。",
            ],
            "market_size_layers": [
                {
                    "layer": "直接市场",
                    "relevance": "移动影像和设计订阅。",
                    "signal": "公开行业报告显示创作软件仍在增长。",
                }
            ],
            "competition_layers": [
                {
                    "layer": "设计平台",
                    "representatives": "Adobe, Canva",
                    "pressure": "提高套件化和团队协作门槛。",
                }
            ],
            "competitive_watch": [
                {
                    "competitor": "Adobe",
                    "move": "Firefly 和 Express 继续加入生成式编辑能力。",
                    "affected_business_line": "图片编辑、设计和企业创作工作流。",
                    "pressure_level": "high",
                    "uncertainty": "商业安全模型可能吸引企业用户。",
                    "source_refs": [{"title": "Adobe Firefly", "url": "https://example.test/adobe"}],
                },
                {
                    "competitor": "Canva",
                    "move": "Canva AI 和 Visual Suite 扩展到更多团队场景。",
                    "affected_business_line": "设计模板和营销素材。",
                    "pressure_level": "medium",
                    "uncertainty": "团队协作场景的迁移速度待验证。",
                    "source_refs": [{"title": "Canva AI", "url": "https://example.test/canva"}],
                },
            ],
            "metrics_to_watch": ["订阅用户", "AI credits 毛利率", "海外 ARPU"],
            "sources": [
                {
                    "title": "Demo annual results",
                    "url": "https://example.test/annual-results",
                    "note": "分部收入与业务说明。",
                }
            ],
        },
        "market_context": {
            "ticker": "DEMO",
            "current_price": 20.0,
            "as_of": "2026-05-29",
            "source_refs": [{"title": "Market data", "url": "https://example.test/quote"}],
        },
        "market_scenarios": {
            "anchor_price": 20.0,
            "base_case": {
                "target_price": 30.0,
                "triggers": ["订阅增长兑现"],
                "validation_points": ["H1 付费用户"],
            },
            "upside_case": {
                "target_price": 40.0,
                "triggers": ["海外高 ARPU 加速"],
                "validation_points": ["海外收入占比"],
            },
            "downside_case": {
                "target_price": 15.0,
                "triggers": ["AI 成本吞噬毛利"],
                "validation_points": ["毛利率"],
            },
        },
        "viewpoint_events": [],
        "open_questions": ["下一次财报是否拆分 AI credits 收入？"],
        "source_gaps": ["仍需主源复核市场规模。"],
        "methodology_signals": [],
    }
