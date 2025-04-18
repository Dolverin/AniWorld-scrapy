#!/usr/bin/env python
# encoding: utf-8

import argparse
import os
import sys
import re
import logging
import subprocess
import platform
import threading
import random
import signal
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed

import npyscreen

from aniworld.search import search_anime
from aniworld import execute, globals as aniworld_globals
from aniworld.common import (
    clear_screen,
    clean_up_leftovers,
    get_season_data,
    set_terminal_size,
    get_version,
    get_language_code,
    is_tail_running,
    get_season_and_episode_numbers,
    setup_anime4k,
    is_version_outdated,
    read_episode_file,
    check_package_installation,
    self_uninstall,
    update_component,
    get_anime_season_title,
    open_terminal_with_command,
    get_random_anime,
    show_messagebox,
    check_internet_connection,
    adventure,
    get_description,
    get_description_with_id
)
from aniworld.extractors import (
    nhentai,
    streamkiste,
    jav,
    hanime
)

# Import für die Datenbankintegration
try:
    from aniworld.database.integration import DatabaseIntegration
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False

from aniworld.globals import DEFAULT_DOWNLOAD_PATH


def format_anime_title(anime_slug):
    logging.debug("Formatting anime title for slug: %s", anime_slug)
    try:
        formatted_title = anime_slug.replace("-", " ").title()
        logging.debug("Formatted title: %s", formatted_title)
        return formatted_title
    except AttributeError:
        logging.debug("AttributeError encountered in format_anime_title")
        sys.exit()


class CustomTheme(npyscreen.ThemeManager):
    default_colors = {
        'DEFAULT': 'WHITE_BLACK',
        'FORMDEFAULT': 'MAGENTA_BLACK',  # Form border
        'NO_EDIT': 'BLUE_BLACK',
        'STANDOUT': 'CYAN_BLACK',
        'CURSOR': 'WHITE_BLACK',  # Text (focused)
        'CURSOR_INVERSE': 'BLACK_WHITE',
        'LABEL': 'CYAN_BLACK',  # Form labels
        'LABELBOLD': 'CYAN_BLACK',  # Form labels (focused)
        'CONTROL': 'GREEN_BLACK',  # Items in form
        'IMPORTANT': 'GREEN_BLACK',
        'SAFE': 'GREEN_BLACK',
        'WARNING': 'YELLOW_BLACK',
        'DANGER': 'RED_BLACK',
        'CRITICAL': 'BLACK_RED',
        'GOOD': 'GREEN_BLACK',
        'GOODHL': 'GREEN_BLACK',
        'VERYGOOD': 'BLACK_GREEN',
        'CAUTION': 'YELLOW_BLACK',
        'CAUTIONHL': 'BLACK_YELLOW',
    }


