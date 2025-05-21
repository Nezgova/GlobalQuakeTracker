# config.py - Version corrigée
import os
from dotenv import load_dotenv

# Charge les variables depuis .env
load_dotenv()

GEMINI_CONFIG = {
    "api_key": os.getenv("GEMINI_API_KEY", ""),  # Sécurisé via .env
    "generation_config": {
        "temperature": 0.7,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 1000,  # Réduit pour économiser les quotas
    },
    "safety_settings": [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        # ... autres paramètres
    ],
    "model_name": "gemini-1.5-pro",
    "api_version": "v1"  # Ajout explicite
}