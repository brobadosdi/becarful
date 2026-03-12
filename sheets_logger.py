import json
import logging
import tempfile
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import config

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# En-têtes des colonnes dans Google Sheets
HEADERS = [
    "Date",
    "Heure",
    "Auteur TikTok",
    "Lien Profil",
    "Commentaire",
    "Score IA",
    "Type",
    "Raison IA",
    "Vidéo ID",
    "Lien Vidéo",
    "Hashtag Source",
    "Statut DM",
]


def _get_client() -> gspread.Client:
    """Crée le client Google Sheets depuis les credentials en variable d'env."""
    creds_json = config.GOOGLE_CREDENTIALS

    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS est vide")

    # Écrire le JSON dans un fichier temporaire
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(creds_json)
        tmp_path = f.name

    try:
        creds = Credentials.from_service_account_file(tmp_path, scopes=SCOPES)
        client = gspread.authorize(creds)
    finally:
        os.unlink(tmp_path)

    return client


def _get_ou_creer_feuille(client: gspread.Client) -> gspread.Worksheet:
    """Ouvre le Google Sheet et initialise les en-têtes si vide."""
    sheet = client.open_by_key(config.GOOGLE_SHEETS_ID)
    worksheet = sheet.sheet1

    # Si la feuille est vide, ajouter les en-têtes
    if worksheet.row_count == 0 or not worksheet.row_values(1):
        worksheet.append_row(HEADERS)
        logger.info("En-têtes Google Sheets initialisés")

    return worksheet


def logger_prospect(prospect: dict, video: dict) -> bool:
    """
    Enregistre un prospect dans Google Sheets.
    """
    try:
        client    = _get_client()
        worksheet = _get_ou_creer_feuille(client)

        maintenant = datetime.now()
        auteur     = prospect.get("auteur", "")
        video_id   = video.get("id", "")

        ligne = [
            maintenant.strftime("%d/%m/%Y"),
            maintenant.strftime("%H:%M"),
            f"@{auteur}",
            f"https://www.tiktok.com/@{auteur}",
            prospect.get("texte", ""),
            prospect.get("score_ia", 0),
            prospect.get("type_ia", ""),
            prospect.get("raison_ia", ""),
            video_id,
            f"https://www.tiktok.com/video/{video_id}",
            video.get("hashtag_source", ""),
            "À contacter",  # Statut DM initial
        ]

        worksheet.append_row(ligne)
        logger.info(f"✅ Prospect @{auteur} loggé dans Google Sheets")
        return True

    except Exception as e:
        logger.error(f"Erreur Google Sheets : {e}")
        return False


def marquer_dm_envoye(auteur: str) -> bool:
    """
    Met à jour le statut DM d'un prospect dans Google Sheets.
    (Optionnel, peut être fait manuellement)
    """
    try:
        client    = _get_client()
        worksheet = _get_ou_creer_feuille(client)

        # Chercher la ligne avec cet auteur
        cellules = worksheet.findall(f"@{auteur}")
        for cellule in cellules:
            worksheet.update_cell(cellule.row, HEADERS.index("Statut DM") + 1, "DM envoyé ✅")

        return True
    except Exception as e:
        logger.error(f"Erreur mise à jour Sheets : {e}")
        return False
