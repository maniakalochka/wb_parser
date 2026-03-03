import asyncio
import logging
import os
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type

log = logging.getLogger("wb.http")


@dataclass
class HttpClient:
    timeout_s: float
    retries: int
    concurrency: int

    def __post_init__(self) -> None:
        cookie = os.getenv("WB_COOKIE")

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Accept-Language": "ru",
            "x-requested-with": "XMLHttpRequest",
            "Referer": "https://www.wildberries.ru/catalog/0/search.aspx",
            "Origin": "https://www.wildberries.ru",
        }
        if cookie:
            headers["Cookie"] = cookie

        self._sem = asyncio.Semaphore(self.concurrency)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_s),
            headers=headers,
            http2=True,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=0.8, max=8.0),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    )
    async def get_json(self, url: str, *, headers: dict[str, str] | None = None) -> dict:
        async with self._sem:
            resp = await self._client.get(url, headers=headers)
            if resp.status_code in (429, 498, 500, 502, 503, 504):
                log.warning("retryable status=%s url=%s", resp.status_code, url)
                resp.raise_for_status()
            resp.raise_for_status()
            return resp.json()