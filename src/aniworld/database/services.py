"""
Service-Klassen für die Geschäftslogik
Verbinden Repository-Zugriffe mit der Anwendungslogik
"""

import logging
import os
from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime
import hashlib
import requests
from io import BytesIO

from .models import (
    AnimeSeries, Season, Episode, Download, Provider, 
    Language, Genre, Tag, VpnService, DownloadPfad, Benutzer
)
from .repositories import (
    AnimeRepository, SeasonRepository, EpisodeRepository, DownloadRepository
)

class LookupService:
    """Service für das Nachschlagen von IDs und Codes"""
    
    @staticmethod
    def get_provider_id(provider_name: str) -> int:
        """
        Gibt die ID eines Providers anhand seines Namens zurück
        Verwendet eine Mapping-Tabelle statt Datenbankabfragen für Effizienz
        
        Args:
            provider_name: Name des Providers (z.B. "VOE", "Vidoza")
            
        Returns:
            Provider-ID oder 0, wenn nicht gefunden
        """
        provider_map = {
            "VOE": 2,
            "Vidoza": 1,
            "Doodstream": 3,
            "Vidmoly": 4,
            "Streamtape": 5,
            "SpeedFiles": 6
        }
        return provider_map.get(provider_name, 0)
    
    @staticmethod
    def get_language_id(language_name: str) -> int:
        """
        Gibt die ID einer Sprache anhand ihres Namens zurück
        Verwendet eine Mapping-Tabelle statt Datenbankabfragen für Effizienz
        
        Args:
            language_name: Name der Sprache (z.B. "German Dub", "English Sub")
            
        Returns:
            Sprach-ID oder 0, wenn nicht gefunden
        """
        language_map = {
            "German Dub": 1,
            "German Sub": 2,
            "English Sub": 3
        }
        return language_map.get(language_name, 0)


