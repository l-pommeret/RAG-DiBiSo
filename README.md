# RAG-DiBiSo

Un système RAG (Retrieval-Augmented Generation) pour les bibliothèques de l'Université Paris-Saclay.

## Description

Ce projet permet d'extraire des informations du site web des bibliothèques de l'Université Paris-Saclay, de les indexer et de créer un chatbot capable de répondre aux questions des utilisateurs sur les bibliothèques, leurs services, et leurs ressources.

## Fonctionnalités

- **Scraping du site web** : Extraction des informations du site des bibliothèques
- **Indexation des données** : Création d'une base de données vectorielle pour la recherche
- **Interface de chat** : Interface en ligne de commande et Flask pour poser des questions
- **RAG** : Système de génération de réponses basé sur les données extraites
- **Modules spécialisés** : Extension pour les horaires et autres informations spécifiques

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/votre-username/RAG-DiBiSo.git
cd RAG-DiBiSo

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

### Extraction des données

```bash
python simple_combined_scraper.py --max_pages 100
```

### Système RAG

```bash
# Lancer le chatbot RAG avec modules spécialisés
python rag_chatbot_enhanced_with_modules.py
```

### Interface web

```bash
# Lancer l'interface web
python flask_app.py
```

## Structure du projet

- `simple_combined_scraper.py` : Scraper pour extraire des données du site
- `rag_chatbot_enhanced_with_modules.py` : Système RAG avec modules spécialisés
- `flask_app.py` : Interface web Flask
- `data/` : Données JSON extraites
- `txt_data/` : Fichiers texte extraits
- `vectordb/` : Base de données vectorielle
- `modules/` : Modules spécialisés (horaires, etc.)

## Licence

Ce projet est sous licence MIT.