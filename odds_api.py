"""Client minimal pour the-odds-api.com (cotes en temps réel)."""

import requests

BASE_URL = "https://api.the-odds-api.com/v4"


def fetch_odds_raw(api_key: str, sport_key: str, region: str = "eu") -> list[dict]:
    """Récupère les matchs à venir d'un sport avec, pour chaque bookmaker,
    les cotes h2h (domicile / nul / extérieur).

    Retourne une liste de dicts :
    {
        "home_team": str, "away_team": str, "commence_time": str,
        "books": {book_title: {"home": float, "draw": float, "away": float}},
    }
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

        books = {}
        for bookmaker in event.get("bookmakers", []):
            title = bookmaker.get("title")
            for market in bookmaker.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                odds = {}
                for outcome in market.get("outcomes", []):
                    name = outcome.get("name")
                    price = outcome.get("price", 0)
                    if name == home:
                        odds["home"] = price
                    elif name == away:
                        odds["away"] = price
                    elif name == "Draw":
                        odds["draw"] = price
                if len(odds) == 3:
                    books[title] = odds

        if books:
            matches.append({
                "home_team": home,
                "away_team": away,
                "commence_time": event.get("commence_time"),
                "books": books,
            })

    return matches
