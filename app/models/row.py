from dataclasses import dataclass


@dataclass
class CatalogRow:
    product_url: str
    article: int
    name: str | None
    price: int | None
    description: str | None
    image_urls: str
    characteristics_json: str
    seller_name: str | None
    seller_url: str | None
    sizes: str
    stock_total: int
    rating: float | None
    reviews_count: int | None
    _country: str | None = None