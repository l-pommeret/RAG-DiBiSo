import os
from langchain.prompts import PromptTemplate
from langchain_community.llms import FakeListLLM
try:
    from langchain_community.llms import HuggingFacePipeline
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
from langchain.chains.retrieval_qa.base import RetrievalQA
import torch
from data_processor import DataProcessor

class BibliothequeRagBot:
    def __init__(self, model_name="fake", vector_db_dir="vectordb"):
        self.vector_db_dir = vector_db_dir
        self.model_name = model_name
        
        # Charger la base de données vectorielle
        self.data_processor = DataProcessor(db_dir=vector_db_dir)
        self.vectordb = self.data_processor.load_vector_db()
        
        # Initialiser le modèle
        self.llm = self._initialize_llm()
        
        # Créer la chaîne de RAG
        self.qa_chain = self._setup_qa_chain()
    
    def _initialize_llm(self):
        """Initialise un modèle de langage pour le RAG."""
        if HF_AVAILABLE and torch.cuda.is_available() and self.model_name != "fake":
            try:
                # Essayer d'utiliser un vrai modèle HuggingFace
                print(f"Initializing HuggingFace model: {self.model_name}")
                from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
                
                # Charger le tokenizer et le modèle
                tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
                
                # Créer le pipeline
                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_new_tokens=512,
                    temperature=0.7,
                    top_p=0.95,
                    repetition_penalty=1.15
                )
                
                # Créer le LLM
                llm = HuggingFacePipeline(pipeline=pipe)
                return llm
            except Exception as e:
                print(f"Error initializing HuggingFace model: {e}")
                print("Falling back to fake LLM")
        
        # Utiliser un LLM factice si HuggingFace n'est pas disponible ou en cas d'erreur
        print("Using fake LLM for testing purposes")
        responses = [
            "Je suis désolé, je n'ai pas d'information précise à ce sujet. Veuillez contacter directement la bibliothèque.",
            "D'après mes informations, les bibliothèques de Paris-Saclay sont généralement ouvertes de 9h à 19h en semaine.",
            "La bibliothèque universitaire propose de nombreuses ressources numériques accessibles 24h/24.",
            "Pour emprunter des livres, vous devez être inscrit à la bibliothèque avec votre carte d'étudiant ou de personnel.",
            "Les salles de travail en groupe peuvent être réservées en ligne sur le site des bibliothèques universitaires."
        ]
        llm = FakeListLLM(responses=responses)
        return llm
    
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
            search_kwargs={"k": 3}
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
        
        result = self.qa_chain({"query": question})
        
        answer = result["result"]
        source_docs = result.get("source_documents", [])
        
        # Afficher les sources (optionnel, pour le debug)
        print("\nSources:")
        for i, doc in enumerate(source_docs):
            print(f"Source {i+1}: {doc.metadata.get('library', 'N/A')} - {doc.metadata.get('source', 'N/A')}")
        
        return answer, source_docs

# Interface en ligne de commande simple
if __name__ == "__main__":
    bot = BibliothequeRagBot()
    print("Bot initialisé. Posez vos questions (tapez 'quit' pour quitter):")
    
    while True:
        question = input("\nVotre question: ")
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        answer, _ = bot.ask(question)
        print(f"\nRéponse: {answer}")