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

def check_ollama_status():
    """Vérifie si Ollama est installé et en cours d'exécution."""
    try:
        # Vérifier si Ollama est installé
        ollama_installed = subprocess.run(["which", "ollama"], capture_output=True, text=True).returncode == 0
        if not ollama_installed:
            print("Ollama n'est pas installé. Veuillez l'installer depuis https://ollama.com/download")
            return False
        
        # Vérifier si Ollama est en cours d'exécution
        response = subprocess.run(["curl", "-s", "http://localhost:11434/api/version"], capture_output=True, text=True)
        if response.returncode != 0 or not response.stdout:
            print("Le serveur Ollama n'est pas en cours d'exécution.")
            return False
        
        print("Ollama est installé et en cours d'exécution.")
        return True
    except Exception as e:
        print(f"Erreur lors de la vérification d'Ollama: {e}")
        return False

def start_ollama_server():
    """Démarre le serveur Ollama s'il n'est pas déjà en cours d'exécution."""
    try:
        # Vérifier si le serveur est déjà en cours d'exécution
        response = subprocess.run(["curl", "-s", "http://localhost:11434/api/version"], capture_output=True, text=True)
        if response.returncode == 0 and response.stdout:
            print("Le serveur Ollama est déjà en cours d'exécution.")
            return True
        
        # Démarrer le serveur en arrière-plan
        print("Démarrage du serveur Ollama...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Attendre que le serveur soit prêt
        import time
        for _ in range(10):  # Essayer 10 fois avec 1 seconde d'attente
            time.sleep(1)
            response = subprocess.run(["curl", "-s", "http://localhost:11434/api/version"], capture_output=True, text=True)
            if response.returncode == 0 and response.stdout:
                print("Serveur Ollama démarré avec succès.")
                return True
        
        print("Échec du démarrage du serveur Ollama.")
        return False
    except Exception as e:
        print(f"Erreur lors du démarrage du serveur Ollama: {e}")
        return False

def check_and_pull_model(model_name):
    """Vérifie si le modèle est déjà téléchargé, sinon le télécharge."""
    try:
        # Vérifier si le modèle est déjà téléchargé
        models = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if model_name in models.stdout:
            print(f"Le modèle {model_name} est déjà téléchargé.")
            return True
        
        # Télécharger le modèle
        print(f"Téléchargement du modèle {model_name}...")
        result = subprocess.run(["ollama", "pull", model_name], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Modèle {model_name} téléchargé avec succès.")
            return True
        else:
            print(f"Échec du téléchargement du modèle {model_name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"Erreur lors de la vérification/téléchargement du modèle: {e}")
        return False

def run_rag(args):
    """Exécute le système RAG."""
    if args.advanced:
        # Vérifier d'abord si la version avec modules existe
        if os.path.exists("rag_chatbot_enhanced_with_modules.py"):
            print("Utilisation de la version avec modules spécialisés")
            rag_script = "rag_chatbot_enhanced_with_modules.py"
        elif os.path.exists("rag_chatbot_enhanced.py"):
            print("Utilisation de la version avancée sans modules")
            rag_script = "rag_chatbot_enhanced.py"
        else:
            print("Aucune version avancée du RAG trouvée. Utilisation de la version simple.")
            cmd = ["python", "simple_rag.py"]
            print(f"Exécution de la commande: {' '.join(cmd)}")
            subprocess.run(cmd)
            return
        
        # Utiliser le modèle spécifié ou llama par défaut
        model = args.model if args.model else "llama"
        
        # Si le modèle est ollama, vérifier/démarrer Ollama et télécharger le modèle
        if model == "ollama":
            if not check_ollama_status():
                print("Tentative de démarrage du serveur Ollama...")
                if not start_ollama_server():
                    print("Impossible de démarrer Ollama. Veuillez le démarrer manuellement avec 'ollama serve'.")
                    return
            
            # Vérifier/télécharger le modèle llama3
            if not check_and_pull_model("llama3"):
                print("Impossible de télécharger le modèle llama3. Veuillez vérifier votre connexion internet.")
                return
        
        cmd = ["python", rag_script, "--model", model]
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

def initialize_vectordb(args):
    """Initialise la base de données vectorielle."""
    from data_processor import DataProcessor
    
    print("Initialisation de la base de données vectorielle...")
    processor = DataProcessor()
    processor.process_data()
    print("Base de données vectorielle initialisée avec succès!")

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
    
    # Commande initialize_vectordb
    vectordb_parser = subparsers.add_parser("initialize_vectordb", help="Initialiser la base de données vectorielle")
    
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
    elif args.command == "initialize_vectordb":
        initialize_vectordb(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()