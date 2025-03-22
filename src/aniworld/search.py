import html
import logging
import os
import webbrowser
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Union
from json import loads
from json.decoder import JSONDecodeError
from urllib.parse import quote
import traceback

import curses
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from mysql.connector import MySQLConnection

from aniworld.common import (
    clear_screen,
    fetch_url_content,
    display_ascii_art,
    show_messagebox,
)
from aniworld.models import AnimeSeries, Season, Episode
from aniworld.database.repositories import AnimeRepository, SeasonRepository, EpisodeRepository

# Logger für dieses Modul einrichten
module_log = logging.getLogger(__name__)

# Datenbankintegration (optional für Systeme ohne Datenbank)
try:
    from aniworld.database import HAS_DATABASE, get_pipeline
except ImportError:
    HAS_DATABASE = False

    def get_pipeline():
        return None

# Temporärer Test der Datenbankverbindung
print("=== DATENBANK-TEST ===")
print(f"HAS_DATABASE vor Import: {HAS_DATABASE}")
try:
    from aniworld.database.pipeline import get_pipeline
    HAS_DATABASE = True
    print(f"HAS_DATABASE nach Import: {HAS_DATABASE}")
    pipeline = get_pipeline()
    print(f"Pipeline erstellt: {pipeline}")
    if pipeline.db is None:
        print("FEHLER: Datenbankverbindung konnte nicht hergestellt werden")
    else:
        print("ERFOLG: Datenbankverbindung erfolgreich hergestellt")
        # Teste eine einfache Datenbankoperation
        try:
            animes = pipeline.db.find_all_animes()
            print(f"Anzahl Anime in der Datenbank: {len(animes)}")
        except Exception as e:
            print(f"FEHLER bei Datenbankabfrage: {str(e)}")
except Exception as e:
    print(f"FEHLER bei Datenbanktest: {str(e)}")
print("=== ENDE DATENBANK-TEST ===")

try:
    from aniworld.database.pipeline import get_pipeline
    HAS_DATABASE = True
except ImportError:
    logging.debug("Datenbankmodul nicht verfügbar, Speicherung wird deaktiviert")


def search_anime(slug: str = None, link: str = None, query: str = None) -> str:
    clear_screen()
    logging.debug("Starting search_anime function")

    not_found = "Die gewünschte Serie wurde nicht gefunden oder ist im Moment deaktiviert."

    if slug:
        return fetch_by_slug(slug, not_found)

    if link:
        return fetch_by_link(link, not_found)

    return search_by_query(query)


def fetch_by_slug(slug: str, not_found: str) -> str:
    url = f"https://aniworld.to/anime/stream/{slug}"
    logging.debug("Fetching using slug: %s", url)
    response = fetch_url_content(url)
    if response and not_found not in response.decode():
        logging.debug("Found matching slug: %s", slug)
        
        # Speichere Daten in der Datenbank, wenn verfügbar
        if HAS_DATABASE:
            try:
                # Extrahiere Anime-Daten aus der Antwort
                html_content = response.decode()
                soup = BeautifulSoup(html_content, 'html.parser')
                save_anime_data_from_html(soup, url)
            except Exception as e:
                logging.error(f"Fehler beim Speichern der Anime-Daten in der Datenbank: {e}")
        
        return slug
    return None


def fetch_by_link(link: str, not_found: str) -> str:
    try:
        logging.debug("Fetching using link: %s", link)
        response = fetch_url_content(link, check=False)
        if response and not_found not in response.decode():
            slug = link.split('/')[-1]
            logging.debug("Found matching slug: %s", slug)
            
            # Speichere Daten in der Datenbank, wenn verfügbar
            if HAS_DATABASE:
                try:
                    # Extrahiere Anime-Daten aus der Antwort
                    html_content = response.decode()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    save_anime_data_from_html(soup, link)
                except Exception as e:
                    logging.error(f"Fehler beim Speichern der Anime-Daten in der Datenbank: {e}")
            
            return slug
    except ValueError:
        logging.debug("ValueError encountered while fetching link")
    return None


