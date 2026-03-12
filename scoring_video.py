import logging
from datetime import datetime, timedelta
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
    if hashtag_source in config.HASHTAGS:
        return 3
    return 1


def _score_engagement(nb_commentaires: int) -> int:
    if nb_commentaires >= 100:
        return 2
    if nb_commentaires >= 10:
        return 1
    return 0


def scorer_video(video: dict) -> dict:
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
    if score_min is None:
        score_min = config.SCORE_VIDEO_MIN

    # Filtre par score
    videos_scorees = [scorer_video(v) for v in videos]
    retenues = [v for v in videos_scorees if v["score_pertinence"] >= score_min]

    # Filtre par date — garder seulement les vidéos du dernier mois
    limite_date = datetime.now() - timedelta(days=30)
    limite_timestamp = limite_date.timestamp()
    avant_filtre_date = len(retenues)
    retenues = [
        v for v in retenues
        if v.get("createTime", 0) > limite_timestamp
    ]

    logger.info(
        f"Filtrage vidéos : {len(videos)} total → "
        f"{avant_filtre_date} après score → "
        f"{len(retenues)} après filtre date (30 jours)"
    )

    # Trier par score décroissant et limiter à 8
    retenues.sort(key=lambda v: v["score_pertinence"], reverse=True)
    retenues = retenues[:8]

    logger.info(f"→ {len(retenues)} vidéos retenues pour analyse des commentaires")
    return retenues
