import os

# ── Credentials (injectés depuis GitHub Secrets) ──────────────────────────────
GEMINI_API_KEY       = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_TOKEN       = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID     = os.environ.get("TELEGRAM_CHAT_ID", "")
GOOGLE_SHEETS_ID     = os.environ.get("GOOGLE_SHEETS_ID", "")
GOOGLE_CREDENTIALS   = os.environ.get("GOOGLE_CREDENTIALS", "")   # JSON brut

# ── Hashtags TikTok à surveiller ──────────────────────────────────────────────
HASHTAGS = [
    "apprendreanglais",
    "anglaisfacile",
    "coursdanglais",
    "apprendrelangues",
    "anglaisdebutant",
    "bilingue",
    "niveauanglais",
    "parleranglais",
    "learnfrench",
    "frenchwithaccent",
]

# ── Mots-clés pour scorer les vidéos (sans IA, local) ────────────────────────
MOTS_CLES_VIDEO = [
    "anglais", "english", "apprendre", "cours", "langue",
    "bilingue", "accent", "grammaire", "vocabulaire", "fluent",
    "parler", "comprendre", "débutant", "niveau", "progrès",
]

# ── Seuils de score ───────────────────────────────────────────────────────────
SCORE_VIDEO_MIN       = 5     # Score minimum pour analyser une vidéo
SCORE_PROSPECT_MIN    = 7     # Score minimum pour alerter sur un commentaire

# ── Paramètres de scraping ────────────────────────────────────────────────────
VIDEOS_PAR_HASHTAG    = 5     # Nombre de vidéos récupérées par hashtag
COMMENTAIRES_PAR_VIDEO = 50   # Nombre de commentaires récupérés par vidéo
BATCH_COMMENTAIRES    = 50    # Taille du batch envoyé à Gemini
DELAI_MIN_SEC         = 4     # Délai minimum entre requêtes (secondes)
DELAI_MAX_SEC         = 12    # Délai maximum entre requêtes (secondes)

# ── Détection trigger words ───────────────────────────────────────────────────
TW_OCCURRENCES_MIN    = 15
TW_POURCENTAGE_MIN    = 10    # % minimum des commentaires
TW_LONGUEUR_MAX_MOTS  = 3     # Longueur max d'un commentaire trigger
TW_RATIO_UNIQUES      = 0.8   # 80% de personnes différentes
TW_SCORE_LEGITIME_MIN = 4     # Score de légitimité minimum

# ── Prompt Gemini ─────────────────────────────────────────────────────────────
PROMPT_SYSTEME = """
Tu es un expert en détection de prospects pour Veebly, une école d'anglais en ligne.
Veebly propose des cours 1-to-1 avec des professeurs natifs, en ligne, flexibles et abordables.

Pour chaque commentaire, détecte si la personne est un prospect chaud : quelqu'un qui montre
une douleur, un blocage, un désir ou un besoin concret lié à l'apprentissage de l'anglais.

Exemples de prospects chauds :
- Douleur : "je comprends rien", "mon accent est nul", "j'arrive pas à parler"
- Blocage : "j'ose pas parler", "j'ai honte", "je freeze quand je dois répondre"
- Désir : "j'aimerais être bilingue", "je veux parler couramment", "j'veux progresser"
- Besoin concret : "pour mon boulot", "pour voyager", "pour mes études à l'étranger"
- Frustration : "ça fait des années que j'apprends et je progresse pas"
- Demande d'aide : "quelqu'un a une bonne méthode ?", "comment vous avez appris ?"

Exemples de NON-prospects :
- Déjà bilingue ou anglophone
- Commentaire hors sujet
- Simple emoji ou réaction
- Spam ou pub
- Trigger word (commentaire d'un seul mot en réponse à une consigne de la vidéo)

Pour chaque commentaire retourne UNIQUEMENT ce JSON (rien d'autre) :
{
  "est_prospect": true ou false,
  "score": nombre entier de 0 à 10,
  "raison": "explication courte en français",
  "type": "besoin" ou "blocage" ou "frustration" ou "desir" ou "demande_aide" ou "faux_positif"
}
""".strip()