def save_anime_data_from_html(
    soup: BeautifulSoup, anime_link: str, session: Optional[MySQLConnection] = None
) -> Union[AnimeSeries, None]:
    """
    Extracts anime data from the HTML content and saves it to the database.

    Args:
        soup: BeautifulSoup object containing the HTML content
        anime_link: Link to the anime page
        session: Database session (optional)

    Returns:
        AnimeSeries object if successful, None otherwise
    """
    module_log.debug(f"Starte Extraktion und Speicherung für: {anime_link}")
    
    try:
        soup_content = soup.prettify()
        if "Wartungsarbeiten" in soup_content or "Wir aktualisieren" in soup_content:
            module_log.error(f"Wartungsarbeiten oder Update der Seite: {anime_link}")
            return None

        # Erstelle das Dictionary im Format für AnimeService.save_from_scraper_data
        anime_data = {"url": anime_link}

        # Extract anime title
        anime_title_element = soup.select_one("h1.seriesCoverMainTitle")
        if anime_title_element:
            anime_title = anime_title_element.text.strip()
            anime_data["title"] = anime_title
            module_log.debug(f"Extrahierter Titel: {anime_title}")
        else:
            module_log.error(f"Kein Anime-Titel gefunden in: {anime_link}")
            return None

        # Extract anime description
        description_element = soup.select_one("div.seriesTooltipDescription")
        if description_element:
            # Entferne <br> Tags und ersetze sie durch Zeilenumbrüche
            for br in description_element.find_all("br"):
                br.replace_with("\n")
            anime_data["description"] = description_element.text.strip()
        else:
            anime_data["description"] = None
            module_log.debug(f"Keine Beschreibung gefunden für: {anime_title}")

        # Extract cover image URL
        cover_image = None
        
        # Erste Versuch: Aus dem Hero-Banner
        hero_image = soup.select_one("div.seriesContentWrapper img.seriesCover")
        if hero_image and hero_image.get("src"):
            cover_image = hero_image["src"]
        
        # Zweiter Versuch: Aus dem seriesCoverContainer
        if not cover_image:
            cover_container = soup.select_one("div.seriesCoverContainer img")
            if cover_container and cover_container.get("src"):
                cover_image = cover_container["src"]
        
        # Dritter Versuch: Suche nach allen Bildern mit "cover" im Klassennamen
        if not cover_image:
            cover_images = soup.select("img[class*='cover']")
            if cover_images and cover_images[0].get("src"):
                cover_image = cover_images[0]["src"]
        
        # Korrekter Schlüssel für AnimeService ist cover_url, nicht cover_image
        anime_data["cover_url"] = cover_image
        
        # Extract genres
        genres = []
        genre_links = soup.select("a[href*='/genre/']")
        for genre_link in genre_links:
            genre_text = genre_link.text.strip()
            if genre_text and genre_text not in genres:
                genres.append(genre_text)
            
        anime_data["genres"] = genres if genres else None
        
        if anime_data["genres"]:
            module_log.debug(f"Extrahierte Genres für {anime_title}: {anime_data['genres']}")

        # Extract seasons and episodes
        seasons_container = soup.select_one("div.seasons-wrapper")
        
        # Debugging für Staffel-Container
        if not seasons_container:
            module_log.debug(f"Kein seasons-wrapper für {anime_title} gefunden.")
            # Versuche alternative Klassen zu finden
            all_classes = [div.get("class", []) for div in soup.find_all("div")]
            possible_season_classes = [cls for class_list in all_classes for cls in class_list if "season" in cls.lower()]
            if possible_season_classes:
                module_log.debug(f"Mögliche season-Klassen: {possible_season_classes}")
        
            # Zeige einen Ausschnitt des HTML-Codes
            module_log.debug(f"HTML-Vorschau: {soup_content[:1000]}...")

        seasons = []
        
        # Sammle alle verfügbaren Season-IDs
        season_elements = soup.select("[data-season-id]")
        season_ids = set()
        for season_element in season_elements:
            season_id = season_element.get("data-season-id")
            if season_id and season_id.isdigit():
                season_ids.add(int(season_id))
        
        # Extrahiere Episodentitel aus der Tabelle
        episode_titles = {}
        episode_table = soup.select_one("table.seasonEpisodesTable")
        if episode_table:
            rows = episode_table.select("tr")
            for row in rows:
                # Überspringe Header-Zeilen
                if row.select_one("th"):
                    continue
                
                # Überprüfe, ob dies eine Episodenzeile ist
                episode_number_cell = row.select_one("td.seasonEpisodeNumber")
                episode_title_cell = row.select_one("td.seasonEpisodeTitle")
                
                if episode_number_cell and episode_title_cell:
                    try:
                        # Extrahiere die Episodennummer
                        episode_text = episode_number_cell.text.strip()
                        # Entferne alle nicht-numerischen Zeichen
                        episode_num = int(''.join(filter(str.isdigit, episode_text)))
                        
                        # Extrahiere den tatsächlichen Titel
                        title = episode_title_cell.text.strip()
                        if title:
                            episode_titles[episode_num] = title
                            module_log.debug(f"Extrahierter Episodentitel: Episode {episode_num} - {title}")
                    except (ValueError, IndexError) as e:
                        module_log.debug(f"Fehler beim Extrahieren des Episodentitels: {e}")
        
        # Extrahiere Informationen für jede Staffel
        for season_id in sorted(season_ids):
            # WICHTIG: AnimeService erwartet "number" nicht "season_id"
            season_data = {"number": season_id, "title": f"Staffel {season_id}", "episodes": []}
            
            # Extrahiere Episode-Links für diese Staffel
            episode_links = soup.select(f"[data-season-id='{season_id}'] a[data-episode-id]")
            
            for episode_link in episode_links:
                episode_id = episode_link.get("data-episode-id")
                if not episode_id or not episode_id.isdigit():
                    continue
                
                episode_id = int(episode_id)
                episode_url = episode_link.get("href")
                
                # Standard-Titel (wird verwendet, wenn kein besserer gefunden wird)
                episode_title = episode_link.get("title", f"Staffel {season_id} Episode {episode_id}")
                
                # Versuche, den tatsächlichen Episodentitel zu verwenden, wenn verfügbar
                if episode_id in episode_titles:
                    episode_title = episode_titles[episode_id]
                
                # WICHTIG: AnimeService erwartet "number" nicht "episode_id"
                episode_data = {
                    "number": episode_id,
                    "title": episode_title,
                    "url": f"https://aniworld.to{episode_url}" if episode_url.startswith("/") else episode_url,
                }
                season_data["episodes"].append(episode_data)
            
            if season_data["episodes"]:
                seasons.append(season_data)

        anime_data["seasons"] = seasons
        module_log.debug(f"Anzahl Staffeln in den Daten: {len(seasons)}")

        # Im Anime Link keine trailing slashes für die Datenbank
        if anime_link.endswith("/"):
            anime_link = anime_link[:-1]

        if "seasons" not in anime_data or not anime_data["seasons"]:
            module_log.debug(f"Keine Staffeldaten im anime_data Dictionary gefunden!")

        # GEÄNDERT: Verwende AnimeService anstelle von direktem SQL
        try:
            from aniworld.database.services import AnimeService
            anime_service = AnimeService()
            anime_id = anime_service.save_from_scraper_data(anime_data)
            
            # Hole das vollständige Anime-Objekt
            anime = anime_service.get_anime_by_id(anime_id)
            module_log.info(f"Anime '{anime_data['title']}' in Datenbank gespeichert mit ID: {anime_id}")
            
            return anime
        except Exception as e:
            module_log.error(f"Fehler beim Speichern über AnimeService: {e}")
            module_log.error(traceback.format_exc())
            
            # Fallback: Versuche minimale Anime-Daten zu speichern
            try:
                from aniworld.database.integration import DatabaseIntegration
                db = DatabaseIntegration()
                anime_id = db.save_minimal_anime(anime_link.split('/')[-1], anime_data["title"])
                if anime_id:
                    anime = db.get_anime_by_id(anime_id)
                    module_log.info(f"Minimale Anime-Daten gespeichert mit ID: {anime_id}")
                    return anime
            except Exception as e2:
                module_log.error(f"Auch Fallback für minimale Speicherung fehlgeschlagen: {e2}")
            
            return None

    except Exception as e:
        module_log.error(f"Fehler bei der Extraktion oder Speicherung der Anime-Daten: {e}")
        module_log.error(traceback.format_exc())
        return None


