from datetime import date
from django.urls import reverse

import pytest

from apps.games.services import pricecharting as pricecharting_module
from apps.games.integrations.pricecharting.client import PricechartingClient
from apps.games.integrations.pricecharting.schemas import SearchItem
from apps.games.models import PriceChartingConnect
from apps.games.services.pricecharting import PricechartingService


pytestmark = pytest.mark.django_db


@pytest.fixture
def fake_search_items():
    return [
        SearchItem(
            title="Super Mario World",
            platform="SNES",
            region="ntsc",
            url="https://www.pricecharting.com/game/snes/super-mario-world",
            slug="snes/super-mario-world",
            image=None,
            prices={"loose": 10, "cib": 20, "new": 30},
        )
    ]


@pytest.fixture
def patch_pricecharting(monkeypatch, fake_search_items):
    def fake_search(q: str, region: str = "all", limit: int = 10):
        return fake_search_items

    def fake_item_details(token: str):
        return {
            "title": "Super Mario World",
            "platform": "SNES",
            "region": "ntsc",
            "url": "https://www.pricecharting.com/game/snes/super-mario-world",
            "slug": "snes/super-mario-world",
            "prices": {"loose": 10, "cib": 20, "new": 30},
        }

    monkeypatch.setattr(PricechartingClient, "search", staticmethod(fake_search))
    monkeypatch.setattr(PricechartingClient, "item_details", staticmethod(fake_item_details))


def test_search_items_uses_client_and_serializes(fake_search_items, patch_pricecharting):
    items = PricechartingService.search_items(q="mario", region="ntsc", limit=5)
    assert len(items) == 1
    assert items[0]["title"] == fake_search_items[0].title
    assert items[0]["prices"]["loose"] == 10


def test_upsert_connect_creates_and_populates(patch_pricecharting):
    url = "https://www.pricecharting.com/game/snes/super-mario-world?ref=123"

    obj = PricechartingService.upsert_connect(url=url)

    assert obj is not None
    assert obj.url == "https://www.pricecharting.com/game/snes/super-mario-world"
    assert obj.current["title"] == "Super Mario World"
    assert obj.current["prices"]["new"] == 30


def test_snapshot_prices_updates_history(patch_pricecharting):
    url = "https://www.pricecharting.com/game/snes/super-mario-world"
    connect = PriceChartingConnect.objects.create(url=url)

    snapshot = PricechartingService.snapshot_prices(connect=connect)
    connect.refresh_from_db()

    today = date.today().isoformat()

    assert snapshot["date"] == today
    assert connect.history[today]["loose"] == 10
    assert connect.current["prices"]["cib"] == 20
    assert connect.last_synced_at is not None


def test_snapshot_prices_migrates_legacy_list_history(patch_pricecharting):
    url = "https://www.pricecharting.com/game/snes/super-mario-world"
    connect = PriceChartingConnect.objects.create(
        url=url,
        history=[
            {"at": "2024-01-01T12:00:00Z", "prices": {"loose": 5}},
            {"date": "2024-01-10", "prices": {"loose": 6}},
        ],
    )

    PricechartingService.snapshot_prices(connect=connect)
    connect.refresh_from_db()

   
    assert isinstance(connect.history, dict)
    assert "2024-01-01" in connect.history
    assert "2024-01-10" in connect.history


@pytest.fixture
def mock_search_items(monkeypatch):
    def fake_search_items(*, q: str, region: str = "all", limit: int = 10):
        return [
            {
                "title": "Super Mario World",
                "platform": "SNES",
                "region": region,
                "url": "https://www.pricecharting.com/game/snes/super-mario-world",
                "slug": "snes/super-mario-world",
                "prices": {"loose": 10},
            }
        ]

    monkeypatch.setattr(
        pricecharting_module.PricechartingService,
        "search_items",
        classmethod(lambda cls, **kwargs: fake_search_items(**kwargs)),
    )


@pytest.fixture
def mock_get_item_details(monkeypatch):
    def fake_get_item_details(*, url=None, slug=None):
        return {
            "title": "Super Mario World",
            "platform": "SNES",
            "region": "ntsc",
            "url": url or "https://example.com",
            "slug": slug or "snes/super-mario-world",
            "prices": {"loose": 10, "cib": 20},
        }

    monkeypatch.setattr(
        pricecharting_module.PricechartingService,
        "get_item_details",
        classmethod(lambda cls, **kwargs: fake_get_item_details(**kwargs)),
    )


def test_pricecharting_search_view_ok(api_client, mock_search_items):
    url = reverse("pricecharting-search")
    resp = api_client.get(url, {"q": "mario", "region": "ntsc", "limit": 5})

    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["title"] == "Super Mario World"


def test_pricecharting_search_view_missing_q(api_client):
    url = reverse("pricecharting-search")
    resp = api_client.get(url)

    assert resp.status_code == 400
    assert "q" in resp.data


def test_pricecharting_item_view_with_slug(api_client, mock_get_item_details):
    url = reverse("pricecharting-item")
    resp = api_client.get(url, {"slug": "snes/super-mario-world"})

    assert resp.status_code == 200
    assert resp.data["title"] == "Super Mario World"
    assert resp.data["slug"] == "snes/super-mario-world"


def test_pricecharting_item_view_requires_url_or_slug(api_client):
    url = reverse("pricecharting-item")
    resp = api_client.get(url)

    assert resp.status_code == 400
    assert "Provide `url` or `slug`." in str(resp.data)