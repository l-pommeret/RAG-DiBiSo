#!/usr/bin/env python3
"""
Script utilitaire pour tester une question sans utiliser l'interface interactive.
Usage:
    python test_question.py "Quels sont les horaires de la bibliothèque?"
"""
import sys
from rag_chatbot_enhanced import EnhancedBibliothequeBot

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_question.py \"Votre question?\"")
        sys.exit(1)
    
    question = sys.argv[1]
    
    # Initialiser le bot avec HuggingFace
    print("Initialisation du bot avec le modèle HuggingFace...")
    bot = EnhancedBibliothequeBot(
        model_name="huggingface",
        data_dir="data",
        db_dir="vectordb"
    )
    
    print(f"\nQuestion: {question}")
    
    # Obtenir la réponse
    answer, sources = bot.ask(question)
    
    print(f"\nRéponse: {answer}")
    
    # Afficher les sources
    if sources:
        print("\nSources:")
        for i, doc in enumerate(sources[:3]):  # Limiter à 3 sources
            source = doc.metadata.get('source', 'N/A')
            title = doc.metadata.get('title', doc.metadata.get('library', 'N/A'))
            url = doc.metadata.get('url', '')
            print(f"Source {i+1}: {title} ({source})")
            if url:
                print(f"  URL: {url}")
    else:
        print("\nAucune source disponible pour cette réponse.")

if __name__ == "__main__":
    main()