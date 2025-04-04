#!/bin/bash
# Script d'installation de llama-cpp-python avec support CUDA

echo "========================================================="
echo "Installation de llama-cpp-python avec support CUDA pour RAG-DiBiSo"
echo "========================================================="

# Vérifier si nous sommes dans Colab
IN_COLAB=0
if [ -z "${COLAB_GPU}" ]; then
    if [ -d "/content" ]; then
        echo "Environnement Colab détecté"
        IN_COLAB=1
    else
        echo "Environnement standard détecté"
    fi
else
    echo "Variable COLAB_GPU détectée, environnement Colab confirmé"
    IN_COLAB=1
fi

# Vérifier si CUDA est disponible
if [ $IN_COLAB -eq 1 ]; then
    echo "Vérification de la disponibilité du GPU dans Colab..."
    if [ ! -f "/usr/local/cuda/version.txt" ]; then
        echo "CUDA n'est pas disponible. Veuillez activer le GPU dans Colab:"
        echo "Runtime > Change runtime type > Hardware accelerator > GPU"
        exit 1
    else
        CUDA_VERSION=$(cat /usr/local/cuda/version.txt)
        echo "CUDA disponible: $CUDA_VERSION"
    fi
else
    # Pour les environnements non-Colab
    if ! command -v nvcc &> /dev/null; then
        echo "CUDA n'est pas disponible. Installation pour CPU uniquement..."
        pip install llama-cpp-python
        exit 0
    else
        CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $6}' | cut -c2-)
        echo "CUDA disponible: $CUDA_VERSION"
    fi
fi

# Installation pour Colab avec T4 GPU
if [ $IN_COLAB -eq 1 ]; then
    echo "Installation optimisée pour Colab avec GPU..."
    
    # Option 1: installation complète avec CUDA
    echo "Méthode 1: Installation avec CMAKE_ARGS..."
    CMAKE_ARGS="-DLLAMA_CUBLAS=ON" FORCE_CMAKE=1 pip install llama-cpp-python --no-cache-dir --upgrade --verbose
    
    # Vérifier si l'installation a réussi
    if python -c "import llama_cpp; print('llama-cpp-python installé avec succès')" &> /dev/null; then
        echo "✅ Installation réussie!"
    else
        echo "❌ Échec de l'installation avec CMAKE_ARGS..."
        
        # Option 2: essayer avec une version pré-compilée (si elle existe)
        echo "Méthode 2: Tentative avec une version pré-compilée..."
        pip install --upgrade --force-reinstall --no-cache-dir llama-cpp-python
        
        # Vérifier si l'installation a réussi
        if python -c "import llama_cpp; print('llama-cpp-python installé avec succès')" &> /dev/null; then
            echo "✅ Installation réussie avec pip!"
        else
            echo "❌ Échec de l'installation. Utilisez l'option HuggingFace ou fake pour le RAG."
            echo "python setup.py rag --advanced --model huggingface"
            exit 1
        fi
    fi
else
    # Installation standard hors Colab
    echo "Installation standard avec support CUDA..."
    CMAKE_ARGS="-DLLAMA_CUBLAS=ON" pip install llama-cpp-python --upgrade
fi

# Vérifier l'installation
echo -e "\nVérification de l'installation..."
python - << 'EOF'
try:
    import llama_cpp
    print(f"✅ llama-cpp-python installé (version {llama_cpp.__version__})")
    
    # Vérifier si CUDA est activé
    if hasattr(llama_cpp.llama_cpp, 'CUBLAS_initialized'):
        cuda_available = llama_cpp.llama_cpp.CUBLAS_initialized()
        print(f"Support CUDA: {'✅ Activé' if cuda_available else '❌ Désactivé'}")
    else:
        print("❓ Impossible de vérifier le support CUDA")
except ImportError as e:
    print(f"❌ Erreur: {e}")
EOF

echo -e "\nInstallation terminée. Utilisez les commandes suivantes pour lancer le RAG:"
echo "python setup.py rag --advanced --model llama  # Pour utiliser llama-cpp-python"
echo "python setup.py rag --advanced --model huggingface  # Alternative si llama échoue"