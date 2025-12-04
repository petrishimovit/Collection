import pytest

from apps.games.models import PriceChartingConnect, normalize_url

pytestmark = pytest.mark.django_db

@pytest.mark.parametrize(
    "raw,expected",
    [
        (" https://example.com/game?q=1#frag ", "https://example.com/game"),
        ("https://example.com/game/", "https://example.com/game"),
        ("http://example.com/path/?a=1&b=2", "http://example.com/path"),
        ("", ""),
        ("not-a-url", ""),
    ],
)
def test_normalize_url(raw, expected):
    assert normalize_url(raw) == expected


def test_pricecharting_connect_properties():
    obj = PriceChartingConnect.objects.create(
        url="https://www.pricecharting.com/game/snes/super-mario-world",
        current={
            "title": "Super Mario World",
            "platform": "SNES",
            "region": "ntsc",
            "url": "https://www.pricecharting.com/game/snes/super-mario-world",
            "slug": "snes/super-mario-world",
            "prices": {"loose": 10, "cib": 20},
        },
        history={},
    )

    assert obj.title == "Super Mario World"
    assert obj.platform == "SNES"
    assert obj.region == "ntsc"
    assert obj.prices["loose"] == 10
