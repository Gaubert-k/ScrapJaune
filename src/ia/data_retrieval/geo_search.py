import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.storage.mongodb_storage import MongoDBStorage
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import logging
import time
import re

logger = logging.getLogger(__name__)


class GeographicSearchEngine:
    """Moteur de recherche géographique étendu avec ciblage par type"""

    def __init__(self, mongo_host='localhost', mongo_port=27017):
        self.mongo_storage = MongoDBStorage(
            host=mongo_host,
            port=mongo_port,
            db_name='pages_jaunes'
        )
        self.mongo_storage.connect()
        self.geolocator = Nominatim(user_agent="business_analyzer_student")

        # Cache des coordonnées pour éviter re-géocodage
        self.coords_cache = {}

    def find_market_competitors(self, business_request, radius_km=5, max_results=15):
        """
        Trouve les concurrents pour un type de business spécifique

        business_request = {
            'type': 'Restaurant',           # Type exact ou proche
            'address': 'Paris 75001',       # Localisation
            'coordinates': (lat, lon)       # Optionnel si déjà géocodé
        }
        """

        logger.info(f" Recherche marché pour: {business_request['type']} à {business_request['address']}")

        # 1. GÉOLOCALISER LA DEMANDE
        target_coords = self._get_coordinates(business_request)
        if not target_coords:
            logger.error("❌ Impossible de géolocaliser la demande")
            return []

        # 2. RECHERCHE CIBLÉE PAR TYPE
        competitors = self._search_by_business_type(
            business_request['type'],
            target_coords,
            radius_km,
            max_results
        )

        # 3. ENRICHISSEMENT AVEC DISTANCES ET SCORES
        enriched_competitors = self._enrich_with_metrics(
            competitors,
            target_coords,
            business_request
        )

        logger.info(f"✅ {len(enriched_competitors)} concurrents trouvés")
        return enriched_competitors

    def _get_coordinates(self, business_request):
        """Récupère ou calcule les coordonnées"""

        # Si déjà fourni
        if 'coordinates' in business_request:
            return business_request['coordinates']

        address = business_request['address']

        # Cache check
        if address in self.coords_cache:
            return self.coords_cache[address]

        # Géocodage
        try:
            time.sleep(0.1)  # Rate limiting
            location = self.geolocator.geocode(address, timeout=10)
            if location:
                coords = (location.latitude, location.longitude)
                self.coords_cache[address] = coords
                logger.info(f" Géocodé: {address} -> {coords}")
                return coords
        except Exception as e:
            logger.warning(f"⚠️ Géocodage échoué pour {address}: {e}")

        # Fallback estimation par code postal
        return self._estimate_coordinates_by_postal(address)

    def _estimate_coordinates_by_postal(self, address):
        """Estimation rapide par code postal français"""

        postal_coords = {
            # Paris par arrondissement
            '75001': (48.8566, 2.3522), '75002': (48.8679, 2.3414), '75003': (48.8630, 2.3522),
            '75004': (48.8545, 2.3532), '75005': (48.8462, 2.3372), '75006': (48.8462, 2.3372),
            '75007': (48.8589, 2.3115), '75008': (48.8738, 2.2974), '75009': (48.8769, 2.3358),
            '75010': (48.8760, 2.3596), '75011': (48.8594, 2.3765), '75012': (48.8434, 2.3897),
            '75013': (48.8322, 2.3561), '75014': (48.8336, 2.3265), '75015': (48.8422, 2.2969),
            '75016': (48.8543, 2.2676), '75017': (48.8849, 2.3088), '75018': (48.8928, 2.3469),
            '75019': (48.8839, 2.3781), '75020': (48.8639, 2.3969),

            # Grandes villes
            '69001': (45.7579, 4.8340), '69002': (45.7485, 4.8270), '69003': (45.7578, 4.8441),
            '13001': (43.2965, 5.3698), '13002': (43.3047, 5.3779), '13003': (43.3072, 5.3860),
            '31000': (43.6047, 1.4442), '33000': (44.8378, -0.5792), '34000': (43.6110, 3.8767),
            '35000': (48.1173, -1.6778), '37000': (47.3941, 0.6848), '38000': (45.1885, 5.7245),
            '44000': (47.2184, -1.5536), '51000': (49.2628, 4.0347), '54000': (48.6921, 6.1844),
            '59000': (50.6292, 3.0573), '67000': (48.5734, 7.7521), '76000': (49.4431, 1.0993)
        }

        # Extraction code postal
        postal_match = re.search(r'\b(\d{5})\b', address)
        if postal_match:
            postal_code = postal_match.group(1)
            if postal_code in postal_coords:
                coords = postal_coords[postal_code]
                self.coords_cache[address] = coords
                logger.info(f" Estimation: {address} -> {coords} (code postal)")
                return coords

        # Fallback Paris centre
        default_coords = (48.8566, 2.3522)
        self.coords_cache[address] = default_coords
        logger.warning(f" Fallback Paris pour: {address}")
        return default_coords

    def _search_by_business_type(self, target_type, coords, radius_km, max_results):
        """Recherche ciblée dans MongoDB par type de business"""

        # Types similaires/connexes pour élargir la recherche
        similar_types = self._get_similar_business_types(target_type)

        try:
            # Requête MongoDB avec types similaires
            collection = self.mongo_storage.db['businesses']

            query = {
                "$or": [
                    {"type": {"$regex": type_pattern, "$options": "i"}}
                    for type_pattern in similar_types
                ],
                "coordinates": {"$exists": True, "$ne": None}
            }

            # Récupération avec tri par qualité
            cursor = collection.find(query).sort("note_moyenne", -1).limit(max_results * 3)

            competitors = []
            lat_center, lon_center = coords

            for doc in cursor:
                try:
                    # Parse coordonnées MongoDB
                    if 'lat' in doc and 'lon' in doc:
                        biz_lat, biz_lon = doc['lat'], doc['lon']
                    elif 'coordinates' in doc and doc['coordinates']:
                        coord_str = str(doc['coordinates'])
                        # Parse "(lat, lon)" ou "lat,lon"
                        coord_clean = coord_str.strip('()[]').split(',')
                        biz_lat = float(coord_clean[0])
                        biz_lon = float(coord_clean[1])
                    else:
                        continue

                    # Filtre géographique rapide
                    distance = geodesic((lat_center, lon_center), (biz_lat, biz_lon)).kilometers

                    if distance <= radius_km:
                        # Enrichir les données
                        doc['distance_km'] = round(distance, 2)
                        doc['lat'] = biz_lat
                        doc['lon'] = biz_lon
                        competitors.append(doc)

                        if len(competitors) >= max_results:
                            break

                except Exception as e:
                    logger.warning(f"⚠️ Erreur parsing business: {e}")
                    continue

            return competitors

        except Exception as e:
            logger.error(f"❌ Erreur recherche MongoDB: {e}")
            return []

    def _get_similar_business_types(self, target_type):
        """Génère des patterns de recherche pour types similaires"""

        # Mapping des types similaires
        business_families = {
            'restaurant': ['restaurant', 'brasserie', 'bistrot', 'taverne', 'café', 'bar'],
            'coiffeur': ['coiffeur', 'salon de coiffure', 'barbier', 'esthétique'],
            'boulangerie': ['boulangerie', 'pâtisserie', 'viennoiserie'],
            'pharmacie': ['pharmacie', 'parapharmacie'],
            'médecin': ['médecin', 'docteur', 'cabinet médical'],
            'dentiste': ['dentiste', 'orthodontiste', 'stomatologie'],
            'avocat': ['avocat', 'cabinet d\'avocat', 'juriste'],
            'garage': ['garage', 'mécanicien', 'carrosserie', 'auto'],
            'immobilier': ['immobilier', 'agence immobilière', 'transaction'],
            'banque': ['banque', 'crédit', 'assurance'],
            'hotel': ['hôtel', 'hébergement', 'auberge'],
            'magasin': ['magasin', 'boutique', 'commerce'],
        }

        target_lower = target_type.lower()

        # Chercher la famille correspondante
        for family, types in business_families.items():
            if any(keyword in target_lower for keyword in types):
                return types

        # Si pas trouvé, utiliser le type exact + variations
        return [target_type, target_lower, target_type.capitalize()]

    def _enrich_with_metrics(self, competitors, target_coords, business_request):
        """Enrichit avec métriques business et scores"""

        enriched = []

        for competitor in competitors:
            try:
                # Métriques de base
                note_moyenne = competitor.get('note_moyenne', 0)
                nombre_avis = competitor.get('nombre_avis', 0)

                # Score de succès calculé
                success_score = self._calculate_success_score(competitor)

                # Score de similarité avec la demande
                similarity_score = self._calculate_similarity_score(
                    business_request['type'],
                    competitor.get('type', ''),
                    competitor['distance_km']
                )

                # Enrichissement final
                competitor.update({
                    'success_score': success_score,
                    'similarity_score': similarity_score,
                    'market_position': self._assess_market_position(success_score, note_moyenne),
                    'threat_level': self._assess_threat_level(similarity_score, competitor['distance_km'])
                })

                enriched.append(competitor)

            except Exception as e:
                logger.warning(f"⚠️ Erreur enrichissement: {e}")
                continue

        # Tri par pertinence (similarité + succès - distance)
        enriched.sort(key=lambda x: (
                x['similarity_score'] + x['success_score'] - x['distance_km']
        ), reverse=True)

        return enriched

    def _calculate_success_score(self, business):
        """Calcule un score de succès 0-10"""

        score = 5.0  # Base

        # Note moyenne (40% du score)
        note = business.get('note_moyenne', 0)
        if note > 0:
            score += (note - 2.5) * 1.6

        # Popularité par avis (30% du score)
        avis = business.get('nombre_avis', 0)
        if avis > 0:
            popularity = min(avis / 20.0, 1.0) * 3
            score += popularity

        # Complétude profil (30% du score)
        if business.get('professional') == 'true': score += 0.5
        if business.get('address'): score += 0.5
        if business.get('horaire'): score += 0.5
        if len(business.get('name', '')) > 5: score += 0.5

        return max(0, min(10, score))

    def _calculate_similarity_score(self, target_type, competitor_type, distance):
        """Score de similarité avec la demande"""

        score = 0

        # Exactitude du type (60 points)
        if target_type.lower() == competitor_type.lower():
            score += 60
        elif target_type.lower() in competitor_type.lower():
            score += 40
        elif competitor_type.lower() in target_type.lower():
            score += 30

        # Proximité géographique (40 points)
        if distance <= 0.5:
            score += 40
        elif distance <= 1:
            score += 30
        elif distance <= 2:
            score += 20
        elif distance <= 5:
            score += 10

        return min(100, score)

    def _assess_market_position(self, success_score, note_moyenne):
        """Évalue la position marché"""
        if success_score >= 8 and note_moyenne >= 4.5:
            return "Leader"
        elif success_score >= 6 and note_moyenne >= 4.0:
            return "Etabli"
        elif success_score >= 4:
            return "Moyen"
        else:
            return "Faible"

    def _assess_threat_level(self, similarity_score, distance):
        """Évalue le niveau de menace concurrentielle"""
        if similarity_score >= 80 and distance <= 1:
            return "Très élevé"
        elif similarity_score >= 60 and distance <= 2:
            return "Élevé"
        elif similarity_score >= 40:
            return "Modéré"
        else:
            return "Faible"

    def close(self):
        """Ferme les connexions"""
        if self.mongo_storage:
            self.mongo_storage.close_connection()
