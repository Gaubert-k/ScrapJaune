#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal pour le scraping PagesJaunes et stockage MongoDB
Lie les scripts pagesjaunes_simple.py et mongodb_storage.py
"""

import os
import sys
import json
import glob
from datetime import datetime
import logging

# Ajouter le dossier src au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.pagesjaunes_simple_module import PagesJaunesScraper
from storage.mongodb_storage import load_and_store_data

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScrapingManager:
    """Gestionnaire principal pour le scraping et stockage"""
    
    def __init__(self, mongo_host="localhost", mongo_port=27017):
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port
        self.dossier_resultats = "resultats"
        
    def demarrer_scraping_complet(self, quoi_qui=None, ou=None, auto_store=True):
        """
        Lance le processus complet de scraping et stockage
        
        Args:
            quoi_qui (str): Ce que l'on recherche (ex: restaurant, coiffeur)
            ou (str): Où chercher (ex: Paris, Lyon, 75001)
            auto_store (bool): Si True, stocke automatiquement en MongoDB
        
        Returns:
            dict: Statistiques du processus
        """
        logger.info("=== DÉBUT DU PROCESSUS DE SCRAPING COMPLET ===")
        
        # 1. Demander les paramètres si non fournis
        if not quoi_qui:
            quoi_qui = input("Que voulez-vous rechercher ? (ex: restaurant, coiffeur, dentiste): ")
        if not ou:
            ou = input("Où ? (ex: Paris, Lyon, 75001): ")
            
        logger.info(f"Recherche: '{quoi_qui}' à '{ou}'")
        
        # 2. Lancer le scraping
        logger.info("Étape 1/3: Lancement du scraping PagesJaunes...")
        
        try:
            scraper = PagesJaunesScraper()
            fichier_json = scraper.executer_scraping(quoi_qui, ou)
            
            if not fichier_json or not os.path.exists(fichier_json):
                logger.error("❌ Échec du scraping - Aucun fichier généré")
                return {"success": False, "error": "Scraping échoué"}
                
            logger.info(f"✅ Scraping terminé - Fichier: {fichier_json}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du scraping: {e}")
            return {"success": False, "error": str(e)}
        
        # 3. Vérifier le contenu du fichier
        logger.info("Étape 2/3: Vérification des données extraites...")
        
        try:
            with open(fichier_json, 'r', encoding='utf-8') as f:
                donnees = json.load(f)
                
            nb_etablissements = len(donnees)
            logger.info(f"✅ {nb_etablissements} établissements trouvés dans le fichier")
            
            if nb_etablissements == 0:
                logger.warning("⚠️ Aucun établissement extrait")
                return {
                    "success": True,
                    "file_path": fichier_json,
                    "establishments_found": 0,
                    "stored_in_db": False
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la lecture du fichier JSON: {e}")
            return {"success": False, "error": f"Lecture fichier échouée: {e}"}
        
        # 4. Stockage en MongoDB (si demandé)
        if auto_store:
            logger.info("Étape 3/3: Stockage en MongoDB...")
            
            try:
                success_db = load_and_store_data(
                    fichier_json,
                    mongo_host=self.mongo_host,
                    mongo_port=self.mongo_port
                )
                
                if success_db:
                    logger.info("✅ Données stockées avec succès en MongoDB")
                    return {
                        "success": True,
                        "file_path": fichier_json,
                        "establishments_found": nb_etablissements,
                        "stored_in_db": True
                    }
                else:
                    logger.error("❌ Échec du stockage en MongoDB")
                    return {
                        "success": True,
                        "file_path": fichier_json,
                        "establishments_found": nb_etablissements,
                        "stored_in_db": False,
                        "db_error": "Stockage échoué"
                    }
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors du stockage MongoDB: {e}")
                return {
                    "success": True,
                    "file_path": fichier_json,
                    "establishments_found": nb_etablissements,
                    "stored_in_db": False,
                    "db_error": str(e)
                }
        else:
            logger.info("Étape 3/3: Stockage MongoDB ignoré (auto_store=False)")
            return {
                "success": True,
                "file_path": fichier_json,
                "establishments_found": nb_etablissements,
                "stored_in_db": False
            }
    
    def stocker_fichier_existant(self, chemin_fichier):
        """
        Stocke un fichier JSON existant en MongoDB
        
        Args:
            chemin_fichier (str): Chemin vers le fichier JSON
            
        Returns:
            bool: True si succès
        """
        logger.info(f"Stockage du fichier existant: {chemin_fichier}")
        
        if not os.path.exists(chemin_fichier):
            logger.error(f"❌ Fichier non trouvé: {chemin_fichier}")
            return False
            
        try:
            success = load_and_store_data(
                chemin_fichier,
                mongo_host=self.mongo_host,
                mongo_port=self.mongo_port
            )
            
            if success:
                logger.info("✅ Fichier stocké avec succès en MongoDB")
            else:
                logger.error("❌ Échec du stockage")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return False
    
    def lister_fichiers_resultats(self):
        """Liste tous les fichiers de résultats disponibles"""
        if not os.path.exists(self.dossier_resultats):
            logger.info("Aucun dossier de résultats trouvé")
            return []
            
        fichiers = glob.glob(os.path.join(self.dossier_resultats, "*.json"))
        fichiers.sort(key=os.path.getmtime, reverse=True)  # Plus récent en premier
        
        logger.info(f"{len(fichiers)} fichier(s) de résultats trouvé(s):")
        for i, fichier in enumerate(fichiers, 1):
            taille = os.path.getsize(fichier)
            mtime = datetime.fromtimestamp(os.path.getmtime(fichier))
            logger.info(f"  {i}. {os.path.basename(fichier)} ({taille} bytes, {mtime})")
            
        return fichiers


def menu_principal():
    """Menu interactif principal"""
    manager = ScrapingManager()
    
    while True:
        print("\n" + "="*60)
        print("🕷️  SCRAPER PAGESJAUNES + MONGODB")
        print("="*60)
        print("1. 🚀 Scraping complet (scraping + stockage MongoDB)")
        print("2. 📥 Stocker un fichier JSON existant en MongoDB")
        print("3. 📋 Lister les fichiers de résultats")
        print("4. 🔧 Scraping uniquement (sans stockage)")
        print("5. ❌ Quitter")
        print("="*60)
        
        choix = input("Votre choix (1-5): ").strip()
        
        if choix == "1":
            print("\n🚀 SCRAPING COMPLET")
            print("-" * 30)
            resultat = manager.demarrer_scraping_complet()
            
            print("\n📊 RÉSUMÉ:")
            if resultat["success"]:
                print(f"✅ Fichier généré: {resultat['file_path']}")
                print(f"📍 Établissements trouvés: {resultat['establishments_found']}")
                print(f"💾 Stocké en MongoDB: {'✅' if resultat['stored_in_db'] else '❌'}")
            else:
                print(f"❌ Erreur: {resultat['error']}")
                
        elif choix == "2":
            print("\n📥 STOCKAGE FICHIER EXISTANT")
            print("-" * 30)
            fichiers = manager.lister_fichiers_resultats()
            
            if not fichiers:
                print("Aucun fichier trouvé.")
                continue
                
            try:
                index = int(input("Numéro du fichier à stocker: ")) - 1
                if 0 <= index < len(fichiers):
                    manager.stocker_fichier_existant(fichiers[index])
                else:
                    print("❌ Numéro invalide")
            except ValueError:
                print("❌ Veuillez entrer un numéro valide")
                
        elif choix == "3":
            print("\n📋 FICHIERS DE RÉSULTATS")
            print("-" * 30)
            manager.lister_fichiers_resultats()
            
        elif choix == "4":
            print("\n🔧 SCRAPING UNIQUEMENT")
            print("-" * 30)
            resultat = manager.demarrer_scraping_complet(auto_store=False)
            
            print("\n📊 RÉSUMÉ:")
            if resultat["success"]:
                print(f"✅ Fichier généré: {resultat['file_path']}")
                print(f"📍 Établissements trouvés: {resultat['establishments_found']}")
                print("ℹ️ Stockage MongoDB ignoré")
            else:
                print(f"❌ Erreur: {resultat['error']}")
                
        elif choix == "5":
            print("👋 Au revoir!")
            break
            
        else:
            print("❌ Choix invalide")


if __name__ == "__main__":
    try:
        # Vérifier que nous sommes dans le bon répertoire
        if not os.path.exists("src"):
            print("❌ ERREUR: Veuillez exécuter ce script depuis le dossier ScrapJaune")
            print("💡 Exemple: cd ScrapJaune && python main.py")
            sys.exit(1)
            
        # Créer le dossier de résultats s'il n'existe pas
        if not os.path.exists("resultats"):
            os.makedirs("resultats")
            
        # Lancer le menu principal
        menu_principal()
        
    except KeyboardInterrupt:
        print("\n\n⏸️ Interruption par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1) 