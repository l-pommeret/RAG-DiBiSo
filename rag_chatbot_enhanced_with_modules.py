import os
import sys
import re
from langchain.prompts import PromptTemplate
from langchain_community.llms import FakeListLLM, HuggingFacePipeline, LlamaCpp
from huggingface_hub import hf_hub_download
import torch
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
import json

# Importer le module des horaires
from modules.horaires_module import HorairesModule

class EnhancedBibliothequeBot:
    def __init__(self, model_name='fake', data_dir="data", db_dir="vectordb", rebuild_vectordb=False, use_modules=True):
        self.model_name = model_name
        self.data_dir = data_dir
        self.db_dir = db_dir
        self.use_modules = use_modules
        
        # Initialiser les modules spécialisés si demandé
        if self.use_modules:
            self._initialize_modules()
        
        # Initialiser les embeddings pour la recherche vectorielle
        self.embeddings = self._initialize_embeddings()
        
        # Vérifier si la base de données vectorielle existe ou doit être reconstruite
        if rebuild_vectordb or not os.path.exists(db_dir):
            print("Construction de la base de données vectorielle...")
            self.vectordb = self._build_vectordb()
        else:
            print("Chargement de la base de données vectorielle existante...")
            self.vectordb = self._load_vectordb()
        
        # Initialiser le modèle de langage
        self.llm = self._initialize_llm()
        
        # Configurer la chaîne RAG
        self.qa_chain = self._setup_qa_chain()

    def _initialize_modules(self):
        """Initialise les modules spécialisés."""
        print("Initialisation des modules spécialisés...")
        try:
            # Créer le répertoire cache pour les modules s'il n'existe pas
            cache_dir = os.path.join(self.data_dir, "cache")
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            
            # Initialiser le module d'horaires
            self.horaires_module = HorairesModule(cache_dir=cache_dir)
            print("Module d'horaires initialisé avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'initialisation des modules: {e}")
            self.use_modules = False
    
    def _initialize_embeddings(self):
        """Initialise le modèle d'embeddings."""
        try:
            # Essayer avec HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cuda' if os.environ.get('USE_CUDA', 'False').lower() == 'true' else 'cpu'}
            )
            print(f"Modèle d'embeddings initialisé: sentence-transformers/all-MiniLM-L6-v2")
            return embeddings
        except Exception as e:
            print(f"Erreur lors de l'initialisation de HuggingFaceEmbeddings: {e}")
            # Fallback sur des embeddings simples
            from langchain_community.embeddings import FakeEmbeddings
            print("Utilisation de FakeEmbeddings pour les tests")
            return FakeEmbeddings(size=384)
    
    def _build_vectordb(self):
        """Construit la base de données vectorielle à partir des données."""
        # Créer le répertoire de base de données vectorielle s'il n'existe pas
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        
        # Charger les documents
        documents = self._load_documents()
        
        if not documents:
            print("Aucun document trouvé. Veuillez exécuter le scraper d'abord.")
            return None
        
        # Diviser les documents en chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        
        print(f"Création de {len(chunks)} chunks à partir de {len(documents)} documents...")
        
        # Créer la base de données vectorielle
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.db_dir
        )
        
        # Persister la base de données
        vectordb.persist()
        
        return vectordb
    
    def _load_vectordb(self):
        """Charge une base de données vectorielle existante."""
        return Chroma(
            persist_directory=self.db_dir,
            embedding_function=self.embeddings
        )
    
    def _load_documents(self):
        """Charge tous les documents à partir des fichiers JSON."""
        documents = []
        
        # Vérifier d'abord si nous avons un répertoire de fichiers txt
        txt_dir = "txt_data"
        if os.path.exists(txt_dir) and os.path.isdir(txt_dir):
            print(f"Chargement des fichiers texte depuis {txt_dir}...")
            txt_files = [f for f in os.listdir(txt_dir) if f.endswith('.txt')]
            
            for txt_file in txt_files:
                try:
                    with open(os.path.join(txt_dir, txt_file), 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Essayer de déterminer le titre et l'URL à partir des fichiers json correspondants
                        title = f"Document {txt_file}"
                        url = ""
                        
                        # Le fichier json peut avoir le même nom mais dans un répertoire différent
                        json_file = txt_file.replace('.txt', '.json')
                        if os.path.exists(os.path.join(self.data_dir, json_file)):
                            try:
                                with open(os.path.join(self.data_dir, json_file), 'r', encoding='utf-8') as jf:
                                    json_data = json.load(jf)
                                    title = json_data.get('title', title)
                                    url = json_data.get('url', "")
                            except:
                                pass
                        
                        documents.append(Document(
                            page_content=content,
                            metadata={
                                "source": txt_file,
                                "title": title,
                                "url": url
                            }
                        ))
                except Exception as e:
                    print(f"Erreur lors du chargement de {txt_file}: {e}")
        
        # Ensuite, ajouter les données depuis les fichiers JSON
        print(f"Chargement des données JSON depuis {self.data_dir}...")
        
        # Charger d'abord le fichier JSON global all_pages.json s'il existe
        all_pages_path = os.path.join(self.data_dir, 'all_pages.json')
        if os.path.exists(all_pages_path):
            try:
                with open(all_pages_path, 'r', encoding='utf-8') as f:
                    pages = json.load(f)
                    for page in pages:
                        if isinstance(page, dict):
                            content = page.get('content', '') or page.get('main_content', '')
                            if content:
                                documents.append(Document(
                                    page_content=content,
                                    metadata={
                                        "source": "all_pages",
                                        "title": page.get('title', 'Page sans titre'),
                                        "url": page.get('url', '')
                                    }
                                ))
                print(f"Chargé {len(pages)} pages depuis all_pages.json")
            except Exception as e:
                print(f"Erreur lors du chargement de all_pages.json: {e}")
        
        # Charger ensuite le fichier JSON global all_libraries.json s'il existe
        all_libraries_path = os.path.join(self.data_dir, 'all_libraries.json')
        if os.path.exists(all_libraries_path):
            try:
                with open(all_libraries_path, 'r', encoding='utf-8') as f:
                    libraries = json.load(f)
                    for library in libraries:
                        # Document pour les informations générales
                        documents.append(Document(
                            page_content=library.get('description', ''),
                            metadata={
                                "source": "all_libraries",
                                "library": library.get('name', 'Bibliothèque inconnue'),
                                "url": library.get('url', '')
                            }
                        ))
                        
                        # Document pour les horaires
                        if library.get('hours') and library.get('hours') != "Horaires non disponibles":
                            documents.append(Document(
                                page_content=f"Horaires de la bibliothèque {library.get('name')}: {library.get('hours')}",
                                metadata={
                                    "source": "hours",
                                    "library": library.get('name', 'Bibliothèque inconnue')
                                }
                            ))
                print(f"Chargé {len(libraries)} bibliothèques depuis all_libraries.json")
            except Exception as e:
                print(f"Erreur lors du chargement de all_libraries.json: {e}")
        
        # Charger les fichiers JSON individuels qui ne sont pas all_pages.json ou all_libraries.json
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json') and filename not in ['all_pages.json', 'all_libraries.json', 'pages.json', 'passages.json']:
                try:
                    with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Si c'est un dictionnaire avec une clé 'body' ou 'content', c'est une page simple
                        if isinstance(data, dict):
                            content = data.get('content', '') or data.get('body', '') or data.get('description', '') or data.get('main_content', '')
                            if content:
                                documents.append(Document(
                                    page_content=content,
                                    metadata={
                                        "source": filename,
                                        "title": data.get('title', 'Document sans titre'),
                                        "url": data.get('url', '')
                                    }
                                ))
                except Exception as e:
                    print(f"Erreur lors du chargement de {filename}: {e}")
        
        print(f"Chargé un total de {len(documents)} documents")
        return documents
    
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
            print("Initialisation du modèle Llama-3 8B...")
            
            try:
                # Utiliser LlamaCpp avec Llama-2 (plus accessible) ou Llama-3
                # Modèle local spécifique à l'environnement Colab
                print("Vérification des modèles locaux...")
                local_model_paths = [
                    "/content/llama-2-7b-chat.Q5_K_M.gguf",  # Chemin probable dans Colab
                    "/content/models/llama-2-7b-chat.Q5_K_M.gguf",  # Alternative
                ]
                
                # Vérifier si un modèle local existe
                model_path = None
                for path in local_model_paths:
                    if os.path.exists(path):
                        model_path = path
                        print(f"Utilisation du modèle local: {path}")
                        break
                
                # Si pas de modèle local, essayer le téléchargement
                if not model_path:
                    try:
                        # Télécharger Llama-2 qui est plus accessible sans authentification
                        print("Téléchargement de Llama-2-7B...")
                        model_path = hf_hub_download(
                            repo_id="TheBloke/Llama-2-7B-Chat-GGUF",
                            filename="llama-2-7b-chat.Q5_K_M.gguf"
                        )
                    except Exception as e:
                        print(f"Téléchargement de Llama-2 échoué: {e}")
                        raise Exception("Impossible de charger un modèle Llama")
                
                # Vérifier si CUDA est activé
                use_gpu = torch.cuda.is_available() and os.environ.get('USE_CUDA', 'False').lower() == 'true'
                n_gpu_layers = -1 if use_gpu else 0  # -1 = toutes les couches sur GPU
                
                # Paramètres GPU améliorés
                llm_params = {
                    "model_path": model_path,
                    "temperature": 0.1,
                    "max_tokens": 2000,
                    "top_p": 0.95,
                    "n_ctx": 4096,  # Contexte plus large
                    "verbose": False,
                    "n_threads": 4,  # Exploiter les CPU multi-cœurs
                }
                
                # Ajouter les paramètres GPU spécifiques si GPU disponible
                if use_gpu:
                    llm_params.update({
                        "n_gpu_layers": n_gpu_layers,
                        "f16_kv": True,  # Utiliser float16 pour les clés/valeurs
                        "n_batch": 512,  # Augmenter taille de batch pour GPU
                        "use_mlock": False,  # Pas besoin de verrouiller la mémoire
                        "use_mmap": True,  # Utiliser mmap pour charger le modèle
                        "verbose": True,  # Activer les logs verbeux pour debug
                        "n_ctx": 2048,  # Contexte réduit pour utiliser plus de GPU
                        "model_kwargs": {"offload_kqv": True}  # Placer offload_kqv dans model_kwargs
                    })
                    print(f"Configuration GPU active: {n_gpu_layers} couches sur GPU")
                print("Attention: pour vérifier l'utilisation réelle du GPU, exécutez nvidia-smi pendant l'inférence")
                
                llm = LlamaCpp(**llm_params)
                
                device_info = "GPU" if n_gpu_layers != 0 else "CPU"
                print(f"Modèle Llama-3 8B initialisé avec succès sur {device_info}!")
                return llm
                
            except Exception as e:
                print(f"ERREUR lors de l'initialisation de Llama-3: {e}")
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
    
    def _preprocess_query(self, query):
        """
        Prétraite la requête pour améliorer les résultats de recherche.
        
        Args:
            query (str): La requête originale
            
        Returns:
            str: La requête prétraitée
        """
        query_lower = query.lower()
        
        # Enrichissement de requêtes spécifiques
        if "prix" in query_lower or "coût" in query_lower or "tarif" in query_lower:
            if "impression" in query_lower or "imprime" in query_lower or "imprimer" in query_lower:
                if "a4" in query_lower or "page" in query_lower or "feuille" in query_lower:
                    # Requête sur les prix d'impression de page A4
                    return f"{query} prix impression a4 photocopie"
        
        # Par défaut, retourner la requête inchangée
        return query
    
    def _setup_qa_chain(self):
        """Configure la chaîne RAG pour la question-réponse."""
        if not self.vectordb:
            print("ERREUR: Base de données vectorielle non initialisée")
            return None
            
        # Créer le prompt template avec les documents récupérés
        prompt_template = """Vous êtes un assistant virtuel spécialisé dans les bibliothèques de l'Université Paris-Saclay.
        Utilisez les informations suivantes pour répondre à la question.
        Si vous ne connaissez pas la réponse, dites simplement que vous n'avez pas cette information et suggérez de contacter directement la bibliothèque.
        Ne fabriquez pas de réponse si l'information n'est pas présente dans le contexte fourni.
        
        Contexte:
        {context}
        
        Question: {question}
        
        Réponse:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template, 
            input_variables=["context", "question"]
        )
        
        # Configurer la chaîne de recherche et réponse
        try:
            # Augmenter le nombre de documents récupérés pour améliorer la pertinence
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 5}),
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT}
            )
            print("Chaîne RAG configurée avec succès")
            return qa_chain
        except Exception as e:
            print(f"ERREUR lors de la configuration de la chaîne RAG: {e}")
            return None
    
    def _is_horaires_question(self, question):
        """
        Détermine si une question concerne les horaires d'une bibliothèque.
        
        Args:
            question (str): La question posée
            
        Returns:
            bool: True si la question concerne les horaires, False sinon
        """
        question = question.lower()
        
        # Mots-clés liés aux horaires
        horaires_keywords = [
            "horaire", "ouverture", "ouvre", "ouvert", 
            "fermeture", "ferme", "fermé",
            "heure", "temps", "quand", "moment", "période",
            "disponible", "accès", "accessible"
        ]
        
        # Vérifier si la question contient des mots-clés liés aux horaires
        if any(keyword in question for keyword in horaires_keywords):
            # Vérifier aussi si la question mentionne une bibliothèque
            bibliotheque_keywords = [
                "biblio", "bu ", "bibliothèque", "mediathèque", "médiathèque",
                "orsay", "sceaux", "kremlin", "bicêtre", "lumen",
                "science", "droit", "médecine", "learning"
            ]
            
            if any(keyword in question for keyword in bibliotheque_keywords):
                return True
        
        return False
    
    def ask(self, question):
        """Pose une question au système RAG ou aux modules spécialisés si approprié."""
        print(f"Question: {question}")
        
        # Si les modules sont activés, vérifier si la question concerne les horaires
        if self.use_modules and self._is_horaires_question(question):
            print("Détection d'une question sur les horaires, utilisation du module spécialisé")
            try:
                # Utiliser le module d'horaires pour répondre
                answer = self.horaires_module.handle_query(question)
                
                # Ajouter un message pour indiquer que les données sont actualisées
                note = "\n\nNote: Ces informations sont récupérées en temps réel depuis les sources officielles."
                
                # Préparation du contenu de la page pour utilisation dans les sources
                content_for_source = str(answer)
                
                # Créer une source virtuelle avec les données dynamiques d'horaires
                # qui inclut le contenu de la réponse pour que le LLM puisse le citer
                source_docs = [Document(
                    page_content=content_for_source,
                    metadata={
                        "source": "module_horaires",
                        "title": "Horaires des bibliothèques",
                        "url": "https://www.bibliotheques.universite-paris-saclay.fr/horaires-et-affluence"
                    }
                )]
                
                return answer + note, source_docs
            except Exception as e:
                print(f"Erreur avec le module d'horaires: {e}")
                # Continuer avec la méthode standard en cas d'erreur avec le module
        
        # Utiliser la chaîne RAG standard pour les autres questions
        if not self.qa_chain:
            print("ERREUR: La chaîne RAG n'est pas configurée")
            return "Je suis désolé, je rencontre un problème technique. Veuillez réessayer plus tard.", []
        
        try:
            # Prétraiter la question pour améliorer les résultats
            processed_query = self._preprocess_query(question)
            
            # Utiliser la chaîne RAG pour obtenir une réponse
            result = self.qa_chain({"query": processed_query})
            
            if isinstance(result, dict):
                answer = result.get("result", "")
                source_docs = result.get("source_documents", [])
            else:
                # Fallback si le résultat n'est pas au format attendu
                answer = str(result)
                source_docs = []
            
            # Afficher les sources pour le debug
            print("\nSources:")
            for i, doc in enumerate(source_docs):
                source = doc.metadata.get('source', 'N/A')
                title = doc.metadata.get('title', 'N/A')
                library = doc.metadata.get('library', 'N/A')
                print(f"Source {i+1}: {source} - {title or library}")
            
            return answer, source_docs
            
        except Exception as e:
            print(f"ERREUR lors de la génération de la réponse: {e}")
            return "Je suis désolé, une erreur s'est produite lors du traitement de votre question. Veuillez réessayer.", []

# Interface en ligne de commande
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Chatbot RAG pour les bibliothèques de Paris-Saclay')
    parser.add_argument('--model', '-m', help='Modèle à utiliser (fake, llama)', default='fake')
    parser.add_argument('--data', '-d', help='Répertoire des données', default='data')
    parser.add_argument('--db', '-db', help='Répertoire de la base vectorielle', default='vectordb')
    parser.add_argument('--rebuild', '-r', help='Reconstruire la base vectorielle', action='store_true')
    parser.add_argument('--no-modules', help='Désactiver les modules spécialisés', action='store_true')
    parser.add_argument('--use-cuda', help='Utiliser CUDA pour l\'accélération GPU', action='store_true')
    
    args = parser.parse_args()
    
    # Définir la variable d'environnement pour CUDA si demandé
    if args.use_cuda:
        if torch.cuda.is_available():
            os.environ['USE_CUDA'] = 'True'
            print(f"CUDA activé pour l'accélération GPU - {torch.cuda.get_device_name(0)}")
            print(f"Mémoire GPU disponible: {torch.cuda.get_device_properties(0).total_memory / 1024 / 1024 / 1024:.2f} GB")
        else:
            print("WARNING: CUDA demandé mais non disponible sur ce système - utilisation du CPU")
    
    bot = EnhancedBibliothequeBot(
        model_name=args.model,
        data_dir=args.data,
        db_dir=args.db,
        rebuild_vectordb=args.rebuild,
        use_modules=not args.no_modules
    )
    
    print("Bot initialisé. Posez vos questions (tapez 'quit' pour quitter):")
    
    while True:
        question = input("\nVotre question: ")
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        answer, sources = bot.ask(question)
        print(f"\nRéponse: {answer}")
        
        # Afficher les sources
        if sources:
            print("\nSources:")
            for i, doc in enumerate(sources[:3]):  # Limiter à 3 sources
                source = doc.metadata.get('source', 'N/A')
                title = doc.metadata.get('title', doc.metadata.get('library', 'N/A'))
                url = doc.metadata.get('url', '')
                print(f"Source {i+1}: {title} ({source})")
                if url:
                    print(f"  URL: {url}")
        else:
            print("\nAucune source disponible pour cette réponse.")