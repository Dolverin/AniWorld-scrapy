"""
Integrationsmodul für die Datenbankfunktionen
"""

import logging
from typing import Dict, Any, Optional, Tuple, List

from aniworld.database.services import AnimeService, DownloadService
from aniworld.database.models import AnimeSeries, Episode


class DatabaseIntegration:
    """
    Integrationsklasse für die Datenbank, die als zentrale Schnittstelle zwischen
    dem Scraper und der Datenbank dient.
    
    Diese Klasse nutzt die Service-Klassen, um gescrapte Daten zu speichern
    und Informationen über Downloads zu verwalten.
    """
    
    def __init__(self):
        """
        Initialisiert die Datenbankintegration.
        """
        self.logger = logging.getLogger('aniworld.db.integration')
        self.anime_service = AnimeService()
        self.download_service = DownloadService()
        self.logger.info("Datenbankintegration initialisiert")
    
    def save_anime_data(self, anime_data: Dict[str, Any]) -> int:
        """
        Speichert gescrapte Anime-Daten in der Datenbank.
        
        Args:
            anime_data: Ein Dictionary mit den gescrapten Daten des Anime
                        (Format: siehe AnimeService.save_from_scraper_data)
        
        Returns:
            Die ID des gespeicherten Anime
        """
        self.logger.info(f"Speichere Anime-Daten: {anime_data.get('title', 'Unbekannt')}")
        try:
            anime_id = self.anime_service.save_from_scraper_data(anime_data)
            self.logger.debug(f"Anime erfolgreich gespeichert mit ID: {anime_id}")
            return anime_id
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Anime-Daten: {e}")
            raise
            
    def get_anime_by_url(self, url: str) -> Optional[AnimeSeries]:
        """
        Ruft einen Anime anhand seiner Aniworld-URL ab.
        
        Args:
            url: Die Aniworld-URL des Anime
            
        Returns:
            Das AnimeSeries-Objekt oder None, wenn kein Anime mit dieser URL gefunden wurde
        """
        self.logger.debug(f"Suche Anime mit URL: {url}")
        try:
            anime = self.anime_service.get_anime_by_url(url)
            if anime:
                self.logger.debug(f"Anime gefunden: {anime.titel} (ID: {anime.series_id})")
            else:
                self.logger.debug(f"Kein Anime mit URL {url} gefunden")
            return anime
        except Exception as e:
            self.logger.error(f"Fehler beim Suchen des Anime mit URL {url}: {e}")
            return None
    
    def find_all_animes(self) -> List[AnimeSeries]:
        """
        Gibt eine Liste aller gespeicherten Anime zurück.
        
        Returns:
            Liste aller Anime in der Datenbank
        """
        self.logger.debug("Rufe alle Anime-Serien ab")
        try:
            animes = self.anime_service.find_all_animes()
            self.logger.debug(f"{len(animes)} Anime-Serien gefunden")
            return animes
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen aller Anime-Serien: {e}")
            return []
    
    def get_episode_data(self, episode_url: str) -> Optional[Episode]:
        """
        Ruft die Daten einer Episode anhand ihrer URL ab.
        
        Args:
            episode_url: Die Aniworld-URL der Episode
            
        Returns:
            Das Episode-Objekt oder None, wenn keine Episode mit dieser URL gefunden wurde
        """
        self.logger.debug(f"Suche Episode mit URL: {episode_url}")
        try:
            episode = self.anime_service.get_episode_by_url(episode_url)
            if episode:
                self.logger.debug(f"Episode gefunden: {episode.titel} (ID: {episode.episode_id})")
            else:
                self.logger.debug(f"Keine Episode mit URL {episode_url} gefunden")
            return episode
        except Exception as e:
            self.logger.error(f"Fehler beim Suchen der Episode mit URL {episode_url}: {e}")
            return None
    
    def record_download(self, 
                        episode_url: str, 
                        provider: str, 
                        sprache: str, 
                        zieldatei: str) -> int:
        """
        Zeichnet einen neuen Download in der Datenbank auf.
        
        Args:
            episode_url: Die URL der heruntergeladenen Episode
            provider: Der Provider, von dem heruntergeladen wurde (z.B. "Vidoza")
            sprache: Die Sprache des Downloads (z.B. "Deutsch")
            zieldatei: Der vollständige Pfad der Zieldatei
            
        Returns:
            Die ID des aufgezeichneten Downloads oder -1 bei einem Fehler
        """
        self.logger.info(f"Zeichne Download auf: {episode_url} ({provider}, {sprache})")
        try:
            episode = self.get_episode_data(episode_url)
            if not episode:
                self.logger.warning(f"Episode mit URL {episode_url} nicht gefunden")
                return -1
                
            download_id = self.download_service.record_download(
                episode_id=episode.episode_id,
                provider=provider,
                sprache=sprache,
                zieldatei=zieldatei,
                status="gestartet"
            )
            self.logger.debug(f"Download aufgezeichnet mit ID: {download_id}")
            return download_id
        except Exception as e:
            self.logger.error(f"Fehler beim Aufzeichnen des Downloads: {e}")
            return -1
    
    def update_download_status(self, download_id: int, status: str) -> bool:
        """
        Aktualisiert den Status eines Downloads.
        
        Args:
            download_id: Die ID des Downloads
            status: Der neue Status (z.B. "abgeschlossen", "fehlgeschlagen")
            
        Returns:
            True bei Erfolg, False bei einem Fehler
        """
        self.logger.debug(f"Aktualisiere Download-Status für ID {download_id} auf '{status}'")
        try:
            result = self.download_service.update_download_status(download_id, status)
            if result:
                self.logger.debug(f"Download-Status erfolgreich aktualisiert")
            else:
                self.logger.warning(f"Download mit ID {download_id} nicht gefunden")
            return result
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Download-Status: {e}")
            return False
    
    def get_active_downloads(self) -> List[Dict[str, Any]]:
        """
        Ruft alle aktiven Downloads aus der Datenbank ab.
        
        Returns:
            Eine Liste von aktiven Downloads als Dictionaries
        """
        self.logger.debug("Rufe aktive Downloads ab")
        try:
            downloads = self.download_service.get_active_downloads()
            
            # Konvertieren der Download-Objekte in Dictionaries
            result = []
            for download in downloads:
                result.append({
                    'download_id': download.download_id,
                    'episode_id': download.episode_id,
                    'provider_id': download.provider_id,
                    'language_id': download.language_id,
                    'download_pfad': download.download_pfad,
                    'status': download.status,
                    'download_datum': download.download_datum,
                    'qualitaet': download.qualitaet
                })
            
            self.logger.debug(f"{len(result)} aktive Downloads gefunden")
            return result
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen aktiver Downloads: {e}")
            return []


# Singleton-Instanz der Integration
_integration_instance = None


def get_integration() -> DatabaseIntegration:
    """
    Gibt die Singleton-Instanz der Datenbankintegration zurück.
    
    Returns:
        DatabaseIntegration-Instanz
    """
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = DatabaseIntegration()
    return _integration_instance 