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

from aniworld.common import (
    clear_screen,
    fetch_url_content,
    display_ascii_art,
    show_messagebox,
    random_user_agent,
)
from aniworld.models import AnimeSeries, Season, Episode
from aniworld.database.repositories import AnimeSeriesRepository, SeasonRepository, EpisodeRepository

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
                save_anime_data_from_html(html_content, url, slug)
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
                    save_anime_data_from_html(html_content, link, slug)
                except Exception as e:
                    logging.error(f"Fehler beim Speichern der Anime-Daten in der Datenbank: {e}")
            
            return slug
    except ValueError:
        logging.debug("ValueError encountered while fetching link")
    return None


def save_anime_data_from_html(
    soup: BeautifulSoup, anime_link: str, session: Optional[Session] = None
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
    should_close_session = False
    if session is None:
        from aniworld.database import SessionLocal

        session = SessionLocal()
        should_close_session = True

    soup_content = soup.prettify()
    if "Wartungsarbeiten" in soup_content or "Wir aktualisieren" in soup_content:
        module_log.error(f"Wartungsarbeiten oder Update der Seite: {anime_link}")
        return None

    anime_data = {}

    # Extract anime title
    anime_title_element = soup.select_one("h1.seriesCoverMainTitle")
    if anime_title_element:
        anime_title = anime_title_element.text.strip()
        anime_data["title"] = anime_title
    else:
        module_log.debug(f"Kein Anime-Titel gefunden in: {anime_link}")
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
    
    anime_data["cover_image"] = cover_image
    
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
        season_data = {"season_id": season_id, "episodes": []}
        
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
                
            episode_data = {
                "episode_id": episode_id,
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
        return None

    # Speichere die Daten in der Datenbank
    try:
        # 1. Speichere oder aktualisiere den Anime
        anime_repo = AnimeSeriesRepository(session)
        anime = anime_repo.find_by_url(anime_link)

        if anime is None:
            anime = AnimeSeries(
                title=anime_data["title"],
                url=anime_link,
                description=anime_data["description"],
                cover_image=anime_data["cover_image"],
                genres=",".join(anime_data["genres"]) if anime_data["genres"] else None,
            )
            anime_repo.save(anime)
        else:
            # Aktualisieren der bestehenden Anime-Daten
            anime.title = anime_data["title"]
            anime.description = anime_data["description"]
            anime.cover_image = anime_data["cover_image"]
            anime.genres = ",".join(anime_data["genres"]) if anime_data["genres"] else None
            anime.updated_at = datetime.now()
            anime_repo.update(anime)

        # 2. Speichere oder aktualisiere die Staffeln
        season_repo = SeasonRepository(session)
        for season_data in anime_data["seasons"]:
            season_id = season_data["season_id"]
            season = season_repo.find_by_anime_and_season_id(anime.id, season_id)

            if season is None:
                season = Season(
                    anime_id=anime.id,
                    season_id=season_id,
                )
                season_repo.save(season)

            # 3. Speichere oder aktualisiere die Episoden
            episode_repo = EpisodeRepository(session)
            for episode_data in season_data["episodes"]:
                episode_id = episode_data["episode_id"]
                episode = episode_repo.find_by_season_and_episode_id(
                    season.id, episode_id
                )

                if episode is None:
                    episode = Episode(
                        season_id=season.id,
                        episode_id=episode_id,
                        title=episode_data["title"],
                        url=episode_data["url"],
                    )
                    episode_repo.save(episode)
                else:
                    # Aktualisiere den Episodentitel, wenn ein besserer gefunden wurde
                    if episode_data["title"] != f"Staffel {season_id} Episode {episode_id}":
                        episode.title = episode_data["title"]
                        episode.updated_at = datetime.now()
                        episode_repo.update(episode)

        return anime

    except Exception as e:
        module_log.error(f"Fehler beim Speichern der Anime-Daten: {e}")
        traceback.print_exc()
        if should_close_session:
            session.rollback()
        return None
    finally:
        if should_close_session:
            session.close()


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
                            # Anime-Daten aus HTML extrahieren und in Datenbank speichern
                            anime_id = save_anime_data_from_html(html_content, anime_link, anime_link.split('/')[-1])
                            logging.info(f"Anime '{anime_item.get('name', 'Unbekannt')}' in Datenbank gespeichert mit ID: {anime_id}")
                except Exception as e:
                    logging.error(f"Fehler beim Speichern des Anime {anime_item.get('name', 'Unbekannt')}: {e}")

        if len(json_data) == 1:
            logging.debug("Only one anime found: %s", json_data[0])
            return json_data[0].get('link', 'No Link Found')

        selected_slug = curses.wrapper(display_menu, json_data)
        logging.debug("Found matching slug: %s", selected_slug)
        return selected_slug


def fetch_anime_json(url: str):
    try:
        if os.getenv("USE_PLAYWRIGHT"):
            page_content = html.unescape(fetch_url_content(url).decode('utf-8'))
            soup = BeautifulSoup(page_content, 'html.parser')
            json_data = soup.find('pre').text
        else:
            json_data = html.unescape(fetch_url_content(url).decode('utf-8'))

        decoded_data = loads(json_data)
        if isinstance(decoded_data, list) and decoded_data:
            return decoded_data
    except (AttributeError, JSONDecodeError):
        logging.debug("Error fetching or decoding the anime data.")
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
