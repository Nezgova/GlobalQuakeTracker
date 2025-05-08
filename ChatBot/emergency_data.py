# emergency_data.py
DISASTER_KEYWORDS = [
    "tremblement", "séisme", "inondation", "incendie", "feu",
    "ouragan", "tempête", "tsunami", "glissement", "catastrophe",
    "urgence", "danger", "aide", "secours", "sauvetage", "évacuation",
    "alerte", "blessé", "piégé", "météo", "urgence", "danger",
    "secourisme", "premiers soins", "risque", "alerte", "météo"
]

EMERGENCY_PROTOCOLS = {
    "tremblement de terre": {
        "description": "Mouvement soudain du sol causé par des fractures géologiques",
        "actions": [
            "Restez où vous êtes jusqu'à ce que les secousses s'arrêtent",
            "Mettez-vous à l'abri sous un meuble solide",
            "Éloignez-vous des fenêtres"
        ],
        "numéro_urgence": "112"
    },
    "inondation": {
        "description": "Submersion d'une zone habituellement sèche",
        "actions": [
            "Montez à l'étage ou sur un toit",
            "Évitez de marcher dans l'eau courante"
        ],
        "numéro_urgence": "112"
    }
}