import requests
import logging
import config

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}"


def _envoyer_message(texte: str) -> bool:
    """Envoie un message texte sur Telegram."""
    try:
        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id":    config.TELEGRAM_CHAT_ID,
                "text":       texte,
                "parse_mode": "HTML",
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
    """
    Envoie une alerte Telegram pour un prospect détecté.
    """
    score    = prospect.get("score_ia", 0)
    type_ia  = prospect.get("type_ia", "")
    raison   = prospect.get("raison_ia", "")
    auteur   = prospect.get("auteur", "inconnu")
    texte_commentaire = prospect.get("texte", "")
    video_id = video.get("id", "")
    video_desc = video.get("description", "")[:80]

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

    message = f"""{emoji} <b>PROSPECT DÉTECTÉ — Score {score}/10</b>

{type_label}

👤 <b>Profil :</b> @{auteur}
🔗 <b>Profil TikTok :</b> https://www.tiktok.com/@{auteur}

💬 <b>Commentaire :</b>
<i>"{texte_commentaire}"</i>

🧠 <b>Analyse IA :</b> {raison}

📹 <b>Vidéo :</b> {video_desc}...
🔗 https://www.tiktok.com/video/{video_id}

─────────────────
👉 <b>ACTION :</b> Ouvre BlueStacks et envoie un DM à @{auteur}"""

    succes = _envoyer_message(message)
    if succes:
        logger.info(f"✅ Alerte Telegram envoyée pour @{auteur} (score={score})")
    return succes


def alerter_resume(stats: dict) -> bool:
    """
    Envoie un résumé du cycle d'analyse sur Telegram.
    """
    message = f"""📊 <b>Résumé du cycle</b>

🎬 Vidéos analysées : {stats.get('videos_analysees', 0)}
💬 Commentaires analysés : {stats.get('commentaires_analyses', 0)}
🎯 Prospects détectés : {stats.get('prospects_detectes', 0)}
🔑 Trigger words : {stats.get('trigger_words', 0)}

⏱ Prochain cycle dans 2h"""

    return _envoyer_message(message)


def alerter_erreur(erreur: str) -> bool:
    """Alerte en cas d'erreur critique dans le script."""
    message = f"⚠️ <b>Erreur script TikTok</b>\n\n{erreur}"
    return _envoyer_message(message)
