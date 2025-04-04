#!/usr/bin/env python3
"""
Script pour vérifier si le GPU est détecté et utilisable.
"""

import os
import sys
import torch

def check_gpu():
    """Vérifie si un GPU est disponible via PyTorch."""
    print("=== Vérification du GPU ===")
    
    if torch.cuda.is_available():
        print(f"✅ GPU détecté: {torch.cuda.get_device_name(0)}")
        print(f"   Nombre de GPUs: {torch.cuda.device_count()}")
        print(f"   Mémoire GPU totale: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        print(f"   Mémoire GPU utilisée: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
        print(f"   CUDA version: {torch.version.cuda}")
        
        # Test simple pour vérifier que le GPU fonctionne
        a = torch.tensor([1., 2., 3.], device="cuda")
        b = torch.tensor([4., 5., 6.], device="cuda")
        c = a + b
        print(f"   Test d'addition GPU: {a} + {b} = {c}")
        
        print("\n✅ Le GPU est fonctionnel et peut être utilisé pour l'inférence.")
        return True
    else:
        print("❌ Aucun GPU détecté par PyTorch")
        print("\n❌ GPU non disponible. Les modèles s'exécuteront sur CPU.")
        return False

if __name__ == "__main__":
    print("Script de vérification du GPU pour RAG-DiBiSo\n")
    check_gpu()
    
    print("\nRecommandations pour le RAG:")
    print("1. Si vous utilisez Colab, vérifiez que le runtime est configuré pour utiliser un GPU")
    print("   (Runtime > Change runtime type > Hardware accelerator > GPU)")
    print("2. Pour llama-cpp-python, si l'installation avec CUDA échoue, utilisez le modèle HuggingFace:")
    print("   python setup.py rag --advanced --model huggingface")
    print("3. Pour un modèle plus rapide et léger, utilisez le modèle factice:")
    print("   python setup.py rag --advanced --model fake")