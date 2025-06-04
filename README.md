# 🕷️ ScrapJaune - Scraper PagesJaunes avec MongoDB

Un système complet de scraping pour PagesJaunes.fr avec stockage automatique en base de données MongoDB.

## 📋 Fonctionnalités

- ✅ Scraping automatisé des pages PagesJaunes.fr
- ✅ Extraction complète des données d'établissements
- ✅ Gestion de la pagination automatique
- ✅ Stockage structuré en MongoDB
- ✅ Gestion des doublons intelligente
- ✅ Interface de menu intuitive
- ✅ Logs détaillés

## 🎯 Données extraites

Pour chaque établissement :

- **Nom** de l'établissement
- **Type/Activité** (restaurant, coiffeur, etc.)
- **Adresse** complète
- **Certification professionnelle** (oui/non)
- **Avis clients** (note + commentaire)
- **Horaires** d'ouverture
- **Métadonnées** (note moyenne, nombre d'avis, etc.)

## 🛠️ Installation

### Prérequis

1. **Python 3.7+**
2. **Google Chrome** (pour Selenium)
3. **MongoDB** (local ou distant)

### Installation des dépendances

```bash
pip install selenium pymongo
```

### Configuration Chrome

Assurez-vous que ChromeDriver est installé ou utilisez la gestion automatique de Selenium.

## 🚀 Utilisation

### Lancement du menu principal

```bash
cd ScrapJaune
python main.py
```

### Menu interactif

```
🕷️  SCRAPER PAGESJAUNES + MONGODB
============================================================
1. 🚀 Scraping complet (scraping + stockage MongoDB)
2. 📥 Stocker un fichier JSON existant en MongoDB
3. 📋 Lister les fichiers de résultats
4. 🔧 Scraping uniquement (sans stockage)
5. ❌ Quitter
============================================================
```

### Options disponibles

1. **Scraping complet** : Lance le scraping ET stocke automatiquement en MongoDB
2. **Stockage fichier existant** : Importe un fichier JSON déjà généré en MongoDB
3. **Lister fichiers** : Affiche tous les fichiers de résultats disponibles
4. **Scraping seul** : Lance seulement le scraping (génère un fichier JSON)

## 📁 Structure du projet

```
ScrapJaune/
├── main.py                                    # Script principal avec menu
├── src/
│   ├── scrapers/
│   │   └── pagesjaunes_simple_module.py      # Module de scraping
│   └── storage/
│       └── mongodb_storage.py                # Module de stockage MongoDB
├── resultats/                                 # Fichiers JSON générés
├── scraping.log                              # Logs d'exécution
└── README.md                                 # Documentation
```

## 🗃️ Structure des données

### Format JSON généré par le scraper

```json
[
  {
    "name": "Restaurant Le Gourmet",
    "professional": "true",
    "type": "Restaurant",
    "address": "123 Rue de la Paix, 75001 Paris",
    "avis": [
      ["4/5", "Excellent service et nourriture délicieuse"],
      ["5/5", "Je recommande vivement ce restaurant"]
    ],
    "horaire": [
      ["09:00-12:00 / 14:00-22:00 -> Lundi"],
      ["09:00-12:00 / 14:00-22:00 -> Mardi"],
      ["Fermé -> Dimanche"]
    ]
  }
]
```

### Structure MongoDB

```javascript
{
  "name": "Restaurant Le Gourmet",
  "professional": true,
  "type": "Restaurant",
  "address": "123 Rue de la Paix, 75001 Paris",
  "avis": [...],
  "horaires": {
    "Lundi": "09:00-12:00 / 14:00-22:00",
    "Mardi": "09:00-12:00 / 14:00-22:00",
    "Dimanche": "Fermé"
  },
  "metadata": {
    "hash_id": "abc123...",
    "inserted_at": "2024-01-15T10:30:00Z",
    "note_moyenne": 4.5,
    "nombre_avis": 2,
    "source": "pagesjaunes_scraper"
  },
  "searchable_name": "restaurant le gourmet",
  "has_reviews": true,
  "has_schedule": true
}
```

## ⚙️ Configuration

### MongoDB

Par défaut, le système se connecte à :

- **Host** : localhost
- **Port** : 27017
- **Base** : pagesjaunes_db
- **Collection** : pageJaune

### Modifier la configuration

Dans `main.py` :

```python
manager = ScrapingManager(mongo_host="votre_host", mongo_port=27017)
```

## 📊 Fonctionnalités avancées

### Gestion des doublons

Le système utilise un hash basé sur le nom + adresse pour éviter les doublons :

- **Nouvel établissement** → Insertion
- **Établissement existant** → Mise à jour
- **Données identiques** → Ignoré

### Index MongoDB automatiques

- Index textuel sur nom + type
- Index sur l'adresse
- Index sur les notes et avis
- Index unique sur le hash_id
- Index sur le statut professionnel

### Statistiques

Le système fournit des statistiques complètes :

- Nombre d'établissements traités
- Nouveaux insérés vs mis à jour
- Doublons ignorés
- Erreurs rencontrées
- Statistiques globales de la collection

## 🔧 Utilisation programmatique

### Scraping seul

```python
from src.scrapers.pagesjaunes_simple_module import PagesJaunesScraper

scraper = PagesJaunesScraper()
fichier = scraper.executer_scraping("restaurant", "Paris")
print(f"Résultats sauvés dans : {fichier}")
```

### Stockage seul

```python
from src.storage.mongodb_storage import load_and_store_data

success = load_and_store_data("resultats/mon_fichier.json")
```

### Processus complet

```python
from main import ScrapingManager

manager = ScrapingManager()
stats = manager.demarrer_scraping_complet("coiffeur", "Lyon")
print(stats)
```

## 📝 Logs

Les logs sont sauvegardés dans `scraping.log` et affichés en temps réel.

Niveaux de log :

- **INFO** : Progression générale
- **DEBUG** : Détails des opérations
- **WARNING** : Avertissements non bloquants
- **ERROR** : Erreurs importantes

## ⚠️ Limitations

- Nécessite une connexion internet stable
- Dépendant de la structure HTML de PagesJaunes
- Peut être affecté par les limitations de débit
- Nécessite Chrome installé

## 🤝 Contribution

Pour contribuer :

1. Fork le projet
2. Créez une branche feature
3. Commitez vos changements
4. Pushez vers la branche
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est à des fins éducatives. Respectez les conditions d'utilisation de PagesJaunes.fr.

---

**Développé avec ❤️ en Python**
