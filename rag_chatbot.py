import os
from langchain.prompts import PromptTemplate
from langchain_community.llms import FakeListLLM
try:
    from langchain_community.llms import HuggingFacePipeline, LlamaCpp
    from huggingface_hub import hf_hub_download
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
import torch
from langchain_core.documents import Document

class SimpleBibliothequeBot:
    def __init__(self, model_name='fake'):
        # Initialiser le modèle
        self.model_name = model_name
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
        """Initialise un modèle de langage (LLM)."""
        if self.model_name.lower() == 'fake':
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
        
        elif self.model_name.lower() == 'llama':
            print("Initialisation du modèle Llama...")
            
            # Vérifier que les bibliothèques nécessaires sont disponibles
            if not HF_AVAILABLE:
                print("ERREUR: Les bibliothèques nécessaires pour Llama ne sont pas installées.")
                print("Veuillez installer les packages requis: pip install langchain-community transformers")
                return self._fallback_to_fake_llm()
                
            try:
                # Utiliser LlamaCpp pour un modèle plus léger
                model_path = hf_hub_download(
                    repo_id="TheBloke/Llama-2-7B-Chat-GGUF",
                    filename="llama-2-7b-chat.Q4_K_M.gguf"
                )
                
                llm = LlamaCpp(
                    model_path=model_path,
                    temperature=0.1,
                    max_tokens=2000,
                    top_p=1,
                    n_ctx=2048,
                    verbose=False,
                )
                
                print("Modèle Llama initialisé avec succès!")
                return llm
                
            except Exception as e:
                print(f"ERREUR lors de l'initialisation de Llama: {e}")
                return self._fallback_to_fake_llm()
        else:
            print(f"Modèle '{self.model_name}' non reconnu, utilisation du LLM factice par défaut")
            return self._fallback_to_fake_llm()
    
    def _fallback_to_fake_llm(self):
        """Utilise un LLM factice en cas d'échec de l'initialisation du modèle principal."""
        print("Utilisation d'un LLM factice comme fallback")
        responses = [
            "Je suis désolé, je n'ai pas d'information précise à ce sujet. Veuillez contacter directement la bibliothèque.",
            "D'après mes informations, les bibliothèques de Paris-Saclay sont généralement ouvertes de 9h à 19h en semaine.",
            "La bibliothèque universitaire propose de nombreuses ressources numériques accessibles 24h/24.",
            "Pour emprunter des livres, vous devez être inscrit à la bibliothèque avec votre carte d'étudiant ou de personnel.",
            "Les salles de travail en groupe peuvent être réservées en ligne sur le site des bibliothèques universitaires."
        ]
        return FakeListLLM(responses=responses)
    
    def ask(self, question):
        """Pose une question au système."""
        print(f"Question: {question}")
        
        # Utiliser la méthode invoke du LLM pour générer une réponse
        from langchain_core.outputs import LLMResult
        try:
            # Nouvelle méthode invoke pour LangChain >=0.1.7
            result = self.llm.invoke(question)
            answer = result
        except Exception:
            # Fallback vers l'ancienne méthode predict pour compatibilité
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