class AnimeService:
    """Service für Anime-Serien, Staffeln und Episoden"""
    
    def __init__(self):
        self.anime_repo = AnimeRepository()
        self.season_repo = SeasonRepository()
        self.episode_repo = EpisodeRepository()
    
    def get_or_create_anime(self, aniworld_url: str, titel: str) -> AnimeSeries:
        """
        Findet eine Anime-Serie anhand der URL oder erstellt sie, wenn sie nicht existiert
        
        Args:
            aniworld_url: AniWorld-URL der Serie
            titel: Titel der Serie
            
        Returns:
            AnimeSeries-Objekt
        """
        anime = self.anime_repo.find_by_url(aniworld_url)
        if not anime:
            anime = AnimeSeries(
                titel=titel,
                aniworld_url=aniworld_url
            )
            anime.series_id = self.anime_repo.save(anime)
            logging.info(f"Neue Anime-Serie angelegt: {titel} (ID: {anime.series_id})")
        return anime
    
    def get_or_create_season(self, series_id: int, staffel_nummer: int, aniworld_url: str = None) -> Season:
        """
        Findet eine Staffel anhand der Serie und Staffelnummer oder erstellt sie, wenn sie nicht existiert
        
        Args:
            series_id: ID der Anime-Serie
            staffel_nummer: Nummer der Staffel
            aniworld_url: AniWorld-URL der Staffel (optional)
            
        Returns:
            Season-Objekt
        """
        seasons = self.season_repo.find_by_series_id(series_id)
        for season in seasons:
            if season.staffel_nummer == staffel_nummer:
                return season
        
        # Erstelle neue Staffel
        season = Season(
            series_id=series_id,
            staffel_nummer=staffel_nummer,
            aniworld_url=aniworld_url
        )
        season.season_id = self.season_repo.save(season)
        logging.info(f"Neue Staffel angelegt: {staffel_nummer} für Serie {series_id} (ID: {season.season_id})")
        return season
    
    def get_or_create_episode(self, season_id: int, episode_nummer: int, aniworld_url: str = None) -> Episode:
        """
        Findet eine Episode anhand der Staffel und Episodennummer oder erstellt sie, wenn sie nicht existiert
        
        Args:
            season_id: ID der Staffel
            episode_nummer: Nummer der Episode
            aniworld_url: AniWorld-URL der Episode (optional)
            
        Returns:
            Episode-Objekt
        """
        episodes = self.episode_repo.find_by_season_id(season_id)
        for episode in episodes:
            if episode.episode_nummer == episode_nummer:
                return episode
        
        # Erstelle neue Episode
        episode = Episode(
            season_id=season_id,
            episode_nummer=episode_nummer,
            aniworld_url=aniworld_url
        )
        episode.episode_id = self.episode_repo.save(episode)
        logging.info(f"Neue Episode angelegt: {episode_nummer} für Staffel {season_id} (ID: {episode.episode_id})")
        return episode
    
    def save_from_scraper_data(self, anime_data: Dict[str, Any]) -> int:
        """
        Speichert Daten, die vom Scraper gesammelt wurden, in der Datenbank
        
        Args:
            anime_data: Gescrapte Daten wie Titel, Beschreibung, etc.
            
        Returns:
            ID der gespeicherten Anime-Serie
        """
        # Erstelle oder aktualisiere Anime-Serie
        anime = self.get_or_create_anime(
            aniworld_url=anime_data.get('url', ''),
            titel=anime_data.get('title', 'Unbekannt')
        )
        
        # Aktualisiere weitere Felder, wenn vorhanden
        anime.beschreibung = anime_data.get('description', anime.beschreibung)
        anime.cover_url = anime_data.get('cover_url', anime.cover_url)
        anime.original_titel = anime_data.get('original_title', anime.original_titel)
        anime.erscheinungsjahr = anime_data.get('year', anime.erscheinungsjahr)
        anime.status = anime_data.get('status', anime.status)
        anime.studio = anime_data.get('studio', anime.studio)
        anime.regisseur = anime_data.get('director', anime.regisseur)
        
        # Speichere aktualisierte Anime-Daten
        self.anime_repo.save(anime)
        
        # Speichere Cover-Bild, wenn URL vorhanden und noch nicht gespeichert
        if anime.cover_url and not anime.cover_data:
            try:
                response = requests.get(anime.cover_url, timeout=10)
                if response.status_code == 200:
                    self.anime_repo.save_cover_data(anime.series_id, response.content)
                    logging.info(f"Cover-Bild für Anime {anime.series_id} gespeichert")
            except Exception as e:
                logging.error(f"Fehler beim Speichern des Cover-Bilds: {e}")
        
        # Verarbeite Staffel- und Episodeninformationen, wenn vorhanden
        if 'seasons' in anime_data:
            for season_data in anime_data['seasons']:
                season_num = season_data.get('number', 0)
                if season_num > 0:
                    season = self.get_or_create_season(
                        series_id=anime.series_id,
                        staffel_nummer=season_num,
                        aniworld_url=season_data.get('url')
                    )
                    
                    # Aktualisiere Staffeldaten
                    season.titel = season_data.get('title', season.titel)
                    season.beschreibung = season_data.get('description', season.beschreibung)
                    season.erscheinungsjahr = season_data.get('year', season.erscheinungsjahr)
                    season.anzahl_episoden = season_data.get('episode_count', season.anzahl_episoden)
                    self.season_repo.save(season)
                    
                    # Verarbeite Episoden
                    if 'episodes' in season_data:
                        for episode_data in season_data['episodes']:
                            episode_num = episode_data.get('number', 0)
                            if episode_num > 0:
                                episode = self.get_or_create_episode(
                                    season_id=season.season_id,
                                    episode_nummer=episode_num,
                                    aniworld_url=episode_data.get('url')
                                )
                                
                                # Aktualisiere Episodendaten
                                episode.titel = episode_data.get('title', episode.titel)
                                episode.beschreibung = episode_data.get('description', episode.beschreibung)
                                episode.laufzeit = episode_data.get('duration', episode.laufzeit)
                                episode.luftdatum = episode_data.get('air_date', episode.luftdatum)
                                self.episode_repo.save(episode)
        
        return anime.series_id
    
    def get_episode_by_url(self, episode_url: str) -> Optional[Tuple[AnimeSeries, Season, Episode]]:
        """
        Findet eine Episode anhand ihrer URL und gibt auch die zugehörige Serie und Staffel zurück
        
        Args:
            episode_url: AniWorld-URL der Episode
            
        Returns:
            Tuple aus (AnimeSeries, Season, Episode) oder None, wenn nicht gefunden
        """
        episode = self.episode_repo.find_by_url(episode_url)
        if not episode:
            return None
        
        season = self.season_repo.find_by_id(episode.season_id)
        if not season:
            return None
        
        anime = self.anime_repo.find_by_id(season.series_id)
        if not anime:
            return None
        
        return (anime, season, episode)


