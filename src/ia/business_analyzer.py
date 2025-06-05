import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from .data_retrieval.market_analyzer import MarketAnalyzer
from .llm_integration.llm_client import LLMClient
from .llm_integration.prompt_manager import PromptManager
from .config.llm_config import LLMConfig, MongoConfig
import logging
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


class BusinessAnalyzer:
    """
    Interface principale pour l'analyse d'opportunités business
    Combine recherche marché + analyse IA
    """

    def __init__(self, mongo_host: Optional[str] = None, mongo_port: Optional[int] = None):
        """
        Initialise l'analyseur business complet

        Args:
            mongo_host: Adresse MongoDB (optionnel, utilise .env)
            mongo_port: Port MongoDB (optionnel, utilise .env)
        """

        # Configuration depuis .env ou paramètres
        self.mongo_host = mongo_host or MongoConfig.HOST
        self.mongo_port = mongo_port or MongoConfig.PORT

        # Initialisation des composants
        self.market_analyzer = None
        self.llm_client = None
        self.prompt_manager = PromptManager()

        # Métriques globales
        self.analysis_count = 0
        self.total_analysis_time = 0
        self.success_count = 0

        logger.info(" BusinessAnalyzer initialisé")

    def _initialize_components(self):
        """Initialisation lazy des composants"""

        if self.market_analyzer is None:
            logger.info(" Initialisation MarketAnalyzer...")
            self.market_analyzer = MarketAnalyzer(self.mongo_host, self.mongo_port)

        if self.llm_client is None:
            logger.info(" Initialisation LLMClient...")
            self.llm_client = LLMClient()

    def analyze_business_opportunity(self, business_type: str, location: str,
                                     radius_km: float = 5.0,
                                     analysis_depth: str = 'standard') -> Dict:
        """
        Analyse complète d'opportunité business

        Args:
            business_type: Type d'activité (ex: "Restaurant", "Coiffeur")
            location: Localisation (ex: "Paris 75001", "Lyon")
            radius_km: Rayon de recherche en km
            analysis_depth: 'quick', 'standard', 'detailed'

        Returns:
            {
                'success': bool,
                'business_request': {...},
                'market_analysis': {...},
                'ai_analysis': {...},
                'recommendations': {...},
                'performance_metrics': {...}
            }
        """

        logger.info(f" Analyse business: {business_type} à {location}")
        start_time = time.time()

        try:
            # Initialisation des composants
            self._initialize_components()

            # Validation des paramètres
            validation_result = self._validate_request(business_type, location)
            if not validation_result['valid']:
                return self._error_response(validation_result['error'])

            # 1. PRÉPARATION DE LA DEMANDE
            business_request = {
                'type': business_type.strip(),
                'address': location.strip(),
                'radius_km': radius_km,
                'analysis_depth': analysis_depth
            }

            # 2. ANALYSE MARCHÉ LOCAL
            logger.info(" Recherche et analyse du marché local...")
            market_analysis = self.market_analyzer.analyze_market_opportunity(
                business_request,
                radius_km=radius_km
            )

            # 3. ANALYSE IA
            logger.info(" Analyse IA de l'opportunité...")
            ai_analysis = self.llm_client.analyze_business_opportunity(
                market_analysis,
                business_request
            )

            # 4. GÉNÉRATION RECOMMANDATIONS
            recommendations = self._generate_recommendations(
                market_analysis,
                ai_analysis,
                business_request
            )

            # 5. MÉTRIQUES DE PERFORMANCE
            analysis_time = time.time() - start_time
            performance_metrics = self._calculate_performance_metrics(analysis_time, ai_analysis)

            # Mise à jour des compteurs
            self.analysis_count += 1
            self.total_analysis_time += analysis_time
            if ai_analysis.get('success', False):
                self.success_count += 1

            # Résultat final
            result = {
                'success': True,
                'business_request': business_request,
                'market_analysis': market_analysis,
                'ai_analysis': ai_analysis,
                'recommendations': recommendations,
                'performance_metrics': performance_metrics
            }

            logger.info(f"✅ Analyse terminée en {analysis_time:.1f}s")
            return result

        except Exception as e:
            analysis_time = time.time() - start_time
            logger.error(f"❌ Erreur analyse business: {e}")
            return self._error_response(f"Erreur système: {str(e)}", analysis_time)

    def _validate_request(self, business_type: str, location: str) -> Dict:
        """Valide les paramètres de la demande"""

        if not business_type or not business_type.strip():
            return {'valid': False, 'error': 'Type de business requis'}

        if not location or not location.strip():
            return {'valid': False, 'error': 'Localisation requise'}

        if len(business_type.strip()) < 3:
            return {'valid': False, 'error': 'Type de business trop court (min 3 caractères)'}

        if len(location.strip()) < 3:
            return {'valid': False, 'error': 'Localisation trop courte (min 3 caractères)'}

        return {'valid': True}

    def _generate_recommendations(self, market_analysis: Dict, ai_analysis: Dict,
                                  business_request: Dict) -> Dict:
        """Génère des recommandations actionables"""

        recommendations = {
            'priority_actions': [],
            'strategic_advice': [],
            'risk_mitigation': [],
            'success_factors': [],
            'next_steps': []
        }

        try:
            # Données du marché
            market_summary = market_analysis.get('market_summary', {})
            opportunity_metrics = market_analysis.get('opportunity_metrics', {})
            strategic_insights = market_analysis.get('strategic_insights', {})

            # Analyse IA
            if ai_analysis.get('success') and ai_analysis.get('analysis'):
                ai_data = ai_analysis['analysis']

                # Actions prioritaires
                if ai_data.get('action_prioritaire'):
                    recommendations['priority_actions'].append(ai_data['action_prioritaire'])

                # Conseils stratégiques
                if ai_data.get('positionnement_conseille'):
                    recommendations['strategic_advice'].append(ai_data['positionnement_conseille'])

            # Recommandations basées sur le marché
            competitor_count = market_summary.get('total_competitors', 0)
            avg_rating = market_summary.get('avg_rating', 0)
            opportunity_score = opportunity_metrics.get('opportunity_score', 50)

            # Actions selon la concurrence
            if competitor_count == 0:
                recommendations['priority_actions'].append("Valider la demande locale avant l'investissement")
                recommendations['strategic_advice'].append("Positionnement pionnier - miser sur la visibilité")
            elif competitor_count > 10:
                recommendations['risk_mitigation'].append("Étudier la différenciation forte nécessaire")

            # Actions selon la qualité
            if avg_rating > 0 and avg_rating < 3.5:
                recommendations['strategic_advice'].append("Opportunité de qualité supérieure identifiée")
            elif avg_rating >= 4.2:
                recommendations['risk_mitigation'].append("Niveau d'excellence élevé requis")

            # Actions selon l'opportunité
            if opportunity_score >= 70:
                recommendations['success_factors'].append("Marché favorable - exécution qualitative essentielle")
            elif opportunity_score <= 40:
                recommendations['risk_mitigation'].append("Marché difficile - validation approfondie recommandée")

            # Insights stratégiques
            main_opportunities = strategic_insights.get('main_opportunities', [])
            for opp in main_opportunities[:2]:
                recommendations['strategic_advice'].append(opp)

            key_risks = strategic_insights.get('key_risks', [])
            for risk in key_risks[:2]:
                recommendations['risk_mitigation'].append(risk)

            # Prochaines étapes
            recommendations['next_steps'] = [
                "Valider les hypothèses par une étude terrain",
                "Analyser les réglementations locales",
                "Estimer l'investissement initial requis",
                "Définir le business plan détaillé"
            ]

        except Exception as e:
            logger.warning(f"⚠️ Erreur génération recommandations: {e}")

        return recommendations

    def _calculate_performance_metrics(self, analysis_time: float, ai_analysis: Dict) -> Dict:
        """Calcule les métriques de performance"""

        metrics = {
            'analysis_time': round(analysis_time, 2),
            'avg_analysis_time': round(self.total_analysis_time / max(self.analysis_count, 1), 2),
            'success_rate': round(self.success_count / max(self.analysis_count, 1) * 100, 1),
            'llm_performance': ai_analysis.get('performance_metrics', {})
        }

        # Évaluation qualité
        if ai_analysis.get('success'):
            ai_data = ai_analysis.get('analysis', {})
            confidence = ai_data.get('niveau_confiance', 'Moyen')

            if confidence == 'Élevé' and analysis_time <= 15:
                metrics['quality_rating'] = 'Excellent'
            elif confidence in ['Élevé', 'Moyen'] and analysis_time <= 30:
                metrics['quality_rating'] = 'Bon'
            else:
                metrics['quality_rating'] = 'Acceptable'
        else:
            metrics['quality_rating'] = 'Échec'

        return metrics

    def _error_response(self, error_message: str, analysis_time: float = 0) -> Dict:
        """Génère une réponse d'erreur standardisée"""

        return {
            'success': False,
            'error': error_message,
            'business_request': None,
            'market_analysis': None,
            'ai_analysis': None,
            'recommendations': None,
            'performance_metrics': {
                'analysis_time': round(analysis_time, 2),
                'quality_rating': 'Échec'
            }
        }

    def quick_evaluation(self, business_type: str, location: str) -> Dict:
        """Évaluation rapide (marché local + score IA uniquement)"""

        return self.analyze_business_opportunity(
            business_type,
            location,
            radius_km=3.0,
            analysis_depth='quick'
        )

    def test_system_health(self) -> Dict:
        """Test de santé du système complet"""

        logger.info(" Test de santé du système...")

        health_report = {
            'overall_status': 'unknown',
            'components': {},
            'performance': {},
            'recommendations': []
        }

        try:
            # Test MongoDB
            try:
                self._initialize_components()
                # Test simple de connexion
                health_report['components']['mongodb'] = 'operational'
            except Exception as e:
                health_report['components']['mongodb'] = f'error: {str(e)}'

            # Test LLM
            if self.llm_client:
                llm_test = self.llm_client.test_connection()
                health_report['components']['llm'] = 'operational' if llm_test[
                    'success'] else f"error: {llm_test['message']}"
                health_report['performance']['llm_response_time'] = llm_test.get('response_time', 0)

            # Statut global
            all_operational = all(
                status == 'operational'
                for status in health_report['components'].values()
            )

            health_report['overall_status'] = 'healthy' if all_operational else 'degraded'

            # Recommandations
            if health_report['components'].get('mongodb') != 'operational':
                health_report['recommendations'].append("Vérifier la connexion MongoDB")

            if health_report['components'].get('llm') != 'operational':
                health_report['recommendations'].append("Vérifier la connexion LLM")

            # Métriques globales
            if self.analysis_count > 0:
                health_report['performance']['total_analyses'] = self.analysis_count
                health_report['performance']['avg_response_time'] = round(
                    self.total_analysis_time / self.analysis_count, 2)
                health_report['performance']['success_rate'] = round(self.success_count / self.analysis_count * 100, 1)

        except Exception as e:
            health_report['overall_status'] = 'critical'
            health_report['error'] = str(e)

        logger.info(f" Statut système: {health_report['overall_status']}")
        return health_report

    def get_system_stats(self) -> Dict:
        """Statistiques d'utilisation du système"""

        stats = {
            'usage': {
                'total_analyses': self.analysis_count,
                'successful_analyses': self.success_count,
                'success_rate': round(self.success_count / max(self.analysis_count, 1) * 100, 1),
                'avg_analysis_time': round(self.total_analysis_time / max(self.analysis_count, 1), 2)
            },
            'llm_stats': {},
            'configuration': {
                'mongo_host': self.mongo_host,
                'mongo_port': self.mongo_port,
                'llm_url': LLMConfig.BASE_URL,
                'llm_model': LLMConfig.MODEL_NAME
            }
        }

        if self.llm_client:
            stats['llm_stats'] = self.llm_client.get_performance_stats()

        return stats

    def close(self):
        """Ferme les connexions"""

        logger.info(" Fermeture BusinessAnalyzer...")

        if self.market_analyzer:
            self.market_analyzer.close()

        # LLMClient utilise requests.Session qui se ferme automatiquement

        logger.info("✅ BusinessAnalyzer fermé")


# Interface simplifiée pour utilisation rapide
def analyze_business(business_type: str, location: str, radius_km: float = 5.0) -> Dict:
    """
    Interface simplifiée pour analyse rapide

    Usage:
        from ia.business_analyzer import analyze_business
        result = analyze_business("Restaurant", "Paris 75001")
    """

    analyzer = BusinessAnalyzer()
    try:
        return analyzer.analyze_business_opportunity(business_type, location, radius_km)
    finally:
        analyzer.close()
