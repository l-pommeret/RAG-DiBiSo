import requests
import json
import os
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import logging

class HorairesModule:
    """
    Module pour gérer les questions relatives aux horaires des bibliothèques de l'Université Paris-Saclay.
    Ce module peut récupérer les horaires les plus récents depuis le site web et l'API Affluences.
    """
    
    def __init__(self, cache_dir="cache", cache_expiry_hours=24):
        """
        Initialise le module d'horaires.
        
        Args:
            cache_dir (str): Répertoire pour stocker les données en cache
            cache_expiry_hours (int): Nombre d'heures avant expiration du cache
        """
        self.cache_dir = cache_dir
        self.cache_expiry_hours = cache_expiry_hours
        self.horaires_url = "https://www.bibliotheques.universite-paris-saclay.fr/horaires-et-affluence"
        self.bibliotheques = {
            "orsay": {
                "nom": "BU Sciences d'Orsay",
                "id_affluences": "1",  # ID fictif, à remplacer par le vrai ID
                "url": "https://www.universite-paris-saclay.fr/vie-de-campus/bibliotheques/bibliotheque-universitaire-orsay"
            },
            "sceaux": {
                "nom": "BU Droit-Économie-Gestion (Sceaux)",
                "id_affluences": "2",  # ID fictif, à remplacer par le vrai ID
                "url": "https://www.universite-paris-saclay.fr/vie-de-campus/bibliotheques/bibliotheque-universitaire-sceaux"
            },
            "kremlin-bicetre": {
                "nom": "BU Kremlin-Bicêtre",
                "id_affluences": "3",  # ID fictif, à remplacer par le vrai ID
                "url": "https://www.universite-paris-saclay.fr/vie-de-campus/bibliotheques/bibliotheque-universitaire-kremlin-bicetre"
            },
            "lumen": {
                "nom": "Lumen Learning Center Paris-Saclay",
                "id_affluences": "4",  # ID fictif, à remplacer par le vrai ID
                "url": "https://www.universite-paris-saclay.fr/lumen-learning-center"
            }
        }
        
        # Création du répertoire de cache s'il n'existe pas
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("HorairesModule")
    
    def _get_cache_path(self, library_id):
        """Génère le chemin du fichier de cache pour une bibliothèque donnée."""
        return os.path.join(self.cache_dir, f"horaires_{library_id}.json")
    
    def _is_cache_valid(self, cache_path):
        """Vérifie si le cache est valide (non expiré)."""
        if not os.path.exists(cache_path):
            return False
        
        try:
            # Vérifier la date de modification du fichier
            file_modification_time = os.path.getmtime(cache_path)
            modification_datetime = datetime.fromtimestamp(file_modification_time)
            expiry_time = modification_datetime + timedelta(hours=self.cache_expiry_hours)
            
            return datetime.now() < expiry_time
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du cache: {e}")
            return False
    
    def _save_to_cache(self, library_id, data):
        """Sauvegarde les données dans le cache."""
        cache_path = self._get_cache_path(library_id)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Données mises en cache pour {library_id}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du cache: {e}")
            return False
    
    def _load_from_cache(self, library_id):
        """Charge les données depuis le cache."""
        cache_path = self._get_cache_path(library_id)
        try:
            if self._is_cache_valid(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.logger.info(f"Données chargées depuis le cache pour {library_id}")
                return data
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du cache: {e}")
            return None
    
    def _fetch_from_web(self, library_id):
        """
        Récupère les horaires depuis le site web de la bibliothèque spécifiée.
        Cette méthode devrait être personnalisée pour chaque bibliothèque si nécessaire.
        """
        try:
            library = self.bibliotheques.get(library_id)
            if not library:
                return None
            
            response = requests.get(library["url"], timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Cette partie doit être adaptée en fonction de la structure HTML de chaque site
            horaires_section = soup.find("div", class_="horaires") or soup.find("section", id="horaires")
            
            if horaires_section:
                horaires_text = horaires_section.get_text(strip=True)
                # Nettoyer et formater le texte des horaires
                return self._format_horaires(horaires_text, library_id)
            
            # Si aucune information spécifique n'est trouvée, essayer de chercher dans le texte
            page_text = soup.get_text()
            horaires_pattern = r"(horaires|heures d'ouverture)\s*:?\s*([^\n.]*)"
            matches = re.search(horaires_pattern, page_text, re.IGNORECASE)
            if matches:
                return self._format_horaires(matches.group(2), library_id)
            
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des horaires depuis le web pour {library_id}: {e}")
            return None
    
    def _fetch_from_affluences(self, library_id):
        """
        Récupère les horaires depuis l'API Affluences.
        Cette méthode nécessite l'ID Affluences correct pour chaque bibliothèque.
        """
        try:
            library = self.bibliotheques.get(library_id)
            if not library or not library["id_affluences"]:
                return None
            
            # URL de l'API Affluences (à remplacer par la vraie URL)
            api_url = f"https://api.affluences.com/location/{library['id_affluences']}/opening-hours"
            
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Traiter les données JSON de l'API Affluences
            # Cette partie doit être adaptée en fonction de la structure de l'API
            if "openingHours" in data:
                opening_hours = data["openingHours"]
                return self._format_affluences_data(opening_hours, library_id)
            
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des horaires depuis Affluences pour {library_id}: {e}")
            return None
    
    def _format_horaires(self, horaires_text, library_id):
        """
        Formate le texte des horaires récupéré depuis le site web.
        """
        # À personnaliser selon le format des horaires sur le site
        if not horaires_text:
            return None
        
        # Nettoyer le texte (supprimer les espaces multiples, etc.)
        horaires_text = re.sub(r'\s+', ' ', horaires_text).strip()
        
        # Formater les informations
        library = self.bibliotheques.get(library_id, {})
        return {
            "source": "web",
            "library_id": library_id,
            "library_name": library.get("nom", ""),
            "horaires": horaires_text,
            "url": library.get("url", ""),
            "last_updated": datetime.now().isoformat()
        }
    
    def _format_affluences_data(self, opening_hours, library_id):
        """
        Formate les données d'horaires récupérées depuis l'API Affluences.
        """
        # À personnaliser selon le format des données d'Affluences
        if not opening_hours:
            return None
        
        # Exemple de formatage pour des horaires hebdomadaires
        formatted_hours = {}
        days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        
        for day_data in opening_hours:
            if "dayOfWeek" in day_data and "hours" in day_data:
                day_index = day_data["dayOfWeek"] - 1  # Si Affluences utilise 1-7 pour lundi-dimanche
                if 0 <= day_index < 7:
                    day_name = days_fr[day_index]
                    hours = day_data["hours"]
                    if hours:
                        formatted_hours[day_name] = hours
        
        library = self.bibliotheques.get(library_id, {})
        return {
            "source": "affluences",
            "library_id": library_id,
            "library_name": library.get("nom", ""),
            "horaires_details": formatted_hours,
            "url": f"https://affluences.com/{library_id}",
            "last_updated": datetime.now().isoformat()
        }
    
    def get_horaires(self, library_id=None):
        """
        Récupère les horaires d'une bibliothèque spécifique ou de toutes les bibliothèques.
        Essaie d'abord le cache, puis Affluences, puis le site web.
        
        Args:
            library_id (str, optional): ID de la bibliothèque. Si None, récupère pour toutes les bibliothèques.
        
        Returns:
            dict: Données des horaires formatées
        """
        if library_id:
            if library_id not in self.bibliotheques:
                self.logger.warning(f"Bibliothèque inconnue: {library_id}")
                return {"error": f"Bibliothèque inconnue: {library_id}"}
            
            # Essayer le cache d'abord
            cache_data = self._load_from_cache(library_id)
            if cache_data:
                return cache_data
            
            # Essayer Affluences ensuite
            affluences_data = self._fetch_from_affluences(library_id)
            if affluences_data:
                self._save_to_cache(library_id, affluences_data)
                return affluences_data
            
            # Essayer le site web en dernier recours
            web_data = self._fetch_from_web(library_id)
            if web_data:
                self._save_to_cache(library_id, web_data)
                return web_data
            
            # Si tout échoue, retourner un message d'erreur
            return {
                "library_id": library_id,
                "library_name": self.bibliotheques[library_id]["nom"],
                "error": "Impossible de récupérer les horaires",
                "fallback_url": self.bibliotheques[library_id]["url"]
            }
        else:
            # Récupérer les horaires pour toutes les bibliothèques
            results = {}
            for lib_id in self.bibliotheques:
                results[lib_id] = self.get_horaires(lib_id)
            return results
    
    def get_library_by_name(self, name):
        """
        Trouve une bibliothèque par son nom (recherche approximative).
        
        Args:
            name (str): Nom ou partie du nom de la bibliothèque
        
        Returns:
            str: ID de la bibliothèque correspondante ou None si non trouvée
        """
        name = name.lower()
        
        # Correspondance exacte d'abord
        for lib_id, lib_info in self.bibliotheques.items():
            if name == lib_info["nom"].lower():
                return lib_id
        
        # Correspondance partielle ensuite
        for lib_id, lib_info in self.bibliotheques.items():
            if name in lib_info["nom"].lower() or lib_id.lower() in name:
                return lib_id
        
        # Correspondances spécifiques
        if "orsay" in name or "science" in name:
            return "orsay"
        elif "sceaux" in name or "droit" in name or "eco" in name or "gestion" in name:
            return "sceaux"
        elif "kremlin" in name or "medecine" in name or "médecine" in name or "bicetre" in name or "bicêtre" in name:
            return "kremlin-bicetre"
        elif "lumen" in name or "learning" in name:
            return "lumen"
        
        return None
    
    def format_response(self, data, full_details=False):
        """
        Formate les données des horaires en une réponse textuelle.
        
        Args:
            data (dict): Données des horaires
            full_details (bool): Si True, inclut tous les détails
        
        Returns:
            str: Réponse formatée
        """
        if "error" in data:
            return f"Je n'ai pas pu récupérer les horaires de la {data.get('library_name', 'bibliothèque')}. " \
                   f"Veuillez consulter directement le site web: {data.get('fallback_url', self.horaires_url)}"
        
        library_name = data.get("library_name", "bibliothèque")
        
        if data.get("source") == "affluences":
            # Formater les données Affluences
            response = f"Horaires de la {library_name}:\n"
            
            horaires_details = data.get("horaires_details", {})
            if horaires_details:
                for day, hours in horaires_details.items():
                    response += f"- {day}: {hours}\n"
            else:
                response += "Horaires non disponibles en détail.\n"
            
            response += f"\nDernière mise à jour: {data.get('last_updated', 'inconnue')}"
            if full_details:
                response += f"\nSource: Affluences\nURL: {data.get('url', self.horaires_url)}"
            
            return response
        else:
            # Formater les données du site web
            response = f"Horaires de la {library_name}: {data.get('horaires', 'non disponibles')}"
            
            if full_details:
                response += f"\nDernière mise à jour: {data.get('last_updated', 'inconnue')}"
                response += f"\nSource: Site web\nURL: {data.get('url', self.horaires_url)}"
            
            response += f"\n\nPour des informations en temps réel, consultez: {self.horaires_url}"
            
            return response
    
    def handle_query(self, query):
        """
        Traite une question sur les horaires.
        
        Args:
            query (str): Question de l'utilisateur
        
        Returns:
            str: Réponse formatée
        """
        query = query.lower()
        
        # Détecter la bibliothèque mentionnée dans la question
        library_id = None
        for lib_id, lib_info in self.bibliotheques.items():
            if lib_id in query or lib_info["nom"].lower() in query:
                library_id = lib_id
                break
        
        # Si aucune bibliothèque spécifique n'est mentionnée, essayer de la déduire
        if not library_id:
            if "orsay" in query or "science" in query:
                library_id = "orsay"
            elif "sceaux" in query or "droit" in query or "eco" in query or "gestion" in query:
                library_id = "sceaux"
            elif "kremlin" in query or "medecine" in query or "médecine" in query:
                library_id = "kremlin-bicetre"
            elif "lumen" in query or "learning" in query:
                library_id = "lumen"
        
        # Récupérer les horaires
        if library_id:
            horaires_data = self.get_horaires(library_id)
            return self.format_response(horaires_data)
        else:
            # Si aucune bibliothèque spécifique n'est identifiée, donner un aperçu général
            response = "Voici les horaires des principales bibliothèques de l'Université Paris-Saclay:\n\n"
            
            for lib_id in ["orsay", "sceaux", "kremlin-bicetre", "lumen"]:
                horaires_data = self.get_horaires(lib_id)
                if "error" not in horaires_data:
                    response += f"{horaires_data.get('library_name', 'Bibliothèque')}: "
                    
                    if horaires_data.get("source") == "affluences" and "horaires_details" in horaires_data:
                        # Simplifier pour l'aperçu général
                        today = datetime.now().strftime("%A").lower().capitalize()
                        days_fr = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", 
                                  "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"}
                        today_fr = days_fr.get(today, today)
                        
                        today_hours = horaires_data["horaires_details"].get(today_fr, "horaires non disponibles")
                        response += f"{today_hours} (aujourd'hui)\n"
                    else:
                        response += f"{horaires_data.get('horaires', 'horaires non disponibles')}\n"
                else:
                    response += f"{self.bibliotheques[lib_id]['nom']}: horaires non disponibles\n"
            
            response += f"\nPour des informations détaillées et en temps réel, consultez: {self.horaires_url}"
            
            return response


# Test du module
if __name__ == "__main__":
    horaires_module = HorairesModule(cache_dir="./cache")
    
    # Test avec une bibliothèque spécifique
    print("Test pour la BU d'Orsay:")
    test_orsay = horaires_module.get_horaires("orsay")
    print(horaires_module.format_response(test_orsay, full_details=True))
    
    print("\nTest de la fonction handle_query:")
    test_query = "Quels sont les horaires de la bibliothèque d'Orsay aujourd'hui?"
    print(f"Question: {test_query}")
    print(horaires_module.handle_query(test_query))