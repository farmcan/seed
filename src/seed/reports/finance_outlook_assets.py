from __future__ import annotations

from html import escape
from typing import Any


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _render_link(*, title: Any, url: Any) -> str:
    label = str(title or url or "").strip()
    href = str(url or "").strip()
    if not href:
        return escape(label)
    safe_url = escape(href, quote=True)
    return f"<a href=\"{safe_url}\" target=\"_blank\" rel=\"noopener noreferrer\">{escape(label)}</a>"


def _normalize_company_asset(value: Any, *, default_kind: str) -> dict[str, Any] | None:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        return {"kind": default_kind, "title": default_kind, "url": text}
    if not isinstance(value, dict):
        return None
    url = str(value.get("url") or value.get("image_url") or value.get("src") or "").strip()
    title = str(value.get("title") or value.get("name") or value.get("caption") or default_kind).strip()
    source_url = str(value.get("source_url") or value.get("source") or "").strip()
    source_title = str(value.get("source_title") or value.get("source_name") or "").strip()
    if not any([url, title, source_url, source_title]):
        return None
    return {
        "kind": str(value.get("kind") or default_kind).strip() or default_kind,
        "title": title,
        "url": url,
        "alt": str(value.get("alt") or title).strip(),
        "caption": str(value.get("caption") or value.get("description") or "").strip(),
        "source_url": source_url,
        "source_title": source_title,
        "license_note": str(value.get("license_note") or value.get("usage_note") or "").strip(),
    }


