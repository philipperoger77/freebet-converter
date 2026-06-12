"""Drapeaux pour les noms d'équipes nationales renvoyées par the-odds-api.

Les emojis drapeau ne s'affichent pas correctement sous Windows (lettres ISO
au lieu du drapeau), et flagcdn.com est inaccessible depuis certains réseaux ;
on utilise donc les SVG du package flag-icons servis via jsdelivr.
"""

_COUNTRY_CODES = {
    "Uzbekistan": "uz", "Colombia": "co", "Canada": "ca", "Bosnia & Herzegovina": "ba",
    "Ghana": "gh", "Panama": "pa", "Haiti": "ht", "Ecuador": "ec", "Curaçao": "cw",
    "Portugal": "pt", "DR Congo": "cd", "USA": "us", "Paraguay": "py", "Qatar": "qa",
    "Switzerland": "ch", "France": "fr", "Senegal": "sn", "Iraq": "iq",
    "Netherlands": "nl", "Sweden": "se", "Germany": "de", "Brazil": "br",
    "Tunisia": "tn", "New Zealand": "nz", "Egypt": "eg", "Spain": "es",
    "Cape Verde": "cv", "Uruguay": "uy", "Croatia": "hr", "Austria": "at",
    "Jordan": "jo", "Algeria": "dz", "Argentina": "ar", "Turkey": "tr",
    "Australia": "au", "Belgium": "be", "Norway": "no", "Czech Republic": "cz",
    "South Africa": "za", "Mexico": "mx", "South Korea": "kr", "Ivory Coast": "ci",
    "Iran": "ir", "Japan": "jp", "Morocco": "ma", "Saudi Arabia": "sa",
    "Italy": "it", "Poland": "pl", "Denmark": "dk", "Serbia": "rs",
    "England": "gb-eng", "Scotland": "gb-sct", "Wales": "gb-wls",
}


def flag_img(team_name: str, height: int = 16) -> str:
    """Retourne une balise <img> (drapeau via jsdelivr/flag-icons), ou '' si inconnu."""
    code = _COUNTRY_CODES.get(team_name)
    if not code:
        return ""
    return (
        f'<img src="https://cdn.jsdelivr.net/npm/flag-icons@7/flags/4x3/{code}.svg" '
        f'alt="" height="{height}" style="vertical-align:middle;border-radius:2px;margin-right:4px;">'
    )
