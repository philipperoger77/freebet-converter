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

import streamlit as st

from freebet_calc import compute_freebet_split, best_split_for_match
from odds_api import fetch_odds_raw


st.set_page_config(page_title="La Grappille des Super Sans Plomb 95", page_icon="⛽", layout="centered")

st.image("assets/banniere.png", width=300)

st.title("⛽ La Grappille des Super Sans Plomb 95")
st.caption("Convertis un freebet en gain garanti, quelle que soit l'issue du match.")

with st.sidebar:
    st.header("Paramètres")
    default_key = st.secrets.get("ODDS_API_KEY", "")
    odds_api_key = st.text_input("Clé API the-odds-api.com (optionnel)", value=default_key, type="password")

st.subheader("1. Cotes")

col_n1, col_n2 = st.columns(2)
with col_n1:
    nom_eq1 = st.text_input("Nom équipe 1 (cash)", value="Équipe 1")
with col_n2:
    nom_eq2 = st.text_input("Nom équipe 2 (freebet)", value="Équipe 2")

col1, col2, col3 = st.columns(3)
with col1:
    cote_eq1 = st.number_input(f"Cote {nom_eq1} (book 1, cash)", min_value=1.01, value=1.41, step=0.01, format="%.2f")
with col2:
    cote_nul = st.number_input("Cote nul (book 2, freebet)", min_value=1.01, value=4.70, step=0.01, format="%.2f")
with col3:
    cote_eq2 = st.number_input(f"Cote {nom_eq2} (book 2, freebet)", min_value=1.01, value=9.00, step=0.01, format="%.2f")

st.subheader("2. Montant du freebet")
montant_fb = st.number_input("Montant du freebet (€)", min_value=0.01, value=20.0, step=1.0, format="%.2f")

result = compute_freebet_split(cote_eq1, cote_nul, cote_eq2, montant_fb)

st.subheader(f"3. Résultat — {nom_eq1} vs {nom_eq2}")

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
sport_label = st.selectbox("Compétition", list(SPORTS.keys()))
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
        except Exception as e:
            st.error(f"Erreur API : {e}")
            st.session_state["matches"] = []
            st.session_state["quota"] = {}

matches = st.session_state.get("matches", [])
quota = st.session_state.get("quota", {})

if quota.get("remaining") is not None:
    st.caption(f"Quota the-odds-api.com : {quota['remaining']} requêtes restantes (résultats mis en cache 5 min).")

if matches:
    all_books = sorted({book for m in matches for book in m["books"]})
    book2 = st.selectbox("Bookmaker du freebet (book 2)", all_books)

    rows = []
    for m in matches:
        fb_odds = m["books"].get(book2)
        if not fb_odds:
            continue

        best_odds = {
            outcome: max(book.get(outcome, 0) for book in m["books"].values())
            for outcome in ("home", "draw", "away")
        }

        best = best_split_for_match(best_odds, fb_odds, montant_fb)
        if best is None:
            continue

        names = {"home": m["home_team"], "draw": "Nul", "away": m["away_team"]}
        rows.append({
            "match": f"{m['home_team']} vs {m['away_team']}",
            "commence_time": m["commence_time"],
            "taux": best["taux"],
            "cash_sur": names[best["cash_outcome"]],
            "cote_cash": best["cote_cash"],
            "mise_cash": best["mise_eq1"],
            "fb_1": f"{names[best['fb_outcomes'][0]]} (cote {best['cote_fb1']:.2f})",
            "fb_1_montant": best["fb_nul"],
            "fb_2": f"{names[best['fb_outcomes'][1]]} (cote {best['cote_fb2']:.2f})",
            "fb_2_montant": best["fb_eq2"],
            "gain_net": best["gain_net"],
        })

    rows.sort(key=lambda r: r["taux"], reverse=True)

    if not rows:
        st.info(f"Aucune cote disponible chez {book2} pour ces matchs.")
    else:
        for r in rows:
            taux_pct = r["taux"]
            icon = "✅" if taux_pct >= 0.70 else "⚠️"
            st.markdown(f"**{r['match']}** — {r['commence_time']} — {icon} **{taux_pct:.1%}**")
            st.write(f"- Cash sur **{r['cash_sur']}** (cote {r['cote_cash']:.2f}) : {r['mise_cash']:.2f} €")
            st.write(f"- Freebet sur **{r['fb_1']}** : {r['fb_1_montant']:.2f} €")
            st.write(f"- Freebet sur **{r['fb_2']}** : {r['fb_2_montant']:.2f} €")
            st.write(f"- Gain net garanti : {r['gain_net']:.2f} €")
            st.markdown("---")
else:
    st.caption("Clique sur \"Récupérer les cotes\" pour lancer le scan.")
