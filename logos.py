"""Logos des bookmakers et des clubs de football.

- Winamax / Unibet : logos hébergés sur Wikimedia Commons.
- Clubs de foot : recherche dynamique du blason via l'API TheSportsDB
  (mise en cache pour éviter de re-requêter à chaque rerun).
"""

import re

import requests
import streamlit as st

WINAMAX_LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Winamax_Logo.svg/120px-Winamax_Logo.svg.png"
UNIBET_LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Unibet_logo.svg/120px-Unibet_logo.svg.png"

# Alias pour faire correspondre les noms renvoyés par the-odds-api aux noms
# connus de TheSportsDB, quand ils diffèrent trop pour que la recherche marche.
_TEAM_ALIASES = {
    "Paris Saint Germain": "Paris Saint-Germain",
    "Inter Milan": "Internazionale",
    "AC Milan": "AC Milan",
    "Wolverhampton Wanderers": "Wolverhampton Wanderers",
}

_EXCLUDE_KEYWORDS = ("women", "wfc", "youth", "academy", "reserve")
_EXCLUDE_PATTERN = re.compile(r"\bu-?\d{1,2}\b")


def _badge_logo_html(url: str, height: int = 18) -> str:
    return (
        f'<img src="{url}" alt="" height="{height}" '
        f'style="vertical-align:middle;border-radius:2px;margin-right:4px;">'
    )


def winamax_logo(height: int = 18) -> str:
    return _badge_logo_html(WINAMAX_LOGO_URL, height)


def unibet_logo(height: int = 18) -> str:
    return _badge_logo_html(UNIBET_LOGO_URL, height)


@st.cache_data(ttl=86400, show_spinner=False)
def _search_team_badge(team_name: str) -> str:
    query = _TEAM_ALIASES.get(team_name, team_name)
    try:
        resp = requests.get(
            "https://www.thesportsdb.com/api/v1/json/3/searchteams.php",
            params={"t": query},
            timeout=5,
        )
        resp.raise_for_status()
        teams = resp.json().get("teams") or []
    except Exception:
        return ""

    for team in teams:
        name = (team.get("strTeam") or "").lower()
        if any(kw in name for kw in _EXCLUDE_KEYWORDS) or _EXCLUDE_PATTERN.search(name):
            continue
        badge = team.get("strBadge")
        if badge:
            return badge

    return ""


def club_logo(team_name: str, height: int = 18) -> str:
    """Retourne une balise <img> avec le blason du club, ou '' si introuvable."""
    badge = _search_team_badge(team_name)
    if not badge:
        return ""
    return (
        f'<img src="{badge}" alt="" height="{height}" '
        f'style="vertical-align:middle;margin-right:4px;">'
    )
