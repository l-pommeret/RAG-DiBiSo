import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin, urlparse
import time
import random

class BibliothequesScraper:
    def __init__(self, base_url="https://www.bibliotheques.universite-paris-saclay.fr/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.data = []
        self.output_dir = "data"
        self.visited_urls = set()  # Pour éviter de visiter les mêmes URLs
        self.all_pages = []  # Pour stocker toutes les pages
        
        # Créer le répertoire de sortie s'il n'existe pas
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
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
    
    def scrape_library_list(self):
        """Récupère la liste des bibliothèques."""
        soup = self.get_soup(self.base_url)
        
        # Afficher le titre de la page pour débug
        print(f"Page title: {soup.title.text if soup.title else 'No title'}")
        
        # Approche plus générique: rechercher tous les liens qui pourraient être des bibliothèques
        library_links = []
        
        # Rechercher tous les liens sur la page
        all_links = soup.find_all('a')
        print(f"Found {len(all_links)} links on the page")
        
        # Mots-clés qui pourraient indiquer un lien vers une bibliothèque
        keywords = [
            'bibliotheque', 'bibliothèque', 'bu ', 'learning center', 
            'documentation', 'médiathèque', 'mediatheque'
        ]
        
        # Parcourir tous les liens et identifier ceux qui semblent pointer vers des bibliothèques
        for link in all_links:
            href = link.get('href', '')
            text = link.text.strip().lower()
            
            # Vérifier si le lien ou le texte contient un des mots-clés
            is_library_link = any(keyword in href.lower() for keyword in keywords) or \
                             any(keyword in text for keyword in keywords)
            
            if is_library_link and href:
                full_url = urljoin(self.base_url, href)
                print(f"Found library link: {text} -> {full_url}")
                library_links.append({
                    'url': full_url,
                    'name': link.text.strip() or f"Bibliothèque {len(library_links) + 1}"
                })
        
        # Ajouter des URLs codées en dur pour enrichir le dataset
        print("Adding additional hardcoded library URLs.")
        
        # Liste d'URLs connues des bibliothèques de Paris-Saclay et autres pages pertinentes
        hardcoded_libraries = [
            {
                'name': 'BU des Sciences d\'Orsay',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/bibliotheque/bu-sciences-orsay'
            },
            {
                'name': 'Learning Center Paris-Saclay',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/bibliotheque/learning-center-paris-saclay'
            },
            {
                'name': 'BU de Pharmacie',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/bibliotheque/bu-pharmacie'
            },
            {
                'name': 'BU Droit-Économie-Gestion',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/bibliotheque/bu-droit-economie-gestion'
            },
            {
                'name': 'Services aux chercheurs',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/services-aux-chercheurs' 
            },
            {
                'name': 'Formations documentaires',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/formation-documentaire'
            },
            {
                'name': 'Explorer les ressources',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/explorer-les-ressources'
            },
            {
                'name': 'Chercher un document',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/explorer-les-ressources/chercher-un-document'
            },
            {
                'name': 'Ressources 24h sur 24',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/explorer-les-ressources/ressources-24h24'
            },
            {
                'name': 'Thèses et mémoires',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/explorer-les-ressources/rechercher-un-memoire-une-these'
            },
            {
                'name': 'Annales d\'examens',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/explorer-les-ressources/acceder-aux-annales-dexamens'
            },
            {
                'name': 'Science ouverte',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/services-aux-chercheurs/science-ouverte'
            },
            {
                'name': 'HAL Paris-Saclay',
                'url': 'https://www.bibliotheques.universite-paris-saclay.fr/services-aux-chercheurs/hal-universite-paris-saclay'
            }
        ]
        
        library_links.extend(hardcoded_libraries)
        
        return library_links
    
    def scrape_library_details(self, library):
        """Scrape les détails d'une bibliothèque spécifique."""
        print(f"Scraping {library['name']} ({library['url']})")
        soup = self.get_soup(library['url'])
        
        library_data = {
            'name': library['name'],
            'url': library['url'],
            'hours': self.extract_hours(soup),
            'address': self.extract_address(soup),
            'contact': self.extract_contact(soup),
            'services': self.extract_services(soup),
            'description': self.extract_description(soup)
        }
        
        return library_data
    
    def extract_hours(self, soup):
        """Extrait les heures d'ouverture."""
        # Approche plus générique: chercher des éléments ou textes liés aux horaires
        keywords = ['horaires', 'heures d\'ouverture', 'ouverture', 'fermé']
        
        # Recherche par classe ou ID
        hours_section = None
        for div in soup.find_all('div'):
            class_str = ' '.join(div.get('class', [])).lower()
            id_str = (div.get('id', '') or '').lower()
            
            if any(kw in class_str or kw in id_str for kw in keywords):
                hours_section = div
                print(f"Found hours section via class/id: {class_str or id_str}")
                break
        
        # Si non trouvé, recherche par texte
        if not hours_section:
            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span']):
                if any(kw in element.text.lower() for kw in keywords):
                    # Prendre le paragraphe parent ou le prochain paragraphe
                    parent = element.parent
                    if parent.name == 'p':
                        hours_section = parent
                    else:
                        # Chercher le prochain paragraphe ou div
                        hours_section = element.find_next(['p', 'div'])
                    
                    print(f"Found hours section via text: {element.text.strip()[:50]}...")
                    break
        
        # Si toujours non trouvé, chercher dans un tableau
        if not hours_section:
            for table in soup.find_all('table'):
                table_text = table.get_text().lower()
                if any(kw in table_text for kw in keywords):
                    hours_section = table
                    print(f"Found hours section via table content")
                    break
        
        # Extraire le texte si une section a été trouvée
        if hours_section:
            hours_text = hours_section.get_text().strip()
            # Limiter à quelques lignes pour éviter de prendre trop de contenu
            lines = hours_text.split('\n')
            relevant_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) < 100]
            return '\n'.join(relevant_lines[:10])  # Limiter à 10 lignes maximum
            
        return "Horaires non disponibles"
    
    def extract_address(self, soup):
        """Extrait l'adresse."""
        address_section = soup.find('div', class_='field-adresse') or soup.find('div', class_='address')
        
        if address_section:
            return address_section.get_text().strip()
        return "Adresse non disponible"
    
    def extract_contact(self, soup):
        """Extrait les informations de contact."""
        contact_section = soup.find('div', class_='field-contact') or soup.find('div', class_='contact')
        
        contacts = {}
        if contact_section:
            emails = soup.select('a[href^="mailto:"]')
            if emails:
                contacts['email'] = [email.get('href').replace('mailto:', '') for email in emails]
            
            phones = soup.select('a[href^="tel:"]')
            if phones:
                contacts['phone'] = [phone.get('href').replace('tel:', '') for phone in phones]
            
            return contacts
        return "Contact non disponible"
    
    def extract_services(self, soup):
        """Extrait les services proposés."""
        services_section = soup.find('div', class_='field-services') or soup.find(string=lambda text: 'services' in text.lower() if text else False)
        
        if services_section:
            if isinstance(services_section, str):
                parent = services_section.parent
                # Recherche des listes à proximité
                services_list = parent.find_next('ul') or parent.parent.find_next('ul')
                if services_list:
                    return [li.get_text().strip() for li in services_list.find_all('li')]
            else:
                services_list = services_section.find('ul')
                if services_list:
                    return [li.get_text().strip() for li in services_list.find_all('li')]
        return []
    
    def extract_description(self, soup):
        """Extrait la description générale et le maximum de contenu textuel pertinent de façon structurée."""
        page_data = {
            "title": soup.title.text.strip() if soup.title else "No title",
            "main_content": "",
            "sections": [],
            "paragraphs": [],
            "tables": [],
            "lists": [],
            "links": [],
            "metadata": {},
            "raw_text": "",
            "article_content": ""
        }
        
        # Extraire les métadonnées
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            if tag.get('name') and tag.get('content'):
                page_data["metadata"][tag.get('name')] = tag.get('content')
        
        # Trouver le contenu principal
        main_content = soup.find('main') or soup.find('div', class_='main-content') or soup.find('div', class_='content') or soup.find('article')
        if not main_content:
            # Si pas de container principal, prendre le body entier
            main_content = soup.body
        
        # Trouver l'article ou le contenu principal plus précisément
        article = soup.find('article') or soup.find('div', class_='node__content') or soup.find('div', class_=['field--type-text-with-summary', 'field--type-text-long'])
        
        if article:
            # Récupérer le contenu de l'article
            page_data["article_content"] = article.get_text(" ", strip=True)
        
        if main_content:
            page_data["main_content"] = main_content.get_text(" ", strip=True)
            
            # Extraire les sections avec titres
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                heading_text = heading.get_text().strip()
                if heading_text:
                    # Récupérer tout le contenu jusqu'au prochain titre
                    content = []
                    current = heading.next_sibling
                    while current and not (isinstance(current, type(heading)) and current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                        if current.name == 'p' or current.name == 'div':
                            text = current.get_text().strip()
                            if text:
                                content.append(text)
                        current = current.next_sibling
                    
                    page_data["sections"].append({
                        "heading": heading_text,
                        "level": int(heading.name[1]),
                        "content": "\n".join(content)
                    })
            
            # Extraire tous les paragraphes
            paragraphs = main_content.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if text:
                    page_data["paragraphs"].append(text)
            
            # Extraire les tableaux
            tables = main_content.find_all('table')
            for table in tables:
                rows = []
                for tr in table.find_all('tr'):
                    row = []
                    for cell in tr.find_all(['th', 'td']):
                        row.append(cell.get_text().strip())
                    if row:
                        rows.append(row)
                if rows:
                    page_data["tables"].append(rows)
            
            # Extraire les listes
            lists = main_content.find_all(['ul', 'ol'])
            for list_elem in lists:
                items = []
                for li in list_elem.find_all('li'):
                    text = li.get_text().strip()
                    if text:
                        items.append(text)
                if items:
                    page_data["lists"].append({
                        "type": "ordered" if list_elem.name == "ol" else "unordered",
                        "items": items
                    })
            
            # Extraire les liens importants
            links = main_content.find_all('a', href=True)
            for link in links:
                text = link.get_text().strip()
                href = link['href']
                if text and href and not href.startswith('#'):
                    page_data["links"].append({
                        "text": text,
                        "url": href
                    })
        
        # Construire une représentation texte bien formatée
        content_parts = []
        
        # Ajouter le titre
        content_parts.append(f"# {page_data['title']}")
        content_parts.append("")
        
        # Ajouter le contenu de l'article si disponible
        if page_data["article_content"]:
            content_parts.append("## Contenu de l'article")
            content_parts.append(page_data["article_content"])
            content_parts.append("")
        # Ou ajouter le contenu principal brut si disponible et pas d'article
        elif page_data["main_content"]:
            content_parts.append("## Contenu principal (texte brut)")
            content_parts.append(page_data["main_content"])
            content_parts.append("")
        
        # Ajouter les sections
        if page_data["sections"]:
            content_parts.append("## Sections structurées")
            for section in page_data["sections"]:
                # Utiliser le bon niveau de titre markdown
                prefix = "#" * min(section["level"] + 2, 6)  # Pour éviter de dépasser h6
                content_parts.append(f"{prefix} {section['heading']}")
                if section["content"]:
                    content_parts.append(section["content"])
                content_parts.append("")
        
        # Ajouter les paragraphes
        if page_data["paragraphs"]:
            content_parts.append("## Paragraphes")
            for p in page_data["paragraphs"]:
                content_parts.append(p)
                content_parts.append("")
        
        # Ajouter les listes
        if page_data["lists"]:
            content_parts.append("## Listes")
            for lst in page_data["lists"]:
                for item in lst["items"]:
                    if lst["type"] == "ordered":
                        content_parts.append(f"1. {item}")
                    else:
                        content_parts.append(f"* {item}")
            content_parts.append("")
        
        # Ajouter les tableaux
        if page_data["tables"]:
            content_parts.append("## Tableaux")
            for table in page_data["tables"]:
                # Créer un tableau markdown simple
                for row in table:
                    content_parts.append(" | ".join(row))
                content_parts.append("")
        
        # Ajouter les liens importants
        if page_data["links"]:
            content_parts.append("## Liens importants")
            for link in page_data["links"][:10]:  # Limiter à 10 liens
                content_parts.append(f"* [{link['text']}]({link['url']})")
            content_parts.append("")
        
        # Construire le contenu textuel final
        formatted_content = "\n".join(content_parts)
        
        # Si le contenu formaté est vide, utiliser le texte brut
        if not formatted_content.strip():
            # Nettoyer le texte brut
            raw_text = soup.get_text(" ", strip=True)
            # Supprimer les espaces multiples
            raw_text = " ".join(raw_text.split())
            # Limiter la longueur
            return raw_text[:20000]  # Limiter à 20000 caractères
        
        return formatted_content
    
    def is_valid_url(self, url):
        """Vérifie si l'URL appartient au même domaine et n'est pas déjà visitée."""
        # Vérifier si l'URL est dans le même domaine
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)
        
        # Exclure certains types de fichiers
        excluded_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar']
        if any(url.lower().endswith(ext) for ext in excluded_extensions):
            return False
            
        # Exclure les liens mailto: et tel:
        if url.lower().startswith('mailto:') or url.lower().startswith('tel:'):
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
    
    def crawl_recursive(self, start_url=None, max_pages=10, delay_min=0.1, delay_max=0.2):
        """Crawl récursivement le site web à partir d'une URL de départ."""
        if start_url is None:
            start_url = self.base_url
            
        # Limiter le nombre de pages pour éviter un crawl trop long
        if len(self.all_pages) >= max_pages:
            print(f"Reached maximum page limit ({max_pages})")
            return
            
        if start_url in self.visited_urls:
            return
            
        # Marquer l'URL comme visitée
        self.visited_urls.add(start_url)
        
        # Récupérer et parser la page
        soup = self.get_soup(start_url)
        
        if soup:
            # Extraire le contenu
            page_data = {
                'url': start_url,
                'title': soup.title.text if soup.title else 'No title',
                'content': self.extract_description(soup)
            }
            
            print(f"Crawled: {page_data['title']} - {start_url}")
            self.all_pages.append(page_data)
            
            # Sauvegarder la page immédiatement
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
            
            # Trouver tous les liens sur la page
            links = self.extract_links(soup, start_url)
            print(f"Found {len(links)} links on {start_url}")
            
            # Crawl récursivement chaque lien (seulement si on n'a pas atteint la limite)
            if len(self.all_pages) < max_pages:
                for link in links:
                    # Arrêter si on a atteint la limite
                    if len(self.all_pages) >= max_pages:
                        break
                        
                    # Pause aléatoire pour éviter de surcharger le serveur
                    sleep_time = random.uniform(delay_min, delay_max)
                    time.sleep(sleep_time)
                    self.crawl_recursive(link, max_pages, delay_min, delay_max)
    
    def scrape_all(self):
        """Scrape toutes les bibliothèques et crawl récursivement le site."""
        # D'abord, scraper les bibliothèques comme avant
        libraries = self.scrape_library_list()
        
        for library in libraries:
            library_data = self.scrape_library_details(library)
            self.data.append(library_data)
            
            # Sauvegarde individuelle
            safe_name = library_data['name'].replace(' ', '_').replace('/', '_').replace('\\', '_').lower()
            filename = f"{self.output_dir}/{safe_name}.json"
            print(f"Saving to {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(library_data, f, ensure_ascii=False, indent=4)
            
            # Marquer cette URL comme visitée pour éviter de la recrawler
            self.visited_urls.add(library_data['url'])
        
        # Sauvegarde globale des bibliothèques
        with open(f"{self.output_dir}/all_libraries.json", 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        
        # Ensuite, crawler récursivement le site sans limite de pages
        print("\nStarting recursive crawl of website pages...")
        self.crawl_recursive(max_pages=float('inf'), delay_min=0.1, delay_max=0.2)
        
        # Sauvegarde globale de toutes les pages
        with open(f"{self.output_dir}/all_pages.json", 'w', encoding='utf-8') as f:
            json.dump(self.all_pages, f, ensure_ascii=False, indent=4)
        
        print(f"Scraped {len(self.data)} libraries and {len(self.all_pages)} total pages.")
        return self.data, self.all_pages

def test_page_extraction(url):
    """Test d'extraction sur une seule page."""
    scraper = BibliothequesScraper()
    
    print(f"Analysing single page: {url}")
    soup = scraper.get_soup(url)
    
    content = scraper.extract_description(soup)
    
    # Sauvegarder le contenu extrait dans un fichier pour inspection
    output_file = "single_page_test.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Le contenu extrait a été sauvegardé dans {output_file}")
    print(f"Longueur du contenu extrait: {len(content)} caractères")
    
    # Afficher un échantillon du contenu
    print("\nDébut du contenu extrait:")
    print("----------")
    print(content[:1000] + "..." if len(content) > 1000 else content)
    print("----------")
    
    return content

if __name__ == "__main__":
    # Pour exécuter seulement un test d'extraction sur une seule page, décommentez les lignes ci-dessous:
    # test_url = "https://www.bibliotheques.universite-paris-saclay.fr/salle-de-travail-en-groupe"
    # test_page_extraction(test_url)
    
    # Exécution du scraping complet avec les améliorations d'extraction
    scraper = BibliothequesScraper()
    libraries_data, all_pages = scraper.scrape_all()
    print(f"Scraped {len(libraries_data)} libraries and {len(all_pages)} total pages. Data saved to 'data' directory.")