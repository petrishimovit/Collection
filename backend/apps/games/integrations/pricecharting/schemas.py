from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional

from .types import Region


@dataclass
class SearchItem:
    """
    result item returned from pricecharting search.
    """

    title: str
    platform: str
    region: Region
    url: str
    slug: str
    image: Optional[str]
    prices: Dict[str, Optional[Decimal]]


__all__ = ["SearchItem"]
