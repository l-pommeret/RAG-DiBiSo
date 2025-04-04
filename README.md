# RAG-DiBiSo

Un système RAG (Retrieval-Augmented Generation) pour les bibliothèques de l'Université Paris-Saclay.

## Description

Ce projet permet d'extraire des informations du site web des bibliothèques de l'Université Paris-Saclay, de les indexer et de créer un chatbot capable de répondre aux questions des utilisateurs sur les bibliothèques, leurs services, et leurs ressources.

Il intègre le scraper du projet qa_haystack pour l'extraction des données.

## Fonctionnalités

- **Scraping du site web** : Extraction des informations du site des bibliothèques
- **Indexation des données** : Création d'une base de données vectorielle pour la recherche
- **Interface de chat** : Interface en ligne de commande et Flask pour poser des questions
- **RAG** : Système de génération de réponses basé sur les données extraites

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
# Utiliser le scraper simple avec le fichier de sous-répertoires
python simple_combined_scraper.py --subdirs qa_haystack/DiBISOData/subdirectories.txt

# Ou faire un crawl récursif du site
python simple_combined_scraper.py --max_pages 20
```

### Système RAG

```bash
# Lancer le chatbot RAG simple
python simple_rag.py

# Lancer le chatbot RAG avancé (nécessite PyTorch compatible)
python rag_chatbot_enhanced.py
```

### Interface web

```bash
# Lancer l'interface web
python flask_app.py
```

## Structure du projet

- `simple_combined_scraper.py` : Version simplifiée du scraper combiné
- `simple_rag.py` : Système RAG simple basé sur les mots-clés
- `rag_chatbot_enhanced.py` : Système RAG avancé avec LLM
- `flask_app.py` : Interface web Flask
- `data/` : Données JSON extraites
- `txt_data/` : Fichiers texte extraits
- `vectordb/` : Base de données vectorielle
- `test_*.py` : Scripts de test

## Notes d'intégration

Pour plus de détails sur l'intégration du scraper qa_haystack, consultez [README_integration.md](README_integration.md).

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.