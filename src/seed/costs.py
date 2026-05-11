from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify


QWEN_VL_PRICING_SOURCE = "https://www.alibabacloud.com/help/zh/model-studio/model-pricing"
DEFAULT_QWEN_VL_PRICE_REGION = "china-mainland"
DEFAULT_QWEN_VL_CURRENCY = "USD"

QWEN_VL_PRICE_TABLE: dict[str, dict[str, tuple[float, float]]] = {
    "international": {
        "qwen-vl-max": (0.8, 3.2),
        "qwen-vl-max-latest": (0.8, 3.2),
        "qwen-vl-plus": (0.21, 0.63),
        "qwen-vl-plus-latest": (0.21, 0.63),
    },
    "china-mainland": {
        "qwen-vl-max": (0.23, 0.574),
        "qwen-vl-max-latest": (0.23, 0.574),
        "qwen-vl-plus": (0.21, 0.63),
        "qwen-vl-plus-latest": (0.21, 0.63),
    },
}


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_counts(
        cls,
        *,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> TokenUsage:
        resolved_input = int(input_tokens or 0)
        resolved_output = int(output_tokens or 0)
        resolved_total = int(total_tokens or resolved_input + resolved_output)
        return cls(
            input_tokens=resolved_input,
            output_tokens=resolved_output,
            total_tokens=resolved_total,
        )


@dataclass(frozen=True)
class TokenRate:
    currency: str
    input_per_million: float
    output_per_million: float
    region: str
    source_url: str


@dataclass(frozen=True)
class CostEstimate:
    amount: float
    currency: str


def video_cost_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "costs" / f"{slugify(title)}.cost.json"


def cost_ledger_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "costs" / f"{slugify(title)}.ledger.json"


def qwen_vl_token_rate(model: str, *, region: str | None = None) -> TokenRate:
    resolved_region = region or os.getenv("SEED_QWEN_VL_PRICE_REGION", DEFAULT_QWEN_VL_PRICE_REGION)
    currency = os.getenv("SEED_QWEN_VL_PRICE_CURRENCY", DEFAULT_QWEN_VL_CURRENCY)
    input_override = os.getenv("SEED_QWEN_VL_INPUT_PRICE_PER_M")
    output_override = os.getenv("SEED_QWEN_VL_OUTPUT_PRICE_PER_M")
    if input_override is not None and output_override is not None:
        return TokenRate(
            currency=currency,
            input_per_million=float(input_override),
            output_per_million=float(output_override),
            region=resolved_region,
            source_url=QWEN_VL_PRICING_SOURCE,
        )

    table = QWEN_VL_PRICE_TABLE.get(resolved_region, QWEN_VL_PRICE_TABLE[DEFAULT_QWEN_VL_PRICE_REGION])
    input_per_million, output_per_million = table.get(
        model,
        table.get(model.removesuffix("-latest"), table["qwen-vl-max"]),
    )
    return TokenRate(
        currency=currency,
        input_per_million=input_per_million,
        output_per_million=output_per_million,
        region=resolved_region,
        source_url=QWEN_VL_PRICING_SOURCE,
    )


def estimate_token_cost(usage: TokenUsage, rate: TokenRate) -> CostEstimate:
    amount = (
        usage.input_tokens / 1_000_000 * rate.input_per_million
        + usage.output_tokens / 1_000_000 * rate.output_per_million
    )
    return CostEstimate(amount=round(amount, 8), currency=rate.currency)


def build_qwen_vl_cost_item(
    *,
    title: str,
    model: str,
    usage: TokenUsage,
    artifact_path: Path,
    frame_count: int,
    region: str | None = None,
) -> dict[str, Any]:
    rate = qwen_vl_token_rate(model, region=region)
    estimate = estimate_token_cost(usage, rate)
    return {
        "kind": "qwen_vl",
        "provider": "dashscope",
        "model": model,
        "operation": "analyze-frames",
        "title": title,
        "artifact_path": str(artifact_path),
        "frame_count": frame_count,
        "usage": asdict(usage),
        "rate": asdict(rate),
        "estimated_cost": asdict(estimate),
    }


def reserved_codex_cost_item() -> dict[str, Any]:
    return reserved_cost_item(
        kind="codex",
        provider="codex",
        operation="summarize-or-analyze",
    )


def reserved_cost_item(*, kind: str, provider: str, operation: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "provider": provider,
        "status": "reserved",
        "operation": operation,
        "usage": None,
        "rate": None,
        "estimated_cost": None,
    }


def write_video_cost_report(
    path: Path,
    *,
    title: str,
    items: list[dict[str, Any]],
) -> Path:
    billable_items = [
        item
        for item in items
        if item.get("estimated_cost") and item["estimated_cost"].get("amount") is not None
    ]
    currencies = sorted({item["estimated_cost"]["currency"] for item in billable_items})
    totals = {
        currency: round(
            sum(
                float(item["estimated_cost"]["amount"])
                for item in billable_items
                if item["estimated_cost"]["currency"] == currency
            ),
            8,
        )
        for currency in currencies
    }
    report = {
        "version": 1,
        "title": title,
        "created_at": datetime.now(UTC).isoformat(),
        "pricing_note": "Estimated from recorded token usage and configured per-million-token rates.",
        "items": items,
        "totals": totals,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_cost_ledger(
    *,
    title: str,
    cost_report_paths: list[Path],
    scope: str = "video",
    reserved_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    reports = [load_cost_report(path) for path in cost_report_paths if path.exists()]
    items: list[dict[str, Any]] = []
    for report in reports:
        report_path = report.get("_path")
        for item in report.get("items", []):
            items.append({**item, "source_report_path": report_path})
    items.extend(reserved_items or [])
    return {
        "version": 1,
        "kind": "cost_ledger",
        "scope": scope,
        "title": title,
        "created_at": datetime.now(UTC).isoformat(),
        "pricing_note": (
            "Estimated from recorded usage and configured rates. Provider invoices remain the "
            "source of truth."
        ),
        "source_reports": [str(path) for path in cost_report_paths if path.exists()],
        "items": items,
        "totals": calculate_totals(items),
    }


def write_cost_ledger(path: Path, ledger: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_cost_report(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(report, dict):
        report["_path"] = str(path)
        return report
    return {"_path": str(path), "items": [], "totals": {}}


def calculate_totals(items: list[dict[str, Any]]) -> dict[str, float]:
    currencies = sorted(
        {
            item["estimated_cost"]["currency"]
            for item in items
            if item.get("estimated_cost") and item["estimated_cost"].get("currency")
        }
    )
    return {
        currency: round(
            sum(
                float(item["estimated_cost"]["amount"])
                for item in items
                if item.get("estimated_cost")
                and item["estimated_cost"].get("currency") == currency
                and item["estimated_cost"].get("amount") is not None
            ),
            8,
        )
        for currency in currencies
    }


def ledger_total(ledger: dict[str, Any], *, currency: str = DEFAULT_QWEN_VL_CURRENCY) -> float:
    return float((ledger.get("totals") or {}).get(currency, 0.0))
