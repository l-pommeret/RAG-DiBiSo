#!/usr/bin/env python3
"""
Script d'installation et de configuration pour RAG-DiBiSo
Ce script permet de configurer l'environnement et d'exécuter les différentes
parties du projet de manière simple.
"""
import os
import sys
import argparse
import subprocess

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées."""
    try:
        import requests
        import bs4  # Correction: beautifulsoup4 s'importe sous le nom 'bs4'
        import flask
        import nltk
        return True
    except ImportError as e:
        print(f"Dépendance manquante: {e}")
        print("Veuillez installer les dépendances avec 'pip install -r requirements.txt'")
        return False

def download_nltk_data():
    """Télécharge les données NLTK nécessaires."""
    import nltk
    nltk_resources = ["punkt"]
    for resource in nltk_resources:
        try:
            nltk.data.find(f"tokenizers/{resource}")
            print(f"Ressource NLTK '{resource}' déjà installée")
        except LookupError:
            print(f"Téléchargement de la ressource NLTK '{resource}'...")
            nltk.download(resource)

def create_directories():
    """Crée les répertoires nécessaires s'ils n'existent pas."""
    directories = ["data", "txt_data", "vectordb"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Répertoire '{directory}' créé")
        else:
            print(f"Répertoire '{directory}' existe déjà")

def run_scraper(args):
    """Exécute le scraper."""
    cmd = ["python", "simple_combined_scraper.py"]
    
    if args.test:
        cmd.extend(["--test", args.test])
    elif args.subdirs:
        cmd.extend(["--subdirs", args.subdirs])
    else:
        cmd.extend(["--max_pages", str(args.max_pages)])
    
    print(f"Exécution de la commande: {' '.join(cmd)}")
    subprocess.run(cmd)

def run_rag(args):
    """Exécute le système RAG."""
    if args.advanced and os.path.exists("rag_chatbot_enhanced.py"):
        # Utiliser le modèle spécifié ou llama par défaut
        model = args.model if args.model else "llama"
        cmd = ["python", "rag_chatbot_enhanced.py", "--model", model]
        if args.rebuild:
            cmd.append("--rebuild")
    else:
        cmd = ["python", "simple_rag.py"]
    
    print(f"Exécution de la commande: {' '.join(cmd)}")
    subprocess.run(cmd)

def run_web(args):
    """Lance l'interface web."""
    cmd = ["python", "flask_app.py"]
    if args.port:
        cmd.extend(["--port", str(args.port)])
    
    print(f"Exécution de la commande: {' '.join(cmd)}")
    subprocess.run(cmd)

def run_tests(args):
    """Exécute les tests."""
    tests = []
    if args.all or args.scraper:
        tests.append("test_simple_scraper.py")
    if args.all or args.rag:
        tests.append("test_simple_rag.py")
    
    for test in tests:
        cmd = ["python", test]
        print(f"Exécution du test: {test}")
        subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Configuration et exécution de RAG-DiBiSo")
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Commande setup
    setup_parser = subparsers.add_parser("setup", help="Configurer l'environnement")
    
    # Commande scrape
    scrape_parser = subparsers.add_parser("scrape", help="Exécuter le scraper")
    scrape_parser.add_argument("--test", help="URL pour tester l'extraction", type=str)
    scrape_parser.add_argument("--subdirs", help="Fichier de sous-répertoires à scraper", type=str)
    scrape_parser.add_argument("--max_pages", help="Nombre maximum de pages à crawler", type=int, default=0)
    
    # Commande rag
    rag_parser = subparsers.add_parser("rag", help="Exécuter le système RAG")
    rag_parser.add_argument("--advanced", help="Utiliser la version avancée", action="store_true")
    rag_parser.add_argument("--rebuild", help="Reconstruire la base vectorielle", action="store_true")
    rag_parser.add_argument("--model", help="Modèle à utiliser (fake, llama, huggingface)", default=None)
    
    # Commande web
    web_parser = subparsers.add_parser("web", help="Lancer l'interface web")
    web_parser.add_argument("--port", help="Port pour le serveur", type=int, default=5000)
    
    # Commande test
    test_parser = subparsers.add_parser("test", help="Exécuter les tests")
    test_parser.add_argument("--all", help="Exécuter tous les tests", action="store_true")
    test_parser.add_argument("--scraper", help="Tester le scraper", action="store_true")
    test_parser.add_argument("--rag", help="Tester le système RAG", action="store_true")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        if check_dependencies():
            download_nltk_data()
            create_directories()
            print("Configuration terminée avec succès")
        else:
            sys.exit(1)
    elif args.command == "scrape":
        run_scraper(args)
    elif args.command == "rag":
        run_rag(args)
    elif args.command == "web":
        run_web(args)
    elif args.command == "test":
        run_tests(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()