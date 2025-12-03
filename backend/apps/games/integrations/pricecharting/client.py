from __future__ import annotations

import logging
import re
from decimal import Decimal
from typing import Dict, List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from django.conf import settings

from .schemas import SearchItem
from .types import Region

logger = logging.getLogger(__name__)

BASE: str = getattr(settings, "PRICECHARTING_URL", "https://www.pricecharting.com")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": BASE + "/",
}

_MONEY_RE = re.compile(r"\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)", re.I)


def _parse_money(s: str) -> Optional[Decimal]:
    """
    parse money-like string into Decimal or return None if parsing fails.
    """
    m = _MONEY_RE.search(s or "")
    return Decimal(m.group(1).replace(",", "")) if m else None


class PricechartingClient:
    """
    low level html-scraping client for pricecharting.com.
    """

    REGION_MAP = {"all": "all", "japan": "japan", "ntsc": "ntsc", "pal": "pal"}


    @staticmethod
    def _client() -> httpx.Client:
        """Return a configured httpx.Client instance for PriceCharting requests."""
        return httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True)

   

    @staticmethod
    def _pick_results_table(soup: BeautifulSoup):
        """
        Heuristically select a result table with titles and prices.

        We look for a <table> whose header row contains "title" and at least
        one of the supported set of price columns:
        - "low" + "mid"
        - "loose" + "cib"
        """
        for tbl in soup.find_all("table"):
            th_texts = [th.get_text(" ", strip=True).lower() for th in tbl.find_all("th")]
            joined = " | ".join(th_texts)
            if "title" in joined and (
                ("low" in joined and "mid" in joined)
                or ("loose" in joined and "cib" in joined)
            ):
                return tbl
        return None

    @staticmethod
    def _col_indices(table) -> Dict[str, int]:
        """
        Compute column indices for title/set/low/mid/high columns.

        Multiple variations of column naming are supported:
        - "low" or "loose"
        - "mid" or "cib"
        - "high" or "new"
        """
        headers = [th.get_text(" ", strip=True).lower() for th in table.select("tr th")]

        def col_idx(parts):
            for i, h in enumerate(headers):
                if all(p in h for p in parts):
                    return i
            return -1

        title_i = col_idx(["title"])
        set_i = col_idx(["set"])
        low_raw = col_idx(["low"])
        low_i = low_raw if low_raw != -1 else col_idx(["loose"])
        mid_raw = col_idx(["mid"])
        mid_i = mid_raw if mid_raw != -1 else col_idx(["cib"])
        high_raw = col_idx(["high"])
        high_i = high_raw if high_raw != -1 else col_idx(["new"])

        return {"title": title_i, "set": set_i, "low": low_i, "mid": mid_i, "high": high_i}

    @staticmethod
    def _extract_from_table(
        soup: BeautifulSoup,
        region: Region,
        limit: int,
    ) -> List[SearchItem]:
        """
        Extract SearchItem objects from PriceCharting HTML table.

        If the main result table isn't found, returns an empty list.
        """
        table = PricechartingClient._pick_results_table(soup)
        if not table:
            return []

        idx = PricechartingClient._col_indices(table)
        out: List[SearchItem] = []
        rows = table.select("tr")

        for tr in rows[1:]:
            tds = tr.find_all("td")
            if not tds:
                continue

            title = url = slug = ""
            image: Optional[str] = None

            if 0 <= idx["title"] < len(tds):
                title_td = tds[idx["title"]]
                img = title_td.select_one("img[src]")
                if img:
                    image = img.get("src", "").strip()
                    if image.startswith("//"):
                        image = "https:" + image

                cands = title_td.select("a[href*='/game/']")
                link = next(
                    (a for a in cands if a.get_text(strip=True)),
                    cands[0] if cands else None,
                )
                if not link:
                    continue

                title = link.get_text(strip=True)
                href = link.get("href", "").strip()
                if not href:
                    continue

                url = href if href.startswith("http") else urljoin(BASE, href)
                slug = href.split("/game/", 1)[-1].lstrip("/")
            else:
                continue

            platform = ""
            if 0 <= idx["set"] < len(tds):
                platform = tds[idx["set"]].get_text(" ", strip=True)

            def td_money(i: int) -> Optional[Decimal]:
                if i == -1 or i >= len(tds):
                    return None
                return _parse_money(tds[i].get_text(" ", strip=True))

            loose = td_money(idx["low"])
            cib = td_money(idx["mid"])
            new = td_money(idx["high"])

            out.append(
                SearchItem(
                    title=title,
                    platform=platform,
                    region=region,
                    url=url,
                    slug=slug,
                    image=image,
                    prices={"loose": loose, "cib": cib, "new": new},
                )
            )
            if len(out) >= limit:
                break

        return out

    @staticmethod
    def _extract_games_anywhere(
        soup: BeautifulSoup,
        region: Region,
        limit: int,
    ) -> List[SearchItem]:
        """
        Fallback extraction if the main table cannot be parsed.
        with only minimal info (no prices).
        """
        items: List[SearchItem] = []
        seen = set()

        for a in soup.select("a[href^='/game/']"):
            href = a.get("href", "").strip()
            if not href.startswith("/game/") or href in seen:
                continue
            seen.add(href)

            url = urljoin(BASE, href)
            slug = href.lstrip("/game/")
            title = a.get_text(strip=True) or slug.split("/")[-1].replace("-", " ").title()
            platform = ""

            row = a.find_parent("tr")
            if row:
                links = row.select("a")
                try:
                    i = links.index(a)
                    if i + 1 < len(links):
                        platform = links[i + 1].get_text(strip=True)
                except ValueError:
                    pass

            items.append(
                SearchItem(
                    title=title,
                    platform=platform,
                    region=region,
                    url=url,
                    slug=slug,
                    image=None,
                    prices={"loose": None, "cib": None, "new": None},
                )
            )
            if len(items) >= limit:
                break

        return items

   

    @staticmethod
    def search(q: str, region: Region = "all", limit: int = 10) -> List[SearchItem]:
        """
        Search games on PriceCharting and return a list of SearchItem.
        """
        q = (q or "").strip()
        params = {
            "type": "prices",
            "q": q,
            "sort": "popularity",
            "broad-category": "all",
            "console-uid": "",
            "exclude-variants": "false",
            "region-name": PricechartingClient.REGION_MAP[region],
            "show-images": "true",
        }

        with PricechartingClient._client() as client:
            logger.info("Pricecharting.search -> %s/search-products params=%s", BASE, params)
            r = client.get(f"{BASE}/search-products", params=params)
            logger.info(
                "Pricecharting.search <- %s [%s]",
                str(r.request.url),
                r.status_code,
            )
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            title_text = soup.title.get_text(strip=True) if soup.title else ""

            if "verify you are a human" in r.text.lower():
                logger.warning(
                    "Pricecharting.search anti-bot page detected for %s",
                    str(r.request.url),
                )

            items = PricechartingClient._extract_from_table(soup, region, limit)
            if items:
                logger.info("Pricecharting.search items_from_table=%d", len(items))
                return items

            logger.warning(
                "Pricecharting.search empty table; title=%r url=%s",
                title_text,
                str(r.request.url),
            )
            alt = PricechartingClient._extract_games_anywhere(soup, region, limit)
            if alt:
                logger.info(
                    "Pricecharting.search recovered via alt scan: %d items",
                    len(alt),
                )
                return alt

            snippet = BeautifulSoup(r.text[:2000], "html.parser").get_text(" ", strip=True)
            logger.warning(
                "Pricecharting.search empty_result q=%r region=%s; page_title=%r; first_html_snippet=%r",
                q,
                region,
                title_text,
                snippet,
            )
            return []

    @staticmethod
    def item_details(url_or_slug: str) -> Dict:
        """
        Fetch and parse a single game page.
        """
        url = (
            url_or_slug
            if url_or_slug.startswith("http")
            else f"{BASE}/game/{url_or_slug.lstrip('/')}"
        )

        with PricechartingClient._client() as client:
            logger.info("Pricecharting.item_details -> %s", url)
            r = client.get(url)
            logger.info(
                "Pricecharting.item_details <- %s [%s]",
                str(r.request.url),
                r.status_code,
            )
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            h1 = soup.select_one("h1")
            title = (h1.get_text(" ", strip=True) if h1 else "").strip()

            plat = soup.select_one(
                "h1 a[href*='/jp-'], h1 a[href*='/pal-'], "
                "h1 a[href*='/playstation'], h1 a[href*='/xbox'], "
                "h1 a[href*='/sega'], h1 a"
            )
            platform = (plat.get_text(strip=True) if plat else "").strip()

            slug = url.split("/game/", 1)[-1]
            region: Region = "all"

            low = slug.lower()
            if low.startswith("jp-") or "jp " in platform.lower():
                region = "japan"
            elif low.startswith("pal-") or "pal " in platform.lower():
                region = "pal"
            elif (
                low.startswith("ntsc")
                or "ntsc" in platform.lower()
                or "usa" in platform.lower()
            ):
                region = "ntsc"

            text = soup.get_text(" ", strip=True)

            def pick(name_regex: str) -> Optional[Decimal]:
                m = re.search(
                    name_regex
                    + r".{0,80}?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)",
                    text,
                    re.I | re.S,
                )
                return Decimal(m.group(1).replace(",", "")) if m else None

            prices = {
                "loose": pick(r"(?:Loose Price)"),
                "cib": pick(r"(?:Complete Price|CIB Price)"),
                "new": pick(r"(?:New Price)"),
                "graded": pick(r"(?:Graded Price)"),
                "box_only": pick(r"(?:Box Only Price)"),
                "manual_only": pick(r"(?:Manual Only Price)"),
            }

            return {
                "title": title,
                "platform": platform,
                "region": region,
                "url": url,
                "slug": slug,
                "prices": prices,
            }


__all__ = ["PricechartingClient"]
