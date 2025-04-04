"""
Exemple d'intégration du module des horaires dans un système RAG existant.
Ce script montre comment connecter le module d'horaires aux systèmes RAG existants
sans avoir à modifier directement le code source principal.
"""

import sys
import os
import re

# Ajouter le répertoire parent au chemin Python pour permettre l'importation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importer les systèmes RAG existants
from rag_chatbot import BibliothequeBot
from rag_chatbot_enhanced import EnhancedBibliothequeBot
from simple_rag import SimpleRAG

# Importer le module des horaires
from modules.horaires_module import HorairesModule

class ModuleIntegrator:
    """
    Classe qui intègre les modules spécialisés avec les systèmes RAG existants.
    """
    
    def __init__(self, rag_system, cache_dir="data/cache"):
        """
        Initialise l'intégrateur avec un système RAG existant.
        
        Args:
            rag_system: Une instance d'un système RAG existant
            cache_dir (str): Répertoire pour stocker les données en cache
        """
        self.rag_system = rag_system
        self.cache_dir = cache_dir
        
        # Créer le répertoire cache s'il n'existe pas
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Initialiser les modules spécialisés
        self.horaires_module = HorairesModule(cache_dir=cache_dir)
        
        print(f"ModuleIntegrator initialisé avec {type(rag_system).__name__} et HorairesModule")
    
    def is_horaires_question(self, question):
        """
        Détermine si une question concerne les horaires.
        
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
        """
        Répond à une question en utilisant soit le module spécialisé approprié,
        soit le système RAG standard.
        
        Args:
            question (str): La question posée
            
        Returns:
            str: La réponse à la question
            list: Les sources utilisées (si disponibles)
        """
        print(f"Question reçue: {question}")
        
        # Vérifier si la question concerne les horaires
        if self.is_horaires_question(question):
            print("Question sur les horaires détectée. Utilisation du module spécialisé.")
            try:
                answer = self.horaires_module.handle_query(question)
                
                # Ajouter une note sur la source des données
                answer += "\n\nNote: Ces informations sont récupérées en temps réel depuis les sources officielles."
                
                # Créer une source virtuelle pour l'affichage
                source = {
                    "title": "Horaires des bibliothèques (données en temps réel)",
                    "url": "https://www.bibliotheques.universite-paris-saclay.fr/horaires-et-affluence"
                }
                
                # Si le système RAG retourne les sources dans un format particulier, adapter
                if hasattr(self.rag_system, 'ask'):
                    # Pour les systèmes comme EnhancedBibliothequeBot qui retournent (answer, sources)
                    from langchain_core.documents import Document
                    source_docs = [Document(
                        page_content="Données d'horaires récupérées en temps réel",
                        metadata={
                            "source": "module_horaires",
                            "title": "Horaires des bibliothèques",
                            "url": "https://www.bibliotheques.universite-paris-saclay.fr/horaires-et-affluence"
                        }
                    )]
                    return answer, source_docs
                else:
                    # Pour les systèmes plus simples qui retournent juste une réponse
                    return answer
            except Exception as e:
                print(f"Erreur avec le module d'horaires: {e}")
                # Continuer avec la méthode standard en cas d'erreur
        
        # Utiliser le système RAG standard pour les autres questions
        print("Utilisation du système RAG standard.")
        return self.rag_system.ask(question)

# Exemple d'utilisation
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Intégration des modules spécialisés avec les systèmes RAG')
    parser.add_argument('--system', choices=['simple', 'standard', 'enhanced'], default='enhanced', 
                        help='Système RAG à utiliser')
    parser.add_argument('--model', default='fake', help='Modèle à utiliser (fake, llama, etc.)')
    parser.add_argument('--data', default='data', help='Répertoire des données')
    parser.add_argument('--db', default='vectordb', help='Répertoire de la base vectorielle')
    
    args = parser.parse_args()
    
    # Initialiser le système RAG approprié
    if args.system == 'simple':
        rag_system = SimpleRAG(data_dir=args.data)
    elif args.system == 'standard':
        rag_system = BibliothequeBot(data_dir=args.data)
    else:  # enhanced
        rag_system = EnhancedBibliothequeBot(
            model_name=args.model,
            data_dir=args.data,
            db_dir=args.db
        )
    
    # Initialiser l'intégrateur
    integrator = ModuleIntegrator(rag_system, cache_dir=os.path.join(args.data, "cache"))
    
    print(f"Intégrateur initialisé avec {args.system}. Posez vos questions (tapez 'quit' pour quitter):")
    
    while True:
        question = input("\nVotre question: ")
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        result = integrator.ask(question)
        
        # Adapter l'affichage au format retourné
        if isinstance(result, tuple) and len(result) == 2:
            answer, sources = result
            print(f"\nRéponse: {answer}")
            
            # Afficher les sources si disponibles
            if sources:
                print("\nSources:")
                for i, doc in enumerate(sources[:3]):  # Limiter à 3 sources
                    if hasattr(doc, 'metadata'):
                        # Pour les documents LangChain
                        source = doc.metadata.get('source', 'N/A')
                        title = doc.metadata.get('title', doc.metadata.get('library', 'N/A'))
                        url = doc.metadata.get('url', '')
                    else:
                        # Pour d'autres formats
                        source = doc.get('source', 'N/A')
                        title = doc.get('title', 'N/A')
                        url = doc.get('url', '')
                        
                    print(f"Source {i+1}: {title} ({source})")
                    if url:
                        print(f"  URL: {url}")
        else:
            # Format simple
            print(f"\nRéponse: {result}")