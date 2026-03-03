from app.models import CatalogRow

def is_filtered(row: CatalogRow) -> bool:
    if row.rating is None or row.rating < 4.5:
        return False

    if row.price is not None and row.price > 10_000:
        return False

    country = (row._country or "").strip().lower()
    if country and "рос" not in country:
        return False

    return True