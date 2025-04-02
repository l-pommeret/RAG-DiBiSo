import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin

class BibliothequesScraper:
    def __init__(self, base_url="https://www.bibliotheques.universite-paris-saclay.fr/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.data = []
        self.output_dir = "data"
        
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
        
        # Si aucune bibliothèque n'est trouvée, utiliser des URLs codées en dur en dernier recours
        if not library_links:
            print("No library links found automatically. Using hardcoded URLs.")
            
            # Liste d'URLs connues des bibliothèques de Paris-Saclay (à compléter si nécessaire)
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
        """Extrait la description générale."""
        desc_section = soup.find('div', class_='field-description') or soup.find('div', class_='content')
        
        if desc_section:
            paragraphs = desc_section.find_all('p')
            if paragraphs:
                return "\n".join([p.get_text().strip() for p in paragraphs])
            return desc_section.get_text().strip()
        return "Description non disponible"
    
    def scrape_all(self):
        """Scrape toutes les bibliothèques."""
        libraries = self.scrape_library_list()
        
        for library in libraries:
            library_data = self.scrape_library_details(library)
            self.data.append(library_data)
            
            # Sauvegarde individuelle (pour chaque bibliothèque)
            filename = f"{self.output_dir}/{library_data['name'].replace(' ', '_').lower()}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(library_data, f, ensure_ascii=False, indent=4)
        
        # Sauvegarde globale (toutes les bibliothèques)
        with open(f"{self.output_dir}/all_libraries.json", 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        
        return self.data

if __name__ == "__main__":
    scraper = BibliothequesScraper()
    libraries_data = scraper.scrape_all()
    print(f"Scraped {len(libraries_data)} libraries. Data saved to 'data' directory.")