def search_by_query(query: str) -> str:
    while True:
        clear_screen()
        if not query:
            print(display_ascii_art())
            query = input("Search for a series: ")
            if query.lower().strip() == "boku no piko":
                show_messagebox("This is not on aniworld...\nThank god...", "Really?...", "info")
        else:
            logging.debug("Using provided query: %s", query)

        url = f"https://aniworld.to/ajax/seriesSearch?keyword={quote(query)}"
        logging.debug("Fetching Anime List with query: %s", query)

        json_data = fetch_anime_json(url)

        if not json_data:
            print("No series found. Try again...")
            query = None
            continue
            
        # Debug: Zeige die Struktur der JSON-Daten
        print("JSON-Daten Struktur:")
        for i, item in enumerate(json_data):
            print(f"  Item {i}: {item}")

        # Hier speichern wir alle gefundenen Anime in der Datenbank, bevor wir fortfahren
        if HAS_DATABASE:
            try:
                logging.info(f"Speichere {len(json_data)} gefundene Anime in die Datenbank...")
                for anime_item in json_data:
                    try:
                        # Anime-Link extrahieren und Details abrufen
                        anime_link = anime_item.get('link')
                        if anime_link:
                            print(f"Original Link aus Suchergebnissen: '{anime_link}'")
                            logging.debug(f"Hole Details für Anime: {anime_link}")
                            # Vollständige URL erstellen, falls notwendig
                            if not anime_link.startswith('http'):
                                print(f"Link beginnt nicht mit http, füge Präfix hinzu")
                                # Prüfen, ob der Link bereits mit / beginnt
                                if not anime_link.startswith('/'):
                                    anime_link = f"/anime/stream/{anime_link}"
                                anime_link = f"https://aniworld.to{anime_link}"
                            
                            print(f"Endgültiger Link für Abfrage: '{anime_link}'")
                            
                            # HTML-Inhalt der Anime-Detailseite abrufen
                            response = fetch_url_content(anime_link)
                            if response:
                                html_content = response.decode()
                                # HTML-Inhalt in BeautifulSoup-Objekt umwandeln
                                soup = BeautifulSoup(html_content, 'html.parser')
                                # Anime-Daten aus HTML extrahieren und in Datenbank speichern
                                anime_id = save_anime_data_from_html(soup, anime_link)
                                logging.info(f"Anime '{anime_item.get('name', 'Unbekannt')}' in Datenbank gespeichert mit ID: {anime_id}")
                    except Exception as e:
                        logging.error(f"Fehler beim Speichern des Anime {anime_item.get('name', 'Unbekannt')}: {e}")
                        print(f"Fehler beim Speichern von '{anime_item.get('name', 'Unbekannt')}': {e}")
                        traceback.print_exc()
            except Exception as e:
                logging.error(f"Kritischer Fehler beim Datenbankvorgang: {e}")
                print(f"Kritischer Fehler bei der Datenbankoperation: {e}")
                traceback.print_exc()
                # Wenn ein kritischer Fehler auftritt, deaktivieren wir temporär die Datenbankfunktionalität
                logging.warning("Datenbankfunktionalität für diese Suche temporär deaktiviert")
                print("Datenbankfunktionalität für diese Suche temporär deaktiviert")

        if len(json_data) == 1:
            logging.debug("Only one anime found: %s", json_data[0])
            return json_data[0].get('link', 'No Link Found')

        selected_slug = curses.wrapper(display_menu, json_data)
        logging.debug("Found matching slug: %s", selected_slug)
        return selected_slug


