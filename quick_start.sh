#!/bin/bash
# Script de démarrage rapide pour RAG-DiBiSo

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Python 3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# Installer les dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt

# Configurer l'environnement
echo "Configuration de l'environnement..."
python setup.py setup

# Demander à l'utilisateur quelle action effectuer
echo ""
echo "Que souhaitez-vous faire ?"
echo "1. Extraire des données (scraping)"
echo "2. Lancer le système RAG"
echo "3. Lancer l'interface web"
echo "4. Exécuter les tests"
echo "5. Quitter"
read -p "Votre choix (1-5): " choice

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
        echo ""
        echo "Options du système RAG :"
        echo "1. Utiliser la version simple"
        echo "2. Utiliser la version avancée avec Llama (GPU)"
        echo "3. Utiliser la version avancée avec reconstruction de la base vectorielle"
        echo "4. Utiliser la version avancée avec HuggingFace (alternative GPU)"
        echo "5. Utiliser la version avancée avec modèle factice (fallback)"
        echo "6. Installer llama-cpp-python avec support CUDA (si problème GPU)"
        read -p "Votre choix (1-6): " rag_choice
        
        case $rag_choice in
            1)
                python setup.py rag
                ;;
            2)
                # Vérification GPU avant d'utiliser Llama
                python check_gpu.py
                echo "Lancement de RAG avec Llama..."
                python setup.py rag --advanced --model llama
                ;;
            3)
                # Vérification GPU avant d'utiliser Llama avec reconstruction
                python check_gpu.py
                echo "Lancement de RAG avec Llama et reconstruction de la base vectorielle..."
                python setup.py rag --advanced --rebuild --model llama
                ;;
            4)
                # Utiliser HuggingFace comme alternative au GPU
                echo "Lancement de RAG avec HuggingFace (utilise aussi le GPU)..."
                python setup.py rag --advanced --model huggingface
                ;;
            5)
                echo "Lancement de RAG avec un modèle factice (rapide mais limité)..."
                python setup.py rag --advanced --model fake
                ;;
            6)
                echo "Installation de llama-cpp-python avec support CUDA..."
                ./install_llama_cpp_python.sh
                ;;
            *)
                echo "Choix invalide"
                exit 1
                ;;
        esac
        ;;
    3)
        python setup.py web
        ;;
    4)
        python setup.py test --all
        ;;
    5)
        echo "Au revoir !"
        exit 0
        ;;
    *)
        echo "Choix invalide"
        exit 1
        ;;
esac