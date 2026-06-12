"""
Freebet Converter - Outil de conversion de freebets en gain garanti.

Logique :
- Tu as un freebet (FB) sur le bookmaker B (book 2), valeur = montant du FB.
- Tu places de l'argent réel (cash) sur l'issue 1 chez un autre bookmaker (book 1).
- Tu répartis le FB entre les issues "nul" et "issue 2" chez book 2.
- Objectif : que le retour soit identique quelle que soit l'issue (nul, eq1, eq2).

Maths :
  R = M_eq1 * cote_eq1 = FB_nul * cote_nul = FB_eq2 * cote_eq2
  FB_nul + FB_eq2 = montant_FB

  => R * (1/cote_nul + 1/cote_eq2) = montant_FB
  => R = montant_FB / (1/cote_nul + 1/cote_eq2)

  FB_nul = R / cote_nul
  FB_eq2 = R / cote_eq2
  M_eq1  = R / cote_eq1

  Gain net = R - M_eq1
  Taux de conversion = Gain net / montant_FB
"""

import json
import os
import time

import streamlit as st

from freebet_calc import compute_freebet_split, best_split_for_match
from odds_api import fetch_odds_raw
from flags import flag_img
from logos import winamax_logo, unibet_logo, club_logo

WINAMAX_LOGO = winamax_logo()
UNIBET_LOGO = unibet_logo()


def team_badge(team_name: str) -> str:
    """Drapeau (équipe nationale) ou blason de club, selon ce qui est connu."""
    return flag_img(team_name) or club_logo(team_name)


LAST_SCAN_FILE = os.path.join(os.path.dirname(__file__), "last_scan.json")


def save_last_scan(sport_key: str, matches: list, quota: dict) -> None:
    with open(LAST_SCAN_FILE, "w", encoding="utf-8") as f:
        json.dump({"sport_key": sport_key, "matches": matches, "quota": quota, "timestamp": time.time()}, f)


