#!/usr/bin/env python
"""
Script simple pour dialoguer avec le chatbot RAG des bibliothèques Paris-Saclay.
"""
from rag_chatbot import BibliothequeRagBot

def main():
    # Initialiser le bot
    bot = BibliothequeRagBot()
    print("Bot initialisé! Posez vos questions (tapez 'quit' pour quitter).")
    
    # Boucle de dialogue
    while True:
        question = input("\nVotre question: ")
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("Au revoir!")
            break
        
        answer, sources = bot.ask(question)
        print(f"\nRéponse: {answer}")
        
        print("\nSources:")
        for i, doc in enumerate(sources):
            print(f"Source {i+1}: {doc.metadata.get('library', 'N/A')} - {doc.metadata.get('source', 'N/A')}")

if __name__ == "__main__":
    main()