def company_assets_from_digest(
    resolved_digest: dict[str, Any],
    source_digest: dict[str, Any],
    market_context: dict[str, Any],
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for container in (source_digest, resolved_digest, market_context):
        for key in ("company_assets", "visual_assets", "brand_assets"):
            raw = _as_dict(container.get(key))
            for field, value in raw.items():
                if field not in merged or not merged[field]:
                    merged[field] = value
    if not merged:
        return {}

    logo = _normalize_company_asset(
        merged.get("logo") or merged.get("logo_image"),
        default_kind="logo",
    )
    product_items: list[dict[str, Any]] = []
    for key in ("products", "product_images", "key_products"):
        for item in _as_list(merged.get(key)):
            normalized = _normalize_company_asset(item, default_kind="product")
            if normalized:
                product_items.append(normalized)
    for item in _as_list(merged.get("images")):
        normalized = _normalize_company_asset(item, default_kind="image")
        if normalized:
            product_items.append(normalized)

    product_names = [
        str(item).strip()
        for item in _as_list(merged.get("product_names") or merged.get("products_text"))
        if str(item).strip()
    ]
    source_refs = [
        item
        for item in _as_list(merged.get("source_refs"))
        if isinstance(item, dict)
    ]
    for asset in ([logo] if logo else []) + product_items:
        if asset.get("source_url") or asset.get("source_title"):
            source_refs.append(
                {
                    "title": asset.get("source_title") or asset.get("title"),
                    "url": asset.get("source_url"),
                    "note": asset.get("license_note") or "company visual asset source",
                }
            )
    deduped_sources: list[dict[str, Any]] = []
    seen_sources: set[tuple[str, str]] = set()
    for source in source_refs:
        title = str(source.get("title") or "").strip()
        url = str(source.get("url") or "").strip()
        key = (title, url)
        if key in seen_sources:
            continue
        seen_sources.add(key)
        deduped_sources.append(source)

    return {
        "status": "available" if (logo or product_items or product_names) else "missing",
        "logo": logo,
        "products": product_items[:6],
        "product_names": product_names[:12],
        "source_refs": deduped_sources[:12],
        "source_note": str(merged.get("source_note") or "").strip(),
        "usage_note": str(
            merged.get("usage_note")
            or "Logo/product images are report context only; keep source links and verify usage rights before customer delivery."
        ).strip(),
    }



def render_company_assets_html(
    company_assets: dict[str, Any],
    *,
    peer_context: dict[str, Any],
) -> str:
    if not company_assets or company_assets.get("status") == "missing":
        return ""
    target_name = str(
        peer_context.get("target_asset")
        or peer_context.get("target_ticker")
        or "当前公司"
    ).strip()
    logo = _as_dict(company_assets.get("logo"))
    product_assets = [
        item for item in _as_list(company_assets.get("products")) if isinstance(item, dict)
    ]
    product_names = [
        str(item).strip()
        for item in _as_list(company_assets.get("product_names"))
        if str(item).strip()
    ]
    product_name_tags = "".join(
        f"<span class='tag'>{escape(name)}</span>" for name in product_names
    )
    logo_html = ""
    if logo:
        logo_url = str(logo.get("url") or "").strip()
        logo_source = _render_link(
            title=logo.get("source_title") or "logo source",
            url=logo.get("source_url"),
        )
        logo_title = str(logo.get("title") or f"{target_name} logo").strip()
        if logo_url:
            logo_html = (
                "<div class='brand-logo-card'>"
                f"<img src='{escape(logo_url, quote=True)}' alt='{escape(str(logo.get('alt') or logo_title), quote=True)}' loading='lazy' />"
                f"<strong>{escape(logo_title)}</strong>"
                f"<span class='small muted'>来源：{logo_source}</span>"
                "</div>"
            )
        else:
            logo_html = (
                "<div class='brand-logo-card logo-fallback'>"
                f"<strong>{escape(logo_title)}</strong>"
                f"<span class='small muted'>来源：{logo_source}</span>"
                "</div>"
            )

    product_html = ""
    if product_assets:
        product_cards = []
        for asset in product_assets:
            image_url = str(asset.get("url") or "").strip()
            title = str(asset.get("title") or asset.get("caption") or "product").strip()
            caption = str(asset.get("caption") or "").strip()
            source = _render_link(
                title=asset.get("source_title") or "source",
                url=asset.get("source_url"),
            )
            image = (
                f"<img src='{escape(image_url, quote=True)}' alt='{escape(str(asset.get('alt') or title), quote=True)}' loading='lazy' />"
                if image_url
                else "<div class='product-image-placeholder'>image pending</div>"
            )
            product_cards.append(
                "<div class='product-card'>"
                f"{image}"
                f"<strong>{escape(title)}</strong>"
                f"<span>{escape(caption) if caption else '核心产品/业务视觉资产'}</span>"
                f"<small>来源：{source}</small>"
                "</div>"
            )
        product_html = "".join(product_cards)

    source_rows = []
    for source in _as_list(company_assets.get("source_refs")):
        if not isinstance(source, dict):
            continue
        link = _render_link(title=source.get("title") or source.get("url") or "source", url=source.get("url"))
        note = str(source.get("note") or "").strip()
        source_rows.append(f"<li>{link}{' ｜ ' + escape(note) if note else ''}</li>")
    usage_note = str(company_assets.get("usage_note") or "").strip()
    source_note = str(company_assets.get("source_note") or "").strip()
    return f"""
    <section class="section brand-context-section">
      <h2>公司与产品识别</h2>
      <div class="brand-context">
        {logo_html}
        <div class="brand-product-grid">
          {product_html or '<div class="product-card"><div class="product-image-placeholder">product assets pending</div><strong>产品视觉待补充</strong><span>可在 company_assets.product_images 中补充官方产品图或授权素材。</span></div>'}
        </div>
        <div class="brand-notes">
          <span class="muted">核心产品/业务</span>
          <div>{product_name_tags or '<span class="small muted">待补充</span>'}</div>
          <ul>{''.join(source_rows) or '<li>视觉来源待补充</li>'}</ul>
          <div class="small muted">{escape(source_note or usage_note or '视觉资产仅用于识别公司和业务，客户级交付前需复核来源和使用权。')}</div>
        </div>
      </div>
    </section>
    """

