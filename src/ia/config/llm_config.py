import os
from dotenv import load_dotenv
from pathlib import Path

# Charger les variables d'environnement
load_dotenv()


class LLMConfig:
    """Configuration centralisée pour le LLM"""

    # URLs et endpoints
    BASE_URL = os.getenv('LLM_BASE_URL', 'http://localhost:1234')
    MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'qwen/qwen3-8b')
    API_ENDPOINT = os.getenv('LLM_API_ENDPOINT', '/v1/chat/completions')
    MODELS_ENDPOINT = '/v1/models'

    # ⏰ TIMEOUTS OPTIMISÉS POUR QWEN3
    TIMEOUT = int(os.getenv('LLM_TIMEOUT', '90'))  # ⬆️ 30s → 90s
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '800'))  # ⬆️ 600 → 800
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.2'))
    TOP_P = float(os.getenv('TOP_P', '0.8'))

    # Configuration analyse
    DEFAULT_RADIUS = float(os.getenv('DEFAULT_SEARCH_RADIUS_KM', '5'))
    MAX_COMPETITORS = int(os.getenv('MAX_COMPETITORS', '15'))
    MIN_CONFIDENCE = int(os.getenv('MIN_CONFIDENCE_SCORE', '60'))

    @classmethod
    def get_full_url(cls, endpoint=None):
        """Construit l'URL complète"""
        endpoint = endpoint or cls.API_ENDPOINT
        return f"{cls.BASE_URL}{endpoint}"

    @classmethod
    def get_request_headers(cls):
        """Headers pour les requêtes"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @classmethod
    def validate_config(cls):
        """Valide la configuration avec timeout adapté"""
        import requests

        try:
            # Test de connexion avec timeout court pour validation
            response = requests.get(
                cls.get_full_url(cls.MODELS_ENDPOINT),
                headers=cls.get_request_headers(),
                timeout=10  # Court pour test rapide
            )

            if response.status_code == 200:
                models = response.json()
                available_models = [m.get('id', '') for m in models.get('data', [])]

                if cls.MODEL_NAME in available_models:
                    return True, f"✅ Modèle {cls.MODEL_NAME} disponible (timeout: {cls.TIMEOUT}s)"
                else:
                    return False, f"❌ Modèle {cls.MODEL_NAME} non trouvé. Disponibles: {available_models}"
            else:
                return False, f"❌ Erreur HTTP {response.status_code}"

        except Exception as e:
            return False, f"❌ Connexion impossible: {e}"


# Configuration MongoDB
class MongoConfig:
    HOST = os.getenv('MONGO_HOST', 'localhost')
    PORT = int(os.getenv('MONGO_PORT', '27017'))
    DB_NAME = os.getenv('MONGO_DB_NAME', 'pages_jaunes')