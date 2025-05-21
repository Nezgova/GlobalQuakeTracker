# config.py - Version optimisée
import os
from dotenv import load_dotenv
from typing import Dict, Any, List

# Charge les variables depuis .env
load_dotenv()

# Configuration de base pour Gemini
GEMINI_CONFIG: Dict[str, Any] = {
    "api_key": os.getenv("GEMINI_API_KEY", ""),  # Clé API sécurisée
    "generation_config": {
        "temperature": 0.5,  # Réduit pour plus de précision
        "top_p": 0.9,
        "top_k": 20,
        "max_output_tokens": 500,  # Optimisé pour les réponses courtes
        "stop_sequences": ["\n\n"]  # Pour éviter les réponses trop longues
    },
    "safety_settings": [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    ],
    "default_models": [  # Modèles par ordre de priorité
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "models/gemini-pro"
    ],
    "api_version": "v1beta" if os.getenv("ENV") == "dev" else "v1",  # Version adaptative
    "timeout": 15  # Timeout en secondes pour les requêtes API
}

# Configuration spécifique pour les urgences
EMERGENCY_CONFIG = {
    "max_retries": 3,
    "cache_ttl": 3600  # Durée de vie du cache en secondes (1h)
}