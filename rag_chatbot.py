import os
from langchain.prompts import PromptTemplate
from langchain.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from transformers import LlamaForCausalLM, LlamaTokenizer, pipeline
import torch
from data_processor import DataProcessor

class BibliothequeRagBot:
    def __init__(self, model_name="meta-llama/Llama-2-7b-chat-hf", vector_db_dir="vectordb"):
        self.vector_db_dir = vector_db_dir
        self.model_name = model_name
        
        # Charger la base de données vectorielle
        self.data_processor = DataProcessor(db_dir=vector_db_dir)
        self.vectordb = self.data_processor.load_vector_db()
        
        # Initialiser le modèle Llama
        self.llm = self._initialize_llm()
        
        # Créer la chaîne de RAG
        self.qa_chain = self._setup_qa_chain()
    
    def _initialize_llm(self):
        """Initialise le modèle Llama."""
        print(f"Initializing {self.model_name}...")
        
        # Vérifier si CUDA est disponible
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        
        # Chargement du tokenizer et du modèle
        tokenizer = LlamaTokenizer.from_pretrained(self.model_name)
        model = LlamaForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            load_in_8bit=device == "cuda",  # Quantization pour réduire l'empreinte mémoire
        )
        
        # Configuration du pipeline
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.1,
            top_p=0.95,
            repetition_penalty=1.2,
            do_sample=True
        )
        
        # Création du LLM LangChain
        llm = HuggingFacePipeline(pipeline=pipe)
        
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