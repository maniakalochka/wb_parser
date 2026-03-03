import os
import pandas as pd

from app.models import CatalogRow

COLUMNS = [
    "product_url",
    "article",
    "name",
    "price",
    "description",
    "image_urls",
    "characteristics_json",
    "seller_name",
    "seller_url",
    "sizes",
    "stock_total",
    "rating",
    "reviews_count",
]


def export_rows(path: str, rows: list[CatalogRow], sheet_name: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    df = pd.DataFrame([r.__dict__ for r in rows])
    if "_country" in df.columns:
        df = df.drop(columns=["_country"])

    for c in COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[COLUMNS]

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)