class DownloadService:
    """Service für Download-Verwaltung"""
    
    def __init__(self):
        self.download_repo = DownloadRepository()
        self.anime_service = AnimeService()
        self.lookup_service = LookupService()
    
    def record_download(self, episode_url: str, provider_name: str, language_name: str, 
                        speicherlink: str, lokaler_pfad: str = None, 
                        qualitaet: str = None, dateigroesse: int = None,
                        vpn_genutzt: bool = False) -> Optional[int]:
        """
        Zeichnet einen Download in der Datenbank auf
        
        Args:
            episode_url: AniWorld-URL der Episode
            provider_name: Name des Providers (z.B. "VOE", "Vidoza")
            language_name: Name der Sprache (z.B. "German Dub", "English Sub")
            speicherlink: Direkter Link zum Herunterladen
            lokaler_pfad: Lokaler Pfad, wo die Datei gespeichert wird (optional)
            qualitaet: Qualität des Downloads (z.B. "1080p", "720p") (optional)
            dateigroesse: Größe der Datei in Bytes (optional)
            vpn_genutzt: Ob ein VPN für den Download verwendet wurde (optional)
            
        Returns:
            ID des aufgezeichneten Downloads oder None, wenn fehlgeschlagen
        """
        # Finde Episode, Staffel und Serie
        result = self.anime_service.get_episode_by_url(episode_url)
        if not result:
            logging.error(f"Episode für URL {episode_url} nicht gefunden")
            return None
        
        anime, season, episode = result
        
        # Finde Provider und Sprache
        provider_id = self.lookup_service.get_provider_id(provider_name)
        language_id = self.lookup_service.get_language_id(language_name)
        
        if provider_id == 0:
            logging.error(f"Provider {provider_name} nicht gefunden")
            return None
        
        if language_id == 0:
            logging.error(f"Sprache {language_name} nicht gefunden")
            return None
        
        # Berechne Hash-Wert für die Datei, wenn lokaler Pfad vorhanden
        hash_wert = None
        if lokaler_pfad and os.path.exists(lokaler_pfad):
            hash_wert = self._calculate_file_hash(lokaler_pfad)
        
        # Erstelle Download-Objekt
        download = Download(
            episode_id=episode.episode_id,
            provider_id=provider_id,
            language_id=language_id,
            speicherlink=speicherlink,
            lokaler_pfad=lokaler_pfad,
            dateigroesse=dateigroesse,
            qualitaet=qualitaet,
            download_datum=datetime.now(),
            format=self._get_file_format(lokaler_pfad) if lokaler_pfad else None,
            hash_wert=hash_wert,
            status="abgeschlossen" if lokaler_pfad else "geplant",
            vpn_genutzt=vpn_genutzt
        )
        
        # Speichere in der Datenbank
        download_id = self.download_repo.save(download)
        logging.info(f"Download für Episode {episode.episode_id} aufgezeichnet (ID: {download_id})")
        
        return download_id
    
    def update_download_status(self, download_id: int, status: str, 
                            lokaler_pfad: str = None, dateigroesse: int = None,
                            download_geschwindigkeit: float = None) -> bool:
        """
        Aktualisiert den Status eines Downloads
        
        Args:
            download_id: ID des Downloads
            status: Neuer Status ('geplant', 'läuft', 'abgeschlossen', 'fehlgeschlagen')
            lokaler_pfad: Aktualisierter lokaler Pfad (optional)
            dateigroesse: Aktualisierte Dateigröße in Bytes (optional)
            download_geschwindigkeit: Aktualisierte Download-Geschwindigkeit in MB/s (optional)
            
        Returns:
            True, wenn erfolgreich, sonst False
        """
        download = self.download_repo.find_by_id(download_id)
        if not download:
            logging.error(f"Download mit ID {download_id} nicht gefunden")
            return False
        
        download.status = status
        
        if lokaler_pfad:
            download.lokaler_pfad = lokaler_pfad
        
        if dateigroesse:
            download.dateigroesse = dateigroesse
        
        if download_geschwindigkeit:
            download.download_geschwindigkeit = download_geschwindigkeit
        
        # Bei abgeschlossenem Download Hash berechnen
        if status == "abgeschlossen" and download.lokaler_pfad and os.path.exists(download.lokaler_pfad):
            download.hash_wert = self._calculate_file_hash(download.lokaler_pfad)
            download.format = self._get_file_format(download.lokaler_pfad)
        
        self.download_repo.save(download)
        logging.info(f"Download-Status für ID {download_id} aktualisiert auf {status}")
        
        return True
    
    def get_active_downloads(self) -> List[Download]:
        """
        Gibt alle aktiven Downloads zurück (Status: geplant oder läuft)
        
        Returns:
            Liste von Download-Objekten
        """
        return self.download_repo.find_active_downloads()
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Berechnet einen SHA-256-Hash für eine Datei
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            SHA-256-Hash als Hex-String
        """
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # Lese die Datei in Blöcken, um den Speicherverbrauch zu reduzieren
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logging.error(f"Fehler beim Berechnen des Hash-Werts: {e}")
            return None
    
    def _get_file_format(self, file_path: str) -> Optional[str]:
        """
        Ermittelt das Dateiformat anhand der Dateiendung
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Dateiformat (z.B. "MP4", "MKV") oder None
        """
        if not file_path:
            return None
        
        extension = os.path.splitext(file_path)[1].lower()
        
        format_map = {
            ".mp4": "MP4",
            ".mkv": "MKV",
            ".avi": "AVI",
            ".mov": "MOV",
            ".wmv": "WMV",
            ".flv": "FLV",
            ".webm": "WEBM"
        }
        
        return format_map.get(extension) 