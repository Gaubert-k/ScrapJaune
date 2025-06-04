import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataCleaner:

    def __init__(self):
        self.stats = {
            "total_processed": 0,
            "cleaned_successfully": 0,
            "errors": 0
        }

    def clean_name(self, name: str) -> str:
        if not name or not isinstance(name, str):
            return ""

        name = re.sub(r'\s+', ' ', name.strip())
        name = re.sub(r'[^\w\s\-\'\.&]', '', name)

        name = ' '.join(word.capitalize() for word in name.split())

        return name

    def clean_address(self, address: str) -> Dict[str, str]:
        """Nettoie et structure l'adresse"""
        if not address or not isinstance(address, str):
            return {
                "full_address": "",
                "street": "",
                "city": "",
                "postal_code": ""
            }

        address = address.strip()

        postal_match = re.search(r'\b(\d{5})\b', address)
        postal_code = postal_match.group(1) if postal_match else ""

        city = ""
        if postal_code:
            city_match = re.search(rf'{postal_code}\s+(.+)', address)
            if city_match:
                city = city_match.group(1).strip().title()

        street = ""
        if postal_code:
            street_match = re.search(rf'(.+?)\s+{postal_code}', address)
            if street_match:
                street = street_match.group(1).strip()
        else:
            street = address

        return {
            "full_address": address,
            "street": street,
            "city": city,
            "postal_code": postal_code
        }

    def clean_avis(self, avis: List[List]) -> List[Dict]:
        if not avis or not isinstance(avis, list):
            return []

        cleaned_avis = []

        for avis_item in avis:
            if not isinstance(avis_item, list) or len(avis_item) < 2:
                continue

            try:
                note_str = str(avis_item[0]).strip()
                note_match = re.search(r'(\d+(?:\.\d+)?)', note_str)
                note = float(note_match.group(1)) if note_match else 0.0

                note = max(0.0, min(5.0, note))

                commentaire = str(avis_item[1]).strip()
                commentaire = re.sub(r'\s+', ' ', commentaire)

                if commentaire:  # Ne garder que les avis avec commentaires
                    cleaned_avis.append({
                        "note": note,
                        "commentaire": commentaire,
                        "longueur": len(commentaire)
                    })

            except Exception as e:
                logger.warning(f"Erreur lors du nettoyage d'un avis: {e}")
                continue

        return cleaned_avis

    def clean_horaires(self, horaires: List[List]) -> Dict[str, str]:
        if not horaires or not isinstance(horaires, list):
            return {}

        horaires_clean = {}
        jours_semaine = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']

        for horaire_item in horaires:
            if not isinstance(horaire_item, list) or not horaire_item:
                continue

            try:
                horaire_str = str(horaire_item[0]).strip().lower()

                # Identifier le jour
                jour_trouve = None
                for jour in jours_semaine:
                    if jour in horaire_str:
                        jour_trouve = jour
                        break

                if jour_trouve:
                    if "fermé" in horaire_str:
                        horaires_clean[jour_trouve] = "Fermé"
                    else:
                        heures_match = re.findall(r'(\d{1,2}h?\d{0,2})\s*[-–]\s*(\d{1,2}h?\d{0,2})', horaire_str)
                        if heures_match:
                            heures_formated = []
                            for debut, fin in heures_match:
                                debut = debut.replace('h', ':') if 'h' in debut else debut
                                fin = fin.replace('h', ':') if 'h' in fin else fin
                                heures_formated.append(f"{debut}-{fin}")
                            horaires_clean[jour_trouve] = " / ".join(heures_formated)
                        else:
                            horaires_clean[jour_trouve] = horaire_str.replace(f"-> {jour_trouve}", "").strip()

            except Exception as e:
                logger.warning(f"Erreur lors du nettoyage d'un horaire: {e}")
                continue

        return horaires_clean

    def clean_business(self, business: Dict) -> Optional[Dict]:
        try:
            cleaned = {
                "name": self.clean_name(business.get("name", "")),
                "professional": business.get("professional", "false") == "true",
                "type": business.get("type", "").strip(),
                "address": self.clean_address(business.get("address", "")),
                "avis": self.clean_avis(business.get("avis", [])),
                "horaires": self.clean_horaires(business.get("horaire", [])),
                "metadata": {
                    "cleaned_at": datetime.utcnow().isoformat(),
                    "original_avis_count": len(business.get("avis", [])),
                    "cleaned_avis_count": 0,
                    "has_address": bool(business.get("address", "")),
                    "has_horaires": bool(business.get("horaire", []))
                }
            }

            cleaned["metadata"]["cleaned_avis_count"] = len(cleaned["avis"])

            if cleaned["avis"]:
                notes = [avis["note"] for avis in cleaned["avis"]]
                cleaned["metadata"]["note_moyenne"] = round(sum(notes) / len(notes), 2)
                cleaned["metadata"]["nombre_avis"] = len(notes)
            else:
                cleaned["metadata"]["note_moyenne"] = 0.0
                cleaned["metadata"]["nombre_avis"] = 0

            if not cleaned["name"]:
                logger.warning("Établissement ignoré: pas de nom")
                return None

            return cleaned

        except Exception as e:
            logger.error(f"Erreur lors du nettoyage d'un établissement: {e}")
            return None

    def process_file(self, input_file: str, output_file: str = None) -> List[Dict]:
        logger.info(f"Début du nettoyage du fichier: {input_file}")

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            if not isinstance(raw_data, list):
                raise ValueError("Le fichier JSON doit contenir une liste d'établissements")

            logger.info(f"Fichier chargé: {len(raw_data)} établissements à traiter")

            cleaned_data = []
            for i, business in enumerate(raw_data):
                self.stats["total_processed"] += 1

                cleaned_business = self.clean_business(business)
                if cleaned_business:
                    cleaned_data.append(cleaned_business)
                    self.stats["cleaned_successfully"] += 1
                else:
                    self.stats["errors"] += 1

                if (i + 1) % 10 == 0:
                    logger.info(f"Traité: {i + 1}/{len(raw_data)}")

            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Données nettoyées sauvegardées dans: {output_file}")

            logger.info(f"Nettoyage terminé:")
            logger.info(f"  - Total traité: {self.stats['total_processed']}")
            logger.info(f"  - Nettoyé avec succès: {self.stats['cleaned_successfully']}")
            logger.info(f"  - Erreurs: {self.stats['errors']}")

            return cleaned_data

        except Exception as e:
            logger.error(f"Erreur lors du traitement du fichier: {e}")
            raise

if __name__ == "__main__":
    cleaner = DataCleaner()

    input_file = "resultats/votre_fichier.json"
    output_file = "data/cleaned_data.json"

    try:
        cleaned_data = cleaner.process_file(input_file, output_file)
        print(f"{len(cleaned_data)} établissements nettoyés avec succès !")
    except Exception as e:
        print(f"Erreur: {e}")