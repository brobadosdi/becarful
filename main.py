import logging
import sys
import time
import random
from datetime import datetime

import config
import scraper
import scoring_video
import trigger_words
import analyse_ia
import telegram_alert
import sheets_logger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")


def verifier_config():
    requis = [
        ("GEMINI_API_KEY",     config.GEMINI_API_KEY),
        ("TELEGRAM_TOKEN",     config.TELEGRAM_TOKEN),
        ("TELEGRAM_CHAT_ID",   config.TELEGRAM_CHAT_ID),
        ("GOOGLE_SHEETS_ID",   config.GOOGLE_SHEETS_ID),
        ("GOOGLE_CREDENTIALS", config.GOOGLE_CREDENTIALS),
    ]
    manquants = [nom for nom, val in requis if not val]
    if manquants:
        raise EnvironmentError(f"Variables manquantes : {', '.join(manquants)}")
    logger.info("✅ Configuration vérifiée")


def run():
    debut = datetime.now()
    logger.info("=" * 60)
    logger.info(f"🚀 Démarrage cycle — {debut.strftime('%d/%m/%Y %H:%M')}")
    logger.info("=" * 60)

    stats = {
        "videos_analysees":      0,
        "commentaires_analyses": 0,
        "prospects_detectes":    0,
        "trigger_words":         0,
    }

    try:
        verifier_config()

        # ── ÉTAPE 1 : Scraping des hashtags ───────────────────────────────────
        logger.info("📡 ÉTAPE 1 — Scraping des hashtags...")
        toutes_videos = scraper.run_scraper_phase1(
            hashtags=config.HASHTAGS,
            videos_par_hashtag=config.VIDEOS_PAR_HASHTAG,
        )
        logger.info(f"→ {len(toutes_videos)} vidéos brutes récupérées")

        if not toutes_videos:
            logger.warning("Aucune vidéo trouvée. Fin du cycle.")
            return

        # ── ÉTAPE 2 : Filtrage des vidéos par score + date ────────────────────
        logger.info("🎯 ÉTAPE 2 — Filtrage des vidéos...")
        videos_retenues = scoring_video.filtrer_videos(toutes_videos)
        stats["videos_analysees"] = len(videos_retenues)
        logger.info(f"→ {len(videos_retenues)} vidéos retenues pour analyse")

        if not videos_retenues:
            logger.warning("Aucune vidéo pertinente. Fin du cycle.")
            return

        # ── PAUSE ANTI-DÉTECTION ──────────────────────────────────────────────
        pause = random.uniform(90, 150)
        logger.info(f"⏸️  Pause anti-détection avant commentaires : {pause:.0f}s...")
        time.sleep(pause)

        # ── ÉTAPE 3 : Récupération des commentaires ───────────────────────────
        logger.info("💬 ÉTAPE 3 — Récupération des commentaires...")
        commentaires_par_video = scraper.run_scraper_phase2(
            videos_retenues=videos_retenues,
            nb_commentaires=config.COMMENTAIRES_PAR_VIDEO,
        )

        # ── ÉTAPE 4 : Détection trigger words + filtrage ──────────────────────
        logger.info("🔍 ÉTAPE 4 — Détection des trigger words...")
        tous_commentaires_nets = []
        video_par_id = {v["id"]: v for v in videos_retenues}

        for video_id, commentaires in commentaires_par_video.items():
            if not commentaires:
                continue
            tws = trigger_words.detecter_trigger_words(commentaires)
            if tws:
                stats["trigger_words"] += len(tws)
                logger.info(f"Vidéo {video_id} → {len(tws)} trigger word(s) détecté(s)")

            commentaires_nets = trigger_words.filtrer_commentaires_trigger(commentaires, tws)
            for c in commentaires_nets:
                c["video_id"] = video_id
            tous_commentaires_nets.extend(commentaires_nets)

        stats["commentaires_analyses"] = len(tous_commentaires_nets)
        logger.info(f"→ {len(tous_commentaires_nets)} commentaires nets à analyser")

        if not tous_commentaires_nets:
            logger.warning("Aucun commentaire à analyser.")
            telegram_alert.alerter_resume(stats)
            return

        # ── ÉTAPE 5 : Analyse IA (Gemini Flash) ──────────────────────────────
        logger.info("🤖 ÉTAPE 5 — Analyse IA des commentaires...")
        prospects = analyse_ia.analyser_tous_commentaires(tous_commentaires_nets)
        stats["prospects_detectes"] = len(prospects)

        # ── ÉTAPE 6 : Alertes + logging ───────────────────────────────────────
        logger.info(f"📣 ÉTAPE 6 — Envoi alertes ({len(prospects)} prospects)...")
        for prospect in prospects:
            video_id = prospect.get("video_id", "")
            video    = video_par_id.get(video_id, {})
            telegram_alert.alerter_prospect(prospect, video)
            sheets_logger.logger_prospect(prospect, video)

        telegram_alert.alerter_resume(stats)

        duree = (datetime.now() - debut).seconds
        logger.info("=" * 60)
        logger.info(f"✅ Cycle terminé en {duree}s")
        logger.info(
            f"   Vidéos : {stats['videos_analysees']} | "
            f"Commentaires : {stats['commentaires_analyses']} | "
            f"Prospects : {stats['prospects_detectes']}"
        )
        logger.info("=" * 60)

    except EnvironmentError as e:
        logger.critical(f"❌ Erreur de configuration : {e}")
        telegram_alert.alerter_erreur(str(e))
        sys.exit(1)

    except Exception as e:
        logger.critical(f"❌ Erreur inattendue : {e}", exc_info=True)
        telegram_alert.alerter_erreur(f"Erreur inattendue : {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
