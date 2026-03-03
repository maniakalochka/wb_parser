from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True)
class WBEndpoints:
    search_base: str = "https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search"
    detail_base: str = "https://card.wb.ru/cards/v1/detail"

    def search_url(
        self,
        *,
        query: str,
        page: int,
        dest: int,
        curr: str,
        app_type: int,
        lang: str,
        sort: str = "popular",
        resultset: str = "catalog",
        spp: int = 30,
        suppress_spellcheck: bool = False,
        ab_testing: bool = False,
        hide_vflags: int = 4294967296,
    ) -> str:
        params = {
            "ab_testing": str(ab_testing).lower(),
            "appType": app_type,
            "curr": curr,
            "dest": dest,
            "hide_vflags": hide_vflags,
            "lang": lang,
            "page": page,
            "query": query,
            "resultset": resultset,
            "sort": sort,
            "spp": spp,
            "suppressSpellcheck": str(suppress_spellcheck).lower(),
        }
        return f"{self.search_base}?{urlencode(params)}"

    def detail_url(self, *, nm_id: int, dest: int, curr: str, app_type: int, spp: int = 30) -> str:
        params = {"appType": app_type, "curr": curr, "dest": dest, "spp": spp, "nm": nm_id}
        return f"{self.detail_base}?{urlencode(params)}"

    def card_url(
        self,
        *,
        nm_id: int,
        basket_host: str,
        lang: str = "ru",
    ) -> str:
        vol = nm_id // 100_000
        part = nm_id // 1_000
        return f"https://{basket_host}/vol{vol}/part{part}/{nm_id}/info/{lang}/card.json"

    @staticmethod
    def basket_path(nm_id: int, lang: str) -> str:
        vol = nm_id // 100_000
        part = nm_id // 1_000
        return f"/vol{vol}/part{part}/{nm_id}/info/{lang}/card.json"

    @staticmethod
    def basket_url(host: int, nm_id: int, lang: str) -> str:
        return f"https://basket-{host:02d}.wbbasket.ru" + WBEndpoints.basket_path(nm_id, lang)