#!/usr/bin/env python
"""
Script simple pour dialoguer avec le chatbot RAG des bibliothèques Paris-Saclay.
"""
import sys
import argparse
from rag_chatbot import BibliothequeRagBot

def main():
    # Parser des arguments
    parser = argparse.ArgumentParser(description="Chatbot des bibliothèques Paris-Saclay")
    parser.add_argument('--model', type=str, default='fake',
                      help="Nom du modèle LLM à utiliser (fake, llama)")
    parser.add_argument('--question', type=str, help="Question à poser en mode non-interactif")
    args = parser.parse_args()
    
    # Initialiser le bot
    bot = BibliothequeRagBot(model_name=args.model)
    print("Bot initialisé! Posez vos questions (tapez 'quit' pour quitter).")
    
    # Mode non-interactif si une question est fournie en argument
    if args.question:
        process_question(bot, args.question)
        return
    
    # Vérifier si l'entrée vient d'un pipe
    if not sys.stdin.isatty():
        for line in sys.stdin:
            question = line.strip()
            if not question:
                continue
            if question.lower() in ['quit', 'exit', 'q']:
                print("Au revoir!")
                break
            process_question(bot, question)
        return
    
    # Mode interactif
    while True:
        try:
            question = input("\nVotre question: ")
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Au revoir!")
                break
            
            process_question(bot, question)
        except (KeyboardInterrupt, EOFError):
            print("\nAu revoir!")
            break

def process_question(bot, question):
    print(f"\nQuestion: {question}")
    answer, sources = bot.ask(question)
    print(f"\nRéponse: {answer}")
    
    print("\nSources:")
    for i, doc in enumerate(sources):
        print(f"Source {i+1}: {doc.metadata.get('library', 'N/A')} - {doc.metadata.get('source', 'N/A')}")

if __name__ == "__main__":
    main()