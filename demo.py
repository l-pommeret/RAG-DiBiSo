#!/usr/bin/env python
"""
Script de démonstration pour le chatbot RAG des bibliothèques Paris-Saclay.
"""
from rag_chatbot import BibliothequeRagBot

def main():
    # Initialiser le bot
    bot = BibliothequeRagBot()
    print("Bot initialisé!")
    print("Voici quelques exemples de questions-réponses :")
    
    # Questions de démonstration
    questions = [
        "Quels sont les horaires des bibliothèques?",
        "Comment emprunter un livre?",
        "Puis-je travailler en groupe à la bibliothèque?",
        "Où sont situées les bibliothèques?",
        "Comment accéder aux ressources numériques?"
    ]
    
    # Boucle de démonstration
    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i} ---")
        print(f"Q: {question}")
        
        answer, sources = bot.ask(question)
        print(f"R: {answer}")
        
        print("\nSources:")
        for j, doc in enumerate(sources, 1):
            print(f"Source {j}: {doc.metadata.get('library', 'N/A')} - {doc.metadata.get('source', 'N/A')}")
        
        print("-" * 50)
    
    print("\nDémonstration terminée!")

if __name__ == "__main__":
    main()