# Modules supplémentaires pour le système RAG

Ce répertoire contient des modules complémentaires pour étendre les fonctionnalités du système RAG principal.

## Module d'horaires (`horaires_module.py`)

Ce module est spécialisé dans la gestion des questions relatives aux horaires des bibliothèques de l'Université Paris-Saclay. Il permet de récupérer des données en temps réel ou presque, plutôt que de se fier uniquement aux données statiques du RAG.

### Fonctionnalités
- Récupération des horaires depuis les sites web des bibliothèques
- Support pour l'intégration avec l'API Affluences (pour les données en temps réel)
- Mise en cache des données pour éviter les requêtes excessives
- Identification intelligente de la bibliothèque mentionnée dans une question
- Formatage adapté des réponses

### Utilisation
```python
from modules.horaires_module import HorairesModule

# Initialiser le module
horaires_module = HorairesModule()

# Gérer une question sur les horaires
question = "Quels sont les horaires de la bibliothèque d'Orsay aujourd'hui?"
reponse = horaires_module.handle_query(question)
print(reponse)

# Récupérer directement les horaires d'une bibliothèque spécifique
horaires_orsay = horaires_module.get_horaires("orsay")
```

### Configuration requise
- Python 3.6 ou supérieur
- Bibliothèques: requests, BeautifulSoup4
- Un répertoire pour le cache (créé automatiquement si nécessaire)

### Intégration avec le système RAG principal
Pour intégrer ce module à votre RAG, vous pouvez modifier le processus de question-réponse pour détecter les questions relatives aux horaires et les rediriger vers ce module spécialisé.

Exemple d'intégration:
```python
def ask_question(question):
    # Vérifier si la question concerne les horaires
    if any(keyword in question.lower() for keyword in ["horaire", "ouverture", "fermé", "fermeture", "ouvre", "ferme"]):
        # Utiliser le module spécialisé pour les horaires
        return horaires_module.handle_query(question)
    else:
        # Utiliser le système RAG standard pour les autres questions
        return rag_system.ask(question)
```