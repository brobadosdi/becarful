import re
import logging
from collections import Counter
import config

logger = logging.getLogger(__name__)

# Mots parasites qui signalent un faux trigger word (jeu "commente le dernier mot")
MOTS_PARASITES = {
    "dernier", "dernière", "mot", "fin", "fin!", "derniermot",
    "lastword", "last", "word", "end",
}


def _nettoyer_texte(texte: str) -> str:
    """Normalise un commentaire : minuscules, sans ponctuation excessive."""
    texte = texte.lower().strip()
    texte = re.sub(r"[^\w\s]", "", texte)
    return texte


def _compter_mots(texte: str) -> int:
    return len(texte.split())


def detecter_trigger_words(commentaires: list[dict]) -> list[dict]:
    """
    Analyse la liste de commentaires d'une vidéo pour détecter
    les potentiels trigger words (campagnes ManyChat style).

    Retourne la liste des trigger words légitimes détectés.
    """
    if not commentaires:
        return []

    total = len(commentaires)
    auteurs_totaux = len({c["auteur"] for c in commentaires})

    # Compter les commentaires courts (≤ 3 mots)
    courts = [c for c in commentaires if _compter_mots(_nettoyer_texte(c["texte"])) <= config.TW_LONGUEUR_MAX_MOTS]

    # Compter les occurrences de chaque texte court normalisé
    compteur = Counter(_nettoyer_texte(c["texte"]) for c in courts)
    auteurs_par_texte = {}
    for c in courts:
        t = _nettoyer_texte(c["texte"])
        auteurs_par_texte.setdefault(t, set()).add(c["auteur"])

    trigger_words_detectes = []

    for texte, occurrences in compteur.items():
        if not texte:
            continue

        pourcentage = (occurrences / total) * 100
        nb_auteurs_uniques = len(auteurs_par_texte.get(texte, set()))
        ratio_uniques = nb_auteurs_uniques / occurrences if occurrences > 0 else 0

        # Critères de base
        if occurrences < config.TW_OCCURRENCES_MIN:
            continue
        if pourcentage < config.TW_POURCENTAGE_MIN:
            continue
        if ratio_uniques < config.TW_RATIO_UNIQUES:
            continue

        # Score de légitimité
        score_legitimite = _score_legitimite(texte, commentaires)

        logger.debug(
            f"Trigger word candidat '{texte}' | occurrences={occurrences} "
            f"({pourcentage:.1f}%) | légitimité={score_legitimite}"
        )

        if score_legitimite >= config.TW_SCORE_LEGITIME_MIN:
            trigger_words_detectes.append({
                "texte":           texte,
                "occurrences":     occurrences,
                "pourcentage":     round(pourcentage, 1),
                "score_legitimite": score_legitimite,
            })
            logger.info(f"✅ Trigger word légitime détecté : '{texte}' ({occurrences}x)")
        else:
            logger.info(f"❌ Faux trigger word ignoré : '{texte}' (légitimité={score_legitimite})")

    return trigger_words_detectes


def _score_legitimite(texte: str, commentaires: list[dict]) -> int:
    """
    Calcule le score de légitimité d'un trigger word candidat.
    Score élevé = c'est probablement une vraie campagne ManyChat.
    Score bas = c'est probablement un jeu de l'influenceur.
    """
    score = 0

    # Les commentaires qui entourent ce texte ont-ils du contexte ?
    # (présence d'autres mots normaux → +2)
    autres_commentaires = [
        c["texte"] for c in commentaires
        if _nettoyer_texte(c["texte"]) != texte
    ]
    if len(autres_commentaires) > 10:
        score += 2

    # Le texte contient-il des mots parasites ? → forte pénalité
    mots_texte = set(texte.split())
    if mots_texte & MOTS_PARASITES:
        score -= 5

    # Les commentaires autour mentionnent-ils des mots parasites ? → pénalité
    autres_lower = " ".join(autres_commentaires).lower()
    nb_parasites = sum(1 for m in MOTS_PARASITES if m in autres_lower)
    if nb_parasites >= 2:
        score -= 3

    # Le texte ressemble-t-il à un vrai mot d'action / produit ? → bonus
    if len(texte) >= 4 and texte.isalpha():
        score += 3

    return score


def filtrer_commentaires_trigger(commentaires: list[dict], trigger_words: list[dict]) -> list[dict]:
    """
    Retire les commentaires qui sont des réponses à un trigger word,
    pour ne pas les envoyer à Gemini (ce sont des prospects d'un autre type).
    On les garde séparément pour ne pas les scorer comme prospects normaux.
    """
    if not trigger_words:
        return commentaires

    textes_trigger = {tw["texte"] for tw in trigger_words}

    normaux = []
    for c in commentaires:
        texte_norm = _nettoyer_texte(c["texte"])
        if texte_norm in textes_trigger:
            c["est_trigger_word"] = True
        else:
            c["est_trigger_word"] = False
            normaux.append(c)

    return normaux
