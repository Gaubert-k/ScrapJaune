from typing import Dict, List, Optional
import json


class PromptManager:
    """Gestionnaire de prompts optimisés pour différents cas d'usage"""

    def __init__(self):
        self.prompt_templates = {
            'business_analysis': self._get_business_analysis_template(),
            'market_comparison': self._get_market_comparison_template(),
            'quick_evaluation': self._get_quick_evaluation_template()
        }

    def generate_business_analysis_prompt(self, market_data: Dict, business_request: Dict,
                                          analysis_type: str = 'business_analysis') -> str:
        """Génère un prompt optimisé selon le type d'analyse"""

        template = self.prompt_templates.get(analysis_type, self.prompt_templates['business_analysis'])

        # Préparation des données
        context_data = self._prepare_context_data(market_data, business_request)

        # Injection dans le template
        return template.format(**context_data)

    def _prepare_context_data(self, market_data: Dict, business_request: Dict) -> Dict:
        """Prépare les données contextuelles pour les prompts"""

        competitors = market_data.get('competitors', [])
        market_summary = market_data.get('market_summary', {})
        opportunity_metrics = market_data.get('opportunity_metrics', {})
        strategic_insights = market_data.get('strategic_insights', {})

        # Formatage des concurrents top 3
        top_competitors = self._format_top_competitors(competitors[:3])

        # Statistiques marché condensées
        market_stats = self._format_market_statistics(market_summary, opportunity_metrics)

        # Insights stratégiques
        insights_summary = self._format_strategic_insights(strategic_insights)

        # Métriques clés
        key_metrics = self._extract_key_metrics(market_summary, opportunity_metrics)

        return {
            'business_type': business_request.get('type', 'Non spécifié'),
            'business_location': business_request.get('address', 'Non spécifiée'),
            'top_competitors': top_competitors,
            'market_statistics': market_stats,
            'strategic_insights': insights_summary,
            'key_metrics': key_metrics,
            'competitor_count': len(competitors),
            'opportunity_score': opportunity_metrics.get('opportunity_score', 50),
            'market_quality': market_summary.get('quality_level', 'Inconnue'),
            'market_density': market_summary.get('market_density', 'Inconnue')
        }

    def _format_top_competitors(self, competitors: List[Dict]) -> str:
        """Formate les top concurrents pour le prompt"""

        if not competitors:
            return "Aucun concurrent direct identifié dans la zone"

        formatted_lines = []
        for i, comp in enumerate(competitors, 1):
            name = comp.get('name', 'Inconnu')[:40]
            rating = comp.get('note_moyenne', 0)
            reviews = comp.get('nombre_avis', 0)
            distance = comp.get('distance_km', 0)
            threat = comp.get('threat_level', 'Modéré')
            position = comp.get('market_position', 'Moyen')

            line = f"{i}. {name}"
            line += f" | Note: {rating}/5 ({reviews} avis)"
            line += f" | Distance: {distance}km"
            line += f" | Position: {position}"
            line += f" | Menace: {threat}"

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _format_market_statistics(self, market_summary: Dict, opportunity_metrics: Dict) -> str:
        """Formate les statistiques marché"""

        stats_lines = []

        # Données de base
        total_competitors = market_summary.get('total_competitors', 0)
        avg_rating = market_summary.get('avg_rating', 0)
        density = market_summary.get('market_density', 'Inconnue')
        quality = market_summary.get('quality_level', 'Inconnue')

        stats_lines.append(f"• Concurrents totaux: {total_competitors}")
        stats_lines.append(f"• Note moyenne marché: {avg_rating}/5")
        stats_lines.append(f"• Densité concurrentielle: {density}")
        stats_lines.append(f"• Niveau qualité général: {quality}")

        # Métriques d'opportunité
        opp_score = opportunity_metrics.get('opportunity_score', 50)
        saturation = opportunity_metrics.get('market_saturation', 'Inconnue')
        quality_gap = opportunity_metrics.get('quality_gap', 'Inévaluable')
        geo_advantage = opportunity_metrics.get('geographic_advantage', 'Modéré')

        stats_lines.append(f"• Score d'opportunité: {opp_score}/100")
        stats_lines.append(f"• Saturation marché: {saturation}")
        stats_lines.append(f"• Gap qualité: {quality_gap}")
        stats_lines.append(f"• Avantage géographique: {geo_advantage}")

        return "\n".join(stats_lines)

    def _format_strategic_insights(self, strategic_insights: Dict) -> str:
        """Formate les insights stratégiques"""

        if not strategic_insights:
            return "Analyse stratégique en cours..."

        insights_lines = []

        # Opportunités
        opportunities = strategic_insights.get('main_opportunities', [])
        if opportunities:
            insights_lines.append("OPPORTUNITÉS:")
            for opp in opportunities[:2]:  # Max 2
                insights_lines.append(f"  • {opp}")

        # Risques
        risks = strategic_insights.get('key_risks', [])
        if risks:
            insights_lines.append("RISQUES PRINCIPAUX:")
            for risk in risks[:2]:  # Max 2
                insights_lines.append(f"  • {risk}")

        return "\n".join(insights_lines)

    def _extract_key_metrics(self, market_summary: Dict, opportunity_metrics: Dict) -> str:
        """Extrait les métriques clés pour prompt condensé"""

        metrics = []

        # Concurrence
        total_comp = market_summary.get('total_competitors', 0)
        high_perf = opportunity_metrics.get('high_performers_count', 0)
        weak_perf = opportunity_metrics.get('weak_performers_count', 0)

        metrics.append(f"Concurrence: {total_comp} total ({high_perf} forts, {weak_perf} faibles)")

        # Qualité
        avg_rating = market_summary.get('avg_rating', 0)
        quality_gap = opportunity_metrics.get('quality_gap', 'Inévaluable')

        metrics.append(f"Qualité: {avg_rating}/5 moyenne, gap {quality_gap.lower()}")

        # Opportunité
        opp_score = opportunity_metrics.get('opportunity_score', 50)
        entry_difficulty = opportunity_metrics.get('entry_difficulty', 'Modérée')

        metrics.append(f"Opportunité: {opp_score}/100, difficulté {entry_difficulty.lower()}")

        return " | ".join(metrics)

    def _get_business_analysis_template(self) -> str:
        """Template principal d'analyse business"""

        return """Tu es un consultant business expert spécialisé en analyse de marché local. Analyse cette opportunité commerciale de manière factuelle et stratégique.

DEMANDE CLIENT:
Type d'activité: {business_type}
Localisation ciblée: {business_location}

ANALYSE MARCHÉ LOCAL:
{market_statistics}

TOP 3 CONCURRENTS DIRECTS:
{top_competitors}

INSIGHTS STRATÉGIQUES:
{strategic_insights}

MÉTRIQUES CLÉS: {key_metrics}

TÂCHE: Fournis une analyse experte sous forme JSON strictement respectant ce format:

{{
  "score_succes": [entier entre 0 et 100],
  "niveau_confiance": "[Faible/Moyen/Élevé]",
  "atout_principal": "[phrase de 15 mots max]",
  "risque_principal": "[phrase de 15 mots max]",
  "action_prioritaire": "[action concrète en 20 mots max]",
  "positionnement_conseille": "[stratégie en 25 mots max]"
}}

CONTRAINTES STRICTES:
- JSON valide uniquement (pas de texte avant/après)
- Scores basés sur les données marché fournies
- Phrases courtes et orientées action
- Factuel, pas d'opinions générales"""

    def _get_market_comparison_template(self) -> str:
        """Template pour comparaison marché"""

        return """Analyse comparative de marché. Type: {business_type} à {business_location}

CONCURRENCE ({competitor_count} acteurs):
{top_competitors}

BENCHMARKS MARCHÉ:
{market_statistics}

Analyse la position concurrentielle et réponds en JSON:

{{
  "score_succes": [0-100],
  "niveau_confiance": "[Faible/Moyen/Élevé]",
  "atout_principal": "[avantage concurrentiel identifié]",
  "risque_principal": "[menace principale du marché]",
  "action_prioritaire": "[première action recommandée]",
  "positionnement_conseille": "[stratégie de différenciation]"
}}"""

    def _get_quick_evaluation_template(self) -> str:
        """Template pour évaluation rapide"""

        return """Évaluation rapide: {business_type} - {business_location}

Marché: {market_density}, Qualité: {market_quality}, Opportunité: {opportunity_score}/100

Principaux concurrents:
{top_competitors}

Analyse express en JSON:

{{
  "score_succes": [0-100],
  "niveau_confiance": "[Faible/Moyen/Élevé]",
  "atout_principal": "[point fort du projet]",
  "risque_principal": "[obstacle principal]",
  "action_prioritaire": "[action immédiate]",
  "positionnement_conseille": "[positionnement recommandé]"
}}"""

    def validate_prompt_output(self, output: str) -> tuple[bool, List[str]]:
        """Valide que la sortie respecte le format attendu"""

        errors = []

        try:
            # Test JSON parsing
            parsed = json.loads(output.strip())

            # Vérification des champs requis
            required_fields = [
                'score_succes', 'niveau_confiance', 'atout_principal',
                'risque_principal', 'action_prioritaire', 'positionnement_conseille'
            ]

            for field in required_fields:
                if field not in parsed:
                    errors.append(f"Champ manquant: {field}")

            # Validation des types et valeurs
            if 'score_succes' in parsed:
                try:
                    score = int(parsed['score_succes'])
                    if not (0 <= score <= 100):
                        errors.append("score_succes doit être entre 0 et 100")
                except:
                    errors.append("score_succes doit être un entier")

            if 'niveau_confiance' in parsed:
                if parsed['niveau_confiance'] not in ['Faible', 'Moyen', 'Élevé']:
                    errors.append("niveau_confiance invalide")

            return len(errors) == 0, errors

        except json.JSONDecodeError as e:
            return False, [f"JSON invalide: {str(e)}"]
        except Exception as e:
            return False, [f"Erreur validation: {str(e)}"]

    def get_prompt_variants(self, analysis_type: str = 'business_analysis') -> List[str]:
        """Retourne des variantes de prompts pour tests A/B"""

        base_template = self.prompt_templates.get(analysis_type)

        variants = [
            base_template,  # Version originale

            # Variante plus directive
            base_template.replace(
                "Analyse cette opportunité",
                "Évalue précisément cette opportunité"
            ),

            # Variante avec focus concurrence
            base_template.replace(
                "TÂCHE: Fournis une analyse",
                "FOCUS: Analyse concurrentielle puis fournis une évaluation"
            )
        ]

        return variants
