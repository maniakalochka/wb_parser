from app.models import CatalogRow
from app.wb.images import build_image_urls


def build_product_url(nm_id: int) -> str:
    return f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx"


def merge_to_row(
    *,
    nm_id: int,
    search_p: dict,
    detail_p: dict,
    card_p: dict,
    price: int | None,
    sizes: str,
    stock_total: int,
    rating: float | None,
    reviews: int | None,
    seller_name: str | None,
    seller_url: str | None,
    description: str | None,
    characteristics_json: str,
    country: str | None,
    pics: int,
    basket_host: str,
    image_size: str,
) -> CatalogRow:
    img_urls = build_image_urls(
        nm_id=nm_id,
        pics=pics,
        basket_host=basket_host,
        size=image_size,
    )
    image_urls_str = ", ".join(img_urls)

    name = None
    if isinstance(detail_p.get("name"), str):
        name = detail_p["name"]
    elif isinstance(search_p.get("name"), str):
        name = search_p["name"]
    elif isinstance(card_p.get("imt_name"), str):
        name = card_p["imt_name"]

    return CatalogRow(
        product_url=build_product_url(nm_id),
        article=nm_id,
        name=name,
        price=price,
        description=description,
        image_urls=image_urls_str,
        characteristics_json=characteristics_json,
        seller_name=seller_name,
        seller_url=seller_url,
        sizes=sizes,
        stock_total=stock_total,
        rating=rating,
        reviews_count=reviews,
        _country=country,
    )
