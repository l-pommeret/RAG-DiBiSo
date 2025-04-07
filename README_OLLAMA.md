# Utilisation d'Ollama avec RAG-DiBiSo

Ce document explique comment utiliser Ollama avec le système RAG-DiBiSo pour bénéficier du modèle Llama 3.1.

## Prérequis

1. Installer Ollama
   - Téléchargez depuis le site officiel : [https://ollama.com/download](https://ollama.com/download)
   - Suivez les instructions d'installation pour votre système d'exploitation

2. Démarrer le serveur Ollama
   ```bash
   ollama serve
   ```

3. Télécharger le modèle Llama 3.1
   ```bash
   ollama pull llama3
   ```

## Exécution du RAG avec Ollama

### Méthode 1 : Utiliser le script quick_start.sh
```bash
./quick_start.sh
```
Puis choisissez l'option 3 pour lancer le RAG avec Ollama.

### Méthode 2 : Ligne de commande directe
```bash
python rag_chatbot_enhanced.py --model ollama
```

## Avantages de Llama 3.1 via Ollama

- **Performances** : Llama 3.1 est optimisé pour offrir de bonnes performances même sur du matériel modeste
- **Qualité** : Meilleurs résultats que les versions précédentes de Llama
- **Facilité** : Ollama gère le téléchargement et l'exécution du modèle sans configuration complexe
- **Légèreté** : Ollama optimise l'utilisation des ressources pour des performances maximales

## Dépannage

Si vous rencontrez des problèmes avec Ollama :

1. Vérifiez que le serveur Ollama est bien en cours d'exécution :
   ```bash
   curl http://localhost:11434/api/version
   ```

2. Vérifiez que le modèle llama3 est bien installé :
   ```bash
   ollama list
   ```

3. En cas d'erreur, consultez les logs d'Ollama :
   ```bash
   # Sur Linux/macOS, vérifiez les logs système
   journalctl -u ollama.service -f
   ```