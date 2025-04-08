#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test du module de gestion des horaires des bibliothèques.
Ce script permet de tester le module HorairesModule de façon isolée.
"""

import os
import sys
import argparse
from modules.horaires_module import HorairesModule

def main():
    """
    Fonction principale exécutant les tests du module des horaires.
    """
    parser = argparse.ArgumentParser(description='Test du module de gestion des horaires')
    parser.add_argument('--cache-dir', default='data/cache', help='Répertoire pour le cache des données')
    parser.add_argument('--reset-cache', action='store_true', help='Réinitialiser le cache des données')
    
    args = parser.parse_args()
    
    cache_dir = args.cache_dir
    
    # Créer le répertoire de cache s'il n'existe pas
    if not os.path.exists(cache_dir):
        print(f"Création du répertoire de cache: {cache_dir}")
        os.makedirs(cache_dir)
    
    # Réinitialiser le cache si demandé
    if args.reset_cache:
        print("Réinitialisation du cache...")
        for file in os.listdir(cache_dir):
            if file.startswith('horaires_'):
                os.remove(os.path.join(cache_dir, file))
    
    # Initialiser le module des horaires
    print(f"Initialisation du module des horaires avec le cache: {cache_dir}")
    horaires_module = HorairesModule(cache_dir=cache_dir)
    
    # Tests prédéfinis
    test_queries = [
        "Quels sont les horaires de la bibliothèque d'Orsay?",
        "La bibliothèque de Sceaux est ouverte à quelle heure?",
        "Quand ferme la BU de droit?",
        "Est-ce que la bibliothèque de médecine est ouverte le samedi?",
        "Horaires d'ouverture du Lumen?",
        "Quels sont les horaires des bibliothèques?",
        "La BU des Sciences est ouverte aujourd'hui?"
    ]
    
    print("\n=== Démarrage des tests prédéfinis ===")
    for i, query in enumerate(test_queries):
        print(f"\nTest {i+1}: {query}")
        response = horaires_module.handle_query(query)
        print(f"Réponse:\n{response}")
        print("-" * 50)
    
    # Mode interactif
    print("\n=== Mode interactif ===")
    print("Posez des questions sur les horaires des bibliothèques (tapez 'quit' pour quitter)")
    
    while True:
        query = input("\nVotre question: ")
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        response = horaires_module.handle_query(query)
        print(f"Réponse:\n{response}")

if __name__ == "__main__":
    main()