import asyncio
import logging

import typer

from app.config import Config
from app.log import setup_logging
from app.pipeline import run_pipeline

app = typer.Typer(add_completion=False)


@app.command()
def run(
    query: str = typer.Option(Config.query, help="Поисковый запрос."),
    limit: int = typer.Option(300, help="Сколько товаров выгрузить."),
    dest: int = typer.Option(Config.dest, help="Регион dest."),
    max_pages: int = typer.Option(50, help="Safety-limit по страницам."),
    concurrency: int = typer.Option(6, help="Параллелизм запросов."),
    out_dir: str = typer.Option("artifacts", help="Папка для XLSX."),
    save_raw_json: bool = typer.Option(False, help="Сохранять сырые ответы JSON."),
    basket_host: str = typer.Option(
        "basket-16.wbbasket.ru", help="CDN host для картинок и card.json."
    ),
    image_size: str = typer.Option(
        "c246x328", help="Размер картинок (c246x328, c516x688 и т.п.)."
    ),
):
    setup_logging(logging.INFO)

    cfg = Config(
        query=query,
        limit=limit,
        dest=dest,
        max_pages=max_pages,
        concurrency=concurrency,
        out_dir=out_dir,
        save_raw_json=save_raw_json,
        basket_host=basket_host,
        image_size=image_size,
    )

    full_path, filtered_path = asyncio.run(run_pipeline(cfg))
    typer.echo(f"OK:\n- {full_path}\n- {filtered_path}")
