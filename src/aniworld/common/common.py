import glob
import platform
import os
import shutil
import sys
import shlex
import subprocess
import logging
from typing import List, Optional

from bs4 import BeautifulSoup
import requests

from aniworld import globals

def check_dependencies(dependencies: list) -> None:
    """
    Check if dependencies are available in PATH and handle platform-specific cases.

    Args:
        dependencies (list): List of dependency names.

    Returns:
        None

    Exits:
        Exits with error if any dependency is missing.
    """
    resolved_dependencies = []

    for dep in dependencies:
        if dep == "syncplay":
            if platform.system() == "Windows":
                resolved_dependencies.append("SyncplayConsole")
            else:
                resolved_dependencies.append("syncplay")
        else:
            resolved_dependencies.append(dep)

    logging.debug(f"Checking for {resolved_dependencies} in path.")
    missing = [dep for dep in resolved_dependencies if shutil.which(dep) is None]

    if missing:
        logging.critical(f"Missing dependencies: {', '.join(missing)} in path. Please install and try again.")
        sys.exit(1)


def fetch_url_content(url: str, proxy: Optional[str] = None, check: bool = True) -> Optional[bytes]:
    """
    Fetch content from a URL with optional proxy.

    Args:
        url (str): The URL to fetch.
        proxy (str, optional): Proxy URL (supports SOCKS and HTTP).
        check (bool, optional): If True, exits on failure. If False, returns None on failure.

    Returns:
        Optional[bytes]: Content of the URL or None if an error occurs and check is False.

    Exits:
        Exits with error if check is True and the request fails.
    """
    headers = {
        'User-Agent': (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/58.0.3029.110 Safari/537.3"
        )
    }

    proxies = {}
    if proxy:
        if proxy.startswith('socks'):
            proxies = {
                'http': proxy,
                'https': proxy
            }
        else:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'https://{proxy}'
            }
    else:
        proxies = {
            "http": os.getenv("HTTP_PROXY"),
            "https": os.getenv("HTTPS_PROXY"),
        }

    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        response.raise_for_status()

        if "Deine Anfrage wurde als Spam erkannt." in response.text:
            logging.critical("Your IP address is blacklisted. Please use a VPN, complete the captcha by opening the browser link, or try again later.")
            sys.exit(1)

        return response.content
    except requests.exceptions.RequestException as error:
        if check:
            logging.critical(f"Request to {url} failed: {error}")
            sys.exit(1)
        return None


def clear_screen() -> None:
    """
    Clear the terminal screen based on the operating system.
    """
    if not globals.IS_DEBUG_MODE:
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")


def clean_up_leftovers(directory: str) -> None:
    """
    Removes leftover files in the specified directory that match certain patterns.
    Also removes the directory if it becomes empty after cleanup.

    This method searches for files in the given directory that match the following patterns:
    - '*.part'
    - '*.ytdl'
    - '*.part-Frag*'

    Args:
        directory (str): The directory where leftover files are to be removed.

    Returns:
        None: This method does not return any value.
    """
    patterns: List[str] = ['*.part', '*.ytdl', '*.part-Frag*']

    leftover_files: List[str] = []
    for pattern in patterns:
        leftover_files.extend(glob.glob(os.path.join(directory, pattern)))

    for file_path in leftover_files:
        if not os.path.exists(directory):
            logging.warning(f"Directory {directory} no longer exists.")
            return

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.debug(f"Removed leftover file: {file_path}")
            except PermissionError:
                logging.warning(f"Permission denied when trying to remove file: {file_path}")
            except OSError as e:
                logging.warning(f"OS error occurred while removing file {file_path}: {e}")

    if os.path.exists(directory) and not os.listdir(directory):
        try:
            os.rmdir(directory)
            logging.debug(f"Removed empty directory: {directory}")
        except PermissionError:
            logging.warning(f"Permission denied when trying to remove directory: {directory}")
        except OSError as e:
            logging.warning(f"OS error occurred while removing directory {directory}: {e}")


