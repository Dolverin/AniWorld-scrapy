import html
import logging
import os
import webbrowser
import re

from typing import List, Dict, Optional, Tuple
from json import loads
from json.decoder import JSONDecodeError
from urllib.parse import quote

import curses
from bs4 import BeautifulSoup


from aniworld.common import (
    clear_screen,
    fetch_url_content,
    display_ascii_art,
    show_messagebox
)

# Datenbankintegration (optional für Systeme ohne Datenbank)
HAS_DATABASE = False

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


def save_anime_data_from_html(html_content: str, url: str, slug: str) -> Optional[int]:
    """
    Extrahiert Anime-Daten aus HTML-Inhalt und speichert sie in der Datenbank.
    
    Args:
        html_content: Der HTML-Inhalt der Anime-Seite
        url: Die URL der Anime-Seite
        slug: Der Slug des Anime
        
    Returns:
        ID des gespeicherten Anime oder None bei Fehler
    """
    if not HAS_DATABASE:
        print("Datenbank nicht verfügbar - HAS_DATABASE ist False")
        return None
        
    try:
        print(f"Starte Extraktion und Speicherung für Anime: {slug}")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extrahiere Titel
        title_elem = soup.find('h1', class_='series-title')
        title = title_elem.text.strip() if title_elem else slug.replace('-', ' ').title()
        print(f"Extrahierter Titel: {title}")
        
        # Extrahiere Beschreibung
        description_elem = soup.find('div', class_='series-description')
        description = description_elem.text.strip() if description_elem else None
        
        # Extrahiere Cover-URL
        cover_elem = soup.find('div', class_='series-cover')
        cover_url = None
        if cover_elem:
            img = cover_elem.find('img')
            if img and 'src' in img.attrs:
                cover_url = img['src']
                if not cover_url.startswith('http'):
                    cover_url = f"https://aniworld.to{cover_url}"
        
        # Extrahiere zusätzliche Metadaten
        meta_data = {}
        info_box = soup.find('div', class_='series-infos')
        if info_box:
            for div in info_box.find_all('div', class_='series-info'):
                label = div.find('div', class_='series-info-header')
                value = div.find('div', class_='series-info-content')
                if label and value:
                    key = label.text.strip().lower().replace(':', '').replace(' ', '_')
                    meta_data[key] = value.text.strip()
        
        # Stelle Anime-Daten zusammen
        anime_data = {
            'title': title,
            'description': description,
            'url': url,
            'cover_url': cover_url,
            'status': meta_data.get('status'),
            'year': meta_data.get('erscheinungsjahr'),
            'studio': meta_data.get('studio'),
            'original_title': meta_data.get('originaltitel')
        }
        
        # Extrahiere Staffeln und Episoden, wenn vorhanden
        seasons_container = soup.find('div', class_='seasons-wrapper')
        if seasons_container:
            seasons = []
            for season_elem in seasons_container.find_all('div', class_='season'):
                season_title_elem = season_elem.find('h3')
                season_title = season_title_elem.text.strip() if season_title_elem else None
                season_number_match = re.search(r'Staffel (\d+)', season_title) if season_title else None
                season_number = int(season_number_match.group(1)) if season_number_match else 0
                
                season_data = {
                    'number': season_number,
                    'title': season_title,
                    'episodes': []
                }
                
                episode_list = season_elem.find('div', class_='episodes')
                if episode_list:
                    for episode_elem in episode_list.find_all('a'):
                        episode_url = episode_elem.get('href')
                        if episode_url and not episode_url.startswith('http'):
                            episode_url = f"https://aniworld.to{episode_url}"
                            
                        episode_title = episode_elem.text.strip() if episode_elem else None
                        episode_number_match = re.search(r'Episode (\d+)', episode_title) if episode_title else None
                        episode_number = int(episode_number_match.group(1)) if episode_number_match else 0
                        
                        season_data['episodes'].append({
                            'number': episode_number,
                            'title': episode_title,
                            'url': episode_url
                        })
                
                seasons.append(season_data)
            
            anime_data['seasons'] = seasons
        
        # Speichere in der Datenbank
        print("Rufe get_pipeline() auf...")
        pipeline = get_pipeline()
        print(f"Pipeline-Objekt: {pipeline}")
        print("Speichere Anime-Daten in Datenbank...")
        result = pipeline.process_anime(anime_data)
        print(f"Ergebnis der Speicherung: {result}")
        return result
    except Exception as e:
        print(f"KRITISCHER FEHLER bei Anime-Speicherung: {str(e)}")
        import traceback
        traceback.print_exc()
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
