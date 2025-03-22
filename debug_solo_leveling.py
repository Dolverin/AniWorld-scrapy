#!/usr/bin/env python
# encoding: utf-8

import logging
import sys
import traceback
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re

# Konfiguration des Loggers
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def fetch_url(url):
    """Abrufen des HTML-Inhalts einer URL"""
    logging.info(f"Rufe URL ab: {url}")
    try:
        req = Request(url)
        req.add_header('User-Agent', USER_AGENT)
        req.add_header('Accept-Language', 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7')
        req.add_header('Cache-Control', 'max-age=0')
        req.add_header('Sec-Fetch-Mode', 'navigate')
        req.add_header('Sec-Fetch-User', '?1')
        req.add_header('Sec-Fetch-Dest', 'document')

        with urlopen(req, timeout=30) as response:
            logging.info(f"Status Code: {response.getcode()}")
            html_content = response.read()
            return html_content
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der URL: {e}")
        logging.error(traceback.format_exc())
        return None

def analyze_html(html_content):
    """Analyse des HTML-Inhalts"""
    if not html_content:
        logging.error("Kein HTML-Inhalt zum Analysieren")
        return

    logging.info(f"HTML-Länge: {len(html_content)} Bytes")
    
    # BeautifulSoup-Objekt erstellen
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Speichern des HTML-Inhalts in einer Datei
    with open("debug_solo_leveling.html", "wb") as f:
        f.write(html_content)
    logging.info("HTML-Inhalt in debug_solo_leveling.html gespeichert")
    
    # Verschiedene Selektoren testen, um den Titel zu finden
    selectors = [
        "h1.seriesCoverMainTitle",
        "h1",
        ".seriesCoverMainTitle",
        ".title",
        ".animeTitle",
        "title",
        "meta[property='og:title']",
        ".headerTitle"
    ]
    
    logging.info("=== Teste verschiedene Selektoren ===")
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            logging.info(f"Selector '{selector}' ergab {len(elements)} Treffer:")
            for i, element in enumerate(elements):
                logging.info(f"  {i+1}. {element.text.strip() if hasattr(element, 'text') else element.get('content', '')} ({type(element).__name__})")
        else:
            logging.info(f"Selector '{selector}' ergab keine Treffer")
    
    # Nach der Meta-Description für alternative Informationen suchen
    meta_desc = soup.select_one("meta[name='description']")
    if meta_desc:
        logging.info(f"Meta-Description: {meta_desc.get('content', '')}")
    
    # Prüfen, ob wir ein Captcha oder eine Wartungsseite erhalten haben
    page_text = soup.get_text().lower()
    if "captcha" in page_text:
        logging.warning("Seite enthält möglicherweise ein Captcha")
    if "wartung" in page_text or "maintenance" in page_text:
        logging.warning("Seite ist möglicherweise in Wartung")
    
    # Ausgabe der ersten 500 Zeichen des HTML-Inhalts
    logging.info(f"HTML-Vorschau (erste 500 Zeichen):\n{html_content[:500]}")
    
    # Spezielle Suche nach allen h1-Tags
    h1_tags = soup.find_all("h1")
    logging.info(f"Anzahl h1-Tags: {len(h1_tags)}")
    for i, h1 in enumerate(h1_tags):
        logging.info(f"h1 #{i+1}: {h1.text.strip()}")
        logging.info(f"  Attribute: {h1.attrs}")
        logging.info(f"  HTML: {h1}")
    
    # Suche nach Elementen, die "Solo Leveling" enthalten könnten
    pattern = re.compile(r"solo\s*leveling", re.IGNORECASE)
    for element in soup.find_all(text=pattern):
        parent = element.parent
        logging.info(f"Gefundener Text mit 'Solo Leveling': {element}")
        logging.info(f"  Elternelement: {parent.name} mit Klassen: {parent.get('class', '')}")

def main():
    """Hauptfunktion"""
    url = "https://aniworld.to/anime/stream/solo-leveling"
    logging.info(f"Debug-Skript für: {url}")
    
    # HTML-Inhalt abrufen
    html_content = fetch_url(url)
    
    if html_content:
        # HTML analysieren
        analyze_html(html_content)
    else:
        logging.error("Konnte keinen HTML-Inhalt abrufen.")

if __name__ == "__main__":
    main() 