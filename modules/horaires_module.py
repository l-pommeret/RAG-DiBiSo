import requests
import json
import os
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import logging

class HorairesModule:
    def __init__(self, cache_dir="cache", cache_expiry_hours=24):
        self.cache_dir = cache_dir
        self.cache_expiry_hours = cache_expiry_hours
        self.horaires_url = "https://www.bibliotheques.universite-paris-saclay.fr/horaires-et-affluence"
        self.bibliotheques = {
            "orsay": {
                "nom": "BU Sciences d'Orsay",
                "id_affluences": "f1c83d27-7c0c-463e-8177-e56649c2ed6e",
                "url": "https://www.universite-paris-saclay.fr/vie-de-campus/bibliotheques/bibliotheque-universitaire-orsay"
            },
            "sceaux": {
                "nom": "BU Droit-Économie-Gestion (Sceaux)",
                "id_affluences": "ad2d9a57-87bb-481a-9352-3c6b5f70762d",
                "url": "https://www.universite-paris-saclay.fr/vie-de-campus/bibliotheques/bibliotheque-universitaire-sceaux"
            },
            "kremlin-bicetre": {
                "nom": "BU Kremlin-Bicêtre",
                "id_affluences": "0f42bb9c-dac0-4965-8c0a-c44e15f1c47a",
                "url": "https://www.universite-paris-saclay.fr/vie-de-campus/bibliotheques/bibliotheque-universitaire-kremlin-bicetre"
            },
            "lumen": {
                "nom": "Lumen Learning Center Paris-Saclay",
                "id_affluences": "3ddf2999-9484-41b3-91c1-8d598128c23c",
                "url": "https://www.universite-paris-saclay.fr/lumen-learning-center"
            }
        }
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("HorairesModule")
    
    def _get_cache_path(self, library_id):
        return os.path.join(self.cache_dir, f"horaires_{library_id}.json")
    
    def _is_cache_valid(self, cache_path):
        if not os.path.exists(cache_path):
            return False
        
        try:
            file_modification_time = os.path.getmtime(cache_path)
            modification_datetime = datetime.fromtimestamp(file_modification_time)
            expiry_time = modification_datetime + timedelta(hours=self.cache_expiry_hours)
            
            return datetime.now() < expiry_time
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du cache: {e}")
            return False
    
    def _save_to_cache(self, library_id, data):
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
        try:
            library = self.bibliotheques.get(library_id)
            if not library:
                return None
            
            # D'abord, essayer la page spécifique de la bibliothèque
            response = requests.get(library["url"], timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher des sections d'horaires avec différentes classes/id
            horaires_section = (soup.find("div", class_="horaires") or 
                               soup.find("section", id="horaires") or 
                               soup.find("div", class_="hours") or
                               soup.find("div", id="opening-hours"))
            
            if horaires_section:
                horaires_text = horaires_section.get_text(strip=True)
                self.logger.info(f"Horaires trouvés dans une section dédiée pour {library_id}: {horaires_text[:100]}...")
                return self._format_horaires(horaires_text, library_id)
            
            # Chercher des tables qui pourraient contenir des horaires
            tables = soup.find_all("table")
            for table in tables:
                if "horaire" in table.get_text().lower() or "heure" in table.get_text().lower():
                    # Convertir la table en texte structuré
                    horaires_text = ""
                    for row in table.find_all("tr"):
                        cols = row.find_all(["th", "td"])
                        if cols:
                            horaires_text += " | ".join([col.get_text(strip=True) for col in cols]) + "\n"
                    
                    if horaires_text:
                        self.logger.info(f"Horaires trouvés dans une table pour {library_id}: {horaires_text[:100]}...")
                        return self._format_horaires(horaires_text, library_id)
            
            # Essayer de trouver les informations d'horaires dans le texte
            page_text = soup.get_text()
            horaires_patterns = [
                r"(horaires|heures d'ouverture|heures d'accessibilité)\s*:?\s*([^\n.]*)",
                r"(ouvert|ouverte|accessible)\s+(du|de|les)\s+([^\n.]*)",
                r"(ouverture)\s*:?\s*([^\n.]*)"
            ]
            
            for pattern in horaires_patterns:
                matches = re.search(pattern, page_text, re.IGNORECASE)
                if matches:
                    horaires_text = matches.group(2)
                    self.logger.info(f"Horaires trouvés via pattern pour {library_id}: {horaires_text}")
                    return self._format_horaires(horaires_text, library_id)
            
            # Si tout échoue, essayer de chercher sur la page générale des horaires
            if self.horaires_url:
                self.logger.info(f"Essai avec la page générale des horaires pour {library_id}")
                try:
                    response_general = requests.get(self.horaires_url, timeout=10)
                    response_general.raise_for_status()
                    
                    soup_general = BeautifulSoup(response_general.text, 'html.parser')
                    
                    # Recherche améliorée - Chercher des tableaux qui contiennent le nom de la bibliothèque
                    self.logger.info(f"Recherche de tableaux pour {library_id}")
                    tables = soup_general.find_all("table")
                    for table in tables:
                        table_text = table.get_text().lower()
                        if any(part.lower() in table_text for part in library["nom"].split()):
                            self.logger.info(f"Table trouvée qui mentionne {library_id}")
                            # Extraire les horaires du tableau
                            horaires_text = ""
                            for row in table.find_all("tr"):
                                # Vérifier si cette ligne concerne notre bibliothèque
                                row_text = row.get_text().lower()
                                if any(part.lower() in row_text for part in library["nom"].split()):
                                    cells = row.find_all(["th", "td"])
                                    if len(cells) > 1:  # Au moins une cellule pour le nom et une pour les horaires
                                        # Prendre toutes les cellules sauf la première (qui est probablement le nom)
                                        horaires_cells = cells[1:]
                                        horaires_text = " | ".join([cell.get_text(strip=True) for cell in horaires_cells])
                                        self.logger.info(f"Horaires trouvés dans une ligne de tableau pour {library_id}: {horaires_text}")
                                        return self._format_horaires(horaires_text, library_id)
                    
                    # Chercher des sections qui mentionnent cette bibliothèque
                    library_name_parts = library["nom"].lower().split()
                    for section in soup_general.find_all(["div", "section", "article"]):
                        section_text = section.get_text().lower()
                        if all(part in section_text for part in library_name_parts):
                            # Avoir trouvé une section qui semble concerner cette bibliothèque
                            horaires_text = section.get_text(strip=True)
                            self.logger.info(f"Horaires trouvés sur la page générale pour {library_id}: {horaires_text[:100]}...")
                            return self._format_horaires(horaires_text, library_id)
                    
                    # Si aucune section spécifique trouvée, chercher des paragraphes 
                    # contenant à la fois le nom de la bibliothèque et des mots liés aux horaires
                    horaire_keywords = ["horaire", "ouvert", "ferme", "heure", "jour"]
                    for p in soup_general.find_all(["p", "div"]):
                        p_text = p.get_text().lower()
                        if any(part in p_text for part in library_name_parts) and any(kw in p_text for kw in horaire_keywords):
                            horaires_text = p.get_text(strip=True)
                            self.logger.info(f"Horaires trouvés dans un paragraphe pour {library_id}: {horaires_text[:100]}...")
                            return self._format_horaires(horaires_text, library_id)
                    
                    # Chercher des horaires par défaut pour toutes les bibliothèques
                    # (en dernier recours)
                    for h in soup_general.find_all(["h1", "h2", "h3", "h4"]):
                        h_text = h.get_text().lower()
                        if "horaire" in h_text or "ouverture" in h_text:
                            # Récupérer les paragraphes qui suivent ce titre
                            sibling = h.find_next(["p", "div", "ul"])
                            if sibling:
                                horaires_text = sibling.get_text(strip=True)
                                self.logger.info(f"Horaires généraux trouvés dans un paragraphe: {horaires_text[:100]}...")
                                return self._format_horaires(f"Horaires généraux des bibliothèques: {horaires_text}", library_id)
                except Exception as e:
                    self.logger.error(f"Erreur lors de la recherche sur la page générale: {e}")
            
            # Valeurs par défaut si rien d'autre ne fonctionne
            default_horaires = {
                "orsay": "Lundi-Vendredi: 8h30-20h, Samedi: 10h-18h",
                "sceaux": "Lundi-Vendredi: 9h-19h, Fermé le weekend",
                "kremlin-bicetre": "Lundi-Vendredi: 9h-22h, Samedi: 9h-18h",
                "lumen": "Lundi-Vendredi: 8h30-22h30, Samedi-Dimanche: 10h-19h"
            }
            
            if library_id in default_horaires:
                self.logger.info(f"Utilisation des horaires par défaut pour {library_id}")
                return self._format_horaires(default_horaires[library_id], library_id)
            
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des horaires depuis le web pour {library_id}: {e}")
            return None
    
    def _fetch_from_affluences(self, library_id):
        try:
            library = self.bibliotheques.get(library_id)
            if not library or not library["id_affluences"]:
                return None
            
            # Nouvel endpoint API basé sur la V3 de l'API Affluences
            api_url = f"https://api.affluences.com/app/v3/timetables/{library['id_affluences']}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://affluences.com/"
            }
            
            # Obtenir la date du jour formatée pour l'API
            today = datetime.now().date()
            week_later = today + timedelta(days=7)
            
            # Paramètres de requête pour obtenir les horaires de la semaine
            params = {
                "start_date": today.isoformat(),
                "end_date": week_later.isoformat(),
                "offset": 0,
                "timezone": "Europe/Paris"
            }
            
            self.logger.info(f"Requête API Affluences pour {library_id} avec params: {params}")
            response = requests.get(api_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"API Affluences données reçues pour {library_id}: {str(data)[:100]}...")
            
            # Traiter les données selon le nouveau format de l'API
            if data and "data" in data:
                return self._format_affluences_data_v3(data["data"], library_id)
            elif isinstance(data, dict):
                # Si le format est direct sans 'data'
                return self._format_affluences_data_v3(data, library_id)
            
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des horaires depuis Affluences pour {library_id}: {e}")
            return None
    
    def _format_horaires(self, horaires_text, library_id):
        if not horaires_text:
            return None
        
        horaires_text = re.sub(r'\s+', ' ', horaires_text).strip()
        
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
        """Format les données de l'ancienne API Affluences (v1)."""
        if not opening_hours:
            return None
        
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
        
    def _format_affluences_data_v3(self, timetable_data, library_id):
        """Format les données de la nouvelle API Affluences (v3)."""
        if not timetable_data:
            self.logger.warning(f"Aucune donnée dans timetable_data pour {library_id}")
            return None
        
        # Journaliser la structure des données pour débogage
        self.logger.info(f"Structure des données API v3: {str(type(timetable_data))}")
        self.logger.info(f"Clés disponibles: {str(timetable_data.keys()) if isinstance(timetable_data, dict) else 'Pas un dictionnaire'}")
        
        # Adapter en fonction de la structure réelle des données
        days_data = []
        
        # Pour les cas où la structure est un dictionnaire avec des entrées
        if isinstance(timetable_data, dict):
            # Format spécifique de l'API v3 avec 'entries'
            if "entries" in timetable_data:
                days_data = timetable_data["entries"]
                self.logger.info(f"Entrées trouvées dans timetable_data['entries'], nombre: {len(days_data) if isinstance(days_data, list) else 'non-list'}")
                
                # Journal du premier élément pour comprendre la structure
                if isinstance(days_data, list) and days_data:
                    self.logger.info(f"Premier élément des entrées: {str(days_data[0])[:200]}...")
            
            # Format avec 'days'
            elif "days" in timetable_data:
                days_data = timetable_data["days"]
                self.logger.info(f"Jours trouvés dans timetable_data['days'], nombre: {len(days_data)}")
            else:
                # Pour les autres structures possibles
                self.logger.info(f"Structure alternative: {str(list(timetable_data.keys())[:5])}")
        elif isinstance(timetable_data, list):
            days_data = timetable_data
            self.logger.info(f"timetable_data est une liste, nombre d'éléments: {len(days_data)}")
        
        # Vérifier si nous avons des données utilisables
        if not days_data and isinstance(timetable_data, dict):
            # Informations de débogage
            if "message" in timetable_data:
                self.logger.info(f"Message dans les données: {timetable_data['message']}")
            
            if "information" in timetable_data:
                self.logger.info(f"Information dans les données: {timetable_data['information']}")
            
            # Si on a un autre format de données, essayer de l'adapter
            if "timetables" in timetable_data:
                self.logger.info("Format alternatif avec 'timetables' détecté")
                try:
                    if isinstance(timetable_data["timetables"], list):
                        for timetable in timetable_data["timetables"]:
                            if isinstance(timetable, dict) and "days" in timetable:
                                days_data = timetable["days"]
                                self.logger.info(f"Jours trouvés dans un format alternatif, nombre: {len(days_data)}")
                                break
                except Exception as e:
                    self.logger.error(f"Erreur lors de l'analyse du format alternatif: {e}")
        
        # Structure des jours en français
        days_fr = {
            "monday": "Lundi",
            "tuesday": "Mardi",
            "wednesday": "Mercredi",
            "thursday": "Jeudi", 
            "friday": "Vendredi",
            "saturday": "Samedi",
            "sunday": "Dimanche"
        }
        
        # Date d'aujourd'hui pour extraire les horaires pertinents
        today = datetime.now().date()
        
        # Convertir les données brutes en horaires formatés par jour
        formatted_hours = {}
        current_week_hours = {}
        
        # Tracer quelques échantillons pour validation
        if isinstance(days_data, list) and days_data:
            self.logger.info(f"Échantillon premier élément de days_data: {str(days_data[0])[:200]}")
        
        # Extraire les données des horaires
        for entry in days_data:
            if isinstance(entry, dict):
                try:
                    # Journaliser les clés disponibles dans une entrée
                    if len(formatted_hours) == 0:  # Seulement pour le premier
                        self.logger.info(f"Clés d'une entrée: {list(entry.keys())}")
                    
                    # Différentes façons de trouver la date selon le format API
                    day_str = None
                    if "day" in entry:
                        day_str = entry["day"]
                    elif "date" in entry:
                        day_str = entry["date"]
                    
                    if day_str:
                        # Convertir la date ISO en objet date (accommoder différents formats)
                        try:
                            if "T" in day_str:  # Format ISO complet
                                day_date = datetime.fromisoformat(day_str.replace("Z", "+00:00")).date()
                            else:  # Format date simple
                                day_date = datetime.strptime(day_str, "%Y-%m-%d").date()
                            
                            # Vérifier si la date est pour aujourd'hui ou dans la semaine à venir
                            delta = (day_date - today).days
                            if 0 <= delta < 7:  # Aujourd'hui ou dans la semaine à venir
                                # Déterminer le jour de la semaine
                                day_name_en = day_date.strftime("%A").lower()
                                day_name_fr = days_fr.get(day_name_en, day_name_en)
                                
                                # Extraire les horaires d'ouverture (s'adapter aux différents formats)
                                opening_hours = []
                                
                                # Format: entry["opening_hours"] = [{opening_time, closing_time}, ...]
                                if "opening_hours" in entry and isinstance(entry["opening_hours"], list):
                                    for hours in entry["opening_hours"]:
                                        if isinstance(hours, dict):
                                            open_key = next((k for k in hours.keys() if "open" in k.lower()), None)
                                            close_key = next((k for k in hours.keys() if "clos" in k.lower()), None)
                                            
                                            if open_key and close_key:
                                                open_time = hours[open_key]
                                                close_time = hours[close_key]
                                                opening_hours.append(f"{open_time} - {close_time}")
                                
                                # Format alternatif: entry["slots"] avec horaires
                                elif "slots" in entry and isinstance(entry["slots"], list):
                                    for slot in entry["slots"]:
                                        if isinstance(slot, dict) and "start_time" in slot and "end_time" in slot:
                                            open_time = slot["start_time"]
                                            close_time = slot["end_time"]
                                            opening_hours.append(f"{open_time} - {close_time}")
                                
                                # Format alternatif: horaires directement dans l'entrée
                                elif "open" in entry and "close" in entry:
                                    open_time = entry["open"]
                                    close_time = entry["close"]
                                    opening_hours.append(f"{open_time} - {close_time}")
                                
                                # Formater pour affichage
                                if opening_hours:
                                    hours_str = ", ".join(opening_hours)
                                    current_week_hours[day_name_fr] = hours_str
                                    
                                    # Si c'est aujourd'hui, l'ajouter aussi aux horaires formatés
                                    if delta == 0:
                                        formatted_hours[day_name_fr] = hours_str
                                else:
                                    # Vérifier si explicitement fermé
                                    is_closed = False
                                    if "closed" in entry:
                                        is_closed = entry["closed"]
                                    elif "is_closed" in entry:
                                        is_closed = entry["is_closed"]
                                    
                                    status = "Fermé" if is_closed else "Pas d'horaires disponibles"
                                    current_week_hours[day_name_fr] = status
                                    if delta == 0:
                                        formatted_hours[day_name_fr] = status
                        except Exception as e:
                            self.logger.error(f"Erreur lors du parsing de la date {day_str}: {e}")
                    
                except Exception as e:
                    self.logger.error(f"Erreur lors du traitement d'une entrée: {e}")
        
        # Si aucune donnée pour aujourd'hui, utiliser la semaine courante
        if not formatted_hours and current_week_hours:
            formatted_hours = current_week_hours
        
        # Journaliser les résultats
        self.logger.info(f"Horaires trouvés pour aujourd'hui: {formatted_hours}")
        self.logger.info(f"Horaires trouvés pour la semaine: {current_week_hours}")
        
        library = self.bibliotheques.get(library_id, {})
        return {
            "source": "affluences_v3",
            "library_id": library_id,
            "library_name": library.get("nom", ""),
            "horaires_details": formatted_hours,
            "current_week": current_week_hours,
            "url": f"https://affluences.com/{library_id}",
            "last_updated": datetime.now().isoformat()
        }
    
    def get_horaires(self, library_id=None):
        if library_id:
            if library_id not in self.bibliotheques:
                self.logger.warning(f"Bibliothèque inconnue: {library_id}")
                return {"error": f"Bibliothèque inconnue: {library_id}"}
            
            # Vérifier si nous avons des données en cache valides
            cache_data = self._load_from_cache(library_id)
            if cache_data:
                self.logger.info(f"Données récupérées du cache pour {library_id}")
                
                # Si le cache vient de l'API Affluences et contient des horaires, le renvoyer
                if cache_data.get("source") in ["affluences", "affluences_v3"] and cache_data.get("horaires_details"):
                    return cache_data
                
                # Si le cache est de l'API Affluences mais vide, essayer le web scraping
                # sinon nous garderons le cache existant
                if cache_data.get("source") in ["affluences", "affluences_v3"] and not cache_data.get("horaires_details"):
                    self.logger.info(f"Cache Affluences vide pour {library_id}, essai du web scraping")
                    
                    # On force la récupération depuis le web si le cache est vide
                    web_data = self._fetch_from_web(library_id)
                    if web_data and web_data.get('horaires'):
                        self._save_to_cache(library_id, web_data)
                        return web_data
                    
                    # Si le web scraping échoue aussi, on renvoie quand même le cache
                    return cache_data
                else:
                    # Cache web valide
                    return cache_data
            
            # Essayer d'abord avec Affluences (données plus riches et structurées)
            affluences_data = self._fetch_from_affluences(library_id)
            if affluences_data and (affluences_data.get("horaires_details") or affluences_data.get("current_week")):
                self.logger.info(f"Données récupérées avec succès depuis Affluences pour {library_id}")
                self._save_to_cache(library_id, affluences_data)
                return affluences_data
            
            # Si Affluences échoue ou ne retourne pas de données utiles, essayer le web scraping
            self.logger.info(f"Échec ou données vides avec Affluences pour {library_id}, essai du web scraping")
            web_data = self._fetch_from_web(library_id)
            if web_data:
                self.logger.info(f"Données récupérées avec succès depuis le web pour {library_id}")
                self._save_to_cache(library_id, web_data)
                return web_data
            
            # Si aucune méthode ne fonctionne
            self.logger.warning(f"Impossible de récupérer les horaires pour {library_id}")
            return {
                "library_id": library_id,
                "library_name": self.bibliotheques[library_id]["nom"],
                "error": "Impossible de récupérer les horaires",
                "fallback_url": self.bibliotheques[library_id]["url"]
            }
        else:
            results = {}
            for lib_id in self.bibliotheques:
                results[lib_id] = self.get_horaires(lib_id)
            return results
    
    def get_library_by_name(self, name):
        name = name.lower()
        
        for lib_id, lib_info in self.bibliotheques.items():
            if name == lib_info["nom"].lower():
                return lib_id
        
        for lib_id, lib_info in self.bibliotheques.items():
            if name in lib_info["nom"].lower() or lib_id.lower() in name:
                return lib_id
        
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
        if "error" in data:
            return f"Je n'ai pas pu récupérer les horaires de la {data.get('library_name', 'bibliothèque')}. " \
                   f"Veuillez consulter directement le site web: {data.get('fallback_url', self.horaires_url)}"
        
        library_name = data.get("library_name", "bibliothèque")
        
        # Gestion des données provenant de l'API Affluences v3
        if data.get("source") == "affluences_v3":
            # Obtenir la date actuelle pour indiquer le jour d'aujourd'hui
            today = datetime.now().strftime("%A").lower()
            days_fr = {
                "monday": "Lundi",
                "tuesday": "Mardi",
                "wednesday": "Mercredi",
                "thursday": "Jeudi", 
                "friday": "Vendredi",
                "saturday": "Samedi",
                "sunday": "Dimanche"
            }
            today_fr = days_fr.get(today, "Aujourd'hui")
            
            response = f"Horaires de la {library_name}:\n"
            
            # Vérifier si on a des données pour aujourd'hui
            horaires_details = data.get("horaires_details", {})
            horaires_semaine = data.get("current_week", {})
            
            if today_fr in horaires_details:
                response += f"- Aujourd'hui ({today_fr}): {horaires_details[today_fr]}\n\n"
            
            if horaires_semaine:
                response += "Horaires cette semaine:\n"
                for day, hours in horaires_semaine.items():
                    if day == today_fr:
                        response += f"- {day} (aujourd'hui): {hours}\n"
                    else:
                        response += f"- {day}: {hours}\n"
            else:
                response += "Horaires détaillés non disponibles pour cette semaine.\n"
            
            response += f"\nDernière mise à jour: {data.get('last_updated', 'inconnue')}"
            if full_details:
                response += f"\nSource: Affluences\nURL: {data.get('url', self.horaires_url)}"
            
            return response
            
        # Gestion des données provenant de l'API Affluences v1
        elif data.get("source") == "affluences":
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
            
        # Gestion des données provenant du web scraping
        else:
            response = f"Horaires de la {library_name}: {data.get('horaires', 'non disponibles')}"
            
            if full_details:
                response += f"\nDernière mise à jour: {data.get('last_updated', 'inconnue')}"
                response += f"\nSource: Site web\nURL: {data.get('url', self.horaires_url)}"
            
            response += f"\n\nPour des informations en temps réel, consultez: {self.horaires_url}"
            
            return response
    
    def handle_query(self, query):
        query = query.lower()
        
        # Valeurs par défaut pour les bibliothèques
        default_horaires = {
            "orsay": {
                "nom": "BU Sciences d'Orsay",
                "horaires": "Lundi-Vendredi: 8h30-20h, Samedi: 10h-18h"
            },
            "sceaux": {
                "nom": "BU Droit-Économie-Gestion (Sceaux)",
                "horaires": "Lundi-Vendredi: 9h-19h, Fermé le weekend"
            },
            "kremlin-bicetre": {
                "nom": "BU Kremlin-Bicêtre",
                "horaires": "Lundi-Vendredi: 9h-22h, Samedi: 9h-18h"
            },
            "lumen": {
                "nom": "Lumen Learning Center Paris-Saclay",
                "horaires": "Lundi-Vendredi: 8h30-22h30, Samedi-Dimanche: 10h-19h"
            }
        }
        
        # Déterminer de quelle bibliothèque il s'agit
        library_id = None
        for lib_id, lib_info in self.bibliotheques.items():
            if lib_id in query or lib_info["nom"].lower() in query:
                library_id = lib_id
                break
        
        if not library_id:
            if "orsay" in query or "science" in query:
                library_id = "orsay"
            elif "sceaux" in query or "droit" in query or "eco" in query or "gestion" in query:
                library_id = "sceaux"
            elif "kremlin" in query or "medecine" in query or "médecine" in query:
                library_id = "kremlin-bicetre"
            elif "lumen" in query or "learning" in query:
                library_id = "lumen"
        
        # Traiter les questions sur les jours spécifiques
        jour_actuel = datetime.now().strftime("%A").lower()
        jours_fr = {
            "monday": "lundi",
            "tuesday": "mardi",
            "wednesday": "mercredi", 
            "thursday": "jeudi",
            "friday": "vendredi",
            "saturday": "samedi",
            "sunday": "dimanche"
        }
        today_fr = jours_fr.get(jour_actuel, "aujourd'hui")
        
        # Vérifier d'abord si on obtient des données depuis l'API Affluences
        if library_id:
            # Essayer d'obtenir des données réelles via Affluences ou Web
            horaires_data = self.get_horaires(library_id)
            # Vérifier si les données sont utiles et complètes
            if horaires_data and "error" not in horaires_data:
                if (horaires_data.get("source") == "affluences_v3" and 
                    ("horaires_details" in horaires_data or "current_week" in horaires_data)):
                    # Les données Affluences sont bonnes, on les utilise
                    return self.format_response(horaires_data)
            
            # Si pas de données utiles, utiliser les valeurs par défaut
            self.logger.info(f"Utilisation des horaires par défaut pour {library_id}")
            
            # Rechercher si on demande un jour spécifique
            jour_demande = None
            for jour in jours_fr.values():
                if jour in query:
                    jour_demande = jour
                    break
            
            # Préparer la réponse avec les valeurs par défaut
            lib_info = default_horaires.get(library_id, {"nom": self.bibliotheques[library_id]["nom"], "horaires": "horaires non disponibles"})
            
            if "aujourd'hui" in query or "ce jour" in query or today_fr in query:
                # Question sur aujourd'hui
                return f"Aujourd'hui ({today_fr}), la {lib_info['nom']} est ouverte selon ces horaires: {lib_info['horaires']}"
            elif jour_demande:
                # Question sur un jour spécifique
                # Pour simplifier, on extrait l'horaire du jour demandé à partir des horaires par défaut
                if "weekend" in lib_info['horaires'].lower() and jour_demande in ["samedi", "dimanche"]:
                    return f"La {lib_info['nom']} est fermée le {jour_demande}."
                elif "samedi" in lib_info['horaires'].lower() and jour_demande == "samedi":
                    # Extraire les horaires du samedi
                    import re
                    samedi_match = re.search(r'Samedi:\s*([\d:h-]+)', lib_info['horaires'])
                    if samedi_match:
                        samedi_hours = samedi_match.group(1)
                        return f"Le {jour_demande}, la {lib_info['nom']} est ouverte de {samedi_hours}."
                    else:
                        return f"Le {jour_demande}, la {lib_info['nom']} est ouverte selon ces horaires: {lib_info['horaires']}"
                elif jour_demande in ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]:
                    # Extraire les horaires de la semaine
                    import re
                    semaine_match = re.search(r'Lundi-Vendredi:\s*([\d:h-]+)', lib_info['horaires'])
                    if semaine_match:
                        semaine_hours = semaine_match.group(1)
                        return f"Le {jour_demande}, la {lib_info['nom']} est ouverte de {semaine_hours}."
                    else:
                        return f"Le {jour_demande}, la {lib_info['nom']} est ouverte selon ces horaires: {lib_info['horaires']}"
                else:
                    return f"La {lib_info['nom']} est ouverte selon ces horaires: {lib_info['horaires']}"
            else:
                # Question générale sur les horaires
                return f"La {lib_info['nom']} est ouverte selon ces horaires: {lib_info['horaires']}"
        else:
            # Si aucune bibliothèque spécifique n'est mentionnée, donner les horaires pour toutes
            response = "Voici les horaires des principales bibliothèques de l'Université Paris-Saclay:\n\n"
            
            for lib_id, info in default_horaires.items():
                response += f"- {info['nom']}: {info['horaires']}\n"
            
            response += f"\nPour des informations détaillées et en temps réel, consultez: {self.horaires_url}"
            
            return response