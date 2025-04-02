"""
Script pour tester automatiquement le pipeline RAG.
"""

import unittest
from test_simple import SimpleRagTest

class TestRAGPipeline(unittest.TestCase):
    """Tests unitaires pour le pipeline RAG"""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.rag_test = SimpleRagTest(db_dir="vectordb_test")
        print("Test RAG initialisé pour tests unitaires...")
    
    def test_library_hours(self):
        """Test de la récupération des horaires."""
        question = "Quels sont les horaires de la bibliothèque des Sciences?"
        answer, docs = self.rag_test.ask(question)
        self.assertIn("9h à 19h", answer)
        self.assertIn("lundi au vendredi", answer)
    
    def test_library_location(self):
        """Test de la récupération de localisation."""
        question = "Où se trouve la bibliothèque de Droit?"
        answer, docs = self.rag_test.ask(question)
        self.assertIn("bâtiment D", answer)
    
    def test_borrowing_books(self):
        """Test de la récupération d'information sur l'emprunt."""
        question = "Comment emprunter des livres?"
        answer, docs = self.rag_test.ask(question)
        self.assertIn("carte d'étudiant", answer)
    
    def test_digital_library(self):
        """Test des informations sur la bibliothèque numérique."""
        question = "Est-ce que la bibliothèque numérique est accessible en permanence?"
        answer, docs = self.rag_test.ask(question)
        self.assertIn("24h/24", answer)
    
    def test_unknown_information(self):
        """Test de la gestion des informations inconnues."""
        question = "Puis-je manger à la bibliothèque?"
        answer, docs = self.rag_test.ask(question)
        self.assertIn("désolé", answer.lower())
        self.assertIn("contacter", answer.lower())

def run_test():
    """Exécute les tests manuellement avec affichage détaillé."""
    rag_test = SimpleRagTest(db_dir="vectordb_test")
    print("Test RAG initialisé. Exécution des tests automatiques...")
    
    test_questions = [
        "Quels sont les horaires de la bibliothèque des Sciences?",
        "Où se trouve la bibliothèque de Droit?",
        "Comment emprunter des livres?",
        "Est-ce que la bibliothèque numérique est accessible en permanence?",
        "Puis-je manger à la bibliothèque?"
    ]
    
    for question in test_questions:
        print("\n" + "-"*50)
        print(f"Question: {question}")
        
        answer, docs = rag_test.ask(question)
        print(f"\nRéponse: {answer}")
        
    print("\nTests terminés.")

if __name__ == "__main__":
    # Exécuter soit les tests unitaires, soit les tests manuels
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--unittest':
        unittest.main(argv=['first-arg-is-ignored'])
    else:
        run_test()