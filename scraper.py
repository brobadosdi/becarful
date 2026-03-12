import asyncio
import random
import time
import logging
from TikTokApi import TikTokApi
import config

logger = logging.getLogger(__name__)

# ── User-agents rotatifs pour simuler différents appareils ────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def _delai_aleatoire():
    """Pause aléatoire entre les requêtes pour éviter le ban."""
    duree = random.uniform(config.DELAI_MIN_SEC, config.DELAI_MAX_SEC)
    logger.debug(f"Pause {duree:.1f}s")
    time.sleep(duree)


async def _get_videos_hashtag(api: TikTokApi, hashtag: str, count: int) -> list[dict]:
    """Récupère les vidéos récentes pour un hashtag donné."""
    videos = []
    try:
        tag = api.hashtag(name=hashtag)
        async for video in tag.videos(count=count):
            data = video.as_dict
            videos.append({
                "id":          data.get("id", ""),
                "description": data.get("desc", ""),
                "auteur":      data.get("author", {}).get("uniqueId", ""),
                "likes":       data.get("stats", {}).get("diggCount", 0),
                "commentaires_count": data.get("stats", {}).get("commentCount", 0),
                "hashtag_source": hashtag,
            })
        logger.info(f"#{hashtag} → {len(videos)} vidéos récupérées")
    except Exception as e:
        logger.error(f"Erreur scraping #{hashtag}: {e}")
    return videos


async def _get_commentaires_video(api: TikTokApi, video_id: str, count: int) -> list[dict]:
    """Récupère les commentaires d'une vidéo."""
    commentaires = []
    try:
        video = api.video(id=video_id)
        async for comment in video.comments(count=count):
            data = comment.as_dict
            commentaires.append({
                "id":       data.get("cid", ""),
                "texte":    data.get("text", ""),
                "auteur":   data.get("user", {}).get("uniqueId", ""),
                "likes":    data.get("digg_count", 0),
                "video_id": video_id,
            })
        logger.info(f"Vidéo {video_id} → {len(commentaires)} commentaires")
    except Exception as e:
        logger.error(f"Erreur commentaires vidéo {video_id}: {e}")
    return commentaires


async def scraper_hashtags(hashtags: list[str], videos_par_hashtag: int) -> list[dict]:
    """
    Point d'entrée principal.
    Retourne toutes les vidéos trouvées sur les hashtags ciblés.
    """
    ms_tokens = [config.TIKTOK_MS_TOKEN] if config.TIKTOK_MS_TOKEN else None

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=ms_tokens,
            num_sessions=1,
            sleep_after=3,
            headless=True,
            browser="webkit",
        )

        toutes_videos = []
        for hashtag in hashtags:
            videos = await _get_videos_hashtag(api, hashtag, videos_par_hashtag)
            toutes_videos.extend(videos)
            _delai_aleatoire()

    # Dédoublonnage par ID vidéo
    seen = set()
    uniques = []
    for v in toutes_videos:
        if v["id"] not in seen:
            seen.add(v["id"])
            uniques.append(v)

    logger.info(f"Total vidéos uniques : {len(uniques)}")
    return uniques


async def scraper_commentaires(api_instance, videos: list[dict], nb_commentaires: int) -> dict[str, list[dict]]:
    """
    Récupère les commentaires pour une liste de vidéos filtrées.
    Retourne un dict {video_id: [commentaires]}
    """
    resultats = {}

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[config.TIKTOK_MS_TOKEN] if config.TIKTOK_MS_TOKEN else None,
            num_sessions=1,
            sleep_after=3,
            headless=True,
            browser="webkit",
        )

        for video in videos:
            vid_id = video["id"]
            commentaires = await _get_commentaires_video(api, vid_id, nb_commentaires)
            resultats[vid_id] = commentaires
            _delai_aleatoire()

    return resultats


def run_scraper_hashtags(hashtags: list[str], videos_par_hashtag: int) -> list[dict]:
    """Wrapper synchrone pour l'appel depuis main.py."""
    return asyncio.run(scraper_hashtags(hashtags, videos_par_hashtag))


def run_scraper_commentaires(videos: list[dict], nb_commentaires: int) -> dict[str, list[dict]]:
    """Wrapper synchrone pour l'appel depuis main.py."""
    return asyncio.run(scraper_commentaires(None, videos, nb_commentaires))
