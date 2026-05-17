# Earnings Parser

Use this skill when turning SEC filings or earnings artifacts into a factual earnings digest.

## Rules

- Treat SEC EDGAR filings and XBRL facts as primary evidence.
- Keep reported facts separate from analyst interpretation and market reaction.
- Do not make investment recommendations.
- Preserve CIK, accession number, form type, filing date, report date, metric unit, and period.
- When a metric is missing, stale, or uses a company-specific taxonomy, record the source gap.
- Compare periods only when the period basis is clear.

## Output Priorities

- Latest filing references.
- Financial snapshot of revenue, profit, EPS, cash flow, assets, liabilities, and equity when available.
- Directional changes and drivers only when the filing facts support them.
- Industry implications as mechanisms, not predictions.
- Open questions for transcript, filing, call, guidance, or segment details that are not in the artifact.
