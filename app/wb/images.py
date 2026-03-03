def build_image_urls(
    *,
    nm_id: int,
    pics: int,
    basket_host: str = "basket-16.wbbasket.ru",
    size: str = "c246x328",
    ext: str = "webp",
) -> list[str]:
    if pics <= 0:
        return []

    vol = nm_id // 100000
    part = nm_id // 1000

    return [
        f"https://{basket_host}/vol{vol}/part{part}/{nm_id}/images/{size}/{i}.{ext}"
        for i in range(1, pics + 1)
    ]
