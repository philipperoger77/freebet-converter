"""Client minimal pour the-odds-api.com (cotes en temps réel)."""

import requests

BASE_URL = "https://api.the-odds-api.com/v4"


def fetch_best_odds(api_key: str, sport_key: str, region: str = "eu") -> list[dict]:
    """Récupère les matchs à venir d'un sport et la meilleure cote h2h
    (1/N/2) tous bookmakers confondus.
    """
    url = f"{BASE_URL}/sports/{sport_key}/odds"
    params = {
        "apiKey": api_key,
        "regions": region,
        "markets": "h2h",
        "oddsFormat": "decimal",
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    matches = []
    for event in data:
        home = event.get("home_team")
        away = event.get("away_team")

        best_home = {"odds": 0.0, "book": None}
        best_draw = {"odds": 0.0, "book": None}
        best_away = {"odds": 0.0, "book": None}

        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                for outcome in market.get("outcomes", []):
                    name = outcome.get("name")
                    price = outcome.get("price", 0)
                    if name == home and price > best_home["odds"]:
                        best_home = {"odds": price, "book": bookmaker.get("title")}
                    elif name == away and price > best_away["odds"]:
                        best_away = {"odds": price, "book": bookmaker.get("title")}
                    elif name == "Draw" and price > best_draw["odds"]:
                        best_draw = {"odds": price, "book": bookmaker.get("title")}

        matches.append({
            "home_team": home,
            "away_team": away,
            "commence_time": event.get("commence_time"),
            "best_home_odds": best_home["odds"],
            "best_home_book": best_home["book"],
            "best_draw_odds": best_draw["odds"],
            "best_draw_book": best_draw["book"],
            "best_away_odds": best_away["odds"],
            "best_away_book": best_away["book"],
        })

    return matches
