import sys
import os
from pathlib import Path
import argparse
from data_cleaner import DataCleaner
from src.storage.mongodb_storage import load_and_store_data
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pages_jaunes_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Traitement des données Pages Jaunes')
    parser.add_argument('input_file', help='Fichier JSON à traiter')
    parser.add_argument('--skip-cleaning', action='store_true', help='Ignorer le nettoyage (fichier déjà nettoyé)')
    parser.add_argument('--mongo-host', default='localhost', help='Adresse MongoDB')
    parser.add_argument('--mongo-port', type=int, default=27017, help='Port MongoDB')
    parser.add_argument('--output-dir', default='data', help='Dossier de sortie')

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        logger.error(f"Fichier non trouvé: {args.input_file}")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    try:
        cleaned_file = args.input_file

        if not args.skip_cleaning:
            logger.info("🧹 ÉTAPE 1: Nettoyage des données")

            cleaner = DataCleaner()
            cleaned_file = output_dir / "cleaned_data.json"

            cleaned_data = cleaner.process_file(args.input_file, str(cleaned_file))

            if not cleaned_data:
                logger.error("Aucune donnée nettoyée - Arrêt du traitement")
                return 1

            logger.info(f"Nettoyage terminé: {len(cleaned_data)} établissements")
        else:
            logger.info("Nettoyage ignoré (--skip-cleaning)")

        logger.info("🗄️ ÉTAPE 2: Stockage en MongoDB")

        success = load_and_store_data(
            str(cleaned_file),
            mongo_host=args.mongo_host,
            mongo_port=args.mongo_port
        )

        if success:
            logger.info("Données stockées avec succès en MongoDB!")
            logger.info("Traitement terminé avec succès!")
            return 0
        else:
            logger.error("Erreur lors du stockage en MongoDB")
            return 1

    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())