import os
import json
import sys
from collections import defaultdict
import re

class SimpleSearch:
    """
    Une implémentation simple de recherche basée sur les mots-clés.
    """
    def __init__(self, data_dir="data", txt_dir="txt_data"):
        self.data_dir = data_dir
        self.txt_dir = txt_dir
        self.documents = []
        self.load_documents()
        
    def load_documents(self):
        """Charge tous les documents texte et leurs métadonnées."""
        print("Chargement des documents...")
        
        # Charger les fichiers texte
        if os.path.exists(self.txt_dir) and os.path.isdir(self.txt_dir):
            txt_files = [f for f in os.listdir(self.txt_dir) if f.endswith('.txt')]
            
            for txt_file in txt_files:
                try:
                    with open(os.path.join(self.txt_dir, txt_file), 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Chercher les métadonnées dans le répertoire data
                    metadata = {
                        "source": txt_file,
                        "title": f"Document {txt_file}",
                        "url": ""
                    }
                    
                    json_file = txt_file.replace('.txt', '.json')
                    if os.path.exists(os.path.join(self.data_dir, json_file)):
                        try:
                            with open(os.path.join(self.data_dir, json_file), 'r', encoding='utf-8') as jf:
                                json_data = json.load(jf)
                                
                                if isinstance(json_data, dict):
                                    metadata["title"] = json_data.get('title', metadata["title"])
                                    metadata["url"] = json_data.get('url', "")
                        except Exception as e:
                            print(f"Erreur lors du chargement des métadonnées pour {json_file}: {e}")
                    
                    self.documents.append({
                        "content": content,
                        "metadata": metadata
                    })
                except Exception as e:
                    print(f"Erreur lors du chargement de {txt_file}: {e}")
        
        print(f"Chargé {len(self.documents)} documents")
    
    def search(self, query, k=3):
        """
        Recherche les documents les plus pertinents pour la requête.
        Utilise une recherche simple basée sur les mots-clés.
        """
        query = query.lower()
        
        # Extraire les mots-clés (mots de plus de 3 lettres)
        keywords = [word for word in re.findall(r'\b\w+\b', query) if len(word) > 3]
        
        # Si aucun mot-clé n'est trouvé, utiliser tous les mots
        if not keywords:
            keywords = [word for word in re.findall(r'\b\w+\b', query)]
        
        # Calculer un score simple pour chaque document
        scored_docs = []
        for doc in self.documents:
            score = 0
            content = doc["content"].lower()
            
            # Augmenter le score pour chaque occurrence de mot-clé
            for keyword in keywords:
                matches = re.findall(r'\b' + re.escape(keyword) + r'\b', content)
                score += len(matches) * 10
                
                # Donner un bonus pour les mots-clés dans le titre
                title = doc["metadata"]["title"].lower()
                matches_title = re.findall(r'\b' + re.escape(keyword) + r'\b', title)
                score += len(matches_title) * 50
            
            # Ne garder que les documents avec au moins un match
            if score > 0:
                scored_docs.append((doc, score))
        
        # Trier par score décroissant et prendre les k premiers
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored_docs[:k]]

class SimpleRagBot:
    """
    Un système RAG simple qui utilise une recherche basée sur les mots-clés.
    """
    def __init__(self, data_dir="data", txt_dir="txt_data"):
        self.searcher = SimpleSearch(data_dir, txt_dir)
        print(f"Bot initialisé avec {len(self.searcher.documents)} documents")
    
    def generate_answer(self, question, context):
        """
        Génère une réponse à partir de la question et du contexte.
        Dans cette version simplifiée, nous renvoyons juste le contexte.
        """
        return f"En réponse à votre question sur '{question}', voici l'information pertinente :\n\n{context}"
    
    def ask(self, question):
        """
        Répond à une question en utilisant le système RAG.
        """
        print(f"Question: {question}")
        
        # Rechercher les documents pertinents
        relevant_docs = self.searcher.search(question, k=3)
        
        if not relevant_docs:
            return "Je suis désolé, je n'ai pas trouvé d'information pertinente pour cette question.", []
        
        # Extraire les extraits pertinents de chaque document
        context = ""
        for doc in relevant_docs:
            content = doc["content"]
            # Limiter la longueur de l'extrait
            if len(content) > 500:
                content = content[:500] + "..."
            context += f"\n\n--- Extrait de {doc['metadata']['title']} ---\n{content}"
        
        # Générer la réponse
        answer = self.generate_answer(question, context)
        
        # Afficher les sources (pour le debug)
        print("\nSources:")
        for i, doc in enumerate(relevant_docs):
            print(f"Source {i+1}: {doc['metadata']['title']} ({doc['metadata']['source']})")
        
        return answer, relevant_docs

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Système RAG simple pour les bibliothèques de Paris-Saclay')
    parser.add_argument('--data', '-d', help='Répertoire des données JSON', default='data')
    parser.add_argument('--txt', '-t', help='Répertoire des données texte', default='txt_data')
    
    args = parser.parse_args()
    
    bot = SimpleRagBot(args.data, args.txt)
    
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
            for i, doc in enumerate(sources):
                print(f"Source {i+1}: {doc['metadata']['title']} ({doc['metadata']['source']})")
                if doc['metadata'].get('url'):
                    print(f"  URL: {doc['metadata']['url']}")
        else:
            print("\nAucune source disponible pour cette réponse.")