# pylint: disable=too-many-ancestors, too-many-instance-attributes
class EpisodeForm(npyscreen.ActionForm):
    def create(self):
        logging.debug("Creating EpisodeForm")
        try:
            anime_slug = self.parentApp.anime_slug
            if not anime_slug:
                raise ValueError("Anime-Slug ist nicht gesetzt.")
                
            logging.debug(f"EpisodeForm: Verarbeite Anime-Slug: {anime_slug}")

            self.season_episodes = []
            try:
                self.season_episodes = get_season_data(anime_slug)
                logging.debug(f"Gefundene Staffelepisoden für {anime_slug}: {len(self.season_episodes)}")
            except Exception as e:
                logging.error(f"Fehler beim Laden der Staffeldaten für {anime_slug}: {e}", exc_info=True)
                npyscreen.notify_confirm(f"Fehler beim Laden der Staffeldaten: {e}", "Fehler")
                self.season_episodes = [] # Fallback: Leere Liste, um Abstürze zu vermeiden

            if not self.season_episodes:
                logging.warning(f"Keine Staffel- oder Episodendaten für {anime_slug} gefunden oder geladen.")
                npyscreen.notify_confirm(
                    "Keine Episoden für diesen Anime gefunden.",
                    "Keine Episoden"
                )
                self.editing = False
                self.parentApp.switchFormPrevious()
                return

            # Umfassender try-except-Block für den gesamten Erstellungsprozess der Formularelemente
            try:
                season_titles = {}
                try:
                    # Sammle eindeutige Staffeltitel
                    unique_seasons = set()
                    for episode_url in self.season_episodes:
                        season_match = re.search(r'staffel-(\d+)', episode_url)
                        if season_match:
                            season_num = int(season_match.group(1))
                            unique_seasons.add(season_num)

                    for season_num in unique_seasons:
                        try:
                            season_titles[season_num] = get_anime_season_title(anime_slug, season_num)
                        except Exception as e:
                            logging.error(f"Fehler beim Abrufen des Titels für Staffel {season_num}: {e}", exc_info=True)
                            season_titles[season_num] = f"Staffel {season_num}"
                except Exception as e:
                    logging.error(f"Fehler beim Abrufen der Staffeltitel für {anime_slug}: {e}", exc_info=True)
                    season_titles = {} # Fallback: Leeres Dictionary, um Abstürze zu vermeiden

                episode_urls_by_season = {}
                try:
                    for episode_url in self.season_episodes:
                        season_match = re.search(r'staffel-(\d+)', episode_url)
                        if season_match:
                            season_num = int(season_match.group(1))
                            if season_num not in episode_urls_by_season:
                                episode_urls_by_season[season_num] = []
                            episode_urls_by_season[season_num].append(episode_url)
                        else:
                            # Filme oder Specials ohne Staffelnummer
                            if 0 not in episode_urls_by_season:
                                episode_urls_by_season[0] = []
                            episode_urls_by_season[0].append(episode_url)
                except Exception as e:
                    logging.error(f"Fehler beim Gruppieren der Episoden-URLs nach Staffeln für {anime_slug}: {e}", exc_info=True)
                    # Fallback: Falls die Gruppierung fehlschlägt, erstelle eine generische Gruppierung
                    episode_urls_by_season = {1: self.season_episodes}

                # Wenn immer noch keine Episoden nach Staffeln gruppiert sind, erstelle einen Notfall-Fallback
                if not episode_urls_by_season:
                    logging.warning("Keine Episoden nach Staffeln gruppiert. Erstelle Notfall-Fallback.")
                    episode_urls_by_season = {1: self.season_episodes}

                season_list = []
                try:
                    # Erstelle eine sortierte Liste von Staffeln
                    sorted_seasons = sorted(episode_urls_by_season.keys())
                    for season_num in sorted_seasons:
                        season_title = season_titles.get(season_num, f"Staffel {season_num}")
                        episodes_for_season = episode_urls_by_season[season_num]
                        season_list.append(f"{season_title} ({len(episodes_for_season)} Episoden)")
                except Exception as e:
                    logging.error(f"Fehler beim Erstellen der Staffelliste für die Anzeige für {anime_slug}: {e}", exc_info=True)
                    season_list = ["Fehler beim Laden der Staffelliste"] # Fallback: Fehlermeldung, um Abstürze zu vermeiden

                # Sicherstellen, dass die Liste nicht leer ist, um Abstürze zu vermeiden
                if not season_list:
                    logging.warning(f"Keine Staffeln zum Anzeigen für {anime_slug} gefunden. Erstelle Fallback-Eintrag.")
                    season_list = [f"Alle Episoden ({len(self.season_episodes)} Stück)"]
                    episode_urls_by_season = {0: self.season_episodes}

                # Erstelle die UI-Elemente
                self.add(npyscreen.FixedText,
                        value=f"Anime: {format_anime_title(anime_slug)}", editable=False)
                self.season_selector = self.add(
                    npyscreen.TitleSelectOne,
                    max_height=min(12, len(season_list)),
                    value=[0],
                    name="Staffel auswählen:",
                    values=season_list,
                    scroll_exit=True,
                )

                # Sichere Initialisierung der Episode-Liste
                initial_episodes = []
                selected_season_idx = 0  # Standardmäßig wählen wir Staffel 1
                if season_list and selected_season_idx < len(sorted_seasons):
                    selected_season = sorted_seasons[selected_season_idx]
                    initial_episodes = episode_urls_by_season.get(selected_season, [])

                self.episode_selector = self.add(
                    npyscreen.TitleMultiSelect,
                    max_height=min(12, len(initial_episodes) if initial_episodes else 1),
                    value=[],
                    name="Episoden auswählen:",
                    values=self._format_episode_list(initial_episodes) if initial_episodes else ["Keine Episoden gefunden"],
                    scroll_exit=True,
                )

                # Speichere die Daten für spätere Verwendung und Event-Handling
                self.episode_urls_by_season = episode_urls_by_season
                self.sorted_seasons = sorted_seasons
                
                # Füge den Rest der UI-Elemente hinzu
                self._setup_remaining_ui_elements()
                
                # Richte Signal-Handling und Event-Handling ein
                self.setup_signal_handling()
                
                # Nachricht für erfolgreiche Formularerstellung
                logging.debug(f"EpisodeForm erfolgreich erstellt für {anime_slug}")
                
            except Exception as e:
                logging.error(f"Kritischer Fehler bei der Erstellung des Formulars für {anime_slug}: {e}", exc_info=True)
                npyscreen.notify_confirm(
                    f"Es ist ein kritischer Fehler aufgetreten: {str(e)}\n\nDie Anwendung kehrt zum Hauptmenü zurück.",
                    "Kritischer Fehler"
                )
                # Versuche, zum vorherigen Formular zurückzukehren
                try:
                    self.editing = False
                    self.parentApp.switchFormPrevious()
                except:
                    # Wenn alles andere fehlschlägt, beende die Anwendung sauber
                    self.parentApp.switchForm(None)
                return
                
        except Exception as outer_e:
            # Äußerste Fehlerbehandlung - sollte nur bei kritischen Fehlern erreicht werden
            logging.critical(f"Fataler Fehler in EpisodeForm.create(): {outer_e}", exc_info=True)
            try:
                npyscreen.notify_confirm(
                    "Ein schwerwiegender Fehler ist aufgetreten. Die Anwendung kehrt zum Hauptmenü zurück.",
                    "Fataler Fehler"
                )
                self.editing = False
                self.parentApp.switchFormPrevious()
            except:
                # Wenn alles andere fehlschlägt
                try:
                    self.parentApp.switchForm(None)
                except:
                    pass
            return

    def _format_episode_list(self, episode_urls):
        """Hilfsmethode zur Formatierung der Episodenliste"""
        try:
            episode_list = []
            for url in episode_urls:
                try:
                    season_number, episode_number = get_season_and_episode_numbers(url)
                    episode_list.append(f"Episode {episode_number}")
                except:
                    # Fallback für URLs ohne erkennbare Staffel/Episode
                    episode_list.append(f"Episode (URL: {url.split('/')[-1]})")
            return episode_list
        except Exception as e:
            logging.error(f"Fehler beim Formatieren der Episodenliste: {e}", exc_info=True)
            return ["Fehler beim Formatieren der Episodenliste"]
            
    def _setup_remaining_ui_elements(self):
        """Richtet die restlichen UI-Elemente ein"""
        try:
            # Ab hier den restlichen Code aus der create-Methode kopieren
            self.language_selector = self.add(
                npyscreen.TitleSelectOne,
                max_height=5,
                value=[0],
                name="Sprache auswählen:",
                values=["Deutsch", "Englisch", "Japanisch (mit Untertiteln)"],
                scroll_exit=True,
            )
            
            self.provider_selector = self.add(
                npyscreen.TitleSelectOne,
                max_height=3,
                value=[0],
                name="Anbieter auswählen:",
                values=["Vidoza", "Streamtape", "VOE", "Vidmoly", "SpeedFiles"],
                scroll_exit=True,
            )
            
            self.action_selector = self.add(
                npyscreen.TitleSelectOne,
                max_height=3,
                value=[0],
                name="Aktion auswählen:",
                values=['Play', 'Download'],
                scroll_exit=True,
            )
            
            # Sichere Standard-Download-Pfad verwenden
            DEFAULT_DOWNLOAD_PATH = os.path.expanduser("~/Downloads")
            try:
                from aniworld.globals import DEFAULT_DOWNLOAD_PATH as CONFIG_PATH
                if CONFIG_PATH:
                    DEFAULT_DOWNLOAD_PATH = CONFIG_PATH
            except:
                pass
                
            try:
                # Versuche das originale DownloadPathActionPrompted Widget zu verwenden
                self.download_path_input = self.add_widget(
                    DownloadPathActionPrompted(
                        name="Download Pfad:",
                        value=DEFAULT_DOWNLOAD_PATH,
                        labelColor="LABEL",
                    ),
                    rely=22,
                )
            except Exception as widget_error:
                # Fallback: Einfaches Textfeld verwenden
                logging.error(f"Fehler beim Erstellen des DownloadPathActionPrompted Widgets: {widget_error}")
                self.download_path_input = self.add(
                    npyscreen.TitleText,
                    name="Download Pfad:",
                    value=DEFAULT_DOWNLOAD_PATH
                )
                
            # Zusätzliche Elemente wie weitere Optionen, Status-Anzeigen usw. hinzufügen
            # Diese können je nach vorherigem Code variieren
            
        except Exception as e:
            logging.error(f"Fehler beim Einrichten der restlichen UI-Elemente: {e}", exc_info=True)
            # Ignorieren und weitermachen mit minimaler UI, damit die Anwendung nicht abstürzt

    def setup_signal_handling(self):
        def signal_handler(_signal_number, _frame):
            try:
                self.parentApp.switchForm(None)
            except AttributeError:
                pass
            self.cancel_timer()
            sys.exit()

        signal.signal(signal.SIGINT, signal_handler)
        logging.debug("Signal handler for SIGINT registered")

    def start_timer(self):
        self.timer = threading.Timer(  # pylint: disable=attribute-defined-outside-init
            random.randint(600, 900),
            self.delayed_message_box
        )
        self.timer.start()

    def cancel_timer(self):
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
            logging.debug("Timer canceled")

    def delayed_message_box(self):
        show_messagebox("Are you still there?", "Uhm...", "info")

    def update_directory_visibility(self):
        logging.debug("Updating directory visibility")
        selected_action = self.action_selector.get_selected_objects()
        logging.debug("Selected action: %s", selected_action)
        if selected_action and selected_action[0] == "Watch" or selected_action[0] == "Syncplay":
            self.directory_field.hidden = True
            self.aniskip_selector.hidden = False
            logging.debug("Directory field hidden, Aniskip selector shown")
        else:
            self.directory_field.hidden = False
            self.aniskip_selector.hidden = True
            logging.debug("Directory field shown, Aniskip selector hidden")
        self.display()

    def on_ok(self):
        logging.debug("EpisodeForm.on_ok called")
        try:
            selected_item = self.action_selector.value[0]
            selected_action = self.action_options[selected_item]
            selected_episodes = [url for _, url in
                                 self.episode_selector.get_selected_objects()]
            logging.debug("Selected episodes: %s", selected_episodes)

            language = "German Dub"
            if hasattr(self, 'language_selector'):
                language_value = self.language_selector.value[0]
                language = self.language_options[language_value]
            logging.debug("Selected language: %s", language)

            provider_selected = "StreamingProvider"
            if hasattr(self, 'provider_selector'):
                provider_value = self.provider_selector.value[0]
                provider_selected = self.provider_options[provider_value]
            logging.debug("Selected provider: %s", provider_selected)

            provider_validated = self.validate_provider(provider_selected)

            download_directory = ""
            if hasattr(self, 'directory_field'):
                download_directory = self.directory_field.value
            logging.debug("Selected download directory: %s", download_directory)

            download_directory_name = ""
            if hasattr(self, 'directory_field'):
                download_directory_name = self.directory_field.value
            logging.debug(
                "Selected download directory name: %s", download_directory_name
            )

            if language == "Japanese Dub":
                lang_code = "jap"
            elif language == "English Sub":
                lang_code = "en"
            elif language == "German Sub":
                lang_code = "ger-sub"
            else:
                lang_code = "ger"

            if platform.system() == "Windows":
                lang_code = self.get_language_code(language)

            logging.debug("Language code: %s", lang_code)

            if not selected_episodes:
                logging.debug("No episodes selected")
                self.parentApp.setNextForm(None)
                self.editing = False
                self.cancel_timer()
                return

            # Speichere die Anime-Auswahl in der Datenbank, wenn verfügbar
            anime_slug = self.parentApp.anime_slug
            if HAS_DATABASE:
                try:
                    from aniworld.database.integration import DatabaseIntegration
                    db = DatabaseIntegration()
                    
                    # Prüfe, ob der Anime vorhanden ist, wenn nicht, füge ihn hinzu
                    anime = db.get_anime_by_slug(anime_slug)
                    if not anime:
                        # Wir haben keinen vollständigen Anime, aber zumindest den Slug und Titel
                        anime_title = format_anime_title(anime_slug)
                        db.save_minimal_anime(slug=anime_slug, title=anime_title)
                        logging.info(f"Minimaler Anime-Eintrag für '{anime_title}' gespeichert")
                except Exception as e:
                    logging.error(f"Fehler bei der Datenbankoperation für Anime '{anime_slug}': {e}")
                    print(f"Datenbankfehler: {e}")
                    
            self.parentApp.setNextForm(None)
            self.editing = False
            self.cancel_timer()

            # Check if Streamkiste is selected
            if provider_validated == "Streamkiste":
                streamkiste.execute_with_params(
                    selected_action,
                    selected_episodes,
                    download_directory,
                    download_directory_name
                )
            # Check if NHentai is selected
            elif provider_validated == "NHentai":
                if len(selected_episodes) != 1:
                    npyscreen.notify_confirm(
                        "Please select just one episode for NHentai",
                        "Info"
                    )
                else:
                    nhentai.execute_with_params(
                        selected_action,
                        selected_episodes,
                        download_directory,
                        download_directory_name
                    )
            # Check if JAV is selected
            elif provider_validated == "JAV":
                if len(selected_episodes) != 1:
                    npyscreen.notify_confirm(
                        "Please select just one episode for JAV",
                        "Info"
                    )
                else:
                    jav.execute_with_params(
                        selected_action,
                        selected_episodes,
                        download_directory,
                        download_directory_name
                    )
            # Check if Hanime is selected
            elif provider_validated == "Hanime":
                if len(selected_episodes) != 1:
                    npyscreen.notify_confirm(
                        "Please select just one episode for Hanime",
                        "Info"
                    )
                else:
                    hanime.execute_with_params(
                        selected_action,
                        selected_episodes,
                        download_directory,
                        download_directory_name
                    )
            # Default - execute with parameters
            else:
                execute.execute_with_params(
                    selected_action,
                    selected_episodes,
                    download_directory,
                    download_directory_name,
                    lang_code
                )
        except Exception as e:
            logging.error(f"Fehler in EpisodeForm.on_ok: {e}")
            npyscreen.notify_confirm(
                f"Ein Fehler ist aufgetreten: {str(e)}\n\nDie Anwendung wird fortgesetzt.",
                "Fehler"
            )
            # Verhindere, dass die Anwendung beendet wird
            self.editing = True
            return

    def get_language_code(self, language):
        logging.debug("Getting language code for: %s", language)
        return {
            'German Dub': "1",
            'English Sub': "2",
            'German Sub': "3"
        }.get(language, "")

    def validate_provider(self, provider_selected):
        logging.debug("Validating provider: %s", provider_selected)
        valid_providers = ["Vidoza", "Streamtape", "VOE", "Vidmoly", "SpeedFiles"]
        while provider_selected[0] not in valid_providers:
            logging.debug("Invalid provider selected, falling back to Vidoza")
            npyscreen.notify_confirm(
                "Doodstream is currently broken.\nFalling back to Vidoza.",
                title="Provider Error"
            )
            self.provider_selector.value = 0
            provider_selected = ["Vidoza"]
        return provider_selected[0]

    def on_cancel(self):
        logging.debug("Cancel button pressed")
        self.cancel_timer()
        self.parentApp.setNextForm(None)

    def go_to_second_form(self):
        self.parentApp.switchForm("SECOND")


