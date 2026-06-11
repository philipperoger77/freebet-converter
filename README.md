# Freebet Converter

Outil pour convertir un freebet en gain garanti, quelle que soit l'issue d'un match.

## Principe

1. Tu as un freebet sur le bookmaker B (book 2).
2. Tu places de l'argent réel sur l'issue 1 chez un autre bookmaker (book 1).
3. L'app calcule la répartition optimale du freebet entre "nul" et "issue 2"
   pour que le retour soit identique sur les 3 issues possibles.

## Lancer l'app

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Cotes en temps réel (optionnel)

Crée une clé gratuite sur [the-odds-api.com](https://the-odds-api.com/) (500 requêtes/mois)
et renseigne-la dans la barre latérale de l'app pour scanner les cotes disponibles.
