#!/bin/bash
# Script de démarrage rapide pour RAG-DiBiSo

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Python 3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# Installer les dépendances
echo "Installation des dépendances..."
pip3 install -r requirements.txt

# Installer Ollama si nécessaire
if ! command -v ollama &> /dev/null; then
    echo "Installation d'Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "Ollama installé avec succès!"
fi

# Configurer l'environnement
echo "Configuration de l'environnement..."
python setup.py setup

# Demander à l'utilisateur quelle action effectuer
echo ""
echo "Que souhaitez-vous faire ?"
echo "1. Extraire des données (scraping)"
echo "2. Initialiser la base de données vectorielle"
echo "3. Lancer le système RAG"
echo "4. Lancer l'interface web"
echo "5. Exécuter les tests"
echo "6. Quitter"
read -p "Votre choix (1-6): " choice

case $choice in
    1)
        echo ""
        echo "Options de scraping :"
        echo "1. Utiliser le fichier de sous-répertoires qa_haystack"
        echo "2. Crawler le site web (sans limite)"
        echo "3. Crawler le site web (avec limite)"
        echo "4. Tester sur une seule page"
        read -p "Votre choix (1-4): " scrape_choice
        
        case $scrape_choice in
            1)
                python setup.py scrape --subdirs qa_haystack/DiBISOData/subdirectories.txt
                ;;
            2)
                python setup.py scrape
                ;;
            3)
                read -p "Nombre de pages maximum à crawler: " max_pages
                python setup.py scrape --max_pages "$max_pages"
                ;;
            4)
                read -p "URL à tester: " test_url
                python setup.py scrape --test "$test_url"
                ;;
            *)
                echo "Choix invalide"
                exit 1
                ;;
        esac
        ;;
    2)
        echo "Initialisation de la base de données vectorielle..."
        python setup.py initialize_vectordb
        ;;
    3)
        echo "Lancement de RAG avec Ollama (Llama 3.1)..."
        python setup.py rag --advanced --model ollama
        ;;
    4)
        python setup.py web
        ;;
    5)
        python setup.py test --all
        ;;
    6)
        echo "Au revoir !"
        exit 0
        ;;
    *)
        echo "Choix invalide"
        exit 1
        ;;
esac