# pylint: disable=R0901
class SecondForm(npyscreen.ActionFormV2):
    def create(self):
        anime_slug = self.parentApp.anime_slug
        anime_title = format_anime_title(anime_slug)

        text_content1 = get_description(anime_slug)
        text_content2 = get_description_with_id(anime_title, 1)

        wrapped_text1 = "\n".join(textwrap.wrap(text_content1, width=100))
        wrapped_text2 = "\n".join(textwrap.wrap(text_content2, width=100))

        text_content = f"{wrapped_text1}\n\n{wrapped_text2}"

        self.expandable_text = self.add(
            npyscreen.MultiLineEdit,
            value=text_content,
            max_height=None,
            editable=False
        )

    def on_ok(self):
        self.parentApp.switchForm("MAIN")

    def on_cancel(self):
        self.parentApp.switchForm("MAIN")


class AnimeApp(npyscreen.NPSAppManaged):
    def __init__(self, anime_slug):
        logging.debug("Initializing AnimeApp with slug: %s", anime_slug)
        super().__init__()
        self.anime_slug = anime_slug

    def onStart(self):
        logging.debug("Starting AnimeApp")
        npyscreen.setTheme(CustomTheme)
        version = get_version()
        update_notice = " (Update Available)" if is_version_outdated() else ""
        name = f"AniWorld-Downloader{version}{update_notice}"
        self.addForm(
            "MAIN", EpisodeForm,
            name=name
        )
        self.addForm("SECOND", SecondForm, name="Description")


