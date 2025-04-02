"""
Script pour tester automatiquement le pipeline RAG.
"""

from test_simple import SimpleRagTest

def run_test():
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
    run_test()