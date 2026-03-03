import os
from dataclasses import dataclass, field


@dataclass
class Config:
    query: str = "пальто из натуральной шерсти"
    dest: int = -1255987
    curr: str = "rub"
    app_type: int = 1
    lang: str = "ru"
    max_pages: int = 50
    limit: int = 300

    timeout_s: float = 20.0
    concurrency: int = 6
    retries: int = 4

    out_dir: str = "artifacts"
    save_raw_json: bool = False

    basket_host: str = "basket-16.wbbasket.ru"
    basket_hosts: list[str] = field(
        default_factory=lambda: [f"basket-{i:02d}.wbbasket.ru" for i in range(1, 21)]
    )
    image_size: str = "c246x328"

    wb_cookie: str | None = os.getenv("WB_COOKIE")
