from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

# Demander à l'utilisateur quoi rechercher
quoi_qui = input("Que voulez-vous rechercher ? (ex: restaurant, coiffeur, dentiste): ")
ou = input("Où ? (ex: Paris, Lyon, 75001): ")

# Configuration
driver = webdriver.Chrome()

try:
    # Aller sur pagesjaunes.fr
    driver.get("https://www.pagesjaunes.fr")
    
    # Attendre plus longtemps que la page se charge
    print("Chargement de la page...")
    time.sleep(5)
    
    # OBLIGATOIRE : Basculer vers l'iframe et fermer la popup
    print("Recherche de l'iframe de consentement...")
    popup_fermee = False
    
    try:
        wait = WebDriverWait(driver, 30)
        
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
                bouton_accepter = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                bouton_accepter.click()
                print(f"✓ Popup fermée avec le sélecteur: {selector}")
                popup_fermee = True
                break
            except Exception as e:
                print(f"Sélecteur {selector} échoué: {e}")
                continue
        
        # Revenir au document principal
        driver.switch_to.default_content()
        print("✓ Retour au document principal")
        
        if not popup_fermee:
            print("❌ ERREUR: Impossible de fermer la popup dans l'iframe.")
            exit()
        
        # Attendre que la popup disparaisse complètement
        print("Attente du chargement de la page principale...")
        time.sleep(8)
        
        # Vérifier que les champs de recherche sont maintenant présents
        wait.until(EC.presence_of_element_located((By.ID, "quoiqui")))
        print("✓ Page principale chargée")
        
    except Exception as e:
        print(f"❌ ERREUR lors de la gestion de l'iframe: {e}")
        # S'assurer qu'on est revenu au document principal
        driver.switch_to.default_content()
        exit()
    
    print("Remplissage des champs...")
    
    # Remplir les champs
    wait = WebDriverWait(driver, 15)
    
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
    
    time.sleep(5)
    print("🎉 Terminé !")
    
except Exception as e:
    print(f"❌ Erreur: {e}")

finally:
    input("Appuyez sur Entrée pour fermer le navigateur...")
    driver.quit() 