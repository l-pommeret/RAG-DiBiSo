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
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    
    def scrape_library_list(self):
        """Récupère la liste des bibliothèques."""
        soup = self.get_soup(self.base_url)
        
        # Cible les liens des bibliothèques (à adapter selon la structure réelle du site)
        libraries_section = soup.find('nav', class_='menu-bibliotheques')
        
        if not libraries_section:
            # Alternative si le sélecteur ci-dessus ne fonctionne pas
            libraries_section = soup.find('ul', class_='menu')
        
        library_links = []
        
        if libraries_section:
            links = libraries_section.find_all('a')
            for link in links:
                href = link.get('href')
                if href and '/bibliotheque/' in href:
                    library_links.append({
                        'url': urljoin(self.base_url, href),
                        'name': link.text.strip()
                    })
        
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
        hours_section = soup.find('div', class_='field-horaires') or soup.find(string=lambda text: 'horaires' in text.lower() if text else False)
        
        if hours_section:
            if isinstance(hours_section, str):
                parent = hours_section.parent
                hours_text = parent.get_text()
            else:
                hours_text = hours_section.get_text()
            return hours_text.strip()
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