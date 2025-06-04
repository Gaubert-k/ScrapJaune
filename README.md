# 🕷️ ScrapJaune - Scraper PagesJaunes avec MongoDB

Un système complet de scraping pour PagesJaunes.fr avec stockage automatique en collections MongoDB organisées par type d'établissement.

## 📋 Fonctionnalités

- ✅ Scraping automatisé des pages PagesJaunes.fr
- ✅ Extraction complète des données d'établissements
- ✅ Gestion de la pagination automatique
- ✅ **Collections automatiques par type** : Restaurants, Coiffeurs, Dentistes, etc.
- ✅ **Création automatique** de nouvelles collections pour nouveaux types
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

## 🗃️ Organisation MongoDB

### Collections automatiques par type

Le système crée automatiquement une collection pour chaque type d'établissement :

```
pagesjaunes_db/
├── restaurant/          # Collection des restaurants
├── coiffeur/           # Collection des coiffeurs
├── dentiste/           # Collection des dentistes
├── boulangerie/        # Collection des boulangeries
└── ...                 # Autres types découverts automatiquement
```

### Noms de collections automatiques

Les types sont automatiquement nettoyés pour créer des noms valides :

| Type original           | Collection MongoDB    |
| ----------------------- | --------------------- |
| "Restaurant"            | `restaurant`          |
| "Coiffeur / Barbier"    | `coiffeur_barbier`    |
| "Dentiste - Chirurgien" | `dentiste_chirurgien` |
| "Auto-École"            | `auto_ecole`          |

### Avantages de cette organisation

✅ **Organisation claire** : Chaque secteur dans sa propre collection
✅ **Performances optimales** : Requêtes plus rapides par type
✅ **Évolutivité** : Nouveaux types = nouvelles collections automatiques
✅ **Analyses sectorielles** : Statistiques par type d'activité
✅ **Index spécialisés** : Optimisation par secteur

## 🛠️ Installation

### Prérequis

1. **Python 3.7+**
2. **Google Chrome** (pour Selenium)
3. **MongoDB** (local ou distant)

### Installation des dépendances

```bash
pip install -r requirements.txt
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
💾 Mode: Collections par type d'établissement
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
├── requirements.txt                          # Dépendances
└── README.md                                 # Documentation
```

## 🗃️ Structure des données MongoDB

### Document type dans une collection

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
- **Mode** : Collections par type

### Modifier la configuration

Dans `main.py` :

```python
manager = ScrapingManager(
    mongo_host="votre_host",
    mongo_port=27017
)
```

## 📊 Fonctionnalités avancées

### Gestion automatique des collections

- **Détection automatique** : Nouveau type = nouvelle collection
- **Nettoyage des noms** : Caractères spéciaux gérés automatiquement
- **Index automatiques** : Chaque collection a ses propres index
- **Statistiques par type** : Métriques détaillées par secteur

### Gestion des doublons

Le système utilise un hash basé sur le nom + adresse pour éviter les doublons :

- **Nouvel établissement** → Insertion
- **Établissement existant** → Mise à jour
- **Données identiques** → Ignoré

### Index MongoDB automatiques

**Pour chaque collection :**

- Index textuel sur nom + type
- Index sur l'adresse
- Index sur les notes et avis
- Index unique sur le hash_id
- Index sur le statut professionnel
- Index sur la date d'insertion

### Statistiques détaillées

```
=== STATISTIQUES GLOBALES ===
total_establishments: 156
average_rating: 4.2
collections_count: 8

=== DÉTAILS PAR TYPE ===
restaurant: 45 établissements, note moyenne: 4.3
coiffeur: 32 établissements, note moyenne: 4.1
dentiste: 28 établissements, note moyenne: 4.5
...
```

## 🔧 Utilisation programmatique

### Scraping complet

```python
from main import ScrapingManager

manager = ScrapingManager()
stats = manager.demarrer_scraping_complet("restaurant", "Paris")
```

### Stockage seul

```python
from src.storage.mongodb_storage import load_and_store_data

success = load_and_store_data("resultats/mon_fichier.json")
```

### Accès direct aux collections

```python
from pymongo import MongoClient

client = MongoClient("localhost", 27017)
db = client.pagesjaunes_db

# Accès par type
restaurants = db.restaurant.find({"professional": True})
coiffeurs = db.coiffeur.find({"metadata.note_moyenne": {"$gte": 4.0}})
dentistes = db.dentiste.find({"has_reviews": True})
```

### Requêtes utiles

```python
# Top 10 des restaurants les mieux notés
top_restaurants = db.restaurant.find().sort("metadata.note_moyenne", -1).limit(10)

# Coiffeurs professionnels à Paris
coiffeurs_paris = db.coiffeur.find({
    "professional": True,
    "address": {"$regex": "Paris", "$options": "i"}
})

# Dentistes avec horaires d'ouverture
dentistes_ouverts = db.dentiste.find({"has_schedule": True})
```

## 📝 Logs

Les logs sont sauvegardés dans `scraping.log` et affichés en temps réel.

Informations trackées :

- **Collections créées** : Notification lors de création automatique
- **Types découverts** : Liste des collections créées
- **Statistiques par type** : Détails par secteur d'activité

## ⚠️ Limitations

- Nécessite une connexion internet stable
- Dépendant de la structure HTML de PagesJaunes
- Peut être affecté par les limitations de débit
- Nécessite Chrome installé
- **Noms de collections** : Les types très longs sont tronqués (max 50 caractères)

## 💡 Exemples d'utilisation

### Analyse par secteur

```python
# Comparer les notes moyennes par secteur
pipeline = [
    {"$group": {
        "_id": "$type",
        "note_moyenne": {"$avg": "$metadata.note_moyenne"},
        "count": {"$sum": 1}
    }},
    {"$sort": {"note_moyenne": -1}}
]

# Exécuter sur toutes les collections
for collection_name in db.list_collection_names():
    if not collection_name.startswith('system.'):
        result = list(db[collection_name].aggregate(pipeline))
        print(f"{collection_name}: {result}")
```

### Recherche géographique

```python
# Tous les établissements d'un arrondissement
arr_75001 = []
for collection_name in db.list_collection_names():
    if not collection_name.startswith('system.'):
        results = db[collection_name].find({
            "address": {"$regex": "75001", "$options": "i"}
        })
        arr_75001.extend(list(results))
```

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
