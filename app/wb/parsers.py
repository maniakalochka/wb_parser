import json
from typing import Any


def parse_search_products(payload: dict) -> list[dict]:
    products = payload.get("products", [])
    return products if isinstance(products, list) else []


def parse_detail_product(payload: dict) -> dict | None:
    data = payload.get("data")
    if isinstance(data, dict):
        payload = data

    products = payload.get("products", [])
    if isinstance(products, list) and products:
        p0 = products[0]
        return p0 if isinstance(p0, dict) else None
    return None


def extract_sizes_str(detail_product: dict) -> str:
    out: list[str] = []
    for s in detail_product.get("sizes", []) or []:
        if not isinstance(s, dict):
            continue
        val = s.get("origName") or s.get("name")
        if isinstance(val, str) and val.strip():
            out.append(val.strip())
    return ", ".join(dict.fromkeys(out))


def extract_stock_total(detail_product: dict) -> int:
    total = 0
    for s in detail_product.get("sizes", []) or []:
        if not isinstance(s, dict):
            continue
        for st in s.get("stocks", []) or []:
            if not isinstance(st, dict):
                continue
            qty = st.get("qty")
            if isinstance(qty, int):
                total += qty
    return total


def extract_price_rub(detail_product: dict) -> int | None:
    prices: list[int] = []
    for s in detail_product.get("sizes", []) or []:
        if not isinstance(s, dict):
            continue
        pr = (s.get("price") or {}).get("product")
        if isinstance(pr, int):
            prices.append(pr)
    return (min(prices) // 100) if prices else None


def extract_seller(product: dict) -> tuple[str | None, str | None]:
    name = product.get("supplier")
    seller_id = product.get("supplierId")
    seller_url = None
    if isinstance(seller_id, int):
        seller_url = f"https://www.wildberries.ru/seller/{seller_id}"
    return (name if isinstance(name, str) else None), seller_url


def extract_pics(product: dict) -> int:
    pics = product.get("pics")
    return int(pics) if isinstance(pics, int) and pics > 0 else 0


def extract_description(card_payload: dict) -> str | None:
    v = card_payload.get("description")
    return v if isinstance(v, str) else None


def extract_options_struct(card_payload: dict) -> Any:
    return card_payload.get("options")


def options_to_json(options: Any) -> str:
    return json.dumps(options, ensure_ascii=False)


def extract_country_from_options(options: list[dict] | None) -> str | None:
    if not options:
        return None

    keys = {
        "страна",
        "страна производства",
        "страна происхождения",
        "страна изготовитель",
        "страна-изготовитель",
        "производство",
    }

    for opt in options:
        name = (opt.get("name") or "").strip().casefold()
        if name in keys:
            value = (opt.get("value") or "").strip()
            return value or None

    return None


def extract_rating(p: dict) -> float | None:
    for key in ("reviewRating", "rating", "productRating"):
        v = p.get(key)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    return None


def extract_reviews_count(p: dict) -> int | None:
    for key in ("feedbacks", "reviewCount", "nmFeedbacks"):
        v = p.get(key)
        if isinstance(v, int) and v >= 0:
            return v
    return None


def extract_sizes_str_from_card(card_p: dict) -> str | None:
    sizes_table = card_p.get("sizes_table")
    if not isinstance(sizes_table, dict):
        return None

    values = sizes_table.get("values")
    if not isinstance(values, list):
        return None

    sizes = []
    for v in values:
        if isinstance(v, dict):
            tech = v.get("tech_size")
            if isinstance(tech, str) and tech.strip():
                sizes.append(tech.strip())

    if not sizes:
        return None

    return ", ".join(dict.fromkeys(sizes))


def extract_price_rub_from_detail(p: dict) -> int | None:
    sizes = p.get("sizes")
    if isinstance(sizes, list):
        for s in sizes:
            if not isinstance(s, dict):
                continue
            price = s.get("price")
            if isinstance(price, dict):
                product = price.get("product")
                if isinstance(product, int) and product > 0:
                    return product // 100

    for key in ("salePriceU", "priceU", "salePrice", "price"):
        v = p.get(key)
        if isinstance(v, int) and v > 0:
            return v // 100

    return None


def extract_stock_total_from_detail(p: dict) -> int:
    tq = p.get("totalQuantity")
    if isinstance(tq, int) and tq >= 0:
        return tq

    total = 0
    sizes = p.get("sizes")
    if not isinstance(sizes, list):
        return 0

    for s in sizes:
        if not isinstance(s, dict):
            continue
        stocks = s.get("stocks")
        if not isinstance(stocks, list):
            continue
        for st in stocks:
            if not isinstance(st, dict):
                continue
            qty = st.get("qty")
            if isinstance(qty, int) and qty > 0:
                total += qty

    return total


def extract_price_rub_from_search(p: dict) -> int | None:
    for key in ("salePriceU", "priceU", "salePrice", "price"):
        v = p.get(key)
        if isinstance(v, int) and v > 0:
            return v // 100
        if isinstance(v, (float, str)):
            try:
                vv = int(float(v))
                if vv > 0:
                    return vv
            except Exception:
                pass

    sizes = p.get("sizes")
    if isinstance(sizes, list):
        candidates: list[int] = []
        for s in sizes:
            if not isinstance(s, dict):
                continue
            price = s.get("price")
            if not isinstance(price, dict):
                continue
            for k in ("product", "sale", "basic"):
                v = price.get(k)
                if isinstance(v, int) and v > 0:
                    candidates.append(v)
        if candidates:
            return min(candidates) // 100

    return None


def extract_stock_total_from_search(p: dict) -> int:
    tq = p.get("totalQuantity")
    if isinstance(tq, int) and tq >= 0:
        return tq

    total = 0
    sizes = p.get("sizes")
    if not isinstance(sizes, list):
        return 0

    for s in sizes:
        if not isinstance(s, dict):
            continue
        stocks = s.get("stocks")
        if not isinstance(stocks, list):
            continue
        for st in stocks:
            if not isinstance(st, dict):
                continue
            qty = st.get("qty")
            if isinstance(qty, int) and qty > 0:
                total += qty

    return total
