"""Drapeaux (emoji) pour les noms d'équipes nationales renvoyés par the-odds-api."""

_SPECIAL_FLAGS = {
    "England": "🏴",
    "Scotland": "🏴",
    "Wales": "🏴",
}

_COUNTRY_CODES = {
    "Uzbekistan": "UZ", "Colombia": "CO", "Canada": "CA", "Bosnia & Herzegovina": "BA",
    "Ghana": "GH", "Panama": "PA", "Haiti": "HT", "Ecuador": "EC", "Curaçao": "CW",
    "Portugal": "PT", "DR Congo": "CD", "USA": "US", "Paraguay": "PY", "Qatar": "QA",
    "Switzerland": "CH", "France": "FR", "Senegal": "SN", "Iraq": "IQ",
    "Netherlands": "NL", "Sweden": "SE", "Germany": "DE", "Brazil": "BR",
    "Tunisia": "TN", "New Zealand": "NZ", "Egypt": "EG", "Spain": "ES",
    "Cape Verde": "CV", "Uruguay": "UY", "Croatia": "HR", "Austria": "AT",
    "Jordan": "JO", "Algeria": "DZ", "Argentina": "AR", "Turkey": "TR",
    "Australia": "AU", "Belgium": "BE", "Norway": "NO", "Czech Republic": "CZ",
    "South Africa": "ZA", "Mexico": "MX", "South Korea": "KR", "Ivory Coast": "CI",
    "Iran": "IR", "Japan": "JP", "Morocco": "MA", "Saudi Arabia": "SA",
    "Italy": "IT", "Poland": "PL", "Denmark": "DK", "Serbia": "RS",
}


def _flag_from_iso2(code: str) -> str:
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def flag(team_name: str) -> str:
    """Retourne l'emoji drapeau pour un nom d'équipe nationale, ou '' si inconnu."""
    if team_name in _SPECIAL_FLAGS:
        return _SPECIAL_FLAGS[team_name]
    code = _COUNTRY_CODES.get(team_name)
    return _flag_from_iso2(code) if code else ""


def flag_prefix(team_name: str) -> str:
    """Comme flag(), mais suivi d'un espace, ou '' si pas de drapeau."""
    f = flag(team_name)
    return f"{f} " if f else ""
