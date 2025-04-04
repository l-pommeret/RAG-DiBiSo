import os
import sys
from simple_rag import SimpleRagBot

def test_rag_system():
    """Teste le système RAG avec quelques questions prédéfinies."""
    questions = [
        "Quels sont les horaires d'ouverture de la bibliothèque ?",
        "Comment emprunter un livre ?",
        "Où se trouve la bibliothèque des sciences ?",
        "Comment réserver une salle de travail en groupe ?",
        "Quelles sont les ressources électroniques disponibles ?"
    ]
    
    # Créer le bot
    bot = SimpleRagBot()
    
    print("=== TEST DU SYSTÈME RAG SIMPLE ===\n")
    
    for i, question in enumerate(questions):
        print(f"Question {i+1}: {question}")
        answer, sources = bot.ask(question)
        
        print(f"Réponse: {answer[:200]}..." if len(answer) > 200 else f"Réponse: {answer}")
        
        if sources:
            print("Sources trouvées:")
            for j, doc in enumerate(sources[:2]):  # Limiter à 2 sources pour la lisibilité
                print(f"  - {doc['metadata']['title']}")
        else:
            print("Aucune source trouvée.")
        
        print("\n" + "-" * 80 + "\n")
    
    print("Tests terminés.")

if __name__ == "__main__":
    # Vérifier que les répertoires de données existent
    data_dirs = ["data", "txt_data"]
    missing_dirs = [d for d in data_dirs if not os.path.exists(d) or not os.listdir(d)]
    
    if missing_dirs:
        print(f"ERREUR: Les répertoires suivants sont manquants ou vides: {missing_dirs}")
        print("Veuillez d'abord exécuter le scraper pour générer les données.")
        sys.exit(1)
    
    test_rag_system()