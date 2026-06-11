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
