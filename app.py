"""
Freebet Converter - Outil de conversion de freebets en gain garanti.

Logique :
- Tu as un freebet (FB) sur Unibet, valeur = montant du FB (mise NON rendue).
- Tu places de l'argent réel (cash) sur une issue chez Winamax (mise rendue).
- Tu répartis le FB entre les deux autres issues chez Unibet.
- Objectif : que le BÉNÉFICE NET soit identique quelle que soit l'issue.

La formule (qui tient compte du fait que la mise freebet n'est pas rendue) est
détaillée dans freebet_calc.py.
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


def book_logo(title: str) -> str:
    """Logo du bookmaker si on le connaît (Winamax/Unibet), sinon ''."""
    t = title.lower()
    if "winamax" in t:
        return WINAMAX_LOGO
    if "unibet" in t:
        return UNIBET_LOGO
    return ""


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
    st.session_state["cash_sur"] = pending["cash_sur"]

st.session_state.setdefault("nom_eq1", "Équipe 1")
st.session_state.setdefault("nom_eq2", "Équipe 2")
st.session_state.setdefault("cote_eq1", 1.41)
st.session_state.setdefault("cote_nul", 4.70)
st.session_state.setdefault("cote_eq2", 9.00)
st.session_state.setdefault("cash_sur", "home")

col_n1, col_n2 = st.columns(2)
with col_n1:
    nom_eq1 = st.text_input("Nom équipe 1 (domicile)", key="nom_eq1")
    if team_badge(nom_eq1):
        st.markdown(f"{team_badge(nom_eq1)} {nom_eq1}", unsafe_allow_html=True)
with col_n2:
    nom_eq2 = st.text_input("Nom équipe 2 (extérieur)", key="nom_eq2")
    if team_badge(nom_eq2):
        st.markdown(f"{team_badge(nom_eq2)} {nom_eq2}", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    cote_eq1 = st.number_input(f"Cote {nom_eq1}", min_value=1.01, step=0.01, format="%.2f", key="cote_eq1")
with col2:
    cote_nul = st.number_input("Cote nul", min_value=1.01, step=0.01, format="%.2f", key="cote_nul")
with col3:
    cote_eq2 = st.number_input(f"Cote {nom_eq2}", min_value=1.01, step=0.01, format="%.2f", key="cote_eq2")

# L'issue choisie ici reçoit la mise cash (Winamax) ; les deux autres reçoivent
# le freebet (Unibet). Le scanner pré-sélectionne l'issue la plus rentable.
outcome_names = {"home": nom_eq1, "draw": "Nul", "away": nom_eq2}
outcome_odds = {"home": cote_eq1, "draw": cote_nul, "away": cote_eq2}

st.markdown("**Sur quelle issue placer la mise cash ?** (les 2 autres partent en freebet)")
cash_sur = st.radio(
    "Mise cash sur",
    options=["home", "draw", "away"],
    format_func=lambda k: outcome_names[k],
    horizontal=True,
    label_visibility="collapsed",
    key="cash_sur",
)

fb_keys = [k for k in ("home", "draw", "away") if k != cash_sur]
cote_cash = outcome_odds[cash_sur]
cote_fb1 = outcome_odds[fb_keys[0]]
cote_fb2 = outcome_odds[fb_keys[1]]

st.subheader("2. Montant du freebet")
montant_fb = st.number_input("Montant du freebet (€)", min_value=0.01, value=20.0, step=1.0, format="%.2f")

result = compute_freebet_split(cote_cash, cote_fb1, cote_fb2, montant_fb)

st.markdown(
    f"### 3. Résultat — {team_badge(nom_eq1)}{nom_eq1} vs {team_badge(nom_eq2)}{nom_eq2}",
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
c1.metric(f"Mise cash sur {outcome_names[cash_sur]}", f"{result['mise_eq1']:.2f} €")
c2.metric(f"Freebet sur {outcome_names[fb_keys[0]]}", f"{result['fb_nul']:.2f} €")
c3.metric(f"Freebet sur {outcome_names[fb_keys[1]]}", f"{result['fb_eq2']:.2f} €")

st.metric("Gain net garanti (toutes issues)", f"{result['gain_net']:.2f} €")

taux = result['taux']
if taux >= 0.70:
    st.success(f"✅ Taux de conversion : {taux:.1%}")
else:
    st.warning(f"⚠️ Taux de conversion : {taux:.1%} (sous le seuil de 70%)")

mise = result["mise_eq1"]
with st.expander("Vérification (bénéfice net par issue)"):
    st.write(
        f"{outcome_names[cash_sur]} gagne (cash) → {mise:.2f} × {cote_cash:.2f} − {mise:.2f} (mise) "
        f"= {mise * cote_cash - mise:.2f} €"
    )
    st.write(
        f"{outcome_names[fb_keys[0]]} gagne (freebet) → {result['fb_nul']:.2f} × ({cote_fb1:.2f}−1) − {mise:.2f} (cash perdu) "
        f"= {result['fb_nul'] * (cote_fb1 - 1) - mise:.2f} €"
    )
    st.write(
        f"{outcome_names[fb_keys[1]]} gagne (freebet) → {result['fb_eq2']:.2f} × ({cote_fb2:.2f}−1) − {mise:.2f} (cash perdu) "
        f"= {result['fb_eq2'] * (cote_fb2 - 1) - mise:.2f} €"
    )

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

def default_book_idx(options: list, *preferred: str) -> int:
    """Index du 1er book correspondant à une préférence (sous-chaîne), sinon 0."""
    for pref in preferred:
        for i, title in enumerate(options):
            if pref in title.lower():
                return i
    return 0


if matches:
    available_books = sorted({t for m in matches for t in m["books"]})

    # Réinitialise le choix si le book stocké n'existe plus pour ce sport.
    if st.session_state.get("cash_book") not in available_books:
        st.session_state["cash_book"] = available_books[default_book_idx(available_books, "winamax (fr)", "winamax")]
    if st.session_state.get("fb_book") not in available_books:
        st.session_state["fb_book"] = available_books[default_book_idx(available_books, "unibet (fr)", "unibet")]

    colb1, colb2 = st.columns(2)
    with colb1:
        cash_book = st.selectbox("💶 Mise cash chez", available_books, key="cash_book")
    with colb2:
        fb_book = st.selectbox("🎁 Freebet chez", available_books, key="fb_book")

    rows = []
    for m in matches:
        if cash_book not in m["books"] or fb_book not in m["books"]:
            continue

        cash_odds = m["books"][cash_book]
        fb_odds = m["books"][fb_book]

        best = best_split_for_match(cash_odds, fb_odds, montant_fb)
        if best is None:
            continue

        names = {"home": m["home_team"], "draw": "Nul", "away": m["away_team"]}
        fb_1_name = names[best["fb_outcomes"][0]]
        fb_2_name = names[best["fb_outcomes"][1]]
        # Cote à placer dans chaque case du formulaire (issue cash = Winamax,
        # issues freebet = Unibet).
        odds_by_pos = {
            best["cash_outcome"]: best["cote_cash"],
            best["fb_outcomes"][0]: best["cote_fb1"],
            best["fb_outcomes"][1]: best["cote_fb2"],
        }
        rows.append({
            "match": f"{team_badge(m['home_team'])}{m['home_team']} vs {team_badge(m['away_team'])}{m['away_team']}",
            "home_team": m["home_team"],
            "away_team": m["away_team"],
            "cash_outcome": best["cash_outcome"],
            "cote_home": odds_by_pos["home"],
            "cote_draw": odds_by_pos["draw"],
            "cote_away": odds_by_pos["away"],
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
                "nom_eq1": best_row["home_team"],
                "nom_eq2": best_row["away_team"],
                "cote_eq1": best_row["cote_home"],
                "cote_nul": best_row["cote_draw"],
                "cote_eq2": best_row["cote_away"],
                "cash_sur": best_row["cash_outcome"],
            }
            st.session_state["_auto_filled"] = best_row["match"]
            st.rerun()

    if not rows:
        st.info(f"Aucune cote disponible à la fois chez {cash_book} et {fb_book} pour ces matchs.")
    else:
        cash_book_label = f"{book_logo(cash_book)} {cash_book}".strip()
        fb_book_label = f"{book_logo(fb_book)} {fb_book}".strip()
        for r in rows:
            taux_pct = r["taux"]
            icon = "✅" if taux_pct >= 0.70 else "⚠️"
            st.markdown(f"**{r['match']}** — {r['commence_time']} — {icon} **{taux_pct:.1%}**", unsafe_allow_html=True)
            st.markdown(f"- Cash sur **{team_badge(r['cash_sur'])}{r['cash_sur']}** (cote {r['cote_cash']:.2f}) chez {cash_book_label} : {r['mise_cash']:.2f} €", unsafe_allow_html=True)
            st.markdown(f"- Freebet sur **{team_badge(r['fb_1_name'])}{r['fb_1']}** chez {fb_book_label} : {r['fb_1_montant']:.2f} €", unsafe_allow_html=True)
            st.markdown(f"- Freebet sur **{team_badge(r['fb_2_name'])}{r['fb_2']}** chez {fb_book_label} : {r['fb_2_montant']:.2f} €", unsafe_allow_html=True)
            st.write(f"- Gain net garanti : {r['gain_net']:.2f} €")
            st.markdown("---")
else:
    st.caption("Clique sur \"Récupérer les cotes\" pour lancer le scan.")
