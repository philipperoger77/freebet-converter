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

from freebet_calc import compute_freebet_split
from odds_api import fetch_best_odds


st.set_page_config(page_title="Freebet Converter", page_icon="🎯", layout="centered")

st.title("🎯 Freebet Converter")
st.caption("Convertis un freebet en gain garanti, quelle que soit l'issue du match.")

with st.sidebar:
    st.header("Paramètres")
    default_key = st.secrets.get("ODDS_API_KEY", "")
    odds_api_key = st.text_input("Clé API the-odds-api.com (optionnel)", value=default_key, type="password")

st.subheader("1. Cotes")

col1, col2, col3 = st.columns(3)
with col1:
    cote_eq1 = st.number_input("Cote équipe 1 (book 1, cash)", min_value=1.01, value=1.41, step=0.01, format="%.2f")
with col2:
    cote_nul = st.number_input("Cote nul (book 2, freebet)", min_value=1.01, value=4.70, step=0.01, format="%.2f")
with col3:
    cote_eq2 = st.number_input("Cote équipe 2 (book 2, freebet)", min_value=1.01, value=9.00, step=0.01, format="%.2f")

st.subheader("2. Montant du freebet")
montant_fb = st.number_input("Montant du freebet (€)", min_value=0.01, value=20.0, step=1.0, format="%.2f")

result = compute_freebet_split(cote_eq1, cote_nul, cote_eq2, montant_fb)

st.subheader("3. Résultat")

c1, c2, c3 = st.columns(3)
c1.metric("Mise cash sur eq1", f"{result['mise_eq1']:.2f} €")
c2.metric("Freebet sur nul", f"{result['fb_nul']:.2f} €")
c3.metric("Freebet sur eq2", f"{result['fb_eq2']:.2f} €")

st.metric("Retour garanti (toutes issues)", f"{result['retour']:.2f} €")
st.metric("Gain net", f"{result['gain_net']:.2f} €")

taux = result['taux']
if taux >= 0.70:
    st.success(f"✅ Taux de conversion : {taux:.1%}")
else:
    st.warning(f"⚠️ Taux de conversion : {taux:.1%} (sous le seuil de 70%)")

with st.expander("Vérification"):
    st.write(f"eq1 gagne → {result['mise_eq1']:.2f} × {cote_eq1:.2f} = {result['mise_eq1'] * cote_eq1:.2f} €")
    st.write(f"nul → {result['fb_nul']:.2f} × {cote_nul:.2f} = {result['fb_nul'] * cote_nul:.2f} €")
    st.write(f"eq2 gagne → {result['fb_eq2']:.2f} × {cote_eq2:.2f} = {result['fb_eq2'] * cote_eq2:.2f} €")

st.divider()
st.subheader("4. Scanner de cotes (live)")
st.caption("Récupère les meilleures cotes disponibles via the-odds-api.com pour un sport donné.")

sport_key = st.text_input("Sport key (ex: soccer_france_ligue_one)", value="soccer_france_ligue_one")

if st.button("Récupérer les cotes"):
    if not odds_api_key:
        st.error("Renseigne ta clé API dans la barre latérale.")
    else:
        with st.spinner("Récupération des cotes..."):
            try:
                matches = fetch_best_odds(odds_api_key, sport_key)
            except Exception as e:
                st.error(f"Erreur API : {e}")
                matches = []

        for m in matches:
            st.markdown(f"**{m['home_team']} vs {m['away_team']}** — {m['commence_time']}")
            st.write(f"- Meilleure cote {m['home_team']} : {m['best_home_odds']:.2f} ({m['best_home_book']})")
            st.write(f"- Meilleure cote nul : {m['best_draw_odds']:.2f} ({m['best_draw_book']})")
            st.write(f"- Meilleure cote {m['away_team']} : {m['best_away_odds']:.2f} ({m['best_away_book']})")
            st.markdown("---")
