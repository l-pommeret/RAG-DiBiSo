"""
Script simplifié pour tester le pipeline RAG avec des composants de test.
"""

import os
from langchain.prompts import PromptTemplate
from langchain_community.llms import FakeListLLM
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FakeEmbeddings
from langchain_core.documents import Document

class SimpleRagTest:
    def __init__(self, db_dir="vectordb"):
        self.db_dir = db_dir
        print("Initializing simple RAG test...")
        
        # Créer le répertoire si nécessaire
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        # Utiliser des embeddings factices pour le test
        self.embeddings = FakeEmbeddings(size=384)
        
        # Essayer de charger une base de données vectorielle existante ou en créer une de test
        try:
            self.vectordb = Chroma(
                persist_directory=self.db_dir,
                embedding_function=self.embeddings
            )
            print(f"Loaded existing vector database from {self.db_dir}")
        except:
            # Créer des documents de test
            documents = [
                Document(
                    page_content="La bibliothèque des Sciences est ouverte de 9h à 19h du lundi au vendredi.",
                    metadata={"source": "hours", "library": "Sciences"}
                ),
                Document(
                    page_content="La bibliothèque de Droit est située au bâtiment D du campus.",
                    metadata={"source": "address", "library": "Droit"}
                ),
                Document(
                    page_content="Pour emprunter des livres, vous devez présenter votre carte d'étudiant.",
                    metadata={"source": "services", "library": "Toutes"}
                ),
                Document(
                    page_content="La bibliothèque numérique Numaclay est accessible 24h/24.",
                    metadata={"source": "services", "library": "Numaclay"}
                )
            ]
            
            # Créer une base de données vectorielle de test
            self.vectordb = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.db_dir
            )
            print(f"Created test vector database with {len(documents)} documents")
        
        # Initialiser le modèle de langage factice
        self.llm = self._initialize_llm()
        
        # Créer la chaîne de RAG
        self.qa_chain = self._setup_qa_chain()
        
    def _initialize_llm(self):
        """Initialise un modèle de langage factice pour le test."""
        print("Using fake LLM for testing purposes")
        # Mapping de questions vers des réponses pour les tests
        self.response_map = {
            "horaires": "La bibliothèque des Sciences est ouverte de 9h à 19h du lundi au vendredi.",
            "où": "La bibliothèque de Droit est située au bâtiment D du campus.",
            "emprunter": "Pour emprunter des livres, vous devez présenter votre carte d'étudiant.",
            "numérique": "La bibliothèque numérique Numaclay est accessible 24h/24 et propose de nombreuses ressources électroniques.",
            "manger": "Je suis désolé, je n'ai pas cette information. Veuillez contacter la bibliothèque directement."
        }
        
        # Liste des réponses par défaut
        responses = list(self.response_map.values())
        
        # Utiliser un FakeListLLM avec ces réponses
        return FakeListLLM(responses=responses)
        
    def _setup_qa_chain(self):
        """Configure la chaîne de question-réponse avec RAG."""
        # Template de prompt
        template = """
        Tu es un assistant bibliothécaire virtuel pour les bibliothèques de l'Université Paris-Saclay.
        Tu dois répondre aux questions des utilisateurs à propos des bibliothèques de l'université
        en te basant uniquement sur les informations contextuelles fournies ci-dessous.
        
        Si tu ne connais pas la réponse ou si l'information n'est pas dans le contexte,
        dis simplement que tu ne disposes pas de cette information et suggère de contacter
        directement la bibliothèque ou de consulter le site web officiel.
        
        Contexte:
        {context}
        
        Question: {question}
        
        Réponse:
        """
        
        # Création du prompt
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Création de la chaîne de RAG
        retriever = self.vectordb.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 2}
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        
        return qa_chain
        
    def ask(self, question):
        """Pose une question au système RAG."""
        print(f"Question: {question}")
        
        # Pour les tests, utiliser le mapping si possible
        # Chercher des mots clés dans la question
        question_lower = question.lower()
        
        # Nouvelle façon pour détecter quel type de réponse utiliser
        if "horaires" in question_lower or "heures" in question_lower or "ouvert" in question_lower:
            if hasattr(self, 'response_map'):
                response = self.response_map["horaires"]
                print(f"Using mapped response for 'horaires'")
        elif "où" in question_lower or "situe" in question_lower or "trouve" in question_lower:
            if hasattr(self, 'response_map'):
                response = self.response_map["où"]
                print(f"Using mapped response for 'où'")
        elif "emprunter" in question_lower or "livres" in question_lower or "carte" in question_lower:
            if hasattr(self, 'response_map'):
                response = self.response_map["emprunter"]
                print(f"Using mapped response for 'emprunter'")
        elif "numérique" in question_lower or "24" in question_lower or "accessible" in question_lower:
            if hasattr(self, 'response_map'):
                response = self.response_map["numérique"]
                print(f"Using mapped response for 'numérique'")
        elif "manger" in question_lower or "nourriture" in question_lower:
            if hasattr(self, 'response_map'):
                response = self.response_map["manger"]  
                print(f"Using mapped response for 'manger'")
        else:
            # Si aucun mot clé trouvé, utiliser la chaine RAG normalement
            result = self.qa_chain({"query": question})
            response = result["result"]
            source_docs = result.get("source_documents", [])
            
            # Afficher les sources
            print("\nSources:")
            for i, doc in enumerate(source_docs):
                print(f"Source {i+1}: {doc.metadata.get('library', 'N/A')} - {doc.metadata.get('source', 'N/A')}")
                print(f"Contenu: {doc.page_content[:100]}...")
            
            return response, source_docs
        
        # Pour les réponses mappées, simuler des documents sources
        doc = Document(
            page_content=response,
            metadata={"library": "Test Library", "source": "test_data"}
        )
        source_docs = [doc]
        
        return response, source_docs

if __name__ == "__main__":
    rag_test = SimpleRagTest()
    print("Test RAG initialisé. Posez vos questions (tapez 'quit' pour quitter):")
    
    while True:
        try:
            question = input("\nVotre question: ")
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            answer, _ = rag_test.ask(question)
            print(f"\nRéponse: {answer}")
        except KeyboardInterrupt:
            print("\nAu revoir!")
            break
        except EOFError:
            print("\nAu revoir!")
            break