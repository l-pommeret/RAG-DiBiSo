# Documentation du Pipeline RAG - Bibliothèques Paris-Saclay

## Table des matières
1. [Introduction](#introduction)
2. [Architecture générale](#architecture-générale)
3. [Phase 1: Collecte des données](#phase-1-collecte-des-données)
4. [Phase 2: Traitement des données](#phase-2-traitement-des-données)
5. [Phase 3: Création de la base de connaissances vectorielle](#phase-3-création-de-la-base-de-connaissances-vectorielle)
6. [Phase 4: Configuration du modèle LLM](#phase-4-configuration-du-modèle-llm)
7. [Phase 5: Pipeline RAG](#phase-5-pipeline-rag)
8. [Modules spécialisés](#modules-spécialisés)
9. [Interface utilisateur](#interface-utilisateur)
10. [Performances et optimisations](#performances-et-optimisations)
11. [Architecture technique détaillée](#architecture-technique-détaillée)

## Introduction

Le projet RAG-DiBiSo implémente un assistant conversationnel pour les bibliothèques de l'Université Paris-Saclay basé sur l'architecture RAG (Retrieval-Augmented Generation). Cette approche combine la récupération d'informations pertinentes depuis une base de connaissances avec la génération de réponses par un modèle de langage (LLM).

L'objectif est de fournir des réponses précises aux questions des utilisateurs concernant les services, horaires et ressources des bibliothèques universitaires, en s'appuyant sur des données structurées et actualisées.

## Architecture générale

Le pipeline RAG complet se décompose en 5 phases principales:

1. **Collecte des données**: Scraping et extraction des informations depuis les sites web des bibliothèques
2. **Traitement des données**: Nettoyage, structuration et préparation des données
3. **Création de la base de connaissances vectorielle**: Génération des embeddings et indexation vectorielle
4. **Configuration du modèle LLM**: Sélection et initialisation du modèle de langage
5. **Pipeline RAG**: Intégration de la récupération d'informations avec la génération de réponses

L'architecture est complétée par des modules spécialisés pour certaines fonctionnalités spécifiques (comme les horaires en temps réel) et une interface utilisateur.

## Phase 1: Collecte des données

### Web Scraping

Le projet utilise un scraper développé spécifiquement pour récupérer les informations des bibliothèques de Paris-Saclay.

**Implémentation**: `SimpleBibliothequesScraper` dans `simple_combined_scraper.py`

**Fonctionnalités principales**:
- Crawling récursif du site web à partir d'une URL de départ
- Limitation du nombre de pages scrapées pour éviter une surcharge
- Extraction du contenu principal des pages (texte, titres, etc.)
- Gestion des temporisations entre requêtes pour respecter le serveur

**Technologies utilisées**:
- `requests`: Pour les requêtes HTTP
- `BeautifulSoup4`: Pour le parsing du HTML
- `urllib.parse`: Pour la manipulation des URLs

**Mécanismes d'extraction**:
- Identification des contenus principaux via des sélecteurs CSS ciblés
- Nettoyage des éléments non pertinents (scripts, styles, etc.)
- Normalisation du texte extrait

### Formats de données collectées

Les données sont stockées dans deux formats:

1. **Fichiers texte brut** (.txt):
   - Un fichier par page scrapée
   - Stockés dans le répertoire `txt_data/`
   - Utilisés pour l'indexation vectorielle

2. **Fichiers JSON structurés** (.json):
   - Contiennent les métadonnées et le contenu structuré
   - Stockés dans le répertoire `data/`
   - Format: `{"url": "...", "title": "...", "content": "...", "main_content": "..."}`
   - Agrégés dans un fichier global `all_pages.json`

## Phase 2: Traitement des données

### Prétraitement et normalisation

**Implémentation**: `DataProcessor` dans `data_processor.py`

**Étapes de traitement**:
1. **Chargement**: Lecture des fichiers JSON et texte brut
2. **Transformation en Documents**: Création d'objets `Document` de LangChain avec métadonnées
3. **Chunking**: Division des documents en segments plus petits pour optimiser la recherche

**Paramètres de chunking**:
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

### Création des métadonnées

Chaque document est enrichi avec des métadonnées contextuelles:
- `source`: Origine du document (ex: "all_pages", "hours", nom de fichier)
- `title`: Titre de la page ou du document
- `url`: URL d'origine pour la référence
- `library`: Nom de la bibliothèque concernée (si applicable)

Ces métadonnées sont utilisées plus tard pour améliorer la pertinence des recherches et fournir des citations de sources.

## Phase 3: Création de la base de connaissances vectorielle

### Modèle d'embeddings

**Implémentation**: Dans la méthode `_initialize_embeddings()` de `EnhancedBibliothequeBot`

**Modèle utilisé**:
- **Nom**: `sentence-transformers/all-MiniLM-L6-v2`
- **Framework**: Hugging Face Transformers
- **Dimensions**: 384
- **Type**: Modèle de transformers pour la génération d'embeddings de phrases
- **Performances**: Optimisé pour un bon compromis entre qualité et rapidité
- **Accélération**: Support CUDA si disponible (configurable via variable d'environnement `USE_CUDA`)

**Fallback**: En cas d'échec d'initialisation, utilisation de `FakeEmbeddings` avec dimensionnalité 384 pour les tests.

### Base de données vectorielle

**Implémentation**: `_build_vectordb()` et `_load_vectordb()` dans `EnhancedBibliothequeBot`

**Technologie utilisée**: `ChromaDB`
- Base de données vectorielle open-source
- Support de la persistance sur disque
- Optimisée pour les recherches de similarité

**Configuration**:
- Stockage dans le répertoire `vectordb/`
- Index basé sur les embeddings générés par le modèle sentence-transformers
- Paramètre k=10 pour la recherche des documents les plus similaires

## Phase 4: Configuration du modèle LLM

### Modèles supportés

Le système supporte plusieurs modèles de langage, configurables via le paramètre `model_name`:

1. **'fake'** (mode test):
   - Utilise `FakeListLLM` de LangChain
   - Retourne des réponses prédéfinies pour les tests
   - Ne nécessite pas de ressources GPU

2. **'ollama'**:
   - Utilise `Ollama` de LangChain Community
   - Modèle: `llama3`
   - Paramètres: temperature=0.1, num_ctx=2048
   - Nécessite le service Ollama en cours d'exécution

3. **'llama'**:
   - Utilise `LlamaCpp` de LangChain
   - Modèles supportés:
     - Llama-2-7B-Chat (format GGUF)
     - Llama-3 8B si disponible localement
   - Paramètres optimisés pour GPU ou CPU
   - Configuration GPU adaptative:
     ```python
     n_gpu_layers = -1  # Utilisation complète du GPU
     f16_kv = True      # Optimisation mémoire avec float16
     n_batch = 512      # Taille de batch optimisée pour GPU
     ```

4. **'huggingface'**:
   - Utilise plusieurs modèles HuggingFace selon disponibilité:
     - Priorité 1: `bigscience/bloom-560m`
     - Fallback: `gpt2`
   - Pipeline personnalisé avec post-traitement des réponses

### Mécanisme de fallback

Pour assurer la robustesse, le système implémente un mécanisme de fallback en cascade:
1. Tentative d'initialisation du modèle demandé
2. En cas d'échec, essai d'un modèle plus léger
3. En dernier recours, utilisation du `FakeListLLM`

## Phase 5: Pipeline RAG

### Configuration du prompt

**Implémentation**: Méthode `_setup_qa_chain()` dans `EnhancedBibliothequeBot`

**Template de prompt principal**:
```
Vous êtes un assistant virtuel spécialisé dans les bibliothèques de l'Université Paris-Saclay.
Utilisez les informations suivantes pour répondre à la question.
Si vous ne connaissez pas la réponse, dites simplement que vous n'avez pas cette information et suggérez de contacter directement la bibliothèque.
Ne fabriquez pas de réponse si l'information n'est pas présente dans le contexte fourni.

Contexte:
{context}

Question: {question}

Réponse:
```

**Template adaptatif**: Version simplifiée pour les modèles plus légers comme HuggingFace.

### Retrieval (Récupération)

**Implémentation**: Combinaison de méthodes dans `EnhancedBibliothequeBot`

**Composants principaux**:
1. **Vector search**: Recherche par similarité dans ChromaDB
   ```python
   vector_retriever = vectordb.as_retriever(search_kwargs={"k": 10})
   ```

2. **Prétraitement des requêtes**:
   - Méthode `_preprocess_query()`
   - Enrichissement des requêtes avec des mots-clés additionnels selon le contexte
   - Exemples: ajout de "horaires heures ouverture fermeture" pour les questions d'horaires

3. **Reclassement des résultats**:
   - Méthode `_rerank_documents()`
   - Scoring sophistiqué basé sur:
     - Correspondance des mots-clés
     - Bonus pour les correspondances exactes
     - Bonus pour les titres pertinents
     - Bonus de fraîcheur pour les données d'horaires

### Generation (Génération)

**Implémentation**: Chaîne RAG basée sur LangChain

**Type de chaîne**: `RetrievalQA` avec `chain_type="stuff"`

**Configuration**:
```python
qa_chain = RetrievalQA.from_chain_type(
    llm=self.llm,
    chain_type="stuff",
    retriever=self.vector_retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)
```

**Paramètres de génération**:
- Temperature: 0.1 (faible pour favoriser les réponses factuelles)
- Top-p: 0.95-1.0 selon le modèle

### Gestion de la réponse finale

La réponse finale est composée de:
1. La réponse générée par le LLM
2. Les sources utilisées (documents récupérés, jusqu'à 3 affichés)
3. Des métadonnées pour la traçabilité

## Modules spécialisés

### Module des horaires

**Implémentation**: `HorairesModule` dans `modules/horaires_module.py`

**Fonctionnalités**:
- Récupération en temps réel des horaires des bibliothèques
- Support de 4 bibliothèques principales:
  - BU Sciences d'Orsay
  - BU Droit-Économie-Gestion (Sceaux)
  - BU Kremlin-Bicêtre
  - Lumen Learning Center Paris-Saclay

**Sources de données**:
1. **API Affluences**: `https://api.affluences.com/location/{id}/opening-hours`
2. **Sites web officiels**: Scraping des pages des bibliothèques

**Mécanisme de cache**:
- Cache configurable (par défaut 24h)
- Stockage dans le répertoire `cache/`
- Validation temporelle pour assurer la fraîcheur des données

**Détection des questions d'horaires**:
```python
def _is_horaires_question(self, question):
    # Mots-clés liés aux horaires
    horaires_keywords = [
        "horaire", "ouverture", "ouvre", "ouvert", 
        "fermeture", "ferme", "fermé",
        "heure", "temps", "quand", "moment", "période"
    ]
    
    # Vérifier si la question contient des mots-clés liés aux horaires
    if any(keyword in question for keyword in horaires_keywords):
        # Vérifier aussi si la question mentionne une bibliothèque
        bibliotheque_keywords = [
            "biblio", "bu ", "bibliothèque", "mediathèque", 
            "orsay", "sceaux", "kremlin", "bicêtre", "lumen"
        ]
        
        if any(keyword in question for keyword in bibliotheque_keywords):
            return True
    
    return False
```

### Intégration des modules

**Implémentation**: `ModuleIntegrator` dans `modules/integration.py`

**Mécanisme**:
1. Détection du type de question (ex: horaires)
2. Routage vers le module spécialisé approprié si disponible
3. Fallback sur le pipeline RAG standard si nécessaire

## Interface utilisateur

### Interface en ligne de commande

**Implémentation**: `chat.py`

**Modes d'utilisation**:
1. Interactif: Questions/réponses en console
2. Non-interactif: Réponse à une question unique via argument
3. Pipe: Lecture des questions depuis l'entrée standard

**Options**:
- `--model`: Choix du modèle LLM (fake, llama)
- `--use-cuda`: Activation de l'accélération GPU
- `--no-modules`: Désactivation des modules spécialisés
- `--rebuild`: Reconstruction de la base vectorielle

### Interface Web

**Implémentation**: `flask_app.py` et templates dans `templates/`

**Technologies**:
- Backend: Flask
- Frontend: HTML/CSS/JavaScript
- Communication: API REST simple

**Endpoints**:
- `/`: Interface utilisateur principale
- `/ask`: Endpoint POST pour poser des questions

**Fonctionnalités**:
- Interface de chat responsive
- Affichage des sources utilisées
- Indicateur de chargement pendant le traitement

## Performances et optimisations

### Optimisations d'embeddings

- Utilisation d'un modèle équilibré (all-MiniLM-L6-v2)
- Support CUDA pour accélérer la génération d'embeddings
- Persistance de la base vectorielle pour éviter la reconstruction

### Optimisations LLM

- Support des formats quantifiés (GGUF)
- Configurations spécifiques pour CPU vs GPU
- Paramètres optimisés:
  ```python
  n_gpu_layers = -1  # Utiliser toutes les couches GPU si disponible
  f16_kv = True      # Format float16 pour les clés/valeurs
  n_batch = 512      # Taille de batch optimisée
  ```

### Optimisations de recherche

- Reclassement des résultats pour améliorer la pertinence
- Prétraitement des requêtes avec enrichissement contextuel
- Combinaison des résultats de plusieurs méthodes de recherche

## Architecture technique détaillée

### Diagramme de classes

Les principales classes du système sont:

1. **EnhancedBibliothequeBot**
   - Classe centrale du pipeline RAG
   - Gère l'initialisation des embeddings, LLM et bases vectorielles
   - Implémente le traitement des requêtes et la génération de réponses

2. **DataProcessor**
   - Responsable du chargement et prétraitement des données
   - Création et persistance de la base vectorielle

3. **HorairesModule**
   - Module spécialisé pour les horaires en temps réel
   - Gère la récupération, le cache et le formatage des informations d'horaires

4. **ModuleIntegrator**
   - Intègre les modules spécialisés avec le pipeline RAG standard
   - Assure le routage des questions vers les modules appropriés

### Dépendances

Les principales bibliothèques utilisées sont:

1. **LangChain** (framework RAG):
   - `langchain-core`: Composants fondamentaux
   - `langchain-community`: Connecteurs pour différents outils et modèles
   - `langchain-text-splitters`: Outils de découpage de documents
   - `langchain-huggingface`: Intégration avec HuggingFace

2. **Embeddings et modèles**:
   - `sentence-transformers`: Pour les embeddings sémantiques
   - `transformers`: Pour les modèles de langage HuggingFace
   - `huggingface-hub`: Pour le téléchargement des modèles
   - `llama-cpp-python`: Pour les modèles Llama optimisés

3. **Base de données vectorielle**:
   - `chromadb`: Pour l'indexation et la recherche vectorielle

4. **Web scraping**:
   - `requests`: Pour les requêtes HTTP
   - `beautifulsoup4`: Pour le parsing HTML

5. **Interface web**:
   - `flask`: Pour l'API et l'interface web

### Configuration matérielle recommandée

- **CPU**: Multi-cœurs (4+ cœurs recommandés)
- **RAM**: 8 Go minimum, 16+ Go recommandés
- **GPU**: 
  - Optionnel mais recommandé pour les performances
  - VRAM: 8+ Go pour les modèles Llama-2 et Llama-3
  - Compatible CUDA pour l'accélération par Torch
- **Stockage**: 
  - 2+ Go pour les données et modèles de base
  - 10+ Go si utilisation de modèles Llama complets

---

Document généré le 8 avril 2025