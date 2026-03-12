import requests
import logging
import config

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}"


def _echapper(texte: str) -> str:
    """Échappe les caractères spéciaux Markdown Telegram."""
    for char in ["_", "*", "[", "]", "`"]:
        texte = texte.replace(char, f"\\{char}")
    return texte


def _envoyer_message(texte: str) -> bool:
    """Envoie un message texte sur Telegram."""
    try:
        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id":    config.TELEGRAM_CHAT_ID,
                "text":       texte,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Telegram erreur {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Erreur envoi Telegram : {e}")
        return False


def alerter_prospect(prospect: dict, video: dict) -> bool:
    """Envoie une alerte Telegram pour un prospect détecté."""
    score    = prospect.get("score_ia", 0)
    type_ia  = prospect.get("type_ia", "")
    raison   = _echapper(prospect.get("raison_ia", ""))
    auteur   = _echapper(prospect.get("auteur", "inconnu"))
    texte_commentaire = _echapper(prospect.get("texte", ""))
    video_id  = video.get("id", "")
    video_desc = _echapper(video.get("description", "")[:80])

    # Emoji selon le score
    if score >= 9:
        emoji = "🔥🔥"
    elif score >= 8:
        emoji = "🔥"
    else:
        emoji = "⚡"

    # Type lisible
    types_labels = {
        "besoin":       "💡 Besoin concret",
        "blocage":      "😰 Blocage / Honte",
        "frustration":  "😤 Frustration",
        "desir":        "✨ Désir de progresser",
        "demande_aide": "🙋 Demande d'aide",
    }
    type_label = types_labels.get(type_ia, "👤 Prospect")

    message = (
        f"{emoji} *PROSPECT DÉTECTÉ — Score {score}/10*\n\n"
        f"{type_label}\n\n"
        f"👤 *Profil :* @{auteur}\n"
        f"🔗 *Profil TikTok :* https://www.tiktok.com/@{auteur}\n\n"
        f"💬 *Commentaire :*\n"
        f"_{texte_commentaire}_\n\n"
        f"🧠 *Analyse IA :* {raison}\n\n"
        f"📹 *Vidéo :* {video_desc}...\n"
        f"🔗 https://www.tiktok.com/video/{video_id}\n\n"
        f"─────────────────\n"
        f"👉 *ACTION :* Ouvre BlueStacks et envoie un DM à @{auteur}"
    )

    succes = _envoyer_message(message)
    if succes:
        logger.info(f"✅ Alerte Telegram envoyée pour @{auteur} (score={score})")
    return succes


def alerter_resume(stats: dict) -> bool:
    """Envoie un résumé du cycle d'analyse sur Telegram."""
    message = (
        f"📊 *Résumé du cycle*\n\n"
        f"🎬 Vidéos analysées : {stats.get('videos_analysees', 0)}\n"
        f"💬 Commentaires analysés : {stats.get('commentaires_analyses', 0)}\n"
        f"🎯 Prospects détectés : {stats.get('prospects_detectes', 0)}\n"
        f"🔑 Trigger words : {stats.get('trigger_words', 0)}\n\n"
        f"⏱ Prochain cycle dans 2h"
    )
    return _envoyer_message(message)


def alerter_erreur(erreur: str) -> bool:
    """Alerte en cas d'erreur critique dans le script."""
    erreur_propre = _echapper(erreur[:300])
    message = f"⚠️ *Erreur script TikTok*\n\n{erreur_propre}"
    return _envoyer_message(message)