def fetch_anime_json(url: str) -> Optional[List[Dict]]:
    """Abrufen der JSON-Daten für die Suche"""
    print(f"\nSende Suchanfrage an: {url}")
    logging.debug(f"Fetching anime JSON data from: {url}")
    
    response = fetch_url_content(url)
    if not response:
        print("Keine Antwort von der Suchanfrage erhalten!")
        logging.error("Failed to fetch search results")
        return None

    try:
        # Versuche die JSON-Daten zu dekodieren
        response_text = response.decode('utf-8')
        
        # Überprüfe auf mögliche HTML-Antwort (z.B. bei Captcha)
        if "<html" in response_text or "<body" in response_text:
            soup = BeautifulSoup(response_text, 'html.parser')
            # Suche nach pre-Tag, das normalerweise JSON-Daten enthält
            json_tag = soup.find('pre')
            if json_tag:
                response_text = json_tag.text
            else:
                print("Die Antwort enthält HTML statt JSON. Möglicherweise wurde ein Captcha gelöst.")
                # Suche nach einem JSON-ähnlichen Teil in der Antwort
                json_match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
                else:
                    print("Konnte keine JSON-Daten in der HTML-Antwort finden.")
                    logging.error("No JSON data found in HTML response")
                    return None
        
        # Log erste 200 Zeichen der Antwort
        logging.debug(f"Response first 200 chars: {response_text[:200]}")
        print(f"Antwort erhalten, verarbeite Daten...")
        
        # Versuche die JSON-Daten zu parsen
        decoded_data = loads(response_text)
        
        if isinstance(decoded_data, list):
            logging.debug(f"Parsed JSON data: Found {len(decoded_data)} items")
            print(f"Gefunden: {len(decoded_data)} Anime-Einträge")
            return decoded_data
        else:
            print(f"Unerwartetes Antwortformat: {type(decoded_data)}")
            logging.error(f"Unexpected response format: {type(decoded_data)}")
            return None
            
    except JSONDecodeError as e:
        print(f"Fehler beim Dekodieren der JSON-Antwort: {str(e)}")
        logging.error(f"JSON decode error: {str(e)}")
        # Zeige die ersten 200 Zeichen der Antwort an
        if response:
            print(f"Antwort (erste 200 Zeichen): {response.decode('utf-8', errors='replace')[:200]}...")
        return None
    except Exception as e:
        print(f"Unerwarteter Fehler bei der Verarbeitung der Suchantwort: {str(e)}")
        logging.error(f"Unexpected error processing search response: {str(e)}")
        return None


