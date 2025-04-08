#!/usr/bin/env python3
"""
Script utilitaire pour tester une question sans utiliser l'interface interactive.
Usage:
    python test_question.py "Quels sont les horaires de la bibliothèque?"
"""
import sys
from rag_chatbot_enhanced import EnhancedBibliothequeBot

def main():
    # Initialiser le bot avec modèle fake (pour tester rapidement)
    print("Initialisation du bot avec modèle fake...")
    bot = EnhancedBibliothequeBot(
        model_name="fake",
        data_dir="data",
        db_dir="vectordb"
    )
    
    # Si des arguments sont fournis, utiliser comme question
    if len(sys.argv) >= 2:
        question = sys.argv[1]
        process_question(bot, question)
    else:
        # Sinon, exécuter une série de questions de test
        test_questions(bot)
        
def process_question(bot, question):
    """Traite une seule question"""
    print(f"\n===== QUESTION: {question} =====")
    
    # Obtenir la réponse
    answer, sources = bot.ask(question)
    
    print(f"\nRÉPONSE: {answer}")
    
    # Afficher les sources
    if sources:
        print("\nSOURCES:")
        for i, doc in enumerate(sources[:3]):  # Limiter à 3 sources
            source = doc.metadata.get('source', 'N/A')
            title = doc.metadata.get('title', doc.metadata.get('library', 'N/A'))
            url = doc.metadata.get('url', '')
            print(f"Source {i+1}: {title} ({source})")
            if url:
                print(f"  URL: {url}")
    else:
        print("\nAucune source disponible pour cette réponse.")

def test_questions(bot):
    """Exécute une série de questions de test prédéfinies"""
    questions = [
        "Quels sont les horaires de la bibliothèque?",
        "Comment emprunter un livre?",
        "Où trouver des informations sur le master?",
        "Quels sont les services disponibles à la bibliothèque?",
        "Comment réserver une salle de travail en groupe?"
    ]
    
    for question in questions:
        process_question(bot, question)

if __name__ == "__main__":
    main()