def setup_aniskip() -> None:
    """
    Copy 'skip.lua', 'autostart.lua', and 'autoexit.lua'
    to the correct MPV scripts directory based on the OS.
    """
    script_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    skip_source_path = os.path.join(script_directory, 'aniskip', 'skip.lua')
    autostart_source_path = os.path.join(script_directory, 'aniskip', 'autostart.lua')
    autoexit_source_path = os.path.join(script_directory, 'aniskip', 'autoexit.lua')

    if os.name == 'nt':
        mpv_scripts_directory = os.path.join(
            os.environ.get('APPDATA', ''), 'mpv', 'scripts'
        )
    else:
        mpv_scripts_directory = os.path.expanduser('~/.config/mpv/scripts')

    logging.debug(f"Creating directory {mpv_scripts_directory}")
    os.makedirs(mpv_scripts_directory, exist_ok=True)

    skip_destination_path = os.path.join(mpv_scripts_directory, 'skip.lua')
    if not os.path.exists(skip_destination_path):
        logging.debug(f"Copying skip.lua to {mpv_scripts_directory}")
        shutil.copy(skip_source_path, skip_destination_path)

    autostart_destination_path = os.path.join(mpv_scripts_directory, 'autostart.lua')
    if not os.path.exists(autostart_destination_path):
        logging.debug(f"Copying autostart.lua to {mpv_scripts_directory}")
        shutil.copy(autostart_source_path, autostart_destination_path)

    autoexit_destination_path = os.path.join(mpv_scripts_directory, 'autoexit.lua')
    if not os.path.exists(autoexit_destination_path):
        logging.debug(f"Copying autoexit.lua to {mpv_scripts_directory}")
        shutil.copy(autoexit_source_path, autoexit_destination_path)


def execute_command(command: List[str], only_command: bool) -> None:
    """
    Execute a command or print it as a string based on the 'only_command' flag.

    Args:
        command: List of command arguments.
        only_command: If True, print the command; otherwise, execute it.
    """
    if only_command:
        print(' '.join(shlex.quote(arg) for arg in command))
    else:
        subprocess.run(command, check=True)


def raise_runtime_error(message: str) -> None:
    """
    Raises a RuntimeError with the provided message.

    Args:
        message (str): The error message to include in the exception.
    """
    raise RuntimeError(message)


def get_season_episodes(season_url):
    """
    Fetches episode URLs for a given season URL.

    Args:
        season_url (str): The URL of the season.

    Returns:
        List[str]: List of episode URLs.
    """
    season_url_old = season_url
    season_url = season_url[:-2]
    season_suffix = f"/staffel-{season_url_old.split('/')[-1]}"

    logging.debug(f"Fetching Episode URLs from Season {season_suffix}")
    
    season_html = fetch_url_content(season_url)
    if season_html is None:
        return []
    season_soup = BeautifulSoup(season_html, 'html.parser')
    episodes = season_soup.find_all('meta', itemprop='episodeNumber')
    episode_numbers = [int(episode['content']) for episode in episodes]
    highest_episode = max(episode_numbers, default=None)

    episode_urls = [
        f"{season_url}{season_suffix}/episode-{num}"
        for num in range(1, highest_episode + 1)
    ]

    return episode_urls

def get_season_data(anime_slug: str):
    """
    Fetches season data for a given anime slug.

    Args:
        anime_slug (str): The slug of the anime.

    Returns:
        Dict[int, List[str]]: Dictionary with season numbers as keys and lists of episode URLs as values.
    """
    BASE_URL_TEMPLATE = "https://aniworld.to/anime/stream/{anime}/"
    base_url = BASE_URL_TEMPLATE.format(anime=anime_slug)

    logging.debug(f"Fetching Base URL {base_url}")
    main_html = fetch_url_content(base_url)
    if main_html is None:
        logging.critical("Failed to retrieve main page.")
        sys.exit(1)

    soup = BeautifulSoup(main_html, 'html.parser')
    season_meta = soup.find('meta', itemprop='numberOfSeasons')
    number_of_seasons = int(season_meta['content']) if season_meta else 0

    if soup.find('a', title='Alle Filme'):
        number_of_seasons -= 1

    season_data = {}
    for i in range(1, number_of_seasons + 1):
        season_url = f"{base_url}{i}"
        season_data[i] = get_season_episodes(season_url)

    return season_data


def set_terminal_size(columns: int=90, lines:int=27):
    """
    Set the terminal size based on the operating system.

    Args:
        columns (int): Number of columns.
        lines (int): Number of lines.
    """
    system_name = platform.system()

    if system_name == 'Windows':
        os.system(f"mode con: cols={columns} lines={lines}")

    elif system_name in ['Linux', 'Darwin']:
        os.system(f"printf '\033[8;{lines};{columns}t'")

    else:
        raise NotImplementedError(f"Unsupported platform: {system_name}")


def ftoi(value: float) -> str:
    return str(int(value * 1000))
