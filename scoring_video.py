import logging
import config

logger = logging.getLogger(__name__)


def _score_description(description: str) -> int:
    """+2 par mot-clé trouvé dans la description."""
    desc_lower = description.lower()
    score = 0
    for mot in config.MOTS_CLES_VIDEO:
        if mot in desc_lower:
            score += 2
    return score


def _score_hashtag(hashtag_source: str) -> int:
    """
    +3 si le hashtag source est dans notre liste ciblée.
    On l'a forcément scrappé depuis nos hashtags → toujours +3.
    """
    if hashtag_source in config.HASHTAGS:
        return 3
    return 1


def _score_engagement(nb_commentaires: int) -> int:
    """
    +1 si la vidéo a au moins 10 commentaires (signe d'engagement).
    +2 si plus de 100 commentaires.
    """
    if nb_commentaires >= 100:
        return 2
    if nb_commentaires >= 10:
        return 1
    return 0


def scorer_video(video: dict) -> dict:
    """
    Calcule le score de pertinence d'une vidéo.
    Retourne la vidéo enrichie avec son score et le détail.
    """
    s_hashtag     = _score_hashtag(video.get("hashtag_source", ""))
    s_description = _score_description(video.get("description", ""))
    s_engagement  = _score_engagement(video.get("commentaires_count", 0))

    score_total = s_hashtag + s_description + s_engagement

    video["score_pertinence"] = score_total
    video["score_detail"] = {
        "hashtag":     s_hashtag,
        "description": s_description,
        "engagement":  s_engagement,
    }

    logger.debug(
        f"Vidéo {video['id']} | score={score_total} "
        f"(hashtag={s_hashtag}, desc={s_description}, engagement={s_engagement})"
    )

    return video


def filtrer_videos(videos: list[dict], score_min: int = None) -> list[dict]:
    """
    Score toutes les vidéos et garde uniquement celles au-dessus du seuil.
    """
    if score_min is None:
        score_min = config.SCORE_VIDEO_MIN

    videos_scorees = [scorer_video(v) for v in videos]
    retenues = [v for v in videos_scorees if v["score_pertinence"] >= score_min]

    logger.info(
        f"Filtrage vidéos : {len(videos)} total → {len(retenues)} retenues "
        f"(seuil score >= {score_min})"
    )

    # Trier par score décroissant
    retenues.sort(key=lambda v: v["score_pertinence"], reverse=True)
    return retenues
