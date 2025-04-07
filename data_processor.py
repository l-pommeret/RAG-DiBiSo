import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
# Import from the recommended package to éviter LangChainDeprecationWarning
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    # Fallback to legacy import if langchain_huggingface is not installed
    from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings

class DataProcessor:
    def __init__(self, data_dir="data", db_dir="vectordb"):
        self.data_dir = data_dir
        self.db_dir = db_dir
        self.documents = []
        
        # Créer le répertoire de base de données vectorielle s'il n'existe pas
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        
        # Initialiser le modèle d'embedding avec OpenAI pour simplifier
        try:
            # Essayer avec HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cuda' if os.environ.get('USE_CUDA', 'False').lower() == 'true' else 'cpu'}
            )
        except Exception as e:
            print(f"Erreur lors de l'initialisation de HuggingFaceEmbeddings: {e}")
            # Fallback sur des embeddings simples
            from langchain_community.embeddings import FakeEmbeddings
            self.embeddings = FakeEmbeddings(size=384)  # Utiliser des embeddings de test
    
    def load_data(self):
        """Charge les données scrappées depuis les fichiers JSON."""
        all_data = []
        
        # Essayer de charger all_pages.json en priorité
        try:
            with open(f"{self.data_dir}/all_pages.json", 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                print(f"Loaded data from all_pages.json ({len(all_data)} pages).")
                return all_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Couldn't load all_pages.json: {e}")
        
        # Si all_pages.json n'existe pas ou est invalide, charger les fichiers individuels
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json') and filename != 'all_pages.json':
                try:
                    with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
                        page_data = json.load(f)
                        all_data.append(page_data)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        print(f"Loaded data from {len(all_data)} individual JSON files.")
        return all_data
    
    def create_documents(self, data):
        """Transforme les données en documents pour le traitement."""
        documents = []
        
        for page in data:
            # Créer un document par page
            title = page.get('title', 'Sans titre')
            url = page.get('url', '')
            content = page.get('main_content', page.get('content', ''))
            
            if not content or len(content) < 10:
                continue
                
            # Document pour le contenu de la page
            page_info = f"""
Titre: {title}
URL: {url}
Contenu: {content}
            """
            
            documents.append(Document(
                page_content=page_info,
                metadata={
                    "source": "page_data",
                    "title": title,
                    "url": url
                }
            ))
        
        return documents
    
    def split_documents(self, documents):
        """Divise les documents en chunks pour une meilleure recherche."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        return text_splitter.split_documents(documents)
    
    def create_vector_db(self):
        """Crée la base de données vectorielle à partir des documents."""
        # Charger les données
        data = self.load_data()
        
        if not data:
            print("No data found. Please run the scraper first.")
            return None
        
        # Créer les documents
        documents = self.create_documents(data)
        
        # Diviser les documents en chunks
        chunks = self.split_documents(documents)
        
        print(f"Created {len(chunks)} document chunks from {len(documents)} original documents.")
        
        # Créer la base de données vectorielle
        # Chroma persiste automatiquement les données depuis la version 0.4.x
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.db_dir
        )
        
        return vectordb
    
    def load_vector_db(self):
        """Charge une base de données vectorielle existante."""
        return Chroma(
            persist_directory=self.db_dir,
            embedding_function=self.embeddings
        )

    def process_data(self):
        """Process des données et création de la base vectorielle."""
        vectordb = self.create_vector_db()
        if vectordb:
            print(f"Base de données vectorielle créée et sauvegardée dans le répertoire '{self.db_dir}'.")
            return True
        return False

if __name__ == "__main__":
    processor = DataProcessor()
    processor.process_data()