# Utilisation de RAG-DiBiSo dans Google Colab

Ce guide explique comment utiliser RAG-DiBiSo efficacement dans un environnement Google Colab avec GPU.

## Configuration initiale

1. **Activer le GPU dans Colab**:
   - Dans le menu, cliquez sur **Runtime** > **Change runtime type**
   - Sélectionnez **GPU** sous **Hardware accelerator**
   - Cliquez sur **Save**

2. **Vérifier le GPU**:
   ```
   !python check_gpu.py
   ```
   Cela confirmera que le GPU est bien détecté et fonctionnel.

## Utilisation optimale avec llama-cpp-python

Pour les modèles Llama qui utilisent llama-cpp-python, il est recommandé de l'installer avec le support CUDA:

1. **Installation de llama-cpp-python avec CUDA**:
   ```
   !./install_llama_cpp_python.sh
   ```
   ou via le menu:
   ```
   !bash quick_start.sh
   ```
   Et choisir l'option 6.

2. **Exécuter le modèle avancé avec Llama**:
   ```
   !python setup.py rag --advanced --model llama
   ```
   ou via le menu:
   ```
   !bash quick_start.sh
   ```
   Et choisir l'option 2.

## Alternatives si Llama échoue

Si vous rencontrez des problèmes avec Llama malgré l'installation du support CUDA:

1. **Utiliser HuggingFace (utilise aussi le GPU)**:
   ```
   !python setup.py rag --advanced --model huggingface
   ```
   ou via le menu, choisir l'option 4.

2. **Utiliser le modèle factice (rapide mais limité)**:
   ```
   !python setup.py rag --advanced --model fake
   ```
   ou via le menu, choisir l'option 5.

## Test avec une question spécifique

Pour tester le système sans interface interactive:

```
!python test_question.py "Quels sont les horaires de la bibliothèque?"
```

## Problèmes courants

1. **Erreur "Could not import llama-cpp-python"**:
   - Exécutez le script d'installation avec support CUDA
   - Utilisez l'alternative HuggingFace si l'installation échoue

2. **Problèmes de mémoire GPU**:
   - Redémarrez le runtime Colab (Runtime > Restart runtime)
   - Utilisez un modèle plus léger (huggingface ou fake)

3. **Réponses répétitives ou incorrectes**:
   - Le contexte peut être insuffisant dans les documents
   - Essayez de reconstruire la base vectorielle avec l'option 3

## Pour les développeurs

Pour adapter le code à Colab, certains ajustements ont été faits:

1. Post-traitement des réponses pour éviter les répétitions
2. Adaptation du prompt pour différents modèles
3. Tests GPU intégrés au démarrage
4. Script d'installation spécialisé pour llama-cpp-python avec CUDA

Le code est conçu pour détecter automatiquement la disponibilité du GPU et s'adapter en conséquence.