def display_menu(stdscr: curses.window, items: List[Dict[str, Optional[str]]]) -> Optional[str]:
    logging.debug("Starting display_menu function")
    current_row = 0

    konami_code = ['UP', 'UP', 'DOWN', 'DOWN', 'LEFT', 'RIGHT', 'LEFT', 'RIGHT', 'b', 'a']
    entered_keys = []

    key_map = {
        curses.KEY_UP: 'UP',
        curses.KEY_DOWN: 'DOWN',
        curses.KEY_LEFT: 'LEFT',
        curses.KEY_RIGHT: 'RIGHT',
        ord('b'): 'b',
        ord('a'): 'a'
    }

    while True:
        stdscr.clear()
        for idx, anime in enumerate(items):
            name = anime.get('name', 'No Name')
            year = anime.get('productionYear', 'No Year')
            attr = curses.A_REVERSE if idx == current_row else 0
            stdscr.attron(attr)
            stdscr.addstr(idx, 0, f"{name} {year}")
            stdscr.attroff(attr)

        stdscr.refresh()
        key = stdscr.getch()

        if key in key_map:
            entered_keys.append(key_map[key])
            if len(entered_keys) > len(konami_code):
                entered_keys.pop(0)

            if entered_keys == konami_code:
                konami_code_activated()
                entered_keys.clear()
        else:
            entered_keys.clear()

        if key == curses.KEY_DOWN:
            current_row = (current_row + 1) % len(items)
        elif key == curses.KEY_UP:
            current_row = (current_row - 1 + len(items)) % len(items)
        elif key == ord('\n'):
            logging.debug("Selected anime: %s", items[current_row])
            return items[current_row].get('link', 'No Link')
        elif key == ord('q'):
            logging.debug("Exiting menu")
            break

    return None


def konami_code_activated():
    logging.debug("Konami Code activated!")
    curses.endwin()
    webbrowser.open('https://www.youtube.com/watch?v=PDJLvF1dUek')
