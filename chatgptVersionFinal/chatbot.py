# chatbot.py - Version optimisée avec gestion améliorée des erreurs et cache
import logging
from functools import lru_cache
from typing import Optional
import google.generativeai as genai
from emergency_data import DISASTER_KEYWORDS, EMERGENCY_PROTOCOLS
from config import GEMINI_CONFIG

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DisasterChatbot:
    def __init__(self):
        """Initialise le chatbot avec configuration Gemini et cache"""
        self.convo = None
        self._cache = {}  # Cache simple pour les requêtes fréquentes
        self._configure_gemini()
        logger.info("Chatbot initialisé")

    def _configure_gemini(self) -> None:
        """Configure la connexion à l'API Gemini avec prioritisation"""
        MODELES_PRIORITAIRES = [
            "models/gemini-1.5-flash",  # Modèle le plus économique
            "models/gemini-1.5-pro",    # Alternative plus puissante
            "models/gemini-pro"         # Ancienne version
        ]

        try:
            if not GEMINI_CONFIG["api_key"]:
                raise ValueError("Clé API manquante dans la configuration")

            genai.configure(
                api_key=GEMINI_CONFIG["api_key"],
                transport='rest',
                client_options={
                    'api_endpoint': 'generativelanguage.googleapis.com'
                }
            )

            for nom in MODELES_PRIORITAIRES:
                try:
                    self.model = genai.GenerativeModel(
                        model_name=nom,
                        generation_config=GEMINI_CONFIG["generation_config"],
                        safety_settings=GEMINI_CONFIG["safety_settings"]
                    )
                    self.convo = self.model.start_chat(history=[])
                    logger.info(f"Connexion réussie avec le modèle : {nom}")
                    break
                except Exception as e:
                    logger.warning(f"Échec avec le modèle {nom} : {e}")

            if not self.convo:
                raise RuntimeError("Aucun modèle Gemini n'a pu être initialisé.")

        except Exception as e:
            logger.error(f"Erreur configuration Gemini: {str(e)}")
            self.convo = None

    def _is_disaster_related(self, text: str) -> bool:
        """Vérifie si le texte contient des mots-clés de catastrophe"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in DISASTER_KEYWORDS)

    @lru_cache(maxsize=100)
    def _get_local_protocol(self, question: str) -> Optional[str]:
        """Retourne le protocole local si une catastrophe est détectée (avec cache)"""
        question_lower = question.lower()
        for disaster, protocol in EMERGENCY_PROTOCOLS.items():
            if disaster.lower() in question_lower:
                return (
                    f"🔴 {disaster.upper()} 🔴\n\n"
                    f"{protocol['description']}\n\n"
                    "ACTIONS RECOMMANDÉES:\n- " +
                    "\n- ".join(protocol['actions']) +
                    f"\n\n📞 Numéro d'urgence: {protocol['numéro_urgence']}"
                )
        return None

    def generate_response(self, user_input: str) -> str:
        """Génère toujours une réponse str, jamais None"""
        # 1. Vérifier d'abord le cache
        if user_input in self._cache:
            logger.info("Réponse servie depuis le cache")
            return self._cache[user_input]

        # 2. Vérifier les protocoles locaux
        local_response = self._get_local_protocol(user_input)
        if local_response:
            self._cache[user_input] = local_response
            return local_response

        # 3. Essayer Gemini si disponible
        if self.convo:
            try:
                prompt = f"""Vous êtes un expert en catastrophes naturelles. 
                Répondez de façon concise (max 50 mots) en français:
                {user_input}"""
                
                try:
                    response = self.convo.send_message(
                        prompt,
                        request_options={"timeout": 10}  # Timeout de 10s
                    )
                    result = response.text or "Je n'ai pas pu générer de réponse."
                    self._cache[user_input] = result
                    return result
                except genai.types.StopCandidateException as e:
                    logger.warning(f"Réponse interrompue pour sécurité: {e}")
                    return self._get_fallback_response(user_input)
                except Exception as e:
                    if "quota" in str(e).lower():
                        logger.error("Quota API dépassé - utilisation du fallback")
                    else:
                        logger.error(f"Erreur API: {e}")
                    return self._get_fallback_response(user_input)

            except Exception as e:
                logger.error(f"Erreur inattendue: {e}")
                return self._get_fallback_response(user_input)

        # 4. Fallback garanti
        return self._get_fallback_response(user_input)

    def _get_fallback_response(self, user_input: str) -> str:
        """Retourne toujours un message str valide"""
        if self._is_disaster_related(user_input):
            return ("⚠️ Service temporairement indisponible\n"
                    "Contactez les secours au 112 pour assistance immédiate.")
        return ("Je ne peux répondre qu'aux questions sur:\n"
                "- " + "\n- ".join(EMERGENCY_PROTOCOLS.keys()) +
                "\n\nExemple: 'Que faire en cas d'incendie ?'")

    def clear_cache(self):
        """Vide le cache des réponses"""
        self._cache.clear()
        self._get_local_protocol.cache_clear()
        logger.info("Cache vidé")

    def __del__(self):
        """Nettoyage à la destruction de l'instance"""
        if self.convo:
            logger.info("Nettoyage de la session Gemini")
        self.clear_cache()