def load_last_scan() -> dict | None:
    try:
        with open(LAST_SCAN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


st.set_page_config(page_title="La Grappille des Super Sans Plomb 95", page_icon="⛽", layout="centered")

st.image("assets/banniere_landscape.png", use_container_width=True)

st.title("⛽ La Grappille des Super Sans Plomb 95")
st.caption("Convertis un freebet en gain garanti, quelle que soit l'issue du match.")

with st.sidebar:
    st.header("Paramètres")
    default_key = st.secrets.get("ODDS_API_KEY", "")
    odds_api_key = st.text_input("Clé API the-odds-api.com (optionnel)", value=default_key, type="password")

st.subheader("1. Cotes")

if "_pending_fill" in st.session_state:
    pending = st.session_state.pop("_pending_fill")
    st.session_state["nom_eq1"] = pending["nom_eq1"]
    st.session_state["nom_eq2"] = pending["nom_eq2"]
    st.session_state["cote_eq1"] = pending["cote_eq1"]
    st.session_state["cote_nul"] = pending["cote_nul"]
    st.session_state["cote_eq2"] = pending["cote_eq2"]

st.session_state.setdefault("nom_eq1", "Équipe 1")
st.session_state.setdefault("nom_eq2", "Équipe 2")
st.session_state.setdefault("cote_eq1", 1.41)
st.session_state.setdefault("cote_nul", 4.70)
st.session_state.setdefault("cote_eq2", 9.00)

col_n1, col_n2 = st.columns(2)
with col_n1:
    nom_eq1 = st.text_input("Nom équipe 1 (cash)", key="nom_eq1")
    if team_badge(nom_eq1):
        st.markdown(f"{team_badge(nom_eq1)} {nom_eq1}", unsafe_allow_html=True)
with col_n2:
    nom_eq2 = st.text_input("Nom équipe 2 (freebet)", key="nom_eq2")
    if team_badge(nom_eq2):
        st.markdown(f"{team_badge(nom_eq2)} {nom_eq2}", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"{WINAMAX_LOGO} Winamax (cash)", unsafe_allow_html=True)
    cote_eq1 = st.number_input(f"Cote {nom_eq1}", min_value=1.01, step=0.01, format="%.2f", key="cote_eq1")
with col2:
    st.markdown(f"{UNIBET_LOGO} Unibet (freebet)", unsafe_allow_html=True)
    cote_nul = st.number_input("Cote nul", min_value=1.01, step=0.01, format="%.2f", key="cote_nul")
with col3:
    st.markdown(f"{UNIBET_LOGO} Unibet (freebet)", unsafe_allow_html=True)
    cote_eq2 = st.number_input(f"Cote {nom_eq2}", min_value=1.01, step=0.01, format="%.2f", key="cote_eq2")

st.subheader("2. Montant du freebet")
montant_fb = st.number_input("Montant du freebet (€)", min_value=0.01, value=20.0, step=1.0, format="%.2f")

result = compute_freebet_split(cote_eq1, cote_nul, cote_eq2, montant_fb)

st.markdown(
    f"### 3. Résultat — {team_badge(nom_eq1)}{nom_eq1} vs {team_badge(nom_eq2)}{nom_eq2}",
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
c1.metric(f"Mise cash sur {nom_eq1}", f"{result['mise_eq1']:.2f} €")
c2.metric("Freebet sur nul", f"{result['fb_nul']:.2f} €")
c3.metric(f"Freebet sur {nom_eq2}", f"{result['fb_eq2']:.2f} €")

st.metric("Retour garanti (toutes issues)", f"{result['retour']:.2f} €")
st.metric("Gain net", f"{result['gain_net']:.2f} €")

taux = result['taux']
if taux >= 0.70:
    st.success(f"✅ Taux de conversion : {taux:.1%}")
else:
    st.warning(f"⚠️ Taux de conversion : {taux:.1%} (sous le seuil de 70%)")

with st.expander("Vérification"):
    st.write(f"{nom_eq1} gagne → {result['mise_eq1']:.2f} × {cote_eq1:.2f} = {result['mise_eq1'] * cote_eq1:.2f} €")
    st.write(f"Nul → {result['fb_nul']:.2f} × {cote_nul:.2f} = {result['fb_nul'] * cote_nul:.2f} €")
    st.write(f"{nom_eq2} gagne → {result['fb_eq2']:.2f} × {cote_eq2:.2f} = {result['fb_eq2'] * cote_eq2:.2f} €")

st.divider()
st.subheader("4. Scanner de cotes (live)")
st.caption(
    "Récupère les cotes de tous les bookmakers pour un sport, et calcule pour chaque match "
    "le meilleur taux de conversion possible (mise cash sur la meilleure cote dispo, "
    "freebet réparti sur les 2 autres issues chez le book sélectionné)."
)

SPORTS = {
    "Football - Ligue 1 (France)": "soccer_france_ligue_one",
    "Football - Ligue 2 (France)": "soccer_france_ligue_two",
    "Football - Premier League (Angleterre)": "soccer_epl",
    "Football - Liga (Espagne)": "soccer_spain_la_liga",
    "Football - Serie A (Italie)": "soccer_italy_serie_a",
    "Football - Bundesliga (Allemagne)": "soccer_germany_bundesliga",
    "Football - Ligue des Champions": "soccer_uefa_champs_league",
    "Football - Coupe du Monde FIFA": "soccer_fifa_world_cup",
}
# Au premier chargement de la session, on récupère le dernier scan sauvegardé
# sur disque pour ne pas perdre les résultats quand on revient sur le site.
if "matches" not in st.session_state:
    last_scan = load_last_scan()
    if last_scan:
        st.session_state["matches"] = last_scan["matches"]
        st.session_state["quota"] = last_scan["quota"]
        st.session_state["_last_scan_sport"] = last_scan["sport_key"]
        st.session_state["_last_scan_time"] = last_scan["timestamp"]

sport_keys = list(SPORTS.values())
default_sport_key = st.session_state.get("_last_scan_sport")
default_index = sport_keys.index(default_sport_key) if default_sport_key in sport_keys else 0
sport_label = st.selectbox("Compétition", list(SPORTS.keys()), index=default_index)
sport_key = SPORTS[sport_label]


@st.cache_data(ttl=300, show_spinner="Récupération des cotes...")
def cached_fetch_odds(api_key: str, sport: str):
    return fetch_odds_raw(api_key, sport)


if st.button("Récupérer les cotes"):
    if not odds_api_key:
        st.error("Renseigne ta clé API dans la barre latérale.")
    else:
        try:
            st.session_state["matches"], st.session_state["quota"] = cached_fetch_odds(odds_api_key, sport_key)
            st.session_state["_last_scan_sport"] = sport_key
            st.session_state["_last_scan_time"] = time.time()
            save_last_scan(sport_key, st.session_state["matches"], st.session_state["quota"])
        except Exception as e:
            st.error(f"Erreur API : {e}")
            st.session_state["matches"] = []
            st.session_state["quota"] = {}

matches = st.session_state.get("matches", [])
quota = st.session_state.get("quota", {})

if quota.get("remaining") is not None:
    st.caption(f"Quota the-odds-api.com : {quota['remaining']} requêtes restantes (résultats mis en cache 5 min).")

last_scan_time = st.session_state.get("_last_scan_time")
if last_scan_time is not None:
    minutes_ago = int((time.time() - last_scan_time) / 60)
    if minutes_ago < 1:
        st.caption("Dernier scan : à l'instant")
    else:
        st.caption(f"Dernier scan : il y a {minutes_ago} min")

BOOK1_NAME = "winamax"
BOOK2_NAME = "unibet"


def find_book(books: dict, name_substr: str):
    for title in books:
        if name_substr in title.lower():
            return title
    return None


if matches:
    rows = []
    for m in matches:
        book1_title = find_book(m["books"], BOOK1_NAME)
        book2_title = find_book(m["books"], BOOK2_NAME)
        if not book1_title or not book2_title:
            continue

        cash_odds = m["books"][book1_title]
        fb_odds = m["books"][book2_title]

        best = best_split_for_match(cash_odds, fb_odds, montant_fb)
        if best is None:
            continue

        names = {"home": m["home_team"], "draw": "Nul", "away": m["away_team"]}
        fb_1_name = names[best["fb_outcomes"][0]]
        fb_2_name = names[best["fb_outcomes"][1]]
        rows.append({
            "match": f"{team_badge(m['home_team'])}{m['home_team']} vs {team_badge(m['away_team'])}{m['away_team']}",
            "commence_time": m["commence_time"],
            "taux": best["taux"],
            "cash_sur": names[best["cash_outcome"]],
            "cote_cash": best["cote_cash"],
            "mise_cash": best["mise_eq1"],
            "fb_1": f"{fb_1_name} (cote {best['cote_fb1']:.2f})",
            "fb_1_name": fb_1_name,
            "cote_fb1": best["cote_fb1"],
            "fb_1_montant": best["fb_nul"],
            "fb_2": f"{fb_2_name} (cote {best['cote_fb2']:.2f})",
            "fb_2_name": fb_2_name,
            "cote_fb2": best["cote_fb2"],
            "fb_2_montant": best["fb_eq2"],
            "gain_net": best["gain_net"],
        })

    rows.sort(key=lambda r: r["taux"], reverse=True)

    if rows:
        best_row = rows[0]
        if st.session_state.get("_auto_filled") != best_row["match"]:
            st.session_state["_pending_fill"] = {
                "nom_eq1": best_row["cash_sur"],
                "nom_eq2": best_row["fb_2_name"],
                "cote_eq1": best_row["cote_cash"],
                "cote_nul": best_row["cote_fb1"],
                "cote_eq2": best_row["cote_fb2"],
            }
            st.session_state["_auto_filled"] = best_row["match"]
            st.rerun()

    if not rows:
        st.info("Aucune cote disponible chez Winamax/Unibet pour ces matchs.")
    else:
        for r in rows:
            taux_pct = r["taux"]
            icon = "✅" if taux_pct >= 0.70 else "⚠️"
            st.markdown(f"**{r['match']}** — {r['commence_time']} — {icon} **{taux_pct:.1%}**", unsafe_allow_html=True)
            st.markdown(f"- Cash sur **{team_badge(r['cash_sur'])}{r['cash_sur']}** (cote {r['cote_cash']:.2f}) chez {WINAMAX_LOGO} Winamax : {r['mise_cash']:.2f} €", unsafe_allow_html=True)
            st.markdown(f"- Freebet sur **{team_badge(r['fb_1_name'])}{r['fb_1']}** chez {UNIBET_LOGO} Unibet : {r['fb_1_montant']:.2f} €", unsafe_allow_html=True)
            st.markdown(f"- Freebet sur **{team_badge(r['fb_2_name'])}{r['fb_2']}** chez {UNIBET_LOGO} Unibet : {r['fb_2_montant']:.2f} €", unsafe_allow_html=True)
            st.write(f"- Gain net garanti : {r['gain_net']:.2f} €")
            st.markdown("---")
else:
    st.caption("Clique sur \"Récupérer les cotes\" pour lancer le scan.")
