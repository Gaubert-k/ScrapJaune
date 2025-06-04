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

# Demander à l'utilisateur quoi rechercher
quoi_qui = input("Que voulez-vous rechercher ? (ex: restaurant, coiffeur, dentiste): ")
ou = input("Où ? (ex: Paris, Lyon, 75001): ")

# Configuration
driver = webdriver.Chrome()

try:
    # Aller sur pagesjaunes.fr
    driver.get("https://www.pagesjaunes.fr")
    
    # Attendre que la page se charge
    print("Chargement de la page...")
    time.sleep(3)
    
    # OBLIGATOIRE : Basculer vers l'iframe et fermer la popup
    print("Recherche de l'iframe de consentement...")
    popup_fermee = False
    
    try:
        wait = WebDriverWait(driver, 15)  # Réduit de 30 à 15 secondes
        
        # Trouver l'iframe de consentement
        iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title*='consentement'], iframe[title*='Fenêtre de consentement']")))
        print("✓ Iframe trouvée, basculement...")
        
        # Basculer vers l'iframe
        driver.switch_to.frame(iframe)
        
        # Maintenant chercher le bouton dans l'iframe
        selectors = [
            "button.button__acceptAll",
            "button[aria-label*='Accepter']",
            "button.sc-furwcr.joOqIO.button.button--filled.button__acceptAll",
            "button.button--filled.button__acceptAll",
            "button:contains('Accepter')"
        ]
        
        for selector in selectors:
            try:
                print(f"Essai du sélecteur dans iframe: {selector}")
                bouton_accepter = WebDriverWait(driver, 5).until(  # Réduit de 10 à 5 secondes
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                bouton_accepter.click()
                print(f"✓ Popup fermée avec le sélecteur: {selector}")
                popup_fermee = True
                break
            except Exception as e:
                continue  # Pas de print pour aller plus vite
        
        # Revenir au document principal
        driver.switch_to.default_content()
        print("✓ Retour au document principal")
        
        if not popup_fermee:
            print("❌ ERREUR: Impossible de fermer la popup dans l'iframe.")
            exit()
        
        # Attendre que la popup disparaisse - réduit de 8 à 4 secondes
        print("Attente du chargement de la page principale...")
        time.sleep(4)
        
        # Vérifier que les champs de recherche sont maintenant présents
        wait.until(EC.presence_of_element_located((By.ID, "quoiqui")))
        print("✓ Page principale chargée")
        
    except Exception as e:
        print(f"❌ ERREUR lors de la gestion de l'iframe: {e}")
        # S'assurer qu'on est revenu au document principal
        driver.switch_to.default_content()
        exit()
    
    print("Remplissage des champs...")
    
    # Remplir les champs - réduit de 15 à 10 secondes
    wait = WebDriverWait(driver, 10)
    
    # Champ "quoi/qui"
    champ_quoiqui = wait.until(EC.element_to_be_clickable((By.ID, "quoiqui")))
    champ_quoiqui.clear()
    champ_quoiqui.send_keys(quoi_qui)
    print(f"✓ '{quoi_qui}' saisi")
    
    # Champ "où"
    champ_ou = wait.until(EC.element_to_be_clickable((By.ID, "ou")))
    champ_ou.clear()
    champ_ou.send_keys(ou)
    print(f"✓ '{ou}' saisi")
    
    # Bouton recherche
    bouton_recherche = wait.until(EC.element_to_be_clickable((By.ID, "findId")))
    bouton_recherche.click()
    print("✓ Recherche lancée")
    
    time.sleep(3)  # Réduit de 5 à 3 secondes
    print("🎉 Recherche terminée !")
    
    # Attendre que les résultats se chargent
    print("Attente du chargement des résultats...")
    time.sleep(5)
    
    # Parcourir tous les résultats
    print("Recherche des résultats...")
    
    page_actuelle = 1
    numero_resultat_global = 1
    
    while True:
        print(f"\n=== PAGE {page_actuelle} ===")
        
        try:
            # Trouver tous les éléments de résultats
            resultats = driver.find_elements(By.CSS_SELECTOR, "li.bi.bi-generic")
            print(f"✓ {len(resultats)} résultats trouvés sur cette page")
            
            if not resultats:
                print("❌ Aucun résultat trouvé sur cette page")
                break
            else:
                # Parcourir chaque résultat
                for i, resultat in enumerate(resultats, 1):
                    try:
                        print(f"\n--- Traitement du résultat {numero_resultat_global} (page {page_actuelle}, #{i}) ---")
                        
                        # Trouver le lien principal (nom de l'établissement)
                        lien_principal = resultat.find_element(By.CSS_SELECTOR, "a.bi-denomination")
                        nom_etablissement = lien_principal.text.strip()
                        href = lien_principal.get_attribute("href")
                        
                        print(f"Établissement: {nom_etablissement}")
                        print(f"Lien href: {href}")
                        
                        # Sauvegarder l'onglet principal
                        onglet_principal = driver.current_window_handle
                        
                        url_finale = None
                        
                        # Si le href est "#" ou contient chercherlespros, récupérer l'URL depuis data-pjlb
                        if href == "#" or not href or "chercherlespros" in href:
                            print("Lien dynamique détecté - Décodage de data-pjlb...")
                            try:
                                data_pjlb = lien_principal.get_attribute("data-pjlb")
                                if data_pjlb:
                                    # Décoder le JSON
                                    pjlb_data = json.loads(data_pjlb)
                                    url_encoded = pjlb_data.get("url", "")
                                    if url_encoded:
                                        # Décoder de base64
                                        url_decoded = base64.b64decode(url_encoded).decode('utf-8')
                                        # Construire l'URL complète
                                        url_finale = f"https://www.pagesjaunes.fr{url_decoded}"
                                        print(f"URL décodée: {url_finale}")
                                    else:
                                        print("⚠️  Pas d'URL dans data-pjlb - Ignoré")
                                        numero_resultat_global += 1
                                        continue
                                else:
                                    print("⚠️  Pas de data-pjlb trouvé - Ignoré")
                                    numero_resultat_global += 1
                                    continue
                            except Exception as e:
                                print(f"⚠️  Erreur lors du décodage data-pjlb: {e} - Ignoré")
                                numero_resultat_global += 1
                                continue
                        else:
                            # Vérifier si c'est un vrai lien de professionnel
                            if "/pros/" not in href:
                                print("⚠️  Lien invalide ou ne pointe pas vers un professionnel - Ignoré")
                                numero_resultat_global += 1
                                continue
                            url_finale = href
                        
                        # Ouvrir l'URL finale dans un nouvel onglet
                        driver.execute_script("window.open(arguments[0], '_blank');", url_finale)
                        print("✓ Nouvel onglet ouvert")
                        
                        # Attendre un peu que l'onglet s'ouvre
                        time.sleep(2)
                        
                        # Basculer vers le nouvel onglet
                        tous_onglets = driver.window_handles
                        if len(tous_onglets) > 1:
                            nouvel_onglet = [onglet for onglet in tous_onglets if onglet != onglet_principal][0]
                            driver.switch_to.window(nouvel_onglet)
                            print("✓ Basculement vers le nouvel onglet")
                            
                            # Attendre que la page se charge
                            time.sleep(3)
                            
                            # Vérifier que nous sommes bien sur une page de professionnel
                            url_actuelle = driver.current_url
                            print(f"Page chargée: {url_actuelle}")
                            
                            if "chercherlespros" in url_actuelle:
                                print("⚠️  Page redirigée vers la recherche - Lien invalide")
                                driver.close()
                                driver.switch_to.window(onglet_principal)
                                numero_resultat_global += 1
                                continue
                            
                            # Fermer l'onglet actuel
                            driver.close()
                            print("✓ Onglet fermé")
                            
                            # Revenir à l'onglet principal
                            driver.switch_to.window(onglet_principal)
                            print("✓ Retour à l'onglet principal")
                        else:
                            print("⚠️  Aucun nouvel onglet créé - Ignoré")
                        
                        # Petite pause entre les résultats
                        time.sleep(2)
                        numero_resultat_global += 1
                        
                    except Exception as e:
                        print(f"❌ Erreur lors du traitement du résultat {numero_resultat_global}: {e}")
                        # S'assurer qu'on est sur l'onglet principal
                        try:
                            driver.switch_to.window(onglet_principal)
                        except:
                            pass
                        numero_resultat_global += 1
                        continue
                
                print(f"\n✓ Page {page_actuelle} terminée ({len(resultats)} résultats traités)")
        
        except Exception as e:
            print(f"❌ Erreur lors de la recherche des résultats sur la page {page_actuelle}: {e}")
            break
        
        # Chercher le lien "Suivant" pour passer à la page suivante
        print(f"\nRecherche du lien 'Suivant'...")
        try:
            lien_suivant = driver.find_element(By.CSS_SELECTOR, "a.link_pagination.next")
            print("✓ Lien 'Suivant' trouvé")
            
            # Décoder l'URL de la page suivante
            try:
                data_pjlb = lien_suivant.get_attribute("data-pjlb")
                if data_pjlb:
                    # Décoder le JSON
                    pjlb_data = json.loads(data_pjlb)
                    url_encoded = pjlb_data.get("url", "")
                    if url_encoded:
                        # Décoder de base64
                        url_decoded = base64.b64decode(url_encoded).decode('utf-8')
                        # Construire l'URL complète
                        url_page_suivante = f"https://www.pagesjaunes.fr{url_decoded}"
                        print(f"URL page suivante: {url_page_suivante}")
                        
                        # Naviguer vers la page suivante
                        driver.get(url_page_suivante)
                        print("✓ Navigation vers la page suivante")
                        
                        # Attendre que la nouvelle page se charge
                        time.sleep(5)
                        page_actuelle += 1
                        
                    else:
                        print("⚠️  Pas d'URL dans data-pjlb du lien suivant - Fin de pagination")
                        break
                else:
                    print("⚠️  Pas de data-pjlb dans le lien suivant - Fin de pagination")
                    break
            except Exception as e:
                print(f"⚠️  Erreur lors du décodage du lien suivant: {e} - Fin de pagination")
                break
                
        except Exception as e:
            print("⚠️  Pas de lien 'Suivant' trouvé - Fin de pagination")
            break
    
    print(f"\n🎉 Traitement terminé pour {numero_resultat_global-1} résultats sur {page_actuelle} page(s) !")
    
except Exception as e:
    print(f"❌ Erreur: {e}")

finally:
    input("Appuyez sur Entrée pour fermer le navigateur...")
    driver.quit() 