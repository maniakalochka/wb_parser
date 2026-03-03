import logging
import os

import httpx
import orjson
from tqdm.asyncio import tqdm_asyncio

from app.config import Config
from app.export import export_rows
from app.http import HttpClient
from app.pipeline.filters import is_filtered
from app.pipeline.merge import merge_to_row
from app.wb.endpoints import WBEndpoints
from app.wb.parsers import (extract_country_from_options, extract_description,
                            extract_options_struct, extract_pics,
                            extract_price_rub_from_detail,
                            extract_price_rub_from_search, extract_rating,
                            extract_reviews_count, extract_seller,
                            extract_sizes_str, extract_sizes_str_from_card,
                            extract_stock_total_from_detail,
                            extract_stock_total_from_search, options_to_json,
                            parse_detail_product, parse_search_products)

log = logging.getLogger("wb.pipeline")

card_host_cache: dict[int, str] = {}


def _save_raw(out_dir: str, name: str, data: dict) -> None:
    raw_dir = os.path.join(out_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    with open(os.path.join(raw_dir, name), "wb") as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))


async def run_pipeline(cfg: Config) -> tuple[str, str]:
    http = HttpClient(
        timeout_s=cfg.timeout_s, retries=cfg.retries, concurrency=cfg.concurrency
    )
    endpoints = WBEndpoints()

    try:
        search_map: dict[int, dict] = {}
        nm_ids: list[int] = []

        page = 1
        while page <= cfg.max_pages and len(nm_ids) < cfg.limit:
            url = endpoints.search_url(
                query=cfg.query,
                page=page,
                dest=cfg.dest,
                curr=cfg.curr,
                app_type=cfg.app_type,
                lang=cfg.lang,
            )
            payload = await http.get_json(url)
            if cfg.save_raw_json:
                _save_raw(cfg.out_dir, f"search_page_{page}.json", payload)

            products = parse_search_products(payload)
            if not products:
                break

            for p in products:
                nm = p.get("id")
                if not isinstance(nm, int):
                    continue
                if nm in search_map:
                    continue
                search_map[nm] = p
                nm_ids.append(nm)
                if len(nm_ids) >= cfg.limit:
                    break

            page += 1

        log.info("collected nm_ids=%d", len(nm_ids))

        async def fetch_detail(nm_id: int) -> dict | None:
            url = endpoints.detail_url(
                nm_id=nm_id, dest=cfg.dest, curr=cfg.curr, app_type=cfg.app_type
            )

            headers = {}
            if cfg.wb_cookie:
                headers["Cookie"] = cfg.wb_cookie
                headers["Origin"] = "https://www.wildberries.ru"
                headers["Referer"] = "https://www.wildberries.ru/"

            try:
                payload = await http.get_json(url, headers=headers or None)
            except httpx.HTTPStatusError as e:
                if e.response is not None and e.response.status_code == 404:
                    return None
                raise

            if cfg.save_raw_json:
                _save_raw(cfg.out_dir, f"detail_{nm_id}.json", payload)

            return parse_detail_product(payload)

        async def fetch_card(nm_id: int) -> tuple[dict, str] | None:
            headers = {
                "Origin": "https://www.wildberries.ru",
                "Referer": "https://www.wildberries.ru/",
            }

            cached = card_host_cache.get(nm_id)
            if cached:
                url = endpoints.card_url(nm_id=nm_id, basket_host=cached, lang=cfg.lang)
                try:
                    payload = await http.get_json(url, headers=headers)
                    return payload, cached
                except httpx.HTTPStatusError as e:
                    if e.response is None or e.response.status_code != 404:
                        raise

            for host in cfg.basket_hosts:
                url = endpoints.card_url(nm_id=nm_id, basket_host=host, lang=cfg.lang)
                try:
                    payload = await http.get_json(url, headers=headers)
                    card_host_cache[nm_id] = host
                    return payload, host
                except httpx.HTTPStatusError as e:
                    if e.response is not None and e.response.status_code == 404:
                        continue
                    raise

            return None

        detail_list = await tqdm_asyncio.gather(*[fetch_detail(nm) for nm in nm_ids])
        card_list = await tqdm_asyncio.gather(*[fetch_card(nm) for nm in nm_ids])

        detail_map: dict[int, dict] = {}
        card_map: dict[int, dict] = {}
        card_host_map: dict[int, str] = {}

        for nm, d, c in zip(nm_ids, detail_list, card_list):
            if isinstance(d, dict):
                detail_map[nm] = d

            if c is not None:
                payload, host = c
                if isinstance(payload, dict) and isinstance(host, str):
                    card_map[nm] = payload
                    card_host_map[nm] = host

        rows = []
        for nm in nm_ids:
            search_p = search_map.get(nm, {})
            detail_p = detail_map.get(nm, {})
            card_p = card_map.get(nm, {})
            sizes = (
                extract_sizes_str(detail_p) or extract_sizes_str_from_card(card_p) or ""
            )

            price = extract_price_rub_from_detail(
                detail_p
            ) or extract_price_rub_from_search(search_p)

            stock_total = (
                extract_stock_total_from_detail(detail_p)
                or extract_stock_total_from_search(search_p)
                or 0
            )
            rating = extract_rating(search_p) or extract_rating(detail_p)

            reviews = extract_reviews_count(search_p) or extract_reviews_count(detail_p)

            seller_name, seller_url = extract_seller(search_p)
            if seller_name is None:
                seller_name, seller_url = extract_seller(detail_p)

            pics = extract_pics(detail_p) or extract_pics(search_p) or 0

            description = (
                extract_description(card_p)
                or detail_p.get("description")
                or search_p.get("description")
            )

            options = extract_options_struct(card_p)
            characteristics_json = options_to_json(options)

            country = extract_country_from_options(options)

            effective_basket_host = card_host_map.get(nm, cfg.basket_host)

            row = merge_to_row(
                nm_id=nm,
                search_p=search_p,
                detail_p=detail_p,
                card_p=card_p,
                price=price,
                sizes=sizes,
                stock_total=stock_total,
                rating=rating,
                reviews=reviews,
                seller_name=seller_name,
                seller_url=seller_url,
                description=description,
                characteristics_json=characteristics_json,
                country=country,
                pics=pics,
                basket_host=effective_basket_host,
                image_size=cfg.image_size,
            )
            rows.append(row)
        os.makedirs(cfg.out_dir, exist_ok=True)
        full_path = os.path.join(cfg.out_dir, "catalog_full.xlsx")
        filtered_path = os.path.join(cfg.out_dir, "catalog_filtered.xlsx")

        export_rows(full_path, rows, sheet_name="catalog")
        filtered_rows = [r for r in rows if is_filtered(r)]
        export_rows(filtered_path, filtered_rows, sheet_name="catalog_filtered")

        return full_path, filtered_path

    finally:
        await http.aclose()