# pylint: disable=R0912, R0915
def parse_arguments():
    logging.debug("Parsing command line arguments")

    parser = argparse.ArgumentParser(
        description="Parse optional command line arguments."
    )

    # General options
    general_group = parser.add_argument_group('General Options')
    general_group.add_argument(
        '-v', '--version',
        action='store_true',
        help='Print version info'
    )
    general_group.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    general_group.add_argument(
        '-u', '--uninstall',
        action='store_true',
        help='Self uninstall'
    )
    general_group.add_argument(
        '-U', '--update',
        type=str,
        choices=['mpv', 'yt-dlp', 'syncplay', 'all'],
        help='Update mpv, yt-dlp, syncplay, or all.'
    )

    # Search options
    search_group = parser.add_argument_group('Search Options')
    search_group.add_argument(
        '-s', '--slug',
        type=str,
        help='Search query - E.g. demon-slayer-kimetsu-no-yaiba'
    )
    search_group.add_argument(
        '-l', '--link',
        type=str,
        help='Search query - E.g. https://aniworld.to/anime/stream/demon-slayer-kimetsu-no-yaiba'
    )
    search_group.add_argument(
        '-q', '--query',
        type=str,
        help='Search query input - E.g. demon'
    )

    # Database options (Neue Optionsgruppe für Datenbankbefehle)
    if HAS_DATABASE:
        db_group = parser.add_argument_group('Database Options')
        db_group.add_argument(
            '--db-list-anime',
            action='store_true',
            help='Liste alle Anime in der Datenbank auf'
        )
        db_group.add_argument(
            '--db-anime-info',
            type=str,
            help='Zeige detaillierte Informationen zu einem Anime (ID oder URL)'
        )
        db_group.add_argument(
            '--db-list-downloads',
            action='store_true',
            help='Liste alle Downloads auf'
        )
        db_group.add_argument(
            '--db-download-status',
            type=int,
            help='Zeige Status eines Downloads anhand seiner ID'
        )
        db_group.add_argument(
            '--db-stats',
            action='store_true',
            help='Zeige Datenbankstatistiken'
        )

    # Episode options
    episode_group = parser.add_argument_group('Episode Options')
    episode_group.add_argument(
        '-e', '--episode',
        type=str,
        nargs='+',
        help='List of episode URLs'
    )
    episode_group.add_argument(
        '-f', '--episode-file',
        type=str,
        help='File path containing a list of episode URLs'
    )
    episode_group.add_argument(
        '-lf', '--episode-local',
        action='store_true',
        help='NOT IMPLEMENTED YET - Use local episode files instead of URLs'
    )

    # Action options
    action_group = parser.add_argument_group('Action Options')
    action_group.add_argument(
        '-a', '--action',
        type=str,
        choices=['Watch', 'Download', 'Syncplay'],
        default=aniworld_globals.DEFAULT_ACTION,
        help='Action to perform'
    )
    action_group.add_argument(
        '-o', '--output',
        type=str,
        help='Download directory E.g. /Users/phoenixthrush/Downloads',
        default=DEFAULT_DOWNLOAD_PATH
    )
    action_group.add_argument(
        '-O', '--output-directory',
        type=str,
        help=(
            'Final download directory, e.g., ExampleDirectory. '
            'Defaults to anime name if not specified.'
        )
    )
    action_group.add_argument(
        '-L', '--language',
        type=str,
        choices=['German Dub', 'English Sub', 'German Sub'],
        default=aniworld_globals.DEFAULT_LANGUAGE,
        help='Language choice'
    )
    action_group.add_argument(
        '-p', '--provider',
        type=str,
        choices=['Vidoza', 'Streamtape', 'VOE',
                 'Doodstream', 'Vidmoly', 'Doodstream', "SpeedFiles"],
        help='Provider choice'
    )

    # Anime4K options
    anime4k_group = parser.add_argument_group('Anime4K Options')
    anime4k_group.add_argument(
        '-A', '--anime4k',
        type=str,
        choices=['High', 'Low', 'Remove'],
        help=(
            'Set Anime4K optimised mode (High, e.g., GTX 1080, RTX 2070, RTX 3060, '
            'RX 590, Vega 56, 5700XT, 6600XT; Low, e.g., GTX 980, GTX 1060, RX 570, '
            'or Remove).'
        )
    )

    # Syncplay options
    syncplay_group = parser.add_argument_group('Syncplay Options')
    syncplay_group.add_argument(
        '-sH', '--syncplay-hostname',
        type=str,
        help='Set syncplay hostname'
    )
    syncplay_group.add_argument(
        '-sU', '--syncplay-username',
        type=str,
        help='Set syncplay username'
    )
    syncplay_group.add_argument(
        '-sR', '--syncplay-room',
        type=str,
        help='Set syncplay room'
    )
    syncplay_group.add_argument(
        '-sP', '--syncplay-password',
        type=str,
        nargs='+',
        help='Set a syncplay room password'
    )

    # Miscellaneous options
    misc_group = parser.add_argument_group('Miscellaneous Options')
    misc_group.add_argument(
        '-k', '--aniskip',
        action='store_true',
        help='Skip intro and outro'
    )
    misc_group.add_argument(
        '-K', '--keep-watching',
        action='store_true',
        help='Continue watching'
    )
    misc_group.add_argument(
        '-r', '--random-anime',
        type=str,
        nargs='?',
        const="all",
        help='Select random anime (default genre is "all", Eg.: Drama)'
    )
    misc_group.add_argument(
        '-D', '--only-direct-link',
        action='store_true',
        help='Output direct link'
    )
    misc_group.add_argument(
        '-C', '--only-command',
        action='store_true',
        help='Output command'
    )
    misc_group.add_argument(
        '-x', '--proxy',
        type=str,
        help='Set HTTP Proxy - E.g. http://0.0.0.0:8080'
    )
    misc_group.add_argument(
        '-w', '--use-playwright',
        action='store_true',
        help='Bypass fetching with a headless browser using Playwright instead (EXPERIMENTAL!!!)'
    )

    args = parser.parse_args()

    if not args.provider:
        if args.action == "Download":
            args.provider = aniworld_globals.DEFAULT_PROVIDER
        else:
            args.provider = aniworld_globals.DEFAULT_PROVIDER_WATCH

    if args.version:
        update_status = " (Update Available)" if is_version_outdated() else ""
        divider = "-------------------" if is_version_outdated() else ""
        banner = fR"""
     ____________________________________{divider}
    < Installed aniworld {get_version()} via {check_package_installation()}{update_status}. >
     ------------------------------------{divider}
            \\   ^__^
             \\  (oo)\\_______
                (__)\\       )\\/\\
                    ||----w |
                    ||     ||
        """

        print(banner)
        sys.exit()

    if args.episode and args.episode_file:
        msg = "Cannot specify both --episode and --episode-file."
        logging.critical(msg)
        print(msg)
        sys.exit()

    if args.debug:
        os.environ['IS_DEBUG_MODE'] = '1'
        aniworld_globals.IS_DEBUG_MODE = True
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("============================================")
        logging.debug("Welcome to Aniworld!")
        logging.debug("============================================\n")
        logging.debug("Debug mode enabled")

        if platform.system() == "Darwin":
            if not is_tail_running():
                try:
                    subprocess.run(
                        [
                            "osascript",
                            "-e",
                            'tell application "Terminal" to do script "'
                            'trap exit SIGINT; '
                            'tail -f -n +1 $TMPDIR/aniworld.log" '
                            'activate'
                        ],
                        check=True
                    )
                    logging.debug("Started tailing the log file in a new Terminal window.")
                except subprocess.CalledProcessError as e:
                    logging.error("Failed to start tailing the log file: %s", e)
        elif platform.system() == "Windows":
            try:
                command = ('start cmd /c "powershell -NoExit -c Get-Content '
                           '-Wait \\"$env:TEMP\\aniworld.log\\""')
                subprocess.Popen(command, shell=True)  # pylint: disable=consider-using-with
                logging.debug("Started tailing the log file in a new Terminal window.")
            except subprocess.CalledProcessError as e:
                logging.error("Failed to start tailing the log file: %s", e)
        elif platform.system() == "Linux":
            open_terminal_with_command('tail -f -n +1 /tmp/aniworld.log')

    if args.uninstall:
        self_uninstall()

    if args.update:
        update_component(args.update)
        sys.exit()

    if args.proxy:
        os.environ['HTTP_PROXY'] = args.proxy
        os.environ['HTTPS_PROXY'] = args.proxy
        aniworld_globals.DEFAULT_PROXY = args.proxy
        logging.debug("Proxy set to: %s", args.proxy)

    if args.anime4k:
        setup_anime4k(args.anime4k)

    if args.syncplay_password:
        os.environ['SYNCPLAY_PASSWORD'] = args.syncplay_password[0]
        logging.debug("Syncplay password set.")

    if args.syncplay_hostname:
        os.environ['SYNCPLAY_HOSTNAME'] = args.syncplay_hostname
        logging.debug("Syncplay hostname set.")

    if args.syncplay_username:
        os.environ['SYNCPLAY_USERNAME'] = args.syncplay_username
        logging.debug("Syncplay username set.")

    if args.syncplay_room:
        os.environ['SYNCPLAY_ROOM'] = args.syncplay_room
        logging.debug("Syncplay room set.")

    if args.output_directory:
        os.environ['OUTPUT_DIRECTORY'] = args.output_directory
        logging.debug("Output directory set.")

    if args.use_playwright:
        os.environ['USE_PLAYWRIGHT'] = str(args.use_playwright)
        logging.debug("Playwright set.")

    if not args.slug and args.random_anime:
        args.slug = get_random_anime(args.random_anime)

    return args


