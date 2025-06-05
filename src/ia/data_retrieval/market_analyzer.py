from .geo_search import GeographicSearchEngine
import logging
from statistics import mean, median

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """Analyseur de marché avec segmentation avancée"""

    def __init__(self, mongo_host='localhost', mongo_port=27017):
        self.geo_engine = GeographicSearchEngine(mongo_host, mongo_port)

    def analyze_market_opportunity(self, business_request, radius_km=5):
        """
        Analyse complète d'opportunité marché

        Returns: {
            'competitors': [...],
            'market_summary': {...},
            'opportunity_metrics': {...},
            'strategic_insights': {...}
        }
        """

        logger.info(f" Analyse marché: {business_request['type']} à {business_request['address']}")

        # 1. RECHERCHE CONCURRENTS
        competitors = self.geo_engine.find_market_competitors(
            business_request,
            radius_km=radius_km,
            max_results=20  # Plus large pour analyse
        )

        if not competitors:
            return self._generate_empty_market_analysis(business_request)

        # 2. ANALYSE GLOBALE DU MARCHÉ
        market_summary = self._analyze_market_summary(competitors)

        # 3. MÉTRIQUES D'OPPORTUNITÉ
        opportunity_metrics = self._calculate_opportunity_metrics(
            competitors,
            business_request
        )

        # 4. INSIGHTS STRATÉGIQUES
        strategic_insights = self._generate_strategic_insights(
            competitors,
            market_summary,
            opportunity_metrics
        )

        logger.info(f"✅ Analyse terminée: {len(competitors)} concurrents analysés")

        return {
            'competitors': competitors[:15],  # Limite pour LLM
            'market_summary': market_summary,
            'opportunity_metrics': opportunity_metrics,
            'strategic_insights': strategic_insights
        }

    def _analyze_market_summary(self, competitors):
        """Résumé statistique du marché"""

        if not competitors:
            return {}

        # Métriques de base
        notes = [c.get('note_moyenne', 0) for c in competitors if c.get('note_moyenne', 0) > 0]
        avis_counts = [c.get('nombre_avis', 0) for c in competitors]
        success_scores = [c.get('success_score', 5) for c in competitors]
        distances = [c.get('distance_km', 0) for c in competitors]

        # Répartition par position marché
        positions = [c.get('market_position', 'Moyen') for c in competitors]
        position_counts = {pos: positions.count(pos) for pos in set(positions)}

        # Répartition par niveau de menace
        threats = [c.get('threat_level', 'Modéré') for c in competitors]
        threat_counts = {threat: threats.count(threat) for threat in set(threats)}

        return {
            'total_competitors': len(competitors),
            'avg_rating': round(mean(notes), 2) if notes else 0,
            'median_rating': round(median(notes), 2) if notes else 0,
            'avg_review_count': round(mean(avis_counts)) if avis_counts else 0,
            'avg_success_score': round(mean(success_scores), 1),
            'market_density': self._assess_market_density(len(competitors)),
            'avg_distance': round(mean(distances), 2) if distances else 0,
            'position_distribution': position_counts,
            'threat_distribution': threat_counts,
            'quality_level': self._assess_market_quality(notes)
        }

    def _calculate_opportunity_metrics(self, competitors, business_request):
        """Calcule les métriques d'opportunité"""

        # Analyse concurrentielle
        high_performers = [c for c in competitors if c.get('success_score', 5) >= 7]
        weak_performers = [c for c in competitors if c.get('success_score', 5) <= 4]
        close_competitors = [c for c in competitors if c.get('distance_km', 999) <= 1]

        # Score d'opportunité global
        opportunity_score = self._calculate_opportunity_score(competitors)

        # Recommandations de positionnement
        positioning_advice = self._generate_positioning_advice(competitors)

        return {
            'opportunity_score': opportunity_score,
            'market_saturation': self._assess_saturation(competitors),
            'quality_gap': self._identify_quality_gap(competitors),
            'geographic_advantage': self._assess_geographic_advantage(competitors),
            'high_performers_count': len(high_performers),
            'weak_performers_count': len(weak_performers),
            'close_competitors_count': len(close_competitors),
            'positioning_advice': positioning_advice,
            'entry_difficulty': self._assess_entry_difficulty(competitors)
        }

    def _generate_strategic_insights(self, competitors, market_summary, opportunity_metrics):
        """Génère des insights stratégiques"""

        insights = {
            'main_opportunities': [],
            'key_risks': [],
            'success_factors': [],
            'differentiation_potential': []
        }

        # OPPORTUNITÉS
        if opportunity_metrics['weak_performers_count'] >= 3:
            insights['main_opportunities'].append("Marché avec plusieurs acteurs faibles à challenger")

        if market_summary['avg_rating'] < 3.5:
            insights['main_opportunities'].append("Qualité générale faible - opportunité d'excellence")

        if opportunity_metrics['geographic_advantage'] == "Élevé":
            insights['main_opportunities'].append("Zone géographique sous-desservie")

        # RISQUES
        if market_summary['total_competitors'] > 10:
            insights['key_risks'].append("Marché très concurrentiel")

        if opportunity_metrics['high_performers_count'] >= 5:
            insights['key_risks'].append("Plusieurs leaders établis")

        if opportunity_metrics['close_competitors_count'] >= 3:
            insights['key_risks'].append("Forte densité concurrentielle immédiate")

        # FACTEURS DE SUCCÈS
        top_performers = sorted(competitors, key=lambda x: x.get('success_score', 0), reverse=True)[:3]
        if top_performers:
            avg_top_rating = mean([p.get('note_moyenne', 0) for p in top_performers if p.get('note_moyenne', 0) > 0])
            if avg_top_rating:
                insights['success_factors'].append(
                    f"Excellence qualité requise (top performers: {avg_top_rating:.1f}/5)")

        # POTENTIEL DE DIFFÉRENCIATION
        if market_summary['quality_level'] == "Moyen":
            insights['differentiation_potential'].append("Différenciation par la qualité de service")

        return insights

    def _calculate_opportunity_score(self, competitors):
        """Score d'opportunité 0-100"""

        score = 50  # Base

        # Facteur densité
        density = len(competitors)
        if density == 0:
            score += 30
        elif density <= 3:
            score += 20
        elif density <= 7:
            score += 10
        elif density > 15:
            score -= 20

        # Facteur qualité
        avg_rating = mean([c.get('note_moyenne', 0) for c in competitors if c.get('note_moyenne', 0) > 0])
        if avg_rating:
            if avg_rating < 3.5:
                score += 15
            elif avg_rating > 4.3:
                score -= 10

        # Facteur performance
        weak_count = len([c for c in competitors if c.get('success_score', 5) <= 4])
        strong_count = len([c for c in competitors if c.get('success_score', 5) >= 8])

        score += min(weak_count * 5, 20)  # Max +20 pour les faibles
        score -= min(strong_count * 3, 15)  # Max -15 pour les forts

        return max(0, min(100, round(score)))

    def _assess_market_density(self, competitor_count):
        """Évalue la densité du marché"""
        if competitor_count == 0:
            return "Vide"
        elif competitor_count <= 3:
            return "Faible"
        elif competitor_count <= 8:
            return "Modérée"
        elif competitor_count <= 15:
            return "Élevée"
        else:
            return "Saturée"

    def _assess_market_quality(self, ratings):
        """Évalue la qualité générale du marché"""
        if not ratings:
            return "Inconnue"

        avg_rating = mean(ratings)
        if avg_rating >= 4.2:
            return "Très élevée"
        elif avg_rating >= 3.8:
            return "Élevée"
        elif avg_rating >= 3.2:
            return "Correcte"
        else:
            return "Faible"

    def _assess_saturation(self, competitors):
        """Évalue la saturation du marché"""
        density = len(competitors)
        close_competitors = len([c for c in competitors if c.get('distance_km', 999) <= 1])

        if density > 15 and close_competitors > 5:
            return "Très élevée"
        elif density > 10:
            return "Élevée"
        elif density > 5:
            return "Modérée"
        else:
            return "Faible"

    def _identify_quality_gap(self, competitors):
        """Identifie les gaps de qualité"""
        if not competitors:
            return "Inévaluable"

        ratings = [c.get('note_moyenne', 0) for c in competitors if c.get('note_moyenne', 0) > 0]
        if not ratings:
            return "Données insuffisantes"

        avg_rating = mean(ratings)
        weak_count = len([r for r in ratings if r < 3.5])

        if avg_rating < 3.5 and weak_count >= 3:
            return "Important"
        elif avg_rating < 4.0:
            return "Modéré"
        else:
            return "Faible"

    def _assess_geographic_advantage(self, competitors):
        """Évalue l'avantage géographique"""
        if not competitors:
            return "Très élevé"

        close_competitors = [c for c in competitors if c.get('distance_km', 999) <= 0.5]
        nearby_competitors = [c for c in competitors if c.get('distance_km', 999) <= 1.5]

        if len(close_competitors) == 0:
            return "Élevé"
        elif len(nearby_competitors) <= 2:
            return "Modéré"
        else:
            return "Faible"

    def _assess_entry_difficulty(self, competitors):
        """Évalue la difficulté d'entrée sur le marché"""
        strong_competitors = len([c for c in competitors if c.get('success_score', 5) >= 7])
        total_competitors = len(competitors)

        if total_competitors > 15 and strong_competitors >= 5:
            return "Très élevée"
        elif total_competitors > 10 or strong_competitors >= 3:
            return "Élevée"
        elif total_competitors > 5:
            return "Modérée"
        else:
            return "Faible"

    def _generate_positioning_advice(self, competitors):
        """Génère des conseils de positionnement"""
        advice = []

        if not competitors:
            advice.append("Marché vierge - Positionnement libre")
            return advice

        # Analyse des gaps
        ratings = [c.get('note_moyenne', 0) for c in competitors if c.get('note_moyenne', 0) > 0]
        if ratings and mean(ratings) < 3.8:
            advice.append("Miser sur la qualité supérieure")

        weak_count = len([c for c in competitors if c.get('success_score', 5) <= 4])
        if weak_count >= 3:
            advice.append("Opportunité de rachat/remplacement")

        professional_count = len([c for c in competitors if c.get('professional') == 'true'])
        if professional_count < len(competitors) * 0.5:
            advice.append("Certification professionnelle comme avantage")

        return advice if advice else ["Différenciation par le service"]

    def _generate_empty_market_analysis(self, business_request):
        """Analyse pour marché vide"""
        return {
            'competitors': [],
            'market_summary': {
                'total_competitors': 0,
                'market_density': 'Vide',
                'quality_level': 'Inconnue'
            },
            'opportunity_metrics': {
                'opportunity_score': 90,
                'market_saturation': 'Nulle',
                'geographic_advantage': 'Très élevé',
                'entry_difficulty': 'Faible'
            },
            'strategic_insights': {
                'main_opportunities': ['Marché pionnier sans concurrence'],
                'key_risks': ['Demande à valider', 'Investissement en visibilité'],
                'success_factors': ['Qualité de service', 'Marketing local'],
                'differentiation_potential': ['Premier entrant sur le marché']
            }
        }

    def close(self):
        """Ferme les connexions"""
        self.geo_engine.close()
