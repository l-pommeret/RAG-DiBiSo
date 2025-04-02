import os
import argparse
import time
from scraper import BibliothequesScraper
from data_processor import DataProcessor
from rag_chatbot import BibliothequeRagBot
from flask_app import app, initialize_bot, create_templates

def create_requirements_file():
    """Crée un fichier requirements.txt avec les dépendances nécessaires."""
    requirements = """
# Scraping
requests==2.31.0
beautifulsoup4==4.12.2

# LLM et RAG
langchain==0.0.267
transformers==4.33.2
torch==2.0.1
accelerate==0.23.0
sentence-transformers==2.2.2
chromadb==0.4.15

# Interface Web
flask==2.3.3

# Utilitaires
tqdm==4.66.1
    """
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements.strip())
    
    print("Fichier requirements.txt créé.")

def parse_args():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description="Bibliothèques Paris-Saclay RAG Bot")
    
    parser.add_argument('--mode', type=str, default='all',
                       choices=['scrape', 'process', 'chat', 'web', 'all'],
                       help="Mode d'exécution: scrape, process, chat, web ou all (tous)")
    
    parser.add_argument('--model', type=str, default='fake',
                       help="Nom du modèle LLM à utiliser (ou 'fake' pour le mode test)")
    
    parser.add_argument('--use-cuda', action='store_true',
                       help="Utiliser CUDA si disponible")
    
    return parser.parse_args()

def main():
    """Fonction principale pour exécuter le système de RAG."""
    args = parse_args()
    
    # Définir la variable d'environnement USE_CUDA
    if args.use_cuda:
        os.environ['USE_CUDA'] = 'True'
    else:
        os.environ['USE_CUDA'] = 'False'
    
    start_time = time.time()
    
    # Créer le fichier requirements.txt
    create_requirements_file()
    
    # Exécuter les différentes étapes selon le mode choisi
    if args.mode in ['scrape', 'all']:
        print("\n=== ÉTAPE 1: SCRAPING DES DONNÉES ===")
        scraper = BibliothequesScraper()
        libraries_data = scraper.scrape_all()
        print(f"Scraped {len(libraries_data)} libraries. Data saved to 'data' directory.")
        print(f"Temps écoulé: {time.time() - start_time:.2f} secondes")
    
    if args.mode in ['process', 'all']:
        print("\n=== ÉTAPE 2: TRAITEMENT DES DONNÉES ET CRÉATION DES EMBEDDINGS ===")
        processor = DataProcessor()
        vectordb = processor.create_vector_db()
        print(f"Vector database created and saved to '{processor.db_dir}' directory.")
        print(f"Temps écoulé: {time.time() - start_time:.2f} secondes")
    
    if args.mode == 'chat':
        print("\n=== MODE CHAT EN LIGNE DE COMMANDE ===")
        bot = BibliothequeRagBot(model_name=args.model)
        print("Bot initialisé. Posez vos questions (tapez 'quit' pour quitter):")
        
        while True:
            question = input("\nVotre question: ")
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            answer, _ = bot.ask(question)
            print(f"\nRéponse: {answer}")
    
    if args.mode == 'web':
        print("\n=== MODE INTERFACE WEB ===")
        create_templates()
        print("Templates créés.")
        
        # Initialiser le bot
        print(f"Initialisation du bot avec le modèle {args.model}...")
        initialize_bot()
        
        # Démarrer l'application Flask
        print("Démarrage de l'interface web sur http://localhost:5000")
        app.run(debug=False, host='0.0.0.0', port=5000)
    
    if args.mode == 'all':
        print("\n=== ÉTAPE 3: DÉMARRAGE DE L'INTERFACE WEB ===")
        create_templates()
        print("Templates créés.")
        
        # Initialiser le bot
        print(f"Initialisation du bot avec le modèle {args.model}...")
        bot = BibliothequeRagBot(model_name=args.model)
        
        # Démarrer l'application Flask
        print("Démarrage de l'interface web sur http://localhost:5000")
        app.run(debug=False, host='0.0.0.0', port=5000)
    
    print(f"\nTemps total d'exécution: {time.time() - start_time:.2f} secondes")

if __name__ == "__main__":
    main()