import sys

print("Test d'Ollama")
print(f"Python version: {sys.version}")

try:
    print("Tentative d'import de langchain_community.llms.Ollama")
    from langchain_community.llms import Ollama
    print("Import Ollama réussi!")
    
    try:
        print("Tentative d'initialisation d'Ollama avec le modèle llama3")
        llm = Ollama(model="llama3")
        print("Initialisation réussie!")
        
        print("Tentative de génération avec Ollama")
        result = llm.invoke("Bonjour, comment ça va?")
        print(f"Résultat: {result}")
        
    except Exception as e:
        print(f"Erreur lors de l'initialisation ou de la génération: {e}")
        print(f"Type d'erreur: {type(e)}")
except ImportError as ie:
    print(f"Erreur d'importation: {ie}")
    
print("Test terminé")