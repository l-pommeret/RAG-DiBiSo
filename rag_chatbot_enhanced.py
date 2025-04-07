import os
import sys
from langchain.prompts import PromptTemplate
from langchain_community.llms import FakeListLLM, HuggingFacePipeline, LlamaCpp
from huggingface_hub import hf_hub_download
import torch
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.retrievers import BM25Retriever
import json
import re
from typing import List, Dict, Any, Optional

class EnhancedBibliothequeBot:
    def __init__(self, model_name='fake', data_dir="data", db_dir="vectordb", rebuild_vectordb=False):
        self.model_name = model_name
        self.data_dir = data_dir
        self.db_dir = db_dir
        
        # Initialiser les embeddings pour la recherche vectorielle
        self.embeddings = self._initialize_embeddings()
        
        # Vérifier si la base de données vectorielle existe ou doit être reconstruite
        if rebuild_vectordb or not os.path.exists(db_dir):
            print("Construction de la base de données vectorielle...")
            self.vectordb = self._build_vectordb()
        else:
            print("Chargement de la base de données vectorielle existante...")
            self.vectordb = self._load_vectordb()
        
        # Initialiser les documents
        self.documents = self._load_documents()
        
        # Obtenir le retriever vectoriel (augmenter k pour récupérer plus de documents)
        self.vector_retriever = self.vectordb.as_retriever(search_kwargs={"k": 10})
        
        # Initialiser le modèle de langage
        self.llm = self._initialize_llm()
        
        # Configurer la chaîne RAG
        self.qa_chain = self._setup_qa_chain()
    
    def _initialize_embeddings(self):
        """Initialise le modèle d'embeddings."""
        try:
            # Utiliser le même modèle d'embeddings que celui utilisé pour créer la base vectorielle
            # Pour éviter les erreurs de dimension
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
    
    def _initialize_bm25(self):
        """Initialise le retriever BM25."""
        if not self.documents:
            print("Aucun document disponible pour BM25")
            return None
        
        try:
            # Préparer les documents pour BM25 (extraire le contenu)
            texts = [doc.page_content for doc in self.documents]
            
            # Créer le retriever BM25
            bm25_retriever = BM25Retriever.from_texts(texts)
            bm25_retriever.k = 10  # Récupérer un plus grand nombre de documents
            
            # Associer les documents originaux
            bm25_retriever.docs = self.documents
            
            print(f"Retriever BM25 initialisé avec {len(texts)} documents")
            return bm25_retriever
        except Exception as e:
            print(f"Erreur lors de l'initialisation du retriever BM25: {e}")
            return None
    
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
            
        elif self.model_name.lower() == 'ollama':
            print("Initialisation du modèle Ollama (Llama 3.1)...")
            try:
                from langchain_community.llms import Ollama
                llm = Ollama(
                    model="llama3", 
                    temperature=0.1,
                    num_ctx=2048
                )
                print("Modèle Ollama (Llama 3.1) initialisé avec succès!")
                return llm
            except Exception as e:
                print(f"ERREUR lors de l'initialisation d'Ollama: {e}")
                print("Assurez-vous qu'Ollama est installé et que le service est en cours d'exécution.")
                print("Pour installer Ollama: https://ollama.com/download")
                print("Pour démarrer le service: ollama serve")
                print("Pour vérifier que Llama 3.1 est disponible: ollama list")
                print("Pour télécharger Llama 3.1 si nécessaire: ollama pull llama3")
                return self._fallback_to_fake_llm()
        
        elif self.model_name.lower() == 'llama':
            print("Initialisation du modèle Llama...")
            
            try:
                # Vérifier si la bibliothèque llama-cpp-python est disponible
                try:
                    from langchain_community.llms import LlamaCpp
                except ImportError:
                    print("Impossible d'importer LlamaCpp, vérification de llama-cpp-python...")
                    try:
                        import llama_cpp
                        print(f"llama-cpp-python est installé mais pas accessible via langchain: {llama_cpp.__version__}")
                        
                        # Tester si llama_cpp est compilé avec CUDA
                        print("Test de la compatibilité CUDA de llama-cpp-python...")
                        try:
                            # Vérifier si la méthode CUBLAS_initialized existe
                            if hasattr(llama_cpp.llama_cpp, 'CUBLAS_initialized'):
                                print(f"Support CUBLAS détecté dans llama_cpp: {llama_cpp.llama_cpp.CUBLAS_initialized()}")
                            else:
                                print("Méthode CUBLAS_initialized non trouvée, la version installée pourrait ne pas supporter CUDA")
                            
                            # Essayer de créer un contexte Llama (devrait montrer les logs CUDA si supporté)
                            print("Tentative de création d'un contexte Llama...")
                            llama_params = llama_cpp.llama_context_params()
                            llama_params.n_gpu_layers = -1  # Utiliser tous les layers GPU si disponible
                            print("llama_cpp supporte les paramètres GPU")
                            
                        except Exception as e3:
                            print(f"Erreur lors du test CUDA de llama-cpp-python: {e3}")
                            
                    except ImportError:
                        print("La bibliothèque llama-cpp-python n'est pas installée")
                        raise ImportError("Could not import llama-cpp-python. Please install it with CUDA support: CMAKE_ARGS='-DLLAMA_CUBLAS=ON' pip install llama-cpp-python")
                
                # Utiliser LlamaCpp pour un modèle plus léger
                model_path = hf_hub_download(
                    repo_id="TheBloke/Llama-2-7B-Chat-GGUF",
                    filename="llama-2-7b-chat.Q4_K_M.gguf"
                )
                
                # Vérifier la disponibilité du GPU
                gpu_available = torch.cuda.is_available()
                print(f"GPU disponible: {gpu_available}")
                if gpu_available:
                    print(f"GPU utilisé: {torch.cuda.get_device_name(0)}")
                    print(f"Mémoire GPU totale: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
                    print(f"Mémoire GPU utilisée: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
                
                # Configuration tenant compte de différentes versions possibles
                try:
                    n_gpu_layers = -1 if gpu_available else 0
                    llm = LlamaCpp(
                        model_path=model_path,
                        temperature=0.1,
                        max_tokens=2000,
                        top_p=1,
                        n_ctx=2048,
                        verbose=True,  # Activé pour voir l'utilisation du GPU
                        n_gpu_layers=n_gpu_layers,  # Utiliser le GPU pour toutes les couches possibles si disponible
                        n_batch=512       # Augmenter la taille du lot pour améliorer les performances GPU
                    )
                    print(f"Modèle Llama initialisé avec n_gpu_layers={n_gpu_layers}")
                except TypeError as te:
                    # Si certains paramètres ne sont pas supportés
                    print(f"Erreur de paramètres LlamaCpp: {te}")
                    print("Tentative avec configuration minimale...")
                    llm = LlamaCpp(
                        model_path=model_path,
                        temperature=0.1,
                        max_tokens=2000,
                        verbose=True,
                        n_gpu_layers=-1 if gpu_available else 0
                    )
                
                print("Modèle Llama initialisé avec succès!")
                return llm
                
            except Exception as e:
                print(f"ERREUR lors de l'initialisation de Llama: {e}")
                print("Si vous utilisez Colab, essayez d'exécuter cette commande puis de relancer le script:")
                print("!CMAKE_ARGS='-DLLAMA_CUBLAS=ON' FORCE_CMAKE=1 pip install --upgrade llama-cpp-python")
                
                # Tentez d'utiliser un modèle HuggingFace comme repli
                try:
                    print("Tentative d'utilisation d'un modèle HuggingFace comme alternative...")
                    from transformers import pipeline
                    from langchain.llms import HuggingFacePipeline
                    
                    # Essayer d'abord avec un petit modèle
                    try:
                        pipe = pipeline(
                            "text-generation", 
                            model="google/flan-t5-small", 
                            max_length=512, 
                            device=0 if torch.cuda.is_available() else -1
                        )
                        llm = HuggingFacePipeline(pipeline=pipe)
                        print("Modèle flan-t5-small initialisé comme alternative!")
                        return llm
                    except Exception as e2:
                        print(f"Erreur avec le modèle flan-t5-small: {e2}")
                        return self._fallback_to_fake_llm()
                    
                except Exception as e2:
                    print(f"Échec de l'alternative HuggingFace: {e2}")
                    return self._fallback_to_fake_llm()
                
        elif self.model_name.lower() == 'huggingface':
            print("Initialisation d'un modèle HuggingFace...")
            try:
                from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
                from langchain.llms import HuggingFacePipeline
                
                # Utiliser un modèle compatible avec la génération de texte
                print("Chargement d'un modèle GPT-2 français...")
                try:
                    # D'abord essayer avec un modèle français
                    model_name = "bigscience/bloom-560m"  # Plus petit que flan-t5 mais compatible
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        device_map="auto" if torch.cuda.is_available() else None,
                        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                    )
                    
                    # Configuration pour génération de texte
                    pipe = pipeline(
                        "text-generation", 
                        model=model,
                        tokenizer=tokenizer,
                        max_length=512,
                        do_sample=True, 
                        temperature=0.5, 
                        top_p=0.95
                    )
                except Exception as e:
                    print(f"Erreur avec le modèle bloom: {e}")
                    print("Tentative avec un modèle plus petit (GPT-2)...")
                    
                    # Fallback sur GPT-2 plus petit
                    model_name = "gpt2"
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        device_map="auto" if torch.cuda.is_available() else None
                    )
                    
                    pipe = pipeline(
                        "text-generation", 
                        model=model,
                        tokenizer=tokenizer,
                        max_length=512,
                        do_sample=True, 
                        temperature=0.7, 
                        top_p=0.95
                    )
                
                # Intégrer dans LangChain avec post-traitement pour améliorer la qualité
                class EnhancedHuggingFacePipeline(HuggingFacePipeline):
                    """Version améliorée du HuggingFacePipeline avec post-traitement des réponses."""
                    
                    def _call(self, prompt, stop=None, **kwargs):
                        """Surcharge de la méthode _call pour post-traiter les résultats."""
                        # Appeler la méthode _call de la classe parent
                        result = super()._call(prompt, stop=stop, **kwargs)
                        
                        # Si le résultat commence par le prompt ou des parties du prompt, le supprimer
                        if result.startswith(prompt):
                            result = result[len(prompt):].strip()
                        
                        # Supprimer le texte "Réponse:" s'il apparaît au début
                        if "Réponse:" in result:
                            result = result.split("Réponse:", 1)[1].strip()
                        
                        # Limiter la répétition en coupant après une répétition de phrase
                        sentences = result.split('. ')
                        if len(sentences) > 3:
                            # Vérifier si nous avons des répétitions
                            unique_sentences = []
                            for s in sentences:
                                if s not in unique_sentences:
                                    unique_sentences.append(s)
                                else:
                                    break
                            
                            result = '. '.join(unique_sentences[:3])
                            if not result.endswith('.'):
                                result += '.'
                        
                        return result
                
                # Utiliser la version améliorée
                llm = EnhancedHuggingFacePipeline(pipeline=pipe)
                print(f"Modèle HuggingFace {model_name} initialisé avec succès!")
                return llm
            except Exception as e:
                print(f"ERREUR lors de l'initialisation du modèle HuggingFace: {e}")
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
        
        # Détection de requêtes sur les horaires
        if any(word in query_lower for word in ["horaire", "ouvert", "ferme", "heures", "quand"]):
            if any(word in query_lower for word in ["bibliothèque", "biblio", "bu"]):
                # Ajouter des mots-clés spécifiques aux horaires
                return f"{query} horaires heures ouverture fermeture"
        
        # Enrichissement de requêtes spécifiques
        if "prix" in query_lower or "coût" in query_lower or "tarif" in query_lower:
            if "impression" in query_lower or "imprime" in query_lower or "imprimer" in query_lower:
                if "a4" in query_lower or "page" in query_lower or "feuille" in query_lower:
                    # Requête sur les prix d'impression de page A4
                    return f"{query} prix impression a4 photocopie"
        
        # Par défaut, retourner la requête inchangée
        return query
    
    def _rerank_documents(self, docs: List[Document], query: str, top_k: int = 5) -> List[Document]:
        """
        Reclasse les documents récupérés en fonction de leur pertinence.
        
        Args:
            docs: Liste des documents récupérés
            query: Requête utilisateur
            top_k: Nombre de documents à retourner
            
        Returns:
            Liste des documents reclassés
        """
        if not docs:
            return []
        
        # Extraire les mots-clés de la requête
        keywords = re.findall(r'\w+', query.lower())
        keywords = [k for k in keywords if len(k) > 2]  # Ignorer les mots courts
        
        # Calculer un score pour chaque document
        scored_docs = []
        
        for doc in docs:
            # Score initial
            score = 0
            content = doc.page_content.lower()
            
            # Nombre de mots-clés trouvés dans le document
            for keyword in keywords:
                count = content.count(keyword)
                score += count * 2  # Pondération plus élevée pour les mots-clés exacts
            
            # Bonus pour les correspondances exactes de phrases
            exact_phrase_bonus = 0
            if query.lower() in content:
                exact_phrase_bonus = 10
            
            # Bonus pour les titres pertinents
            title_bonus = 0
            if "title" in doc.metadata:
                title = doc.metadata["title"].lower()
                for keyword in keywords:
                    if keyword in title:
                        title_bonus += 5
            
            # Score de fraîcheur pour les horaires (hypothétique)
            freshness_bonus = 0
            if "source" in doc.metadata and doc.metadata["source"] == "hours":
                freshness_bonus = 10
            
            # Score final
            final_score = score + exact_phrase_bonus + title_bonus + freshness_bonus
            
            # Bonus spécial pour les documents qui contiennent exactement les informations demandées
            if "horaire" in query.lower() and "horaire" in content:
                final_score += 15
            
            scored_docs.append((doc, final_score))
        
        # Trier par score décroissant
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Retourner les top_k documents
        return [doc for doc, _ in scored_docs[:top_k]]
    
    def _setup_qa_chain(self):
        """Configure la chaîne RAG pour la question-réponse."""
        if not self.vector_retriever:
            print("ERREUR: Retriever non initialisé")
            return None
            
        # Créer le prompt template avec les documents récupérés
        # Adapter le prompt selon le modèle utilisé pour éviter les problèmes de génération
        if self.model_name.lower() == 'huggingface':
            # Prompt plus court et plus direct pour les modèles HuggingFace
            prompt_template = """Réponds à la question sur les bibliothèques universitaires Paris-Saclay.
Utilise uniquement le contexte suivant:

{context}

Question: {question}

Réponse (en 3 phrases maximum):"""
        else:
            # Prompt original pour les autres modèles
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
            # Utiliser le retriever vectoriel
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT}
            )
            print("Chaîne RAG configurée avec succès")
            return qa_chain
        except Exception as e:
            print(f"ERREUR lors de la configuration de la chaîne RAG: {e}")
            return None
    
    def ask(self, question):
        """Pose une question au système RAG."""
        print(f"Question: {question}")
        
        if not self.qa_chain:
            print("ERREUR: La chaîne RAG n'est pas configurée")
            return "Je suis désolé, je rencontre un problème technique. Veuillez réessayer plus tard.", []
        
        try:
            # Prétraiter la question pour améliorer les résultats
            processed_query = self._preprocess_query(question)
            
            # Méthode hybride de recherche
            bm25_docs = []
            vector_docs = []
            
            # Utiliser seulement la recherche vectorielle
            try:
                # Utiliser la chaîne RAG pour obtenir une réponse, ce qui utilise le vector_retriever
                result = self.qa_chain({"query": processed_query})
                
                if isinstance(result, dict):
                    answer = result.get("result", "")
                    vector_docs = result.get("source_documents", [])
                    print(f"Recherche vectorielle a trouvé {len(vector_docs)} documents")
                else:
                    # Fallback si le résultat n'est pas au format attendu
                    answer = str(result)
                    vector_docs = []
            except Exception as e:
                print(f"Erreur avec la recherche vectorielle: {e}")
                answer = "Je suis désolé, une erreur s'est produite."
                vector_docs = []
            
            # Utiliser directement les documents de la recherche vectorielle
            combined_docs = list(vector_docs)
            
            # 4. Reclasser les documents combinés
            if combined_docs:
                reranked_docs = self._rerank_documents(combined_docs, processed_query)
            else:
                reranked_docs = []
            
            # Afficher les sources pour le debug
            print("\nSources après reclassement:")
            for i, doc in enumerate(reranked_docs[:5]):
                source = doc.metadata.get('source', 'N/A')
                title = doc.metadata.get('title', 'N/A')
                library = doc.metadata.get('library', 'N/A')
                print(f"Source {i+1}: {source} - {title or library}")
            
            # Si la réponse n'a pas été générée par la recherche vectorielle,
            # recréer la réponse avec tous les documents combinés
            if not answer and reranked_docs:
                context = "\n\n".join([doc.page_content for doc in reranked_docs[:3]])
                # Simplifier la réponse
                answer = f"D'après les informations disponibles: {reranked_docs[0].page_content}"
            
            return answer, reranked_docs
            
        except Exception as e:
            print(f"ERREUR lors de la génération de la réponse: {e}")
            return "Je suis désolé, une erreur s'est produite lors du traitement de votre question. Veuillez réessayer.", []

# Interface en ligne de commande
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Chatbot RAG pour les bibliothèques de Paris-Saclay')
    parser.add_argument('--model', '-m', help='Modèle à utiliser (fake, ollama, llama, huggingface)', default='fake')
    parser.add_argument('--data', '-d', help='Répertoire des données', default='data')
    parser.add_argument('--db', '-db', help='Répertoire de la base vectorielle', default='vectordb')
    parser.add_argument('--rebuild', '-r', help='Reconstruire la base vectorielle', action='store_true')
    
    args = parser.parse_args()
    
    bot = EnhancedBibliothequeBot(
        model_name=args.model,
        data_dir=args.data,
        db_dir=args.db,
        rebuild_vectordb=args.rebuild
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