from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import base64
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PagesJaunesScraper:
    """Classe pour scraper PagesJaunes.fr"""
    
    def __init__(self, headless=False):
        """
        Initialise le scraper
        
        Args:
            headless (bool): Si True, lance le navigateur en mode headless
        """
        self.driver = None
        self.headless = headless
        self.tous_les_resultats = []
        self.dossier_sortie = "resultats"
        
    def _configurer_driver(self):
        """Configure et lance le driver Chrome"""
        try:
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            self.driver = webdriver.Chrome(options=options)
            logger.info("✅ Driver Chrome configuré")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la configuration du driver: {e}")
            return False
    
    def _fermer_popup_consentement(self):
        """Ferme la popup de consentement"""
        try:
            wait = WebDriverWait(self.driver, 15)
            
            # Trouver l'iframe de consentement
            iframe = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, 
                "iframe[title*='consentement'], iframe[title*='Fenêtre de consentement']"
            )))
            logger.debug("✓ Iframe trouvée, basculement...")
            
            # Basculer vers l'iframe
            self.driver.switch_to.frame(iframe)
            
            # Chercher le bouton d'acceptation
            selectors = [
                "button.button__acceptAll",
                "button[aria-label*='Accepter']", 
                "button.sc-furwcr.joOqIO.button.button--filled.button__acceptAll",
                "button.button--filled.button__acceptAll"
            ]
            
            for selector in selectors:
                try:
                    bouton_accepter = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    bouton_accepter.click()
                    logger.debug(f"✓ Popup fermée avec le sélecteur: {selector}")
                    break
                except:
                    continue
            
            # Revenir au document principal
            self.driver.switch_to.default_content()
            time.sleep(2)
            
            # Vérifier que les champs sont présents
            wait.until(EC.presence_of_element_located((By.ID, "quoiqui")))
            logger.info("✅ Popup de consentement fermée")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la fermeture de la popup: {e}")
            self.driver.switch_to.default_content()
            return False
    
    def _lancer_recherche(self, quoi_qui, ou):
        """Lance la recherche sur PagesJaunes"""
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Remplir le champ "quoi/qui"
            champ_quoiqui = wait.until(EC.element_to_be_clickable((By.ID, "quoiqui")))
            champ_quoiqui.clear()
            champ_quoiqui.send_keys(quoi_qui)
            
            # Remplir le champ "où"
            champ_ou = wait.until(EC.element_to_be_clickable((By.ID, "ou")))
            champ_ou.clear()
            champ_ou.send_keys(ou)
            
            # Cliquer sur recherche
            bouton_recherche = wait.until(EC.element_to_be_clickable((By.ID, "findId")))
            bouton_recherche.click()
            
            time.sleep(5)  # Attendre les résultats
            logger.info(f"✅ Recherche lancée: '{quoi_qui}' à '{ou}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche: {e}")
            return False
    
    def _extraire_donnees_etablissement(self):
        """Extrait toutes les données d'un établissement"""
        donnees = {
            "name": "",
            "professional": "false",
            "type": "",
            "address": "",
            "avis": [],
            "horaire": []
        }
        
        try:
            # 1. Nom
            try:
                nom_element = self.driver.find_element(By.CSS_SELECTOR, "h1.noTrad.no-margin")
                donnees["name"] = nom_element.text.strip()
            except:
                pass
            
            # 2. Professionnel certifié
            try:
                self.driver.find_element(By.CSS_SELECTOR, ".icon-certification-plein")
                donnees["professional"] = "true"
            except:
                donnees["professional"] = "false"
            
            # 3. Type
            try:
                type_element = self.driver.find_element(By.CSS_SELECTOR, ".activite.weborama-activity")
                donnees["type"] = type_element.text.strip()
            except:
                pass
            
            # 4. Adresse
            try:
                adresse_element = self.driver.find_element(By.CSS_SELECTOR, ".address.streetAddress .noTrad")
                donnees["address"] = adresse_element.text.strip()
            except:
                pass
            
            # 5. Avis
            donnees["avis"] = self._extraire_tous_les_avis()
            
            # 6. Horaires
            donnees["horaire"] = self._extraire_horaires()
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de l'extraction: {e}")
        
        return donnees
    
    def _extraire_tous_les_avis(self):
        """Extrait tous les avis avec gestion de la pagination"""
        tous_avis = []
        
        try:
            # Charger tous les avis
            while True:
                try:
                    bouton_plus = self.driver.find_element(By.CSS_SELECTOR, "#ScrollAvis .value")
                    if "Charger plus d'avis" in bouton_plus.text:
                        bouton_plus.click()
                        time.sleep(3)
                    else:
                        break
                except:
                    break
            
            # Extraire les avis
            avis_elements = self.driver.find_elements(By.CSS_SELECTOR, "li.avis")
            
            for avis in avis_elements:
                try:
                    note_element = avis.find_element(By.CSS_SELECTOR, ".fd-note strong")
                    note = note_element.text.strip()
                    
                    commentaire_element = avis.find_element(By.CSS_SELECTOR, ".commentaire")
                    commentaire = commentaire_element.text.strip()
                    
                    tous_avis.append([note, commentaire])
                    
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Erreur extraction avis: {e}")
        
        return tous_avis
    
    def _extraire_horaires(self):
        """Extrait les horaires d'ouverture"""
        horaires = []
        
        try:
            lignes_horaires = self.driver.find_elements(By.CSS_SELECTOR, ".liste-horaires-principaux tr")
            
            for ligne in lignes_horaires:
                try:
                    jour_element = ligne.find_element(By.CSS_SELECTOR, ".jour")
                    jour = jour_element.text.strip()
                    
                    try:
                        # Vérifier si fermé
                        ligne.find_element(By.CSS_SELECTOR, ".ferme")
                        horaire_str = f"Fermé -> {jour}"
                    except:
                        # Récupérer les horaires
                        horaires_elements = ligne.find_elements(By.CSS_SELECTOR, ".horaire")
                        if horaires_elements:
                            horaires_jour = [h.text.strip() for h in horaires_elements]
                            horaire_str = f"{' / '.join(horaires_jour)} -> {jour}"
                        else:
                            continue
                    
                    horaires.append([horaire_str])
                    
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Erreur extraction horaires: {e}")
        
        return horaires
    
    def _traiter_page_resultats(self, page_actuelle):
        """Traite tous les résultats d'une page"""
        numero_resultat_global = (page_actuelle - 1) * 20 + 1  # Estimation
        
        try:
            resultats = self.driver.find_elements(By.CSS_SELECTOR, "li.bi.bi-generic")
            logger.info(f"✅ {len(resultats)} résultats trouvés sur la page {page_actuelle}")
            
            if not resultats:
                return 0
            
            onglet_principal = self.driver.current_window_handle
            
            for i, resultat in enumerate(resultats, 1):
                try:
                    logger.info(f"Traitement résultat {numero_resultat_global}...")
                    
                    # Trouver le lien
                    lien_principal = resultat.find_element(By.CSS_SELECTOR, "a.bi-denomination")
                    nom_etablissement = lien_principal.text.strip()
                    href = lien_principal.get_attribute("href")
                    
                    url_finale = None
                    
                    # Gérer les liens dynamiques
                    if href == "#" or not href or "chercherlespros" in href:
                        try:
                            data_pjlb = lien_principal.get_attribute("data-pjlb")
                            if data_pjlb:
                                pjlb_data = json.loads(data_pjlb)
                                url_encoded = pjlb_data.get("url", "")
                                if url_encoded:
                                    url_decoded = base64.b64decode(url_encoded).decode('utf-8')
                                    url_finale = f"https://www.pagesjaunes.fr{url_decoded}"
                                else:
                                    numero_resultat_global += 1
                                    continue
                            else:
                                numero_resultat_global += 1
                                continue
                        except Exception as e:
                            logger.debug(f"Erreur décodage data-pjlb: {e}")
                            numero_resultat_global += 1
                            continue
                    else:
                        if "/pros/" not in href:
                            numero_resultat_global += 1
                            continue
                        url_finale = href
                    
                    # Ouvrir dans un nouvel onglet
                    self.driver.execute_script("window.open(arguments[0], '_blank');", url_finale)
                    time.sleep(2)
                    
                    # Basculer vers le nouvel onglet
                    tous_onglets = self.driver.window_handles
                    if len(tous_onglets) > 1:
                        nouvel_onglet = [o for o in tous_onglets if o != onglet_principal][0]
                        self.driver.switch_to.window(nouvel_onglet)
                        time.sleep(3)
                        
                        # Vérifier l'URL
                        url_actuelle = self.driver.current_url
                        if "chercherlespros" in url_actuelle:
                            self.driver.close()
                            self.driver.switch_to.window(onglet_principal)
                            numero_resultat_global += 1
                            continue
                        
                        # Extraire les données
                        donnees_etablissement = self._extraire_donnees_etablissement()
                        
                        if donnees_etablissement["name"]:
                            self.tous_les_resultats.append(donnees_etablissement)
                            logger.info(f"✅ Données extraites: {donnees_etablissement['name']}")
                        
                        # Fermer et revenir
                        self.driver.close()
                        self.driver.switch_to.window(onglet_principal)
                    
                    time.sleep(2)
                    numero_resultat_global += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur traitement résultat {numero_resultat_global}: {e}")
                    try:
                        self.driver.switch_to.window(onglet_principal)
                    except:
                        pass
                    numero_resultat_global += 1
                    continue
            
            return len(resultats)
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement page {page_actuelle}: {e}")
            return 0
    
    def _aller_page_suivante(self):
        """Navigue vers la page suivante"""
        try:
            lien_suivant = self.driver.find_element(By.CSS_SELECTOR, "a.link_pagination.next")
            
            data_pjlb = lien_suivant.get_attribute("data-pjlb")
            if data_pjlb:
                pjlb_data = json.loads(data_pjlb)
                url_encoded = pjlb_data.get("url", "")
                if url_encoded:
                    url_decoded = base64.b64decode(url_encoded).decode('utf-8')
                    url_page_suivante = f"https://www.pagesjaunes.fr{url_decoded}"
                    
                    self.driver.get(url_page_suivante)
                    time.sleep(5)
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _sauvegarder_resultats(self, quoi_qui, ou):
        """Sauvegarde les résultats en JSON"""
        if not os.path.exists(self.dossier_sortie):
            os.makedirs(self.dossier_sortie)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"resultats_pagesjaunes_{quoi_qui.replace(' ', '_')}_{ou.replace(' ', '_')}_{timestamp}.json"
        chemin_fichier = os.path.join(self.dossier_sortie, nom_fichier)
        
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            json.dump(self.tous_les_resultats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Résultats sauvegardés: {chemin_fichier}")
        return chemin_fichier
    
    def executer_scraping(self, quoi_qui, ou):
        """
        Exécute le processus complet de scraping
        
        Args:
            quoi_qui (str): Ce que l'on recherche
            ou (str): Où chercher
            
        Returns:
            str: Chemin vers le fichier JSON généré
        """
        try:
            logger.info(f"🚀 Début du scraping: '{quoi_qui}' à '{ou}'")
            
            # 1. Configurer le driver
            if not self._configurer_driver():
                return None
            
            # 2. Aller sur PagesJaunes
            self.driver.get("https://www.pagesjaunes.fr")
            time.sleep(3)
            
            # 3. Fermer la popup
            if not self._fermer_popup_consentement():
                logger.error("❌ Impossible de fermer la popup")
                return None
            
            # 4. Lancer la recherche
            if not self._lancer_recherche(quoi_qui, ou):
                logger.error("❌ Échec de la recherche")
                return None
            
            # 5. Traiter toutes les pages
            page_actuelle = 1
            
            while True:
                logger.info(f"📄 Traitement de la page {page_actuelle}")
                
                nb_resultats = self._traiter_page_resultats(page_actuelle)
                
                if nb_resultats == 0:
                    logger.info("Aucun résultat sur cette page - Arrêt")
                    break
                
                # Tenter d'aller à la page suivante
                if not self._aller_page_suivante():
                    logger.info("Pas de page suivante - Fin du scraping")
                    break
                
                page_actuelle += 1
            
            # 6. Sauvegarder
            logger.info(f"🎉 Scraping terminé - {len(self.tous_les_resultats)} établissements")
            chemin_fichier = self._sauvegarder_resultats(quoi_qui, ou)
            
            return chemin_fichier
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale du scraping: {e}")
            return None
            
        finally:
            if self.driver:
                self.driver.quit()


# Pour rétrocompatibilité avec l'ancien script
if __name__ == "__main__":
    # Demander à l'utilisateur
    quoi_qui = input("Que voulez-vous rechercher ? (ex: restaurant, coiffeur, dentiste): ")
    ou = input("Où ? (ex: Paris, Lyon, 75001): ")
    
    # Lancer le scraping
    scraper = PagesJaunesScraper()
    fichier_resultat = scraper.executer_scraping(quoi_qui, ou)
    
    if fichier_resultat:
        print(f"✅ Scraping terminé - Fichier: {fichier_resultat}")
    else:
        print("❌ Échec du scraping") 