def handle_query(args):
    logging.debug("Handling query with args: %s", args)
    if args.query and not args.episode:
        slug = search_anime(query=args.query)
        logging.debug("Found slug: %s", slug)
        season_data = get_season_data(anime_slug=slug)
        logging.debug("Season data: %s", season_data)
        episode_list = list(season_data)
        logging.debug("Episode list: %s", episode_list)

        user_input = input("Please enter the episode (e.g., S1E2): ")
        logging.debug("User input: %s", user_input)
        match = re.match(r"S(\d+)E(\d+)", user_input)
        if match:
            s = int(match.group(1))
            e = int(match.group(2))
            logging.debug("Parsed season: %d, episode: %d", s, e)

        args.episode = [f"https://aniworld.to/anime/stream/{slug}/staffel-{s}/episode-{e}"]
        logging.debug("Set episode URL: %s", args.episode)


def get_anime_title(args):
    logging.debug("Getting anime title from args: %s", args)
    if args.link:
        title = args.link.split('/')[-1]
        logging.debug("Anime title from link: %s", title)
        return title
    if args.slug:
        logging.debug("Anime title from slug: %s", args.slug)
        return args.slug
    if args.episode:
        title = args.episode[0].split('/')[5]
        logging.debug("Anime title from episode URL: %s", title)
        return title
    return None


