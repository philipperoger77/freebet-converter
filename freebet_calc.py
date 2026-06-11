"""Logique de calcul de répartition d'un freebet pour un gain garanti."""


def compute_freebet_split(cote_eq1: float, cote_nul: float, cote_eq2: float, montant_fb: float) -> dict:
    """Calcule la répartition optimale d'un freebet entre 'nul' et 'eq2',
    et la mise cash sur 'eq1', pour obtenir un retour identique sur les 3 issues.

    Retourne un dict avec : retour, mise_eq1, fb_nul, fb_eq2, gain_net, taux.
    """
    inv_sum = 1 / cote_nul + 1 / cote_eq2
    retour = montant_fb / inv_sum

    fb_nul = retour / cote_nul
    fb_eq2 = retour / cote_eq2
    mise_eq1 = retour / cote_eq1

    gain_net = retour - mise_eq1
    taux = gain_net / montant_fb

    return {
        "retour": retour,
        "mise_eq1": mise_eq1,
        "fb_nul": fb_nul,
        "fb_eq2": fb_eq2,
        "gain_net": gain_net,
        "taux": taux,
    }


def best_split_for_match(best_odds: dict, fb_odds: dict, montant_fb: float) -> dict:
    """Pour un match à 3 issues (home/draw/away), teste les 3 façons de
    choisir l'issue "cash" (book 1) et répartit le freebet sur les deux
    autres issues via le book du freebet (book 2). Retourne le meilleur
    résultat (taux le plus élevé).

    best_odds : {"home": float, "draw": float, "away": float} -> meilleure
                cote dispo tous books confondus, pour la mise cash.
    fb_odds   : {"home": float, "draw": float, "away": float} -> cotes du
                book où se trouve le freebet, pour la répartition du FB.
    """
    outcomes = ["home", "draw", "away"]
    best = None
    for cash_outcome in outcomes:
        fb_outcomes = [o for o in outcomes if o != cash_outcome]
        cote_cash = best_odds.get(cash_outcome, 0)
        cote_fb1 = fb_odds.get(fb_outcomes[0], 0)
        cote_fb2 = fb_odds.get(fb_outcomes[1], 0)
        if cote_cash < 1.01 or cote_fb1 < 1.01 or cote_fb2 < 1.01:
            continue

        result = compute_freebet_split(cote_cash, cote_fb1, cote_fb2, montant_fb)
        result["cash_outcome"] = cash_outcome
        result["fb_outcomes"] = fb_outcomes
        result["cote_cash"] = cote_cash
        result["cote_fb1"] = cote_fb1
        result["cote_fb2"] = cote_fb2

        if best is None or result["taux"] > best["taux"]:
            best = result

    return best
