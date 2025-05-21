# chatbot.py - Version finale corrigée
import logging
import google.generativeai as genai
from emergency_data import DISASTER_KEYWORDS, EMERGENCY_PROTOCOLS
from config import GEMINI_CONFIG
from typing import Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DisasterChatbot:
    def __init__(self):
        """Initialise le chatbot avec configuration Gemini"""
        self.convo = None
        self._configure_gemini()
        logger.info("Chatbot initialisé")

    def _configure_gemini(self) -> None:
        """Configure la connexion à l'API Gemini"""
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

            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=GEMINI_CONFIG["generation_config"],
                safety_settings=GEMINI_CONFIG["safety_settings"]
            )
            self.convo = self.model.start_chat(history=[])
            logger.info("Connexion à Gemini établie avec succès")

        except Exception as e:
            logger.error(f"Erreur configuration Gemini: {str(e)}")
            self.convo = None

    def _is_disaster_related(self, text: str) -> bool:
        """Vérifie si le texte contient des mots-clés de catastrophe"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in DISASTER_KEYWORDS)

    def _get_local_protocol(self, question: str) -> Optional[str]:
        """Retourne le protocole local si une catastrophe est détectée"""
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
        """
        Génère toujours une réponse str, jamais None
        """
        # 1. D'abord vérifier les protocoles locaux
        local_response = self._get_local_protocol(user_input)
        if local_response:
            return local_response

        # 2. Essayer Gemini si disponible
        if self.convo:
            try:
                prompt = f"""Vous êtes un expert en catastrophes naturelles. 
                Répondez à cette question en moins de 50 mots:
                {user_input}"""
                response = self.convo.send_message(prompt)
                return response.text or "Réponse vide de l'API"
            except Exception as e:
                logger.error(f"Erreur Gemini: {e}")

        # 3. Fallback garanti
        return self._get_fallback_response(user_input)

    def _get_fallback_response(self, user_input: str) -> str:
        """Retourne toujours un message str valide"""
        if self._is_disaster_related(user_input):
            return ("⚠️ Service temporairement indisponible\n"
                    "Contactez les secours au 112 pour assistance immédiate.")
        return ("Je ne peux répondre qu'aux questions sur:\n"
                "- " + "\n- ".join(EMERGENCY_PROTOCOLS.keys()) +
                "\n\nExemple: 'Que faire en cas d'incendie ?'")

    def __del__(self):
        """Nettoyage à la destruction de l'instance"""
        if self.convo:
            logger.info("Nettoyage de la session Gemini")