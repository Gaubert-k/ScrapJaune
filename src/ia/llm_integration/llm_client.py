import requests
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
import re
from ..config.llm_config import LLMConfig

logger = logging.getLogger(__name__)


class LLMClient:
    """Client LLM avec contrôle strict des réponses et validation"""

    def __init__(self):
        self.config = LLMConfig()
        self.session = requests.Session()
        self.session.headers.update(self.config.get_request_headers())

        # Métriques de performance
        self.request_count = 0
        self.total_response_time = 0
        self.error_count = 0

        # Validation initiale
        self._validate_connection()

    def _validate_connection(self):
        """Valide la connexion au LLM au démarrage"""
        try:
            is_valid, message = self.config.validate_config()
            if is_valid:
                logger.info(f"✅ {message}")
            else:
                logger.error(f"❌ Validation LLM échouée: {message}")
                raise ConnectionError(f"LLM non accessible: {message}")
        except Exception as e:
            logger.error(f"❌ Impossible de valider la connexion LLM: {e}")
            raise

    def analyze_business_opportunity(self, market_data: Dict, business_request: Dict) -> Dict:
        """
        Analyse d'opportunité business avec contrôle strict du format

        Returns: {
            'success': bool,
            'analysis': {...} ou None,
            'raw_response': str,
            'validation_errors': [...],
            'performance_metrics': {...}
        }
        """

        logger.info(" Début analyse LLM...")
        start_time = time.time()

        try:
            # 1. GÉNÉRATION DU PROMPT OPTIMISÉ
            prompt = self._generate_analysis_prompt(market_data, business_request)

            # 2. APPEL LLM AVEC RETRY
            raw_response = self._call_llm_with_retry(prompt)

            # 3. VALIDATION ET PARSING STRICT
            validation_result = self._validate_and_parse_response(raw_response)

            # 4. MÉTRIQUES DE PERFORMANCE
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time, validation_result['success'])

            result = {
                'success': validation_result['success'],
                'analysis': validation_result['parsed_data'],
                'raw_response': raw_response,
                'validation_errors': validation_result['errors'],
                'performance_metrics': {
                    'response_time': round(response_time, 2),
                    'avg_response_time': round(self.total_response_time / max(self.request_count, 1), 2),
                    'success_rate': round((self.request_count - self.error_count) / max(self.request_count, 1) * 100, 1)
                }
            }

            if validation_result['success']:
                logger.info(f"✅ Analyse LLM réussie en {response_time:.1f}s")
            else:
                logger.warning(f"⚠️ Analyse LLM avec erreurs: {validation_result['errors']}")

            return result

        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Erreur analyse LLM: {e}")
            return {
                'success': False,
                'analysis': None,
                'raw_response': '',
                'validation_errors': [f"Erreur système: {str(e)}"],
                'performance_metrics': {'response_time': time.time() - start_time}
            }

    def _generate_analysis_prompt(self, market_data: Dict, business_request: Dict) -> str:
        """Génère un prompt optimisé pour Qwen avec contrôle strict"""

        competitors = market_data.get('competitors', [])
        market_summary = market_data.get('market_summary', {})
        opportunity_metrics = market_data.get('opportunity_metrics', {})

        # TOP 3 concurrents pour focus
        top_competitors = competitors[:3] if competitors else []

        # Données marché résumées
        competitor_summary = self._format_competitor_summary(top_competitors)
        market_stats = self._format_market_stats(market_summary, opportunity_metrics)

        prompt = f"""Tu es un consultant business expert. Analyse cette opportunité commerciale de manière factuelle et structurée.

DEMANDE CLIENT:
Type: {business_request.get('type', 'Non spécifié')}
Localisation: {business_request.get('address', 'Non spécifiée')}

MARCHÉ LOCAL:
{market_stats}

TOP 3 CONCURRENTS:
{competitor_summary}

TÂCHE: Réponds EXACTEMENT dans ce format JSON (respecte la structure):

{{
  "score_succes": [nombre entre 0 et 100],
  "niveau_confiance": "[Faible/Moyen/Élevé]",
  "atout_principal": "[Une phrase de 15 mots maximum]",
  "risque_principal": "[Une phrase de 15 mots maximum]",
  "action_prioritaire": "[Une action concrète en 20 mots maximum]",
  "positionnement_conseille": "[Stratégie en 25 mots maximum]"
}}

CONTRAINTES:
- JSON valide uniquement
- Phrases courtes et factuelles
- Scores basés sur les données fournies
- Pas de texte avant/après le JSON
- Ignore les balises <think> dans ta réponse"""

        return prompt

    def _format_competitor_summary(self, competitors: List[Dict]) -> str:
        """Formate le résumé des concurrents pour le prompt"""

        if not competitors:
            return "Aucun concurrent direct identifié"

        summary_lines = []
        for i, comp in enumerate(competitors, 1):
            name = comp.get('name', 'Inconnu')[:30]
            rating = comp.get('note_moyenne', 0)
            distance = comp.get('distance_km', 0)
            threat = comp.get('threat_level', 'Modéré')

            line = f"{i}. {name} - Note: {rating}/5 - Distance: {distance}km - Menace: {threat}"
            summary_lines.append(line)

        return "\n".join(summary_lines)

    def _format_market_stats(self, market_summary: Dict, opportunity_metrics: Dict) -> str:
        """Formate les statistiques marché pour le prompt"""

        total_competitors = market_summary.get('total_competitors', 0)
        avg_rating = market_summary.get('avg_rating', 0)
        market_density = market_summary.get('market_density', 'Inconnue')
        opportunity_score = opportunity_metrics.get('opportunity_score', 50)
        quality_gap = opportunity_metrics.get('quality_gap', 'Inévaluable')

        return f"""Concurrents totaux: {total_competitors}
Note moyenne marché: {avg_rating}/5
Densité marché: {market_density}
Score d'opportunité: {opportunity_score}/100
Gap qualité: {quality_gap}"""

    def _call_llm_with_retry(self, prompt: str, max_retries: int = 2) -> str:
        """Appel LLM avec retry et gestion d'erreurs"""

        request_payload = {
            "model": self.config.MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un consultant business expert. Réponds uniquement en JSON valide, de manière factuelle et concise. Ne utilise jamais de balises <think> ou autres métadonnées."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.config.TEMPERATURE,
            "top_p": self.config.TOP_P,
            "max_tokens": self.config.MAX_TOKENS,
            "stream": False
        }

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f" Tentative {attempt + 1}/{max_retries + 1}")

                response = self.session.post(
                    self.config.get_full_url(),
                    json=request_payload,
                    timeout=self.config.TIMEOUT
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

                    if content.strip():
                        self.request_count += 1
                        return content.strip()
                    else:
                        raise ValueError("Réponse vide du LLM")

                else:
                    raise requests.HTTPError(f"HTTP {response.status_code}: {response.text}")

            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ Tentative {attempt + 1} échouée: {e}")

                if attempt < max_retries:
                    time.sleep(1 * (attempt + 1))  # Backoff progressif

        # Échec final
        raise Exception(f"Échec après {max_retries + 1} tentatives. Dernière erreur: {last_error}")

    def _validate_and_parse_response(self, raw_response: str) -> Dict:
        """Validation stricte et parsing de la réponse LLM"""

        errors = []
        parsed_data = None

        try:
            # 1. NETTOYAGE DE LA RÉPONSE ( SUPPRESSION <think>)
            cleaned_response = self._clean_response_with_think_removal(raw_response)

            # 2. EXTRACTION JSON
            json_content = self._extract_json_from_response(cleaned_response)
            if not json_content:
                errors.append("Aucun JSON valide trouvé dans la réponse")
                return {'success': False, 'errors': errors, 'parsed_data': None}

            # 3. PARSING JSON
            try:
                parsed_json = json.loads(json_content)
            except json.JSONDecodeError as e:
                errors.append(f"JSON invalide: {e}")
                return {'success': False, 'errors': errors, 'parsed_data': None}

            # 4. VALIDATION DES CHAMPS REQUIS
            validation_errors = self._validate_required_fields(parsed_json)
            errors.extend(validation_errors)

            # 5. VALIDATION DES VALEURS
            value_errors = self._validate_field_values(parsed_json)
            errors.extend(value_errors)

            # 6. NORMALISATION DES DONNÉES
            normalized_data = self._normalize_response_data(parsed_json)

            success = len(errors) == 0

            return {
                'success': success,
                'errors': errors,
                'parsed_data': normalized_data if success else None
            }

        except Exception as e:
            errors.append(f"Erreur de validation: {str(e)}")
            return {'success': False, 'errors': errors, 'parsed_data': None}

    def _clean_response_with_think_removal(self, response: str) -> str:
        """ Nettoie la réponse en supprimant les balises <think> de Qwen3"""

        cleaned = response.strip()

        #  SUPPRESSION DES BALISES <think>...</think>
        # Pattern pour capturer tout le contenu entre <think> et </think>
        think_pattern = r'<think>.*?</think>\s*'
        cleaned = re.sub(think_pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Suppression des balises think orphelines
        cleaned = re.sub(r'</?think[^>]*>\s*', '', cleaned, flags=re.IGNORECASE)

        # Supprimer markdown si présent
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*$', '', cleaned)

        # Supprimer commentaires
        cleaned = re.sub(r'//.*$', '', cleaned, flags=re.MULTILINE)

        # Nettoyage espaces multiples
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = cleaned.strip()

        logger.debug(f" Réponse nettoyée: '{cleaned[:100]}...'")
        return cleaned

    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """Extrait le JSON de la réponse"""

        # Chercher JSON entre accolades (méthode améliorée)
        brace_count = 0
        start_idx = -1

        for i, char in enumerate(response):
            if char == '{':
                if start_idx == -1:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    # JSON complet trouvé
                    json_candidate = response[start_idx:i + 1]
                    try:
                        # Test de validation JSON
                        json.loads(json_candidate)
                        return json_candidate
                    except json.JSONDecodeError:
                        # Continuer la recherche
                        start_idx = -1
                        brace_count = 0

        # Fallback: méthode regex simple
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response, re.DOTALL)

        if matches:
            # Prendre le JSON le plus long (probablement le bon)
            return max(matches, key=len)

        # Dernier fallback: première/dernière accolade
        start = response.find('{')
        end = response.rfind('}')

        if start != -1 and end != -1 and end > start:
            return response[start:end + 1]

        return None

    def _validate_required_fields(self, data: Dict) -> List[str]:
        """Valide la présence des champs requis"""

        required_fields = [
            'score_succes',
            'niveau_confiance',
            'atout_principal',
            'risque_principal',
            'action_prioritaire',
            'positionnement_conseille'
        ]

        errors = []

        for field in required_fields:
            if field not in data:
                errors.append(f"Champ requis manquant: {field}")
            elif not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                errors.append(f"Champ vide: {field}")

        return errors

    def _validate_field_values(self, data: Dict) -> List[str]:
        """Valide les valeurs des champs"""

        errors = []

        # Score de succès
        score = data.get('score_succes')
        if score is not None:
            try:
                score_num = float(score)
                if not (0 <= score_num <= 100):
                    errors.append("score_succes doit être entre 0 et 100")
            except (ValueError, TypeError):
                errors.append("score_succes doit être un nombre")

        # Niveau de confiance
        confiance = data.get('niveau_confiance')
        if confiance and confiance not in ['Faible', 'Moyen', 'Élevé']:
            errors.append("niveau_confiance doit être: Faible, Moyen ou Élevé")

        # Longueur des textes
        text_limits = {
            'atout_principal': 100,
            'risque_principal': 100,
            'action_prioritaire': 150,
            'positionnement_conseille': 200
        }

        for field, max_length in text_limits.items():
            text = data.get(field, '')
            if isinstance(text, str) and len(text) > max_length:
                errors.append(f"{field} trop long ({len(text)}>{max_length} caractères)")

        return errors

    def _normalize_response_data(self, data: Dict) -> Dict:
        """Normalise les données de réponse"""

        normalized = {}

        # Score de succès
        try:
            normalized['score_succes'] = int(float(data.get('score_succes', 50)))
        except:
            normalized['score_succes'] = 50

        # Niveau de confiance
        confiance = data.get('niveau_confiance', '').strip()
        if confiance in ['Faible', 'Moyen', 'Élevé']:
            normalized['niveau_confiance'] = confiance
        else:
            normalized['niveau_confiance'] = 'Moyen'

        # Textes nettoyés
        text_fields = ['atout_principal', 'risque_principal', 'action_prioritaire', 'positionnement_conseille']

        for field in text_fields:
            text = data.get(field, '').strip()
            # Nettoyer ponctuation excessive
            text = re.sub(r'[.]{2,}', '.', text)
            text = re.sub(r'[!]{2,}', '!', text)
            text = re.sub(r'\s+', ' ', text)
            normalized[field] = text

        return normalized

    def _update_performance_metrics(self, response_time: float, success: bool):
        """Met à jour les métriques de performance"""

        self.request_count += 1
        self.total_response_time += response_time

        if not success:
            self.error_count += 1

    def get_performance_stats(self) -> Dict:
        """Retourne les statistiques de performance"""

        if self.request_count == 0:
            return {
                'total_requests': 0,
                'avg_response_time': 0,
                'success_rate': 0,
                'error_rate': 0
            }

        return {
            'total_requests': self.request_count,
            'avg_response_time': round(self.total_response_time / self.request_count, 2),
            'success_rate': round((self.request_count - self.error_count) / self.request_count * 100, 1),
            'error_rate': round(self.error_count / self.request_count * 100, 1)
        }

    def test_connection(self) -> Dict:
        """ Test adapté pour Qwen3 avec gestion <think>"""

        test_prompt = "Réponds exactement: {\"test\": \"ok\"}"

        try:
            start_time = time.time()
            response = self._call_llm_with_retry(test_prompt, max_retries=1)
            response_time = time.time() - start_time

            # Nettoyage spécial pour le test
            cleaned = self._clean_response_with_think_removal(response)

            logger.debug(f" Réponse test brute: '{response[:200]}...'")
            logger.debug(f" Réponse test nettoyée: '{cleaned}'")

            # Vérifier si JSON valide
            try:
                parsed = json.loads(cleaned.strip())
                if parsed.get('test') == 'ok':
                    return {
                        'success': True,
                        'response_time': round(response_time, 2),
                        'message': 'Connexion LLM opérationnelle (Qwen3 détecté)',
                        'raw_response': response,
                        'cleaned_response': cleaned
                    }
                else:
                    return {
                        'success': False,
                        'response_time': round(response_time, 2),
                        'message': f'LLM ne respecte pas les instructions. Reçu: {parsed}',
                        'raw_response': response,
                        'cleaned_response': cleaned
                    }
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'response_time': round(response_time, 2),
                    'message': f'LLM ne retourne pas du JSON valide: {str(e)}',
                    'raw_response': response,
                    'cleaned_response': cleaned
                }

        except Exception as e:
            return {
                'success': False,
                'response_time': 0,
                'message': f'Erreur connexion: {str(e)}'
            }
