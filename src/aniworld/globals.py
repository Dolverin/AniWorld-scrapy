import os
import logging
import tempfile
import random
import sys

import colorlog

IS_DEBUG_MODE = os.getenv('IS_DEBUG_MODE', 'False').lower() in ('true', '1', 't', 'y', 'yes')
LOG_FILE_BASENAME = 'aniworld'
LOG_FILE_DIR = tempfile.gettempdir()

def get_log_file_path():
    for i in range(100):
        path = os.path.join(LOG_FILE_DIR, f"{LOG_FILE_BASENAME}-{i}.log")
        if not os.path.exists(path):
            return path
    raise RuntimeError("Could not find a writable log file.")

LOG_FILE_PATH = get_log_file_path()

DEFAULT_ACTION = "Download"     # E.g. Watch, Download, Syncplay
DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.expanduser('~'), 'Downloads')
DEFAULT_LANGUAGE = "German Sub" # German Dub, English Sub, German Sub
DEFAULT_PROVIDER = "VOE"        # Vidoza, Streamtape, VOE, Doodstream
DEFAULT_PROVIDER_WATCH = "Vidoza"
DEFAULT_ANISKIP = False
DEFAULT_KEEP_WATCHING = False
DEFAULT_ONLY_DIRECT_LINK = False
DEFAULT_ONLY_COMMAND = False
DEFAULT_PROXY = None
DEFAULT_USE_PLAYWRIGHT = False
DEFAULT_TERMINAL_SIZE = (90, 28)

log_colors = {
    'DEBUG': 'bold_blue',
    'INFO': 'bold_green',
    'WARNING': 'bold_yellow',
    'ERROR': 'bold_red',
    'CRITICAL': 'bold_purple'
}

if os.path.exists(LOG_FILE_PATH):
    os.remove(LOG_FILE_PATH)
file_handler = logging.FileHandler(LOG_FILE_PATH)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'))

console_handler = colorlog.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors=log_colors
))

logging.basicConfig(
    level=logging.DEBUG if IS_DEBUG_MODE else logging.INFO,
    handlers=[file_handler, console_handler]
)

logging.getLogger('urllib3').setLevel(logging.WARNING)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.3",

    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.3",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) "
    "Gecko/20100101 Firefox/130.",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.3",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.",

    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.",

    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.3",

    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.3",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3",

    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) SamsungBrowser/26.0 Chrome/122.0.0.0 Safari/537.3",

    "Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.",

    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Geck",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Config/91.2.1916.1",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 OPR/112.0.0.",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.3",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) "
    "Gecko/20100101 Firefox/128."
]

DEFAULT_USER_AGENT = random.choice(USER_AGENTS)

class ExitOnError(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            sys.exit(1)

exit_on_error_handler = ExitOnError()
logging.getLogger().addHandler(exit_on_error_handler)
