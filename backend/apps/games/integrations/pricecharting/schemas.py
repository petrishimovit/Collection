from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Dict
from .types import Region

@dataclass
class SearchItem:
    title: str
    platform: str
    region: Region
    url: str
    slug: str
    image: Optional[str]
    prices: Dict[str, Optional[Decimal]]
