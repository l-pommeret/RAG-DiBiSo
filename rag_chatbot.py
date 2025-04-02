import os
from langchain.prompts import PromptTemplate
from langchain_community.llms import FakeListLLM
try:
    from langchain_community.llms import HuggingFacePipeline
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
import torch
from langchain_core.documents import Document

class SimpleBibliothequeBot:
    def __init__(self):
        # Initialiser le modèle
        self.llm = self._initialize_llm()
        
        # Exemples de réponses et sources
        self.sample_sources = [
            Document(
                page_content="Les bibliothèques de Paris-Saclay sont généralement ouvertes de 9h à 19h en semaine.",
                metadata={"library": "Bibliothèque Centrale", "source": "Horaires et affluence"}
            ),
            Document(
                page_content="La bibliothèque propose de nombreuses ressources numériques accessibles 24h/24.",
                metadata={"library": "Ressources numériques", "source": "Ressources 24h sur 24"}
            ),
            Document(
                page_content="Pour emprunter des livres, vous devez être inscrit à la bibliothèque avec votre carte d'étudiant.",
                metadata={"library": "Service des prêts", "source": "Emprunter & Rendre"}
            )
        ]
    
    def _initialize_llm(self):
        """Initialise un modèle de langage factice pour test."""
        print("Utilisation d'un LLM factice pour les tests")
        responses = [
            "Je suis désolé, je n'ai pas d'information précise à ce sujet. Veuillez contacter directement la bibliothèque.",
            "D'après mes informations, les bibliothèques de Paris-Saclay sont généralement ouvertes de 9h à 19h en semaine.",
            "La bibliothèque universitaire propose de nombreuses ressources numériques accessibles 24h/24.",
            "Pour emprunter des livres, vous devez être inscrit à la bibliothèque avec votre carte d'étudiant ou de personnel.",
            "Les salles de travail en groupe peuvent être réservées en ligne sur le site des bibliothèques universitaires."
        ]
        llm = FakeListLLM(responses=responses)
        return llm
    
    def ask(self, question):
        """Pose une question au système."""
        print(f"Question: {question}")
        
        # Utiliser directement le LLM factice pour générer une réponse
        answer = self.llm.predict(question)
        
        # Sélection aléatoire de sources pertinentes (simulé)
        import random
        source_count = random.randint(1, len(self.sample_sources))
        sources = random.sample(self.sample_sources, source_count)
        
        # Afficher les sources (pour le debug)
        print("\nSources:")
        for i, doc in enumerate(sources):
            print(f"Source {i+1}: {doc.metadata.get('library', 'N/A')} - {doc.metadata.get('source', 'N/A')}")
        
        return answer, sources

# Alias pour compatibilité avec le code existant
BibliothequeRagBot = SimpleBibliothequeBot

# Interface en ligne de commande simple
if __name__ == "__main__":
    bot = BibliothequeRagBot()
    print("Bot initialisé. Posez vos questions (tapez 'quit' pour quitter):")
    
    while True:
        question = input("\nVotre question: ")
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        answer, sources = bot.ask(question)
        print(f"\nRéponse: {answer}")
        
        # Afficher les sources
        print("\nSources:")
        for i, doc in enumerate(sources):
            print(f"Source {i+1}: {doc.metadata.get('library', 'N/A')} - {doc.metadata.get('source', 'N/A')}")