def main():
    logging.debug("============================================")
    logging.debug("Welcome to Aniworld!")
    logging.debug("============================================\n")
    if not check_internet_connection():
        clear_screen()

        logging.disable(logging.CRITICAL)
        adventure()

        sys.exit()
    try:
        args = parse_arguments()
        logging.debug("Parsed arguments: %s", args)
        
        # Zuerst Datenbankbefehle prüfen
        if HAS_DATABASE and handle_database_commands(args):
            sys.exit(0)

        validate_link(args)
        handle_query(args)

        language = get_language_code(args.language)
        logging.debug("Language code: %s", language)

        if args.episode_file:
            animes = read_episode_file(args.episode_file)
            for slug, seasons in animes.items():
                if args.output == aniworld_globals.DEFAULT_DOWNLOAD_PATH:
                    args.output = os.path.join(args.output, slug.replace("-", " ").title())
                execute_with_params(args, seasons, slug, language, anime_slug=slug)
            sys.exit()

        anime_title = get_anime_title(args)
        logging.debug("Anime title: %s", anime_title)

        selected_episodes = get_selected_episodes(args, anime_title)

        logging.debug("Selected episodes: %s", selected_episodes)

        if args.episode:
            for episode_url in args.episode:
                slug = episode_url.split('/')[5]
                execute_with_params(args, selected_episodes, anime_title, language, anime_slug=slug)
            logging.debug("Execution complete. Exiting.")
            sys.exit()
    except KeyboardInterrupt:
        logging.debug("KeyboardInterrupt encountered. Exiting.")
        sys.exit()

    run_app_with_query(args)


