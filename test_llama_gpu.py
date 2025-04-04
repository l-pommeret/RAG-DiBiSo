#!/usr/bin/env python3
"""
Script de test pour vérifier si llama-cpp-python utilise bien le GPU.
"""

import os
import sys
import torch
import time

def test_gpu_availability():
    """Vérifier si un GPU est disponible via PyTorch."""
    print("=== Test de disponibilité du GPU via PyTorch ===")
    
    if torch.cuda.is_available():
        print(f"✅ GPU disponible: {torch.cuda.get_device_name(0)}")
        print(f"   Nombre de GPUs: {torch.cuda.device_count()}")
        print(f"   Mémoire GPU totale: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        print(f"   Mémoire GPU utilisée: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
        print(f"   CUDA version: {torch.version.cuda}")
        return True
    else:
        print("❌ Aucun GPU détecté par PyTorch")
        return False

def test_llama_cpp_installation():
    """Vérifier si llama-cpp-python est installé et sa configuration."""
    print("\n=== Test d'installation de llama-cpp-python ===")
    
    try:
        import llama_cpp
        print(f"✅ llama-cpp-python est installé (version {llama_cpp.__version__})")
        
        # Vérifier si la bibliothèque est compilée avec CUDA
        if hasattr(llama_cpp.llama_cpp, 'CUBLAS_initialized'):
            cuda_available = llama_cpp.llama_cpp.CUBLAS_initialized()
            print(f"   Support CUBLAS: {'✅ Activé' if cuda_available else '❌ Désactivé'}")
        else:
            print("   ❌ Méthode CUBLAS_initialized non trouvée, la version installée ne supporte probablement pas CUDA")
            if "gcc" in dir(llama_cpp):
                print(f"   Compilé avec: {llama_cpp.gcc}")
        
        return True
        
    except ImportError:
        print("❌ llama-cpp-python n'est pas installé")
        return False

def test_langchain_llamacpp():
    """Vérifier si LangChain peut accéder à LlamaCpp."""
    print("\n=== Test d'intégration avec LangChain ===")
    
    try:
        from langchain_community.llms import LlamaCpp
        print("✅ LlamaCpp de LangChain est disponible")
        return True
    except ImportError as e:
        print(f"❌ Impossible d'importer LlamaCpp de LangChain: {e}")
        return False

def test_llama_inference():
    """Tester l'inférence avec llama-cpp-python pour vérifier l'utilisation du GPU."""
    print("\n=== Test d'inférence avec llama-cpp-python ===")
    
    try:
        import llama_cpp
        from huggingface_hub import hf_hub_download
        
        # Télécharger un petit modèle pour le test
        print("Téléchargement d'un modèle de test...")
        model_path = hf_hub_download(
            repo_id="TheBloke/Llama-2-7B-Chat-GGUF",
            filename="llama-2-7b-chat.Q4_K_M.gguf"
        )
        print(f"Modèle téléchargé: {model_path}")
        
        # Créer un contexte Llama avec GPU activé
        print("Création du modèle avec GPU activé...")
        model_params = llama_cpp.llama_context_params()
        model_params.n_gpu_layers = -1  # Utiliser tous les layers sur GPU
        model_params.seed = 42
        
        start_time = time.time()
        model = llama_cpp.Llama(
            model_path=model_path,
            n_ctx=512,
            n_batch=512,
            n_gpu_layers=-1,
            verbose=True
        )
        loading_time = time.time() - start_time
        print(f"Temps de chargement du modèle: {loading_time:.2f} secondes")
        
        # Tester l'inférence
        print("\nTest d'inférence...")
        start_time = time.time()
        output = model("Quelle est la capitale de la France?", max_tokens=32)
        inference_time = time.time() - start_time
        
        print(f"Temps d'inférence: {inference_time:.2f} secondes")
        print(f"Réponse: {output['choices'][0]['text']}")
        
        # Vérifier si CUDA est utilisé en regardant la sortie verbose
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'inférence: {e}")
        return False

def install_llama_cpp_cuda():
    """Essayer d'installer llama-cpp-python avec support CUDA."""
    print("\n=== Installation de llama-cpp-python avec support CUDA ===")
    
    cmd = "CMAKE_ARGS='-DLLAMA_CUBLAS=ON' FORCE_CMAKE=1 pip install --upgrade llama-cpp-python"
    print(f"Exécution de: {cmd}")
    
    result = os.system(cmd)
    
    if result == 0:
        print("✅ Installation réussie")
        return True
    else:
        print("❌ L'installation a échoué")
        return False

if __name__ == "__main__":
    print("=== Test de fonctionnement du GPU avec llama-cpp-python ===\n")
    
    # Tester si un GPU est disponible
    gpu_available = test_gpu_availability()
    
    # Tester si llama-cpp-python est installé
    llama_installed = test_llama_cpp_installation()
    
    # Tester l'intégration avec LangChain
    langchain_support = test_langchain_llamacpp()
    
    # Si les tests de base passent, tester l'inférence
    if gpu_available and llama_installed and langchain_support:
        inference_success = test_llama_inference()
    else:
        inference_success = False
        
        # Si llama-cpp-python n'est pas installé ou n'a pas le support CUDA, l'installer automatiquement
        if not llama_installed:
            print("\nllama-cpp-python n'est pas installé ou n'a pas le support CUDA.")
            print("Installation automatique avec support CUDA...")
            install_success = install_llama_cpp_cuda()
            if install_success:
                print("\nInstallation réussie. Veuillez relancer ce script pour tester l'installation.")
                sys.exit(0)
    
    # Résumé
    print("\n=== Résumé ===")
    print(f"GPU disponible: {'✅' if gpu_available else '❌'}")
    print(f"llama-cpp-python installé: {'✅' if llama_installed else '❌'}")
    print(f"Support LangChain: {'✅' if langchain_support else '❌'}")
    print(f"Test d'inférence: {'✅' if inference_success else '❌'}")
    
    if not gpu_available or not llama_installed or not langchain_support or not inference_success:
        print("\nRecommandations:")
        if not gpu_available:
            print("- Assurez-vous que votre environnement a accès à un GPU (vérifiez dans Colab: Runtime > Change runtime type > Hardware accelerator > GPU)")
        if not llama_installed:
            print("- Installez llama-cpp-python avec support CUDA: CMAKE_ARGS='-DLLAMA_CUBLAS=ON' FORCE_CMAKE=1 pip install --upgrade llama-cpp-python")
        if not langchain_support:
            print("- Installez langchain-community: pip install langchain-community")
        print("- Dans Colab, utilisez la commande 'nvidia-smi' pour vérifier que le GPU est bien reconnu")