import os
import sys
import json
from simple_combined_scraper import SimpleBibliothequesScraper, test_page_extraction

def test_single_page_extraction():
    """Teste l'extraction sur une seule page."""
    test_url = "https://www.bibliotheques.universite-paris-saclay.fr/explorer-les-ressources/chercher-un-document"
    
    print("Test d'extraction d'une seule page...")
    content_rich, content_simple = test_page_extraction(test_url, output_dir="test_data")
    
    print(f"Extraction réussie. Contenu riche: {len(content_rich)} caractères, Contenu simple: {len(content_simple)} caractères")
    return content_rich and content_simple

def test_scrap_from_subdirectories():
    """Teste le scraping à partir du fichier de sous-répertoires."""
    # Créer un fichier de test temporaire avec quelques sous-répertoires
    temp_file = "temp_subdirs.txt"
    subdirs = [
        "explorer-les-ressources/chercher-un-document",
        "emprunter",
        "horaires-et-affluence"
    ]
    
    with open(temp_file, "w") as f:
        f.write("\n".join(subdirs))
    
    try:
        print("\nTest de scraping à partir de sous-répertoires...")
        scraper = SimpleBibliothequesScraper(output_dir="test_data", txt_output_dir="test_txt_data")
        pages = scraper.scrape_from_subdirectories_file(temp_file)
        
        print(f"Scraping réussi. {len(pages)} pages extraites.")
        
        # Vérifier que les fichiers ont été créés
        for i in range(len(pages)):
            json_path = f"test_data/{i}.json"
            txt_path = f"test_txt_data/{i}.txt"
            
            if not (os.path.exists(json_path) and os.path.exists(txt_path)):
                print(f"ERREUR: fichiers manquants pour la page {i}")
                return False
        
        # Vérifier que le fichier global a été créé
        if not os.path.exists("test_data/pages.json"):
            print("ERREUR: fichier pages.json manquant")
            return False
            
        return True
    finally:
        # Nettoyer
        if os.path.exists(temp_file):
            os.remove(temp_file)

def run_all_tests():
    """Exécute tous les tests et retourne le nombre de succès."""
    tests = [
        ("Extraction d'une seule page", test_single_page_extraction),
        ("Scraping à partir de sous-répertoires", test_scrap_from_subdirectories),
    ]
    
    success_count = 0
    
    print("=== TESTS DU SCRAPER SIMPLE ===")
    
    for name, test_func in tests:
        print(f"\n--- Test: {name} ---")
        try:
            result = test_func()
            if result:
                print(f"✓ Test réussi: {name}")
                success_count += 1
            else:
                print(f"✗ Test échoué: {name}")
        except Exception as e:
            print(f"✗ Test échoué avec erreur: {name}")
            print(f"  Erreur: {e}")
    
    print(f"\n=== Résultats: {success_count}/{len(tests)} tests réussis ===")
    
    return success_count == len(tests)

if __name__ == "__main__":
    # Créer les répertoires pour les tests s'ils n'existent pas
    for directory in ["test_data", "test_txt_data", "data", "txt_data"]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    success = run_all_tests()
    sys.exit(0 if success else 1)