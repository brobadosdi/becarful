import json
import logging
import time
import google.generativeai as genai
import config

logger = logging.getLogger(__name__)

# Initialisation du client Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=config.PROMPT_SYSTEME,
)


def _construire_batch(commentaires: list[dict]) -> str:
    """Formate un batch de commentaires pour l'envoi à Gemini."""
    lignes = []
    for i, c in enumerate(commentaires):
        lignes.append(f"{i+1}. [ID:{c['id']}] {c['texte']}")
    return "\n".join(lignes)


def _parser_reponse(reponse_texte: str, commentaires: list[dict]) -> list[dict]:
    """
    Parse la réponse JSON de Gemini.
    Gemini retourne un tableau JSON, un objet par commentaire.
    """
    resultats = []

    try:
        # Nettoyage : retirer les backticks markdown si présents
        texte = reponse_texte.strip()
        if texte.startswith("```"):
            texte = texte.split("\n", 1)[1]
            texte = texte.rsplit("```", 1)[0]

        parsed = json.loads(texte)

        if isinstance(parsed, list):
            for i, item in enumerate(parsed):
                if i >= len(commentaires):
                    break
                commentaire = commentaires[i].copy()
                commentaire.update({
                    "est_prospect":  item.get("est_prospect", False),
                    "score_ia":      item.get("score", 0),
                    "raison_ia":     item.get("raison", ""),
                    "type_ia":       item.get("type", ""),
                })
                resultats.append(commentaire)
        else:
            logger.warning("Réponse Gemini inattendue (pas une liste)")
            resultats = _fallback_non_prospect(commentaires)

    except json.JSONDecodeError as e:
        logger.error(f"Erreur parsing JSON Gemini : {e}")
        logger.debug(f"Réponse brute : {reponse_texte[:500]}")
        resultats = _fallback_non_prospect(commentaires)

    return resultats


def _fallback_non_prospect(commentaires: list[dict]) -> list[dict]:
    """En cas d'erreur, marque tous les commentaires comme non-prospects."""
    return [
        {**c, "est_prospect": False, "score_ia": 0, "raison_ia": "erreur_analyse", "type_ia": "faux_positif"}
        for c in commentaires
    ]


def analyser_batch(commentaires: list[dict]) -> list[dict]:
    """
    Envoie un batch de commentaires à Gemini et retourne les résultats analysés.
    """
    if not commentaires:
        return []

    prompt = f"""Analyse ces {len(commentaires)} commentaires TikTok et retourne un tableau JSON.
Le tableau doit contenir exactement {len(commentaires)} objets dans le même ordre.
Chaque objet doit avoir : est_prospect, score, raison, type.

Commentaires :
{_construire_batch(commentaires)}

Retourne UNIQUEMENT le tableau JSON, sans texte avant ou après."""

    try:
        response = model.generate_content(prompt)
        resultats = _parser_reponse(response.text, commentaires)
        logger.info(f"Batch de {len(commentaires)} analysé → {sum(1 for r in resultats if r.get('est_prospect'))} prospects")
        return resultats

    except Exception as e:
        logger.error(f"Erreur appel Gemini : {e}")
        time.sleep(5)  # Pause avant retry
        return _fallback_non_prospect(commentaires)


def analyser_tous_commentaires(commentaires: list[dict]) -> list[dict]:
    """
    Analyse tous les commentaires en les découpant en batches.
    Retourne uniquement les prospects (score >= seuil).
    """
    if not commentaires:
        return []

    taille_batch = config.BATCH_COMMENTAIRES
    tous_resultats = []

    # Découpage en batches
    for i in range(0, len(commentaires), taille_batch):
        batch = commentaires[i:i + taille_batch]
        logger.info(f"Envoi batch {i//taille_batch + 1} ({len(batch)} commentaires)")
        resultats = analyser_batch(batch)
        tous_resultats.extend(resultats)
        time.sleep(2)  # Petite pause entre les batches

    # Filtrer uniquement les prospects avec score suffisant
    prospects = [
        r for r in tous_resultats
        if r.get("est_prospect") and r.get("score_ia", 0) >= config.SCORE_PROSPECT_MIN
    ]

    logger.info(
        f"Analyse complète : {len(commentaires)} commentaires → "
        f"{len(prospects)} prospects (score >= {config.SCORE_PROSPECT_MIN})"
    )

    # Trier par score décroissant
    prospects.sort(key=lambda x: x.get("score_ia", 0), reverse=True)
    return prospects
