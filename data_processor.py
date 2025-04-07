import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
# Import directly from transformers instead
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
        
        # Tenter de charger le fichier global d'abord
        try:
            with open(f"{self.data_dir}/all_libraries.json", 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                print(f"Loaded data for {len(all_data)} libraries from global file.")
                return all_data
        except FileNotFoundError:
            pass
        
        # Si le fichier global n'existe pas, charger les fichiers individuels
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json') and filename != 'all_libraries.json':
                try:
                    with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
                        library_data = json.load(f)
                        all_data.append(library_data)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        print(f"Loaded data for {len(all_data)} libraries from individual files.")
        return all_data
    
    def create_documents(self, data):
        """Transforme les données en documents pour le traitement."""
        documents = []
        
        for library in data:
            # Document pour les informations générales
            general_info = f"""
Nom: {library['name']}
URL: {library['url']}
Adresse: {library['address']}
Description: {library['description']}
            """
            
            documents.append(Document(
                page_content=general_info,
                metadata={
                    "source": "general_info",
                    "library": library['name']
                }
            ))
            
            # Document pour les horaires
            if isinstance(library['hours'], str) and library['hours'] != "Horaires non disponibles":
                documents.append(Document(
                    page_content=f"Horaires de la bibliothèque {library['name']}: {library['hours']}",
                    metadata={
                        "source": "hours",
                        "library": library['name']
                    }
                ))
            
            # Document pour les contacts
            if isinstance(library['contact'], dict) and library['contact']:
                contact_info = f"Contacts de la bibliothèque {library['name']}:\n"
                
                if 'email' in library['contact']:
                    contact_info += f"Emails: {', '.join(library['contact']['email'])}\n"
                
                if 'phone' in library['contact']:
                    contact_info += f"Téléphones: {', '.join(library['contact']['phone'])}\n"
                
                documents.append(Document(
                    page_content=contact_info,
                    metadata={
                        "source": "contact",
                        "library": library['name']
                    }
                ))
            
            # Document pour les services
            if isinstance(library['services'], list) and library['services']:
                services_info = f"Services disponibles à la bibliothèque {library['name']}:\n"
                services_info += "\n".join([f"- {service}" for service in library['services']])
                
                documents.append(Document(
                    page_content=services_info,
                    metadata={
                        "source": "services",
                        "library": library['name']
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
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.db_dir
        )
        
        # Persister la base de données
        vectordb.persist()
        
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