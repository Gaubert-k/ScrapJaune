import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MongoDBStorage:

    def __init__(self, host="localhost", port=27017, db_name="pagesjaunes_db"):
        self.host = host
        self.port = port
        self.db_name = db_name
        self.client = None
        self.db = None
        self.collection = None
        self.stats = {
            "inserted": 0,
            "updated": 0,
            "duplicates": 0,
            "errors": 0
        }

    def connect(self):
        try:
            logger.info(f"Connexion à la BDD Mongo : {self.host}:{self.port}")
            self.client = MongoClient(self.host, self.port, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ismaster')
            self.db = self.client[self.db_name]
            self.collection = self.db.pageJaune

            logger.info(f"Connection à la base de donnée réussi : {self.db_name}")
            return True

        except ConnectionFailure as e:
            logger.error(f"Erreur de connexion MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            return False

    def create_indexes(self):
        try:
            # Index pour la recherche textuelle
            self.collection.create_index([("name", "text"), ("type", "text")])

            # Index sur l'adresse (adaptée à la structure du scraper)
            self.collection.create_index("address")

            # Index sur les métadonnées
            self.collection.create_index("metadata.note_moyenne")
            self.collection.create_index("metadata.nombre_avis")
            self.collection.create_index("metadata.hash_id", unique=True)

            # Index sur le type de professionnel
            self.collection.create_index("professional")

            logger.info("Index créés")

        except Exception as e:
            logger.warning(f"Erreur lors de la création des index: {e}")

    def generate_hash_id(self, business: Dict) -> str:
        # Utiliser nom + adresse pour créer un hash unique
        identifier = f"{business.get('name', '')}-{business.get('address', '')}"
        return hashlib.md5(identifier.encode('utf-8')).hexdigest()

    def _extraire_note_moyenne(self, avis: List) -> float:
        """Calcule la note moyenne à partir des avis"""
        if not avis:
            return 0.0
        
        total = 0
        count = 0
        
        for avis_item in avis:
            if isinstance(avis_item, list) and len(avis_item) >= 1:
                try:
                    # Extraire la note (format "4/5" ou "4")
                    note_str = str(avis_item[0]).strip()
                    if '/' in note_str:
                        note = float(note_str.split('/')[0])
                    else:
                        note = float(note_str)
                    total += note
                    count += 1
                except (ValueError, IndexError):
                    continue
        
        return round(total / count, 2) if count > 0 else 0.0

    def _extraire_horaires_dict(self, horaires: List) -> Dict:
        """Convertit les horaires du format liste vers dictionnaire"""
        horaires_dict = {}
        
        for horaire_item in horaires:
            if isinstance(horaire_item, list) and len(horaire_item) >= 1:
                horaire_str = str(horaire_item[0])
                
                # Format attendu: "09:00-12:00 / 14:00-18:00 -> Lundi"
                if ' -> ' in horaire_str:
                    horaires_part, jour = horaire_str.split(' -> ')
                    horaires_dict[jour.strip()] = horaires_part.strip()
        
        return horaires_dict

    def prepare_document(self, business: Dict) -> Dict:
        """Prépare le document pour insertion en adaptant la structure du scraper"""
        
        # Calculer les métadonnées
        avis = business.get("avis", [])
        note_moyenne = self._extraire_note_moyenne(avis)
        nombre_avis = len(avis)
        
        # Convertir les horaires
        horaires_dict = self._extraire_horaires_dict(business.get("horaire", []))
        
        document = {
            "name": business.get("name", "").strip(),
            "professional": business.get("professional", "false") == "true",
            "type": business.get("type", "").strip(),
            "address": business.get("address", "").strip(),
            "avis": avis,
            "horaires": horaires_dict,
            "metadata": {
                "hash_id": self.generate_hash_id(business),
                "inserted_at": datetime.now(timezone.utc),
                "note_moyenne": note_moyenne,
                "nombre_avis": nombre_avis,
                "source": "pagesjaunes_scraper"
            },
            "searchable_name": business.get("name", "").lower(),
            "has_reviews": nombre_avis > 0,
            "has_schedule": len(horaires_dict) > 0
        }

        return document

    def insert_business(self, business: Dict) -> bool:
        try:
            # Ignorer les établissements sans nom
            if not business.get("name", "").strip():
                self.stats["errors"] += 1
                logger.debug("Établissement ignoré (pas de nom)")
                return False
                
            document = self.prepare_document(business)

            result = self.collection.insert_one(document)

            if result.inserted_id:
                self.stats["inserted"] += 1
                logger.debug(f"Inséré: {document['name']}")
                return True
            else:
                self.stats["errors"] += 1
                return False

        except DuplicateKeyError:
            # Établissement déjà existant - tentative de mise à jour
            try:
                hash_id = self.generate_hash_id(business)
                document = self.prepare_document(business)

                # Mise à jour au lieu d'insertion
                result = self.collection.update_one(
                    {"metadata.hash_id": hash_id},
                    {"$set": document}
                )

                if result.modified_count > 0:
                    self.stats["updated"] += 1
                    logger.debug(f"Mis à jour: {business.get('name', 'Inconnu')}")
                else:
                    self.stats["duplicates"] += 1
                    logger.debug(f"Doublon ignoré: {business.get('name', 'Inconnu')}")

                return True

            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour: {e}")
                self.stats["errors"] += 1
                return False

        except Exception as e:
            logger.error(f"Erreur lors de l'insertion: {e}")
            self.stats["errors"] += 1
            return False

    def bulk_insert(self, businesses: List[Dict]) -> Dict:
        logger.info(f"Début de l'insertion de {len(businesses)} établissements")

        success_count = 0

        for i, business in enumerate(businesses):
            if self.insert_business(business):
                success_count += 1

            if (i + 1) % 50 == 0:
                logger.info(f"Traité: {i + 1}/{len(businesses)} - Succès: {success_count}")

        logger.info("=== STATISTIQUES D'INSERTION ===")
        logger.info(f"Total traité: {len(businesses)}")
        logger.info(f"Nouveaux insérés: {self.stats['inserted']}")
        logger.info(f"Mis à jour: {self.stats['updated']}")
        logger.info(f"Doublons ignorés: {self.stats['duplicates']}")
        logger.info(f"Erreurs: {self.stats['errors']}")

        return self.stats.copy()

    def get_collection_stats(self) -> Dict:
        try:
            total_docs = self.collection.count_documents({})

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "avg_rating": {"$avg": "$metadata.note_moyenne"},
                        "total_reviews": {"$sum": "$metadata.nombre_avis"},
                        "with_reviews": {"$sum": {"$cond": [{"$gt": ["$metadata.nombre_avis", 0]}, 1, 0]}},
                        "professional_count": {"$sum": {"$cond": ["$professional", 1, 0]}}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            stats = result[0] if result else {}

            return {
                "total_establishments": total_docs,
                "average_rating": round(stats.get("avg_rating", 0), 2),
                "total_reviews": stats.get("total_reviews", 0),
                "establishments_with_reviews": stats.get("with_reviews", 0),
                "professional_establishments": stats.get("professional_count", 0)
            }

        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {e}")
            return {}

    def close_connection(self):
        if self.client:
            self.client.close()
            logger.info("Connexion MongoDB fermée")


def load_and_store_data(json_file: str, mongo_host="localhost", mongo_port=27017):
    """
    Charge un fichier JSON et stocke les données en MongoDB
    
    Args:
        json_file (str): Chemin vers le fichier JSON
        mongo_host (str): Hôte MongoDB
        mongo_port (int): Port MongoDB
        
    Returns:
        bool: True si succès
    """
    storage = MongoDBStorage(host=mongo_host, port=mongo_port)

    if not storage.connect():
        logger.error("Impossible de se connecter à MongoDB")
        return False

    try:
        storage.create_indexes()

        logger.info(f"Chargement du fichier: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            businesses = json.load(f)

        logger.info(f"Fichier chargé: {len(businesses)} établissements")

        # Validation basique
        if not isinstance(businesses, list):
            logger.error("Le fichier JSON doit contenir une liste d'établissements")
            return False

        stats = storage.bulk_insert(businesses)

        collection_stats = storage.get_collection_stats()
        logger.info("=== STATISTIQUES DE LA COLLECTION ===")
        for key, value in collection_stats.items():
            logger.info(f"{key}: {value}")

        return True

    except Exception as e:
        logger.error(f"Erreur lors du traitement: {e}")
        return False

    finally:
        storage.close_connection()


if __name__ == "__main__":
    # Test avec un fichier par défaut
    json_file = "data/cleaned_data.json"

    success = load_and_store_data(json_file)

    if success:
        print("Données stockées avec succès en MongoDB!")
    else:
        print("Erreur lors du stockage")