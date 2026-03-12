import asyncio
import random
import time
import logging
from TikTokApi import TikTokApi
import config

logger = logging.getLogger(__name__)

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)

SESSION_OPTIONS = {
    "viewport": {"width": 390, "height": 844},
    "user_agent": MOBILE_UA,
}


def _delai_aleatoire(min_sec=8, max_sec=20):
    """Pause aléatoire pour simuler un comportement humain."""
    duree = random.uniform(min_sec, max_sec)
    logger.debug(f"Pause {duree:.1f}s")
    time.sleep(duree)


async def _get_videos_hashtag(api: TikTokApi, hashtag: str, count: int) -> list[dict]:
    videos = []
    try:
        tag = api.hashtag(name=hashtag)
        async for video in tag.videos(count=count):
            data = video.as_dict
            videos.append({
                "id":                 data.get("id", ""),
                "description":        data.get("desc", ""),
                "auteur":             data.get("author", {}).get("uniqueId", ""),
                "likes":              data.get("stats", {}).get("diggCount", 0),
                "commentaires_count": data.get("stats", {}).get("commentCount", 0),
                "createTime":         data.get("createTime", 0),
                "hashtag_source":     hashtag,
            })
        logger.info(f"#{hashtag} → {len(videos)} vidéos récupérées")
    except Exception as e:
        logger.error(f"Erreur scraping #{hashtag}: {e}")
    return videos


async def _get_commentaires_video(api: TikTokApi, video_id: str, count: int) -> list[dict]:
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
            # Pause humaine entre chaque commentaire lu
            await asyncio.sleep(random.uniform(0.5, 1.5))
        logger.info(f"Vidéo {video_id} → {len(commentaires)} commentaires")
    except Exception as e:
        logger.error(f"Erreur commentaires vidéo {video_id}: {e}")
    return commentaires


async def scraper_complet(
    hashtags: list[str],
    videos_par_hashtag: int,
    videos_retenues: list[dict],
    nb_commentaires: int,
) -> tuple[list[dict], dict[str, list[dict]]]:
    """
    Fait tout en UNE SEULE session TikTok :
    1. Scrape les hashtags
    2. Récupère les commentaires des vidéos retenues
    Retourne (toutes_videos, commentaires_par_video)
    """
    ms_tokens = [config.TIKTOK_MS_TOKEN] if config.TIKTOK_MS_TOKEN else None

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=ms_tokens,
            num_sessions=1,
            sleep_after=8,
            headless=True,
            browser="webkit",
            context_options=SESSION_OPTIONS,
        )

        # ── Phase 1 : Scraping des hashtags ──────────────────────────────────
        toutes_videos = []
        for hashtag in hashtags:
            videos = await _get_videos_hashtag(api, hashtag, videos_par_hashtag)
            toutes_videos.extend(videos)
            _delai_aleatoire(8, 20)

        # Dédoublonnage
        seen = set()
        uniques = []
        for v in toutes_videos:
            if v["id"] not in seen:
                seen.add(v["id"])
                uniques.append(v)
        logger.info(f"Total vidéos uniques : {len(uniques)}")

        # ── Phase 2 : Commentaires des vidéos retenues ────────────────────────
        commentaires_par_video = {}

        if videos_retenues:
            logger.info(f"Récupération commentaires pour {len(videos_retenues)} vidéos...")
            # Pause plus longue avant de changer d'activité (comme un humain)
            _delai_aleatoire(15, 30)

            for video in videos_retenues:
                vid_id = video["id"]
                commentaires = await _get_commentaires_video(api, vid_id, nb_commentaires)
                commentaires_par_video[vid_id] = commentaires
                _delai_aleatoire(10, 25)

    return uniques, commentaires_par_video


def run_scraper_phase1(hashtags: list[str], videos_par_hashtag: int) -> list[dict]:
    """Phase 1 seulement — scrape les hashtags."""
    async def _run():
        ms_tokens = [config.TIKTOK_MS_TOKEN] if config.TIKTOK_MS_TOKEN else None
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=ms_tokens,
                num_sessions=1,
                sleep_after=8,
                headless=True,
                browser="webkit",
                context_options=SESSION_OPTIONS,
            )
            toutes_videos = []
            for hashtag in hashtags:
                videos = await _get_videos_hashtag(api, hashtag, videos_par_hashtag)
                toutes_videos.extend(videos)
                _delai_aleatoire(8, 20)

            seen = set()
            uniques = []
            for v in toutes_videos:
                if v["id"] not in seen:
                    seen.add(v["id"])
                    uniques.append(v)
            logger.info(f"Total vidéos uniques : {len(uniques)}")
            return uniques

    return asyncio.run(_run())


def run_scraper_phase2(videos_retenues: list[dict], nb_commentaires: int) -> dict[str, list[dict]]:
    """Phase 2 seulement — récupère les commentaires."""
    async def _run():
        ms_tokens = [config.TIKTOK_MS_TOKEN] if config.TIKTOK_MS_TOKEN else None
        commentaires_par_video = {}
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=ms_tokens,
                num_sessions=1,
                sleep_after=8,
                headless=True,
                browser="webkit",
                context_options=SESSION_OPTIONS,
            )
            _delai_aleatoire(15, 30)
            for video in videos_retenues:
                vid_id = video["id"]
                commentaires = await _get_commentaires_video(api, vid_id, nb_commentaires)
                commentaires_par_video[vid_id] = commentaires
                _delai_aleatoire(10, 25)
        return commentaires_par_video

    return asyncio.run(_run())
