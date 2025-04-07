# Architecture du Système RAG-DiBiSo

## Introduction

RAG-DiBiSo est un système de questions-réponses sur les bibliothèques de l'Université Paris-Saclay basé sur l'architecture RAG (Retrieval-Augmented Generation). Le système est conçu pour offrir des réponses précises et contextuelles aux questions des utilisateurs sur les horaires, services et ressources des bibliothèques.

Ce document détaille l'architecture technique du système, ses composants, et les méthodes d'amélioration implémentées pour optimiser la pertinence des réponses.

## Vue d'ensemble de l'architecture

Le système RAG-DiBiSo combine plusieurs approches complémentaires pour maximiser la qualité des réponses :

1. **Système RAG de base** : Utilise des embeddings vectoriels pour récupérer les documents pertinents
2. **Recherche BM25** : Améliore la recherche par mots-clés précis
3. **Algorithme de reranking** : Affine les résultats en reclassant les documents selon leur pertinence
4. **Modules spécialisés** : Fournit des réponses dynamiques pour des requêtes spécifiques (ex: horaires)

Cette architecture hybride offre un équilibre entre information statique et données temps réel, permettant une meilleure expérience utilisateur.

## Composants du système

### 1. Récupération basée sur les embeddings vectoriels

La base du système repose sur une recherche vectorielle standard :

```
Texte de la question → Embedding → Recherche de similarité → Documents pertinents
```

**Comment ça fonctionne** :

1. Le texte de la question est converti en un vecteur (embedding) dans un espace dimensionnel
2. On recherche les documents dont les embeddings sont les plus proches (similarité cosinus)
3. Les documents les plus similaires sont récupérés

**Avantages** :
- Capture la sémantique et pas seulement des correspondances exactes
- Fonctionne bien pour des questions conceptuelles ou paraphrasées

**Limitations** :
- Peut manquer des correspondances exactes importantes
- Les relations sémantiques peuvent être trop générales

### 2. BM25 (Best Matching 25)

BM25 est un algorithme de recherche classique basé sur la fréquence des termes (TF-IDF amélioré) :

```
Question → Analyse des termes → Pondération BM25 → Documents pertinents
```

**Comment ça fonctionne** :

1. Analyse la question pour en extraire les termes importants
2. Évalue chaque document en fonction de la présence de ces termes
3. Calcule un score en tenant compte de :
   - La fréquence du terme dans le document
   - La rareté du terme dans l'ensemble des documents
   - La longueur du document (normalisation)

**Formule simplifiée** :

Pour chaque terme de la requête, BM25 calcule :
```
score(D,Q) = ∑ IDF(q) × (f(q,D) × (k1+1)) / (f(q,D) + k1 × (1-b+b × |D|/avgdl))
```
Où:
- `f(q,D)` est la fréquence du terme dans le document
- `IDF(q)` est l'inverse de la fréquence du document
- `|D|` est la longueur du document
- `avgdl` est la longueur moyenne des documents
- `k1` et `b` sont des paramètres d'ajustement

**Avantages** :
- Très efficace pour les correspondances exactes
- Performant pour les mots-clés précis (comme "horaires")
- Ne nécessite pas d'apprentissage préalable

**Limitations** :
- Ne comprend pas les relations sémantiques
- Sensible aux fautes d'orthographe et variations

### 3. Algorithme de reranking personnalisé

Le reranking permet d'affiner les résultats combinés du BM25 et des embeddings :

```
Documents combinés → Calcul de scores personnalisés → Documents reclassés
```

**Comment ça fonctionne** :

1. Combine les résultats des deux méthodes de recherche
2. Évalue chaque document selon plusieurs critères :
   - Correspondance des mots-clés (fréquence pondérée)
   - Correspondance exacte de phrases (bonus important)
   - Pertinence du titre du document
   - Fraîcheur de l'information (pour certaines données)
   - Correspondance avec le type de question (bonus thématique)

**Avantages** :
- Améliore la précision des résultats
- Peut favoriser certains documents en fonction du contexte
- Adaptable aux différents types de questions

### 4. Modules spécialisés

Pour certains types de requêtes fréquentes, des modules dédiés offrent des réponses optimisées :

```
Question → Détection de l'intention → Délégation au module spécialisé → Réponse précise
```

**Exemple : Module Horaires**

1. Détecte les questions sur les horaires des bibliothèques
2. Récupère les informations à jour depuis des sources officielles (API Affluences)
3. Formate une réponse précise avec les horaires actuels
4. Ajoute un lien vers la source officielle pour plus d'informations

**Avantages** :
- Informations toujours à jour
- Réponses plus précises que ce qui est stocké dans la base de connaissance
- Meilleure expérience utilisateur pour les questions courantes

## Processus de traitement des questions

Le traitement complet d'une question suit ce flux :

1. **Prétraitement de la question**
   - Normalisation
   - Détection de l'intention
   - Enrichissement avec mots-clés pertinents

2. **Recherche de documents**
   - Recherche vectorielle
   - Recherche BM25
   - Fusion des résultats

3. **Reranking des documents**
   - Calcul de scores personnalisés
   - Tri des documents

4. **Génération de la réponse**
   - Si module spécialisé : réponse directe du module
   - Sinon : envoi des documents pertinents au LLM avec un prompt approprié

5. **Post-traitement**
   - Formatage de la réponse
   - Ajout des sources

## Optimisations techniques

### 1. Prétraitement de la question

Pour améliorer la pertinence des résultats, le système analyse la question et ajoute des termes pertinents :

