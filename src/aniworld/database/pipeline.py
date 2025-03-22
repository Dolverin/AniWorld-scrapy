"""
Datenbankpipeline für die automatische Speicherung von gescrapten Daten
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

from src.aniworld.database.integration import DatabaseIntegration


class DatabasePipeline:
    """
    Pipeline-Klasse zum automatischen Speichern von gescrapten Anime-Daten in der Datenbank.
    
    Diese Klasse wird in den Scraping-Prozess integriert und speichert die 
    gesammelten Daten direkt in der Datenbank.
    """
    
    def __init__(self):
        """
        Initialisiert die Pipeline mit einer Datenbankverbindung.
        """
        self.logger = logging.getLogger('aniworld.db.pipeline')
        try:
            self.db = DatabaseIntegration()
            self.logger.info("Datenbankpipeline initialisiert")
            self._cache = {}  # Cache für bereits verarbeitete URLs
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren der Datenbankpipeline: {e}")
            self.db = None
    
    def process_anime(self, anime_data: Dict[str, Any]) -> Optional[int]:
        """
        Verarbeitet Anime-Daten und speichert sie in der Datenbank.
        
        Args:
            anime_data: Dictionary mit den gescrapten Daten des Anime
                        
        Returns:
            ID des gespeicherten Anime oder None bei Fehler
        """
        if self.db is None:
            self.logger.warning("Datenbankverbindung nicht verfügbar")
            return None
            
        url = anime_data.get('url')
        if not url:
            self.logger.warning("Keine URL in den Anime-Daten gefunden")
            return None
            
        # Prüfen, ob der Anime bereits im Cache ist
        if url in self._cache:
            self.logger.debug(f"Anime mit URL {url} bereits im Cache, überspringe Speicherung")
            return self._cache[url]
            
        # Prüfen, ob der Anime bereits in der Datenbank existiert
        existing_anime = self.db.get_anime_by_url(url)
        if existing_anime:
            self.logger.debug(f"Anime mit URL {url} bereits in der Datenbank, aktualisiere")
            self._cache[url] = existing_anime.series_id
        
        try:
            anime_id = self.db.save_anime_data(anime_data)
            if anime_id > 0:
                self.logger.info(f"Anime '{anime_data.get('title', 'Unbekannt')}' erfolgreich gespeichert mit ID {anime_id}")
                self._cache[url] = anime_id
                return anime_id
            else:
                self.logger.error(f"Fehler beim Speichern des Anime: {anime_data.get('title', 'Unbekannt')}")
                return None
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Anime-Daten: {e}")
            return None
    
    def process_episode(self, episode_data: Dict[str, Any]) -> Optional[int]:
        """
        Verarbeitet Episodendaten und speichert sie in der Datenbank.
        
        Args:
            episode_data: Dictionary mit den gescrapten Daten der Episode
            
        Returns:
            ID der gespeicherten Episode oder None bei Fehler
        """
        if self.db is None:
            self.logger.warning("Datenbankverbindung nicht verfügbar")
            return None
            
        url = episode_data.get('url')
        if not url:
            self.logger.warning("Keine URL in den Episodendaten gefunden")
            return None
            
        # Diese Funktion ist optional, da Episoden bereits durch save_anime_data gespeichert werden können
        # Sie könnte jedoch für bestimmte Anwendungsfälle nützlich sein
        try:
            # Prüfen, ob die Episode bereits existiert
            episode = self.db.get_episode_data(url)
            if episode:
                self.logger.debug(f"Episode mit URL {url} bereits in der Datenbank, überspringe")
                return episode.episode_id
                
            # Speichern der Episode würde hier implementiert, falls benötigt
            return None
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Episodendaten: {e}")
            return None
    
    def record_download(self, download_data: Dict[str, Any]) -> Optional[int]:
        """
        Zeichnet einen Download in der Datenbank auf.
        
        Args:
            download_data: Dictionary mit Download-Informationen wie URL, Provider, etc.
            
        Returns:
            ID des aufgezeichneten Downloads oder None bei Fehler
        """
        if self.db is None:
            self.logger.warning("Datenbankverbindung nicht verfügbar")
            return None
            
        try:
            episode_url = download_data.get('episode_url')
            provider = download_data.get('provider')
            sprache = download_data.get('sprache')
            zieldatei = download_data.get('zieldatei')
            
            if not episode_url or not provider or not sprache or not zieldatei:
                self.logger.warning("Unvollständige Download-Daten")
                return None
                
            download_id = self.db.record_download(
                episode_url=episode_url,
                provider=provider,
                sprache=sprache,
                zieldatei=zieldatei
            )
            
            if download_id > 0:
                self.logger.info(f"Download erfolgreich aufgezeichnet mit ID {download_id}")
                return download_id
            else:
                self.logger.error("Fehler beim Aufzeichnen des Downloads")
                return None
        except Exception as e:
            self.logger.error(f"Fehler beim Aufzeichnen des Downloads: {e}")
            return None
    
    def update_download_status(self, download_id: int, status: str) -> bool:
        """
        Aktualisiert den Status eines Downloads in der Datenbank.
        
        Args:
            download_id: ID des Downloads
            status: Neuer Status (z.B. 'abgeschlossen', 'fehlgeschlagen', 'abgebrochen')
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if self.db is None:
            self.logger.warning("Datenbankverbindung nicht verfügbar")
            return False
            
        try:
            result = self.db.update_download_status(download_id, status)
            if result:
                self.logger.info(f"Download-Status für ID {download_id} auf '{status}' aktualisiert")
                return True
            else:
                self.logger.warning(f"Download mit ID {download_id} konnte nicht aktualisiert werden")
                return False
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Download-Status: {e}")
            return False
    
    def clear_cache(self) -> None:
        """
        Leert den internen Cache für bereits verarbeitete URLs.
        Nützlich, wenn eine komplette Neu-Indexierung durchgeführt werden soll.
        """
        self._cache = {}
        self.logger.debug("Pipeline-Cache geleert")


# Globale Instanz der Pipeline für einfachen Zugriff
db_pipeline = None

def get_pipeline() -> DatabasePipeline:
    """
    Gibt eine Instanz der DatabasePipeline zurück oder erstellt eine neue,
    wenn noch keine existiert.
    
    Returns:
        Eine Instanz der DatabasePipeline
    """
    global db_pipeline
    if db_pipeline is None:
        db_pipeline = DatabasePipeline()
    return db_pipeline 