def validate_link(args):
    if args.link:
        if args.link.count('/') == 5:
            logging.debug("Provided link format valid.")
        elif args.link.count('/') == 6 and args.link.endswith('/'):
            logging.debug("Provided link format valid.")
            args.link = args.link.rstrip('/')
        else:
            logging.debug("Provided link invalid.")
            args.link = None


def get_selected_episodes(args, anime_title):
    updated_list = None
    if args.keep_watching and args.episode:
        season_data = get_season_data(anime_slug=anime_title)
        logging.debug("Season data: %s", season_data)
        episode_list = list(season_data)
        logging.debug("Episode list: %s", episode_list)

        index = episode_list.index(args.episode[0])
        updated_list = episode_list[index:]
        logging.debug("Updated episode list: %s", updated_list)

    return updated_list if updated_list else args.episode


def check_other_extractors(episode_urls: list):
    logging.debug("Those are all urls: %s", episode_urls)

    jav_urls = []
    nhentai_urls = []
    streamkiste_urls = []
    hanime_urls = []
    remaining_urls = []

    for episode in episode_urls:
        if episode.startswith("https://jav.guru/"):
            jav_urls.append(episode)
        elif episode.startswith("https://nhentai.net/g/"):
            nhentai_urls.append(episode)
        elif episode.startswith("https://streamkiste.tv/movie/"):
            streamkiste_urls.append(episode)
        elif episode.startswith("https://hanime.tv/videos/hentai/"):
            hanime_urls.append(episode)
        else:
            remaining_urls.append(episode)

    logging.debug("Jav URLs: %s", jav_urls)
    logging.debug("Nhentai URLs: %s", nhentai_urls)
    logging.debug("Hanime URLs: %s", hanime_urls)
    logging.debug("Streamkiste URLs: %s", streamkiste_urls)

    for jav_url in jav_urls:
        logging.info("Processing JAV URL: %s", jav_url)
        jav(jav_url)

    for nhentai_url in nhentai_urls:
        logging.info("Processing Nhentai URL: %s", nhentai_url)
        nhentai(nhentai_url)

    for hanime_url in hanime_urls:
        logging.info("Processing hanime URL: %s", hanime_url)
        hanime(hanime_url)

    for streamkiste_url in streamkiste_urls:
        logging.info("Processing Streamkiste URL: %s", streamkiste_url)
        streamkiste(streamkiste_url)

    return remaining_urls


def execute_with_params(args, selected_episodes, anime_title, language, anime_slug):
    selected_episodes = check_other_extractors(selected_episodes)
    logging.debug("Aniworld episodes: %s", selected_episodes)

    params = {
        'selected_episodes': selected_episodes,
        'provider_selected': args.provider,
        'action_selected': args.action,
        'aniskip_selected': args.aniskip,
        'lang': language,
        'output_directory': args.output,
        'anime_title': anime_title.replace('-', ' ').title(),
        'anime_slug': anime_slug,
        'only_direct_link': args.only_direct_link,
        'only_command': args.only_command,
        'debug': args.debug
    }
    logging.debug("Executing with params: %s", params)
    execute(params=params)


def run_app_with_query(args):
    def run_app(query):
        logging.debug("Running app with query: %s", query)
        clear_screen()
        app = AnimeApp(query)
        app.run()

    try:
        try:
            logging.debug("Trying to resize Terminal.")
            set_terminal_size()
            run_app(search_anime(slug=args.slug, link=args.link))
        except npyscreen.wgwidget.NotEnoughSpaceForWidget:
            logging.debug("Not enough space for widget. Asking user to resize terminal.")
            clear_screen()
            print("Please increase your current terminal size.")
            logging.debug("Exiting due to terminal size.")
            sys.exit()
    except KeyboardInterrupt:
        logging.debug("KeyboardInterrupt encountered. Exiting.")
        sys.exit()