```python
def _preprocess_query(self, query):
    query_lower = query.lower()
    
    # Détection de requêtes sur les horaires
    if any(word in query_lower for word in ["horaire", "ouvert", "ferme", "heures", "quand"]):
        if any(word in query_lower for word in ["bibliothèque", "biblio", "bu"]):
            # Ajouter des mots-clés spécifiques aux horaires
            return f"{query} horaires heures ouverture fermeture"
    
    # Autres cas spécifiques...
    
    return query
```

### 2. Détection des questions sur les horaires

Le système identifie intelligemment les questions portant sur les horaires :

```python
def _is_horaires_question(self, question):
    question = question.lower()
    
    # Mots-clés liés aux horaires
    horaires_keywords = [
        "horaire", "ouverture", "ouvre", "ouvert", 
        "fermeture", "ferme", "fermé",
        "heure", "temps", "quand"
    ]
    
    # Vérifier si la question contient des mots-clés liés aux horaires
    if any(keyword in question for keyword in horaires_keywords):
        # Vérifier aussi si la question mentionne une bibliothèque
        bibliotheque_keywords = [
            "biblio", "bu ", "bibliothèque", "orsay", "sceaux"
        ]
        
        if any(keyword in question for keyword in bibliotheque_keywords):
            return True
    
    return False
```

### 3. Algorithme de reranking détaillé

Le reranking utilise plusieurs facteurs pour améliorer la pertinence :

```python
def _rerank_documents(self, docs, query, top_k=5):
    # Extraire les mots-clés de la requête
    keywords = re.findall(r'\w+', query.lower())
    keywords = [k for k in keywords if len(k) > 2]  # Ignorer les mots courts
    
    scored_docs = []
    
    for doc in docs:
        # Score initial
        score = 0
        content = doc.page_content.lower()
        
        # Correspondance des mots-clés
        for keyword in keywords:
            count = content.count(keyword)
            score += count * 2
        
        # Bonus pour les correspondances exactes de phrases
        if query.lower() in content:
            score += 10
        
        # Bonus pour les titres pertinents
        if "title" in doc.metadata:
            title = doc.metadata["title"].lower()
            for keyword in keywords:
                if keyword in title:
                    score += 5
        
        # Bonus pour les données d'horaires
        if "source" in doc.metadata and doc.metadata["source"] == "hours":
            score += 10
        
        # Bonus thématique
        if "horaire" in query.lower() and "horaire" in content:
            score += 15
        
        scored_docs.append((doc, score))
    
    # Trier par score décroissant
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    # Retourner les top_k documents
    return [doc for doc, _ in scored_docs[:top_k]]
```

## Comparaison des approches

|                    | Embeddings seuls | BM25 seul | Hybride + Reranking | Avec modules spécialisés |
|--------------------|------------------|-----------|---------------------|--------------------------|
| Correspondance exacte | Moyen         | Excellent | Excellent           | Excellent                |
| Compréhension sémantique | Excellent  | Faible    | Excellent           | Excellent                |
| Fraîcheur des données   | Limitée    | Limitée   | Limitée             | Excellente (temps réel)  |
| Rapidité              | Bonne        | Excellente | Bonne               | Excellente pour les cas spécifiques |
| Adaptabilité          | Moyenne      | Limitée   | Bonne               | Excellente pour les cas spécifiques |

## Résultats et exemples

### Exemple 1 : Question sur les horaires

**Question** : "Quels sont les horaires de la BU d'Orsay ?"

**Avec RAG de base** :
```
Réponse : Je suis désolé, je n'ai pas d'information précise à ce sujet. 
Veuillez contacter directement la bibliothèque.
```

**Avec l'approche hybride et module spécialisé** :
```
Réponse : Horaires de la BU Sciences d'Orsay : Du lundi au vendredi de 8h30 à 19h00. 
Fermée le week-end pendant les vacances scolaires.

Note : Ces informations sont récupérées en temps réel depuis les sources officielles.
```

### Exemple 2 : Question sur les services d'impression

**Question** : "Combien coûte l'impression d'une page A4 ?"

**Avec RAG de base** :
```
Réponse basée sur un document de 2021, potentiellement obsolète.
```

**Avec l'approche hybride et reranking** :
```
Réponse basée sur le document le plus récent concernant les tarifs d'impression.
```

## Pour aller plus loin

L'architecture actuelle pourrait être encore améliorée par :

1. **Reranking avec un modèle d'IA** : Utiliser un modèle pré-entraîné comme Cross-Encoder pour classer plus finement les documents

2. **Diversification des résultats** : Assurer que les documents récupérés ne sont pas trop similaires entre eux

3. **Feedback utilisateur** : Incorporer un mécanisme permettant aux utilisateurs de noter la pertinence des réponses

4. **Expansion des modules spécialisés** : Ajouter de nouveaux modules pour d'autres types de questions fréquentes (services disponibles, emprunts, etc.)

5. **Analyse des logs** : Étudier les questions fréquentes pour améliorer continuellement le système

## Conclusion

RAG-DiBiSo utilise une approche hybride sophistiquée combinant les forces de différentes méthodes de récupération d'information. L'intégration de BM25, d'embeddings vectoriels, d'un algorithme de reranking personnalisé et de modules spécialisés permet d'offrir des réponses plus précises et actualisées aux utilisateurs.

Cette architecture équilibre les avantages des différentes approches pour compenser leurs faiblesses respectives, créant ainsi un système robuste et flexible capable de répondre efficacement à un large éventail de questions sur les bibliothèques universitaires.