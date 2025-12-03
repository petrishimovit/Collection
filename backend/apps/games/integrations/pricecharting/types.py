from __future__ import annotations

from typing import Literal

#: Region code used by PriceCharting integration.
#: - "all"   – no region filter
#: - "japan" – JP region
#: - "ntsc"  – US/NTSC region
#: - "pal"   – PAL region
Region = Literal["all", "japan", "ntsc", "pal"]

__all__ = ["Region"]
