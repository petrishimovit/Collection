from django.urls import reverse
from pathlib import Path
import json

from apps.games.services.registry import GameRegistry
from apps.games.services.search import GameSearchService
from apps.games.views.games import GameSearchView


def test_registry_loads_from_dir(tmp_path: Path):
    data_dir = tmp_path / "gamesdb"
    data_dir.mkdir()

    (data_dir / "games.json").write_text(
        """
        [
          {"Game": "Super Mario World", "Platform": "SNES", "Year": 1990},
          {"Game": "Super Mario Bros", "Platform": "NES", "Year": 1985}
        ]
        """,
        encoding="utf-8",
    )

    registry = GameRegistry()
    n1, n2 = registry.load_from_dir(data_dir)

    assert n1 == 2
    assert n2 == 2
    assert len(registry.games) == 2
    assert registry.lowers[0]["game"] == "super mario world"


def test_search_by_name_with_platform(tmp_path: Path):
    data_dir = tmp_path / "gamesdb"
    data_dir.mkdir()

    (data_dir / "games.json").write_text(
        """
        [
          {"Game": "Super Mario World", "Platform": "SNES"},
          {"Game": "Super Mario Bros", "Platform": "NES"},
          {"Game": "Metroid", "Platform": "NES"}
        ]
        """,
        encoding="utf-8",
    )

    registry = GameRegistry()
    service = GameSearchService(registry=registry)

    result = service.search_by_name(
        q="super mario",
        platform="snes",
        limit=10,
        offset=0,
        autoload_dir=data_dir,
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["Platform"] == "SNES"


def test_search_by_name_empty_query(tmp_path: Path):
    data_dir = tmp_path / "gamesdb"
    data_dir.mkdir()

    (data_dir / "games.json").write_text(
        """
        [
          {"Game": "Super Mario World", "Platform": "SNES"}
        ]
        """,
        encoding="utf-8",
    )

    registry = GameRegistry()
    service = GameSearchService(registry=registry)

    result = service.search_by_name(
        q="",
        limit=10,
        offset=0,
        autoload_dir=data_dir,
    )

    assert result["total"] == 0
    assert result["items"] == []


def test_games_search_requires_q_param(api_client):
    url = reverse("games-search")
    resp = api_client.get(url)

    assert resp.status_code == 400
    assert "detail" in resp.data
    assert "q" in resp.data["detail"].lower()


def test_games_search_returns_results(api_client):
    url = reverse("games-search")
    resp = api_client.get(url, {"q": "super mario", "limit": 10})

    assert resp.status_code == 200
  
    assert isinstance(resp.data, list)
   
    assert len(resp.data) >= 1
   
    assert len(resp.data) <= 10

   
    first = resp.data[0]
    assert "Game" in first
    assert "Platform" in first


def test_games_search_single_mode(api_client):
    url = reverse("games-search")
    resp = api_client.get(url, {"q": "super mario", "single": "1"})

    assert resp.status_code == 200
   
    assert isinstance(resp.data, dict)
    assert "Game" in resp.data

  
    game_name = (resp.data["Game"] or "").lower()
    assert game_name  
    
    assert "super" in game_name or "mario" in game_name