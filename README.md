# 🎯 TikTok Prospection — Veebly

Script de détection automatique de prospects sur TikTok pour Veebly (école d'anglais en ligne).

## Comment ça marche

1. GitHub Actions lance le script toutes les 2h
2. Le script scrape les hashtags TikTok ciblés
3. Filtre les vidéos pertinentes par score
4. Récupère les commentaires
5. Analyse les commentaires avec Gemini Flash
6. Envoie une alerte Telegram pour chaque prospect (score ≥ 7)
7. Log le prospect dans Google Sheets

## Structure des fichiers

```
├── main.py              # Orchestrateur principal
├── config.py            # Configuration et constantes
├── scraper.py           # Scraping TikTok
├── scoring_video.py     # Score de pertinence des vidéos
├── trigger_words.py     # Détection des trigger words ManyChat
├── analyse_ia.py        # Analyse Gemini Flash
├── telegram_alert.py    # Alertes Telegram
├── sheets_logger.py     # Logging Google Sheets
├── requirements.txt     # Dépendances Python
└── .github/
    └── workflows/
        └── main.yml     # GitHub Actions (toutes les 2h)
```

## Secrets GitHub requis

| Nom | Description |
|-----|-------------|
| `GEMINI_API_KEY` | Clé API Google Gemini |
| `TELEGRAM_TOKEN` | Token du bot Telegram |
| `TELEGRAM_CHAT_ID` | Ton Chat ID Telegram |
| `GOOGLE_SHEETS_ID` | ID du Google Sheet |
| `GOOGLE_CREDENTIALS` | Contenu JSON du compte de service |

## Lancer manuellement

Dans GitHub → Actions → "TikTok Prospection" → "Run workflow"
