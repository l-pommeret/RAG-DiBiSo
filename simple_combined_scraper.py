import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin, urlparse
import time
import random

class SimpleBibliothequesScraper:
    """
    Version simplifiée du scraper qui combine les fonctionnalités de base
    des deux scrapers existants sans les dépendances problématiques.
    """
    def __init__(self, base_url="https://www.bibliotheques.universite-paris-saclay.fr/", 
                 output_dir="data", txt_output_dir="txt_data"):
        self.base_url = base_url
        self.session = requests.Session()
        self.data = []
        self.output_dir = output_dir
        self.txt_output_dir = txt_output_dir
        self.visited_urls = set()  # Pour éviter de visiter les mêmes URLs
        self.all_pages = []  # Pour stocker toutes les pages
        
        # Créer les répertoires de sortie s'ils n'existent pas
        for directory in [self.output_dir, self.txt_output_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def get_soup(self, url):
        """Récupère et parse une page HTML."""
        print(f"Fetching: {url}")
        
        # Ajouter des en-têtes pour simuler un navigateur
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Vérifier que nous avons bien du HTML
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type.lower():
                print(f"Warning: URL did not return HTML content. Content-Type: {content_type}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            # En cas d'échec, retourner une soup vide plutôt que de planter
            return BeautifulSoup("", 'html.parser')
    
    def get_main_content(self, soup):
        """Retourne uniquement le contenu principal de la page."""
        # Essayer plusieurs sélecteurs pour trouver le contenu principal
        selectors = [
            {"class": "main-content"},
            {"class": "content"},
            {"class": "node__content"},
            {"id": "content"},
            {"class": "article-content"},
            {"role": "main"}
        ]
        
        main_content = None
        for selector in selectors:
            main_content = soup.find("div", attrs=selector) or soup.find("main", attrs=selector)
            if main_content:
                break
                
        # Si aucun sélecteur ne fonctionne, essayer de trouver l'article
        if not main_content:
            main_content = soup.find("article")
            
        # Dernier recours: prendre le body
        if not main_content:
            main_content = soup.body
            
        if not main_content:
            return "", "Contenu principal non trouvé"
        
        # Supprimer les éléments de style et de script
        for data in main_content(["style", "script"]):
            data.decompose()
            
        # Supprimer les méta-données et éléments non pertinents
        for div in main_content.find_all("div", {'class': lambda c: c and ('meta' in c or 'menu' in c or 'nav' in c or 'footer' in c or 'header' in c)}): 
            div.decompose()
            
        # Extraire le texte principal
        text = list(main_content.stripped_strings)
        
        # Essayer de trouver un titre
        title = "Sans titre"
        if text:
            title = text[0]
        else:
            # Chercher un titre dans la page
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
            elif soup.title:
                title = soup.title.get_text(strip=True)
                
        text = ' '.join(text)
        
        return text, title
    
    def extract_description(self, soup):
        """Extrait la description générale et le contenu textuel structuré."""
        # Trouver le contenu principal
        main_content = soup.find('main') or soup.find('div', class_='main-content') or soup.find('div', class_='content')
        
        if not main_content:
            # Si pas de container principal, prendre le body entier
            main_content = soup.body
        
        if main_content:
            # Extraire le texte
            return main_content.get_text(" ", strip=True)
        
        # Fallback sur le texte brut de la page
        return soup.get_text(" ", strip=True)
    
    def is_valid_url(self, url):
        """Vérifie si l'URL appartient au même domaine et n'est pas déjà visitée."""
        # Vérifier si l'URL est dans le même domaine
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)
        
        # Exclure certains types de fichiers
        excluded_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar']
        if any(url.lower().endswith(ext) for ext in excluded_extensions):
            return False
        
        # Vérifier si l'URL est dans le même domaine et n'a pas déjà été visitée
        same_domain = parsed_url.netloc == parsed_base.netloc or parsed_url.netloc == ""
        not_visited = url not in self.visited_urls
        
        return same_domain and not_visited
    
    def extract_links(self, soup, current_url):
        """Extrait tous les liens d'une page."""
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            full_url = urljoin(current_url, href)
            
            if self.is_valid_url(full_url):
                links.append(full_url)
        
        return links
    
    def scrape_from_subdirectories_file(self, subdirectories_file):
        """Scrape des pages à partir d'un fichier contenant des sous-répertoires."""
        base = self.base_url
        outputs = []
        
        with open(subdirectories_file, "r") as f:
            subdirectories = f.readlines()
        
        print(f"Found {len(subdirectories)} subdirectories to scrape")
        
        for i, subdir in enumerate(subdirectories):
            subdir = subdir.strip()
            if not subdir:
                continue
                
            # Éviter les doubles slashes
            url = f"{base}{'' if base.endswith('/') else '/'}{subdir}"
            data = {
                "meta": {
                    "title": "",
                    "url": url,
                    "name": f"{i}.txt"
                },
            }
            
            try:
                # Vérifier si l'URL a déjà été visitée
                if url in self.visited_urls:
                    print(f"Skipping {url} (already visited)")
                    continue
                    
                # Marquer l'URL comme visitée
                self.visited_urls.add(url)
                
                # Récupérer le contenu
                soup = self.get_soup(url)
                if not soup:
                    print(f"Failed to get content from {url}")
                    continue
                    
                # Extraire le contenu principal
                main_text, title = self.get_main_content(soup)
                if not main_text:
                    print(f"No main content found for {url}")
                    continue
                    
                # Mettre à jour les métadonnées
                data["meta"]["title"] = title
                
                # Sauvegarder le contenu dans un fichier texte
                txt_path = f"{self.txt_output_dir}/{i}.txt"
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(main_text)
                    
                # Créer le JSON pour cette page
                page_data = {
                    'id': f"{i}",
                    'url': url,
                    'title': title,
                    'body': main_text
                }
                
                outputs.append(page_data)
                
                # Sauvegarder le JSON pour cette page
                json_path = f"{self.output_dir}/{i}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, ensure_ascii=False, indent=4)
                    
                print(f"Saved content for {title} to {txt_path} and {json_path}")
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                
        # Sauvegarder le fichier JSON global
        with open(f"{self.output_dir}/pages.json", 'w', encoding='utf-8') as f:
            json.dump(outputs, f, ensure_ascii=False, indent=4)
            
        # Générer le fichier bash pour le chargement (comme dans l'original)
        bash_output = ""
        for i in range(len(outputs)):
            bash_output += f"curl --request POST --url http://127.0.0.1:8000/file-upload --header 'accept: application/json' --header 'content-type: multipart/form-data' --form files=\"@{i}.txt\" --form meta=\"{{\\\"title\\\": \\\"{outputs[i]['title']}\\\",\\\"url\\\": \\\"{outputs[i]['url']}\\\",\\\"name\\\":\\\"{i}.txt\\\"}}\"\n"
            
        with open(f"{self.txt_output_dir}/chargement_fichiers.bash", 'w') as f:
            f.write(bash_output)
            
        return outputs
    
    def crawl_recursive(self, start_url=None, max_pages=10, delay_min=0.1, delay_max=0.2):
        """Crawl récursivement le site web à partir d'une URL de départ."""
        if start_url is None:
            start_url = self.base_url
            
        # Limiter le nombre de pages pour éviter un crawl trop long
        if max_pages > 0 and len(self.all_pages) >= max_pages:
            print(f"Reached maximum page limit ({max_pages})")
            return
            
        if start_url in self.visited_urls:
            return
            
        # Marquer l'URL comme visitée
        self.visited_urls.add(start_url)
        
        # Récupérer et parser la page
        soup = self.get_soup(start_url)
        
        if soup:
            # Extraire le contenu principal
            main_content, title = self.get_main_content(soup)
            
            # Extraire le contenu enrichi
            rich_content = self.extract_description(soup)
            
            # Créer l'objet page
            page_data = {
                'url': start_url,
                'title': title if title != "Sans titre" else (soup.title.text if soup.title else 'No title'),
                'content': rich_content,
                'main_content': main_content
            }
            
            print(f"Crawled: {page_data['title']} - {start_url}")
            self.all_pages.append(page_data)
            
            # Sauvegarder la page au format JSON
            url_parts = urlparse(start_url)
            path = url_parts.path.strip('/')
            if not path:
                path = "index"
            safe_filename = path.replace('/', '_').replace('\\', '_').lower()
            if not safe_filename:
                safe_filename = "page_" + str(len(self.all_pages))
                
            filename = f"{self.output_dir}/{safe_filename}.json"
            print(f"Saving to {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, ensure_ascii=False, indent=4)
            
            # Sauvegarder également le contenu principal en tant que fichier texte
            if main_content:
                txt_filename = f"{self.txt_output_dir}/{len(self.all_pages)-1}.txt"
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write(main_content)
                print(f"Saved text content to {txt_filename}")
            
            # Trouver tous les liens sur la page
            links = self.extract_links(soup, start_url)
            print(f"Found {len(links)} links on {start_url}")
            
            # Crawl récursivement chaque lien (seulement si on n'a pas atteint la limite)
            if max_pages == 0 or len(self.all_pages) < max_pages:
                for link in links:
                    # Arrêter si on a atteint la limite
                    if max_pages > 0 and len(self.all_pages) >= max_pages:
                        break
                        
                    # Pause aléatoire pour éviter de surcharger le serveur
                    sleep_time = random.uniform(delay_min, delay_max)
                    time.sleep(sleep_time)
                    self.crawl_recursive(link, max_pages, delay_min, delay_max)
    
    def scrape_all(self, max_pages=0, subdirectories_file=None):
        """Scrape toutes les pages du site web."""
        print(f"Starting comprehensive scraping of {self.base_url}...")
        
        # Méthode 1: Si un fichier de sous-répertoires est fourni
        pages_data = []
        if subdirectories_file and os.path.exists(subdirectories_file):
            print(f"Scraping from subdirectories file: {subdirectories_file}")
            pages_data = self.scrape_from_subdirectories_file(subdirectories_file)
        
        # Méthode 2: Crawler récursivement le site (limité au nombre de pages spécifié si > 0)
        if max_pages > 0:
            print(f"\nStarting recursive crawl of website pages (max {max_pages} pages)...")
        else:
            print("\nStarting recursive crawl of website pages (no limit)...")
        self.crawl_recursive(max_pages=max_pages, delay_min=0.1, delay_max=0.2)
        
        # Sauvegarde globale de toutes les pages
        with open(f"{self.output_dir}/all_pages.json", 'w', encoding='utf-8') as f:
            json.dump(self.all_pages, f, ensure_ascii=False, indent=4)
        
        print(f"Scraping completed: {len(self.all_pages)} total pages.")
        return self.all_pages

def test_page_extraction(url, output_dir="data"):
    """Test d'extraction sur une seule page."""
    scraper = SimpleBibliothequesScraper(output_dir=output_dir)
    
    print(f"Analysing single page: {url}")
    soup = scraper.get_soup(url)
    
    # Tester les deux méthodes d'extraction
    content1 = scraper.extract_description(soup)
    content2, title = scraper.get_main_content(soup)
    
    # Sauvegarder les contenus extraits dans des fichiers pour inspection
    with open(f"{output_dir}/single_page_test_rich.txt", 'w', encoding='utf-8') as f:
        f.write(content1)
        
    with open(f"{output_dir}/single_page_test_simple.txt", 'w', encoding='utf-8') as f:
        f.write(content2)
    
    print(f"Le contenu extrait a été sauvegardé dans {output_dir}/single_page_test_*.txt")
    print(f"Longueur du contenu extrait (méthode riche): {len(content1)} caractères")
    print(f"Longueur du contenu extrait (méthode simple): {len(content2)} caractères")
    
    # Afficher un échantillon du contenu
    print("\nDébut du contenu extrait (méthode riche):")
    print("----------")
    print(content1[:500] + "..." if len(content1) > 500 else content1)
    print("----------")
    
    print("\nDébut du contenu extrait (méthode simple):")
    print("----------")
    print(content2[:500] + "..." if len(content2) > 500 else content2)
    print("----------")
    
    return content1, content2

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Bibliothèques scraper simple')
    parser.add_argument('--test', '-t', help='URL pour tester l\'extraction', type=str)
    parser.add_argument('--subdirs', '-s', help='Fichier de sous-répertoires à scraper', type=str)
    parser.add_argument('--output', '-o', help='Répertoire de sortie', type=str, default='data')
    parser.add_argument('--txt_output', '-to', help='Répertoire de sortie pour les fichiers texte', type=str, default='txt_data')
    parser.add_argument('--max_pages', '-m', help='Nombre maximum de pages à crawler (0 = sans limite)', type=int, default=0)
    
    args = parser.parse_args()
    
    # Créer les répertoires de sortie s'ils n'existent pas
    for directory in [args.output, args.txt_output]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Test d'extraction sur une seule page
    if args.test:
        test_page_extraction(args.test, args.output)
    else:
        # Exécution du scraping complet
        scraper = SimpleBibliothequesScraper(output_dir=args.output, txt_output_dir=args.txt_output)
        all_pages = scraper.scrape_all(max_pages=args.max_pages, subdirectories_file=args.subdirs)
            
        print(f"Scraping completed: {len(all_pages)} total pages.")
        print(f"Data saved to '{args.output}' and '{args.txt_output}' directories.")