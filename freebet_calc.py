"""Logique de calcul de répartition d'un freebet pour un gain garanti.

Hypothèse importante : un freebet est un pari gratuit dont la MISE N'EST PAS
RENDUE. Une mise freebet de s à cote c rapporte donc s·(c−1) (le bénéfice seul),
alors qu'une mise CASH de a à cote c rapporte a·c (mise rendue + bénéfice).

On mise du cash réel sur l'issue 1 (cote_eq1) et on répartit le freebet sur les
deux autres issues (cote_nul, cote_eq2). On veut un BÉNÉFICE NET G identique
quelle que soit l'issue.

  Issue cash gagne   : a·c_a − a            = a·(c_a − 1)        = G
  Issue freebet B    : s_b·(c_b − 1) − a                        = G
  Issue freebet C    : s_c·(c_c − 1) − a                        = G
  avec s_b + s_c = montant_fb (le freebet ne coûte rien de réel)

  => a    = G / (c_a − 1)
     s_b  = (G + a) / (c_b − 1)
     s_c  = (G + a) / (c_c − 1)
     (G + a) = G·c_a / (c_a − 1)

  s_b + s_c = montant_fb donne :
     G = montant_fb / [ c_a/(c_a−1) · (1/(c_b−1) + 1/(c_c−1)) ]

  Taux de conversion = G / montant_fb
"""


def compute_freebet_split(cote_eq1: float, cote_nul: float, cote_eq2: float, montant_fb: float) -> dict:
    """Calcule la mise cash sur 'eq1' et la répartition du freebet entre 'nul'
    et 'eq2' pour un bénéfice net identique sur les 3 issues.

    cote_eq1        : cote de l'issue misée en CASH (mise rendue).
    cote_nul/cote_eq2 : cotes des 2 issues misées en FREEBET (mise non rendue).

    Retourne un dict avec : retour, mise_eq1, fb_nul, fb_eq2, gain_net, taux.
    """
    inv_fb = 1 / (cote_nul - 1) + 1 / (cote_eq2 - 1)
    gain_net = montant_fb / ((cote_eq1 / (cote_eq1 - 1)) * inv_fb)

    mise_eq1 = gain_net / (cote_eq1 - 1)
    fb_nul = (gain_net + mise_eq1) / (cote_nul - 1)
    fb_eq2 = (gain_net + mise_eq1) / (cote_eq2 - 1)

    # Retour brut si l'issue cash gagne (mise rendue + bénéfice).
    retour = mise_eq1 * cote_eq1
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
