"""
Integrationsmodul für die Datenbankfunktionen
"""

import logging
from typing import Dict, Any, Optional, Tuple, List

from src.aniworld.database.services import AnimeService, DownloadService


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
    
    def get_episode_data(self, episode_url: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]]:
        """
        Ruft die Daten für eine Episode aus der Datenbank ab.
        
        Args:
            episode_url: Die URL der Episode auf AniWorld
        
        Returns:
            Ein Tupel aus (Anime, Staffel, Episode) oder None, wenn die Episode nicht gefunden wurde
        """
        self.logger.debug(f"Suche nach Episode mit URL: {episode_url}")
        result = self.anime_service.get_episode_by_url(episode_url)
        
        if result is None:
            self.logger.warning(f"Episode nicht gefunden: {episode_url}")
            return None
        
        anime, season, episode = result
        
        # Konvertiert die Objekte in Dictionaries für einfacheren Zugriff
        anime_dict = {
            'series_id': anime.series_id,
            'titel': anime.titel,
            'beschreibung': anime.beschreibung,
            'status': anime.status,
            'aniworld_url': anime.aniworld_url
        }
        
        season_dict = {
            'season_id': season.season_id,
            'series_id': season.series_id,
            'staffel_nummer': season.staffel_nummer,
            'titel': season.titel,
            'aniworld_url': season.aniworld_url
        }
        
        episode_dict = {
            'episode_id': episode.episode_id,
            'season_id': episode.season_id,
            'episode_nummer': episode.episode_nummer,
            'titel': episode.titel,
            'aniworld_url': episode.aniworld_url
        }
        
        return anime_dict, season_dict, episode_dict
    
    def record_download(self, 
                      episode_url: str,
                      provider_name: str,
                      language_name: str,
                      download_pfad: str,
                      qualitaet: str = None) -> int:
        """
        Zeichnet einen Download in der Datenbank auf.
        
        Args:
            episode_url: Die URL der Episode auf AniWorld
            provider_name: Der Name des Anbieters (z.B. "Streamtape")
            language_name: Die Sprache des Downloads (z.B. "Deutsch", "Japanisch")
            download_pfad: Der Pfad, unter dem die Datei gespeichert wird
            qualitaet: Die Qualität des Downloads (z.B. "1080p", "720p")
        
        Returns:
            Die ID des aufgezeichneten Downloads, oder 0 bei Fehler
        """
        self.logger.info(f"Zeichne Download auf: {episode_url}, Anbieter: {provider_name}")
        try:
            download_id = self.download_service.record_download(
                episode_url=episode_url,
                provider_name=provider_name,
                language_name=language_name,
                download_pfad=download_pfad,
                qualitaet=qualitaet
            )
            
            if download_id > 0:
                self.logger.debug(f"Download erfolgreich aufgezeichnet mit ID: {download_id}")
            else:
                self.logger.warning("Download konnte nicht aufgezeichnet werden")
                
            return download_id
        except Exception as e:
            self.logger.error(f"Fehler beim Aufzeichnen des Downloads: {e}")
            return 0
    
    def update_download_status(self, download_id: int, status: str, fehler_details: str = None) -> bool:
        """
        Aktualisiert den Status eines Downloads.
        
        Args:
            download_id: Die ID des Downloads
            status: Der neue Status (z.B. "abgeschlossen", "fehler", "in_bearbeitung")
            fehler_details: Optionale Fehlerdetails, wenn der Status "fehler" ist
        
        Returns:
            True, wenn die Aktualisierung erfolgreich war, sonst False
        """
        self.logger.debug(f"Aktualisiere Download-Status auf '{status}' für ID: {download_id}")
        try:
            result = self.download_service.update_download_status(
                download_id=download_id,
                status=status,
                fehler_details=fehler_details
            )
            
            if result:
                self.logger.debug(f"Download-Status erfolgreich aktualisiert für ID: {download_id}")
            else:
                self.logger.warning(f"Download mit ID {download_id} konnte nicht aktualisiert werden")
                
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