def handle_database_commands(args):
    """
    Verarbeitet die Datenbankkommandos aus den Argumenten
    
    Args:
        args: Die geparsten Argumente
        
    Returns:
        True, wenn ein Datenbankbefehl ausgeführt wurde, sonst False
    """
    if not HAS_DATABASE:
        return False
        
    try:
        db = DatabaseIntegration()
    except Exception as e:
        logging.error(f"Fehler beim Verbinden zur Datenbank: {e}")
        print(f"Datenbankfehler: {e}")
        return True
        
    # --db-list-anime: Liste aller Anime anzeigen
    if hasattr(args, 'db_list_anime') and args.db_list_anime:
        print("\n=== Anime in der Datenbank ===")
        try:
            animes = db.find_all_animes()
            if not animes:
                print("Keine Anime in der Datenbank gefunden.")
            else:
                print(f"Insgesamt {len(animes)} Anime gefunden:\n")
                for anime in animes:
                    status_symbol = "🔄" if anime.status == "laufend" else "✅"
                    print(f"ID: {anime.series_id} | {status_symbol} {anime.titel}")
                    if anime.original_titel:
                        print(f"    Original: {anime.original_titel}")
                    if anime.erscheinungsjahr:
                        print(f"    Jahr: {anime.erscheinungsjahr}")
                    print(f"    URL: {anime.aniworld_url}\n")
        except Exception as e:
            logging.error(f"Fehler beim Auflisten der Anime: {e}")
            print(f"Fehler: {e}")
        return True
        
    # --db-anime-info: Detaillierte Informationen zu einem Anime
    if hasattr(args, 'db_anime_info') and args.db_anime_info:
        anime_identifier = args.db_anime_info
        anime = None
        
        try:
            # Prüfen, ob es eine ID oder URL ist
            if anime_identifier.isdigit():
                # Nach ID suchen
                from aniworld.database.services import AnimeService
                service = AnimeService()
                anime = service.get_anime_by_id(int(anime_identifier))
            else:
                # Nach URL suchen
                anime = db.get_anime_by_url(anime_identifier)
                
            if not anime:
                print(f"Kein Anime mit Identifier '{anime_identifier}' gefunden.")
                return True
                
            print("\n=== Anime Details ===")
            print(f"Titel: {anime.titel}")
            if anime.original_titel:
                print(f"Originaltitel: {anime.original_titel}")
            if anime.beschreibung:
                print(f"\nBeschreibung: {anime.beschreibung}")
            print(f"\nStatus: {anime.status}")
            if anime.erscheinungsjahr:
                print(f"Erscheinungsjahr: {anime.erscheinungsjahr}")
            if anime.studio:
                print(f"Studio: {anime.studio}")
            if anime.regisseur:
                print(f"Regisseur: {anime.regisseur}")
            print(f"AniWorld URL: {anime.aniworld_url}")
            if anime.cover_url:
                print(f"Cover URL: {anime.cover_url}")
            if anime.aktualisiert_am:
                print(f"Letzte Aktualisierung: {anime.aktualisiert_am}")
                
            # Staffeln abrufen
            # Angenommen, es gibt eine Methode, um alle Staffeln eines Anime abzurufen
            # Die genaue Implementierung müsste angepasst werden
            try:
                from aniworld.database.services import AnimeService
                service = AnimeService()
                seasons = service.get_seasons_by_anime_id(anime.series_id)
                
                if seasons:
                    print(f"\nStaffeln ({len(seasons)}):")
                    for season in seasons:
                        print(f"  Staffel {season.staffel_nummer}: {season.titel or 'Ohne Titel'}")
                        
                        # Episoden für diese Staffel abrufen
                        episodes = service.get_episodes_by_season_id(season.season_id)
                        if episodes:
                            print(f"    Episoden ({len(episodes)}):")
                            for episode in episodes:
                                print(f"      Episode {episode.episode_nummer}: {episode.titel or 'Ohne Titel'}")
            except Exception as e:
                logging.error(f"Fehler beim Abrufen der Staffeln: {e}")
                
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Anime-Details: {e}")
            print(f"Fehler: {e}")
        return True
        
    # --db-stats: Datenbankstatistiken anzeigen
    if hasattr(args, 'db_stats') and args.db_stats:
        print("\n=== Datenbankstatistiken ===")
        try:
            # Diese Funktionen müssten noch implementiert werden
            from aniworld.database.services import StatisticsService
            stats = StatisticsService()
            
            anime_count = stats.count_animes()
            season_count = stats.count_seasons()
            episode_count = stats.count_episodes()
            download_count = stats.count_downloads()
            
            print(f"Gesamtzahl Anime: {anime_count}")
            print(f"Gesamtzahl Staffeln: {season_count}")
            print(f"Gesamtzahl Episoden: {episode_count}")
            print(f"Gesamtzahl Downloads: {download_count}")
            
            # Weitere Statistiken könnten hier angezeigt werden
            top_anime = stats.get_top_anime(limit=5)
            if top_anime:
                print("\nTop 5 Anime (nach Episodenanzahl):")
                for i, (anime, count) in enumerate(top_anime, 1):
                    print(f"{i}. {anime.titel} ({count} Episoden)")
                    
            recent_downloads = stats.get_recent_downloads(limit=5)
            if recent_downloads:
                print("\nLetzte 5 Downloads:")
                for dl in recent_downloads:
                    status_emoji = "✅" if dl.status == "abgeschlossen" else "🔄" if dl.status == "gestartet" else "❌"
                    print(f"{status_emoji} {dl.episode_titel} ({dl.provider}, {dl.sprache})")
                    
        except ImportError:
            print("StatisticsService nicht verfügbar. Funktionalität nicht implementiert.")
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Datenbankstatistiken: {e}")
            print(f"Fehler: {e}")
        return True
            
    return False


if __name__ == "__main__":
    main()
