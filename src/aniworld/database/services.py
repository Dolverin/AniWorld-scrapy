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
    
    def get_seasons_by_anime_id(self, series_id: int) -> List[Season]:
        """
        Gibt alle Staffeln einer Anime-Serie zurück.
        
        Args:
            series_id: ID der Anime-Serie
            
        Returns:
            Liste der Staffeln
        """
        return self.season_repo.find_by_anime_id(series_id)
    
    def get_anime_by_url(self, url: str) -> Optional[AnimeSeries]:
        """
        Findet einen Anime anhand seiner Aniworld-URL.
        
        Args:
            url: Die Aniworld-URL des Anime
            
        Returns:
            Das AnimeSeries-Objekt oder None, wenn kein Anime mit dieser URL gefunden wurde
        """
        return self.anime_repo.find_by_url(url)
    
    def find_all_animes(self) -> List[AnimeSeries]:
        """
        Gibt eine Liste aller Anime-Serien zurück.
        
        Returns:
            Liste aller Anime in der Datenbank
        """
        return self.anime_repo.find_all()
    
    def get_episode_by_url(self, url: str) -> Optional[Episode]:
        """
        Findet eine Episode anhand ihrer URL.
        
        Args:
            url: Die URL der Episode
            
        Returns:
            Das Episode-Objekt oder None, wenn keine Episode mit dieser URL gefunden wurde
        """
        return self.episode_repo.find_by_url(url)
    
    def save_from_scraper_data(self, anime_data: Dict[str, Any]) -> int:
        """
        Speichert Daten, die vom Scraper gesammelt wurden, in der Datenbank
        
        Args:
            anime_data: Gescrapte Daten wie Titel, Beschreibung, etc.
            
        Returns:
            ID der gespeicherten Anime-Serie
        """
        logging.debug(f"AnimeService: Speichere Scraper-Daten für Anime '{anime_data.get('title', 'Unbekannt')}'")
        
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
        logging.debug(f"AnimeService: Anime-Grunddaten gespeichert für ID {anime.series_id}")
        
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
            logging.debug(f"AnimeService: Verarbeite {len(anime_data['seasons'])} Staffeln")
            for season_data in anime_data['seasons']:
                season_num = season_data.get('number', 0)
                logging.debug(f"AnimeService: Verarbeite Staffel {season_num}")
                
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
                    logging.debug(f"AnimeService: Staffel {season_num} gespeichert mit ID {season.season_id}")
                    
                    # Verarbeite Episoden
                    if 'episodes' in season_data:
                        episode_count = len(season_data['episodes'])
                        logging.debug(f"AnimeService: Verarbeite {episode_count} Episoden für Staffel {season_num}")
                        
                        for episode_data in season_data['episodes']:
                            episode_num = episode_data.get('number', 0)
                            if episode_num > 0:
                                logging.debug(f"AnimeService: Verarbeite Episode {episode_num}")
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
                                logging.debug(f"AnimeService: Episode {episode_num} gespeichert mit ID {episode.episode_id}")
                else:
                    logging.warning(f"AnimeService: Ungültige Staffelnummer: {season_num}")
        else:
            logging.warning("AnimeService: Keine Staffeldaten im anime_data Dictionary gefunden!")
        
        return anime.series_id


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


class StatisticsService:
    """Service für Datenbankstatistiken"""
    
    def __init__(self):
        """Initialisiert den Statistik-Service mit den erforderlichen Repositories"""
        self.logger = logging.getLogger('aniworld.db.service.stats')
        self.anime_repo = AnimeRepository()
        self.season_repo = SeasonRepository()
        self.episode_repo = EpisodeRepository()
        self.download_repo = DownloadRepository()
    
    def count_animes(self) -> int:
        """
        Zählt die Anzahl der Anime-Serien in der Datenbank
        
        Returns:
            Anzahl der Anime-Serien
        """
        query = "SELECT COUNT(*) FROM anime_series"
        result = self.anime_repo._execute_query_one(query)
        return result[0] if result else 0
    
    def count_seasons(self) -> int:
        """
        Zählt die Anzahl der Staffeln in der Datenbank
        
        Returns:
            Anzahl der Staffeln
        """
        query = "SELECT COUNT(*) FROM seasons"
        result = self.season_repo._execute_query_one(query)
        return result[0] if result else 0
    
    def count_episodes(self) -> int:
        """
        Zählt die Anzahl der Episoden in der Datenbank
        
        Returns:
            Anzahl der Episoden
        """
        query = "SELECT COUNT(*) FROM episoden"
        result = self.episode_repo._execute_query_one(query)
        return result[0] if result else 0
    
    def count_downloads(self) -> int:
        """
        Zählt die Anzahl der Downloads in der Datenbank
        
        Returns:
            Anzahl der Downloads
        """
        query = "SELECT COUNT(*) FROM downloads"
        result = self.download_repo._execute_query_one(query)
        return result[0] if result else 0
    
    def get_top_anime(self, limit: int = 5) -> List[Tuple[AnimeSeries, int]]:
        """
        Gibt die Top-Anime mit den meisten Episoden zurück
        
        Args:
            limit: Anzahl der zurückzugebenden Anime
            
        Returns:
            Liste von Tupeln aus (AnimeSeries, Episodenanzahl)
        """
        query = """
            SELECT a.series_id, a.titel, a.original_titel, a.beschreibung, 
                   a.erscheinungsjahr, a.status, a.studio, a.regisseur, 
                   a.aniworld_url, a.cover_url, a.letzte_aktualisierung,
                   COUNT(e.episode_id) as episode_count
            FROM anime_series a
            JOIN seasons s ON a.series_id = s.series_id
            JOIN episoden e ON s.season_id = e.season_id
            GROUP BY a.series_id
            ORDER BY episode_count DESC
            LIMIT %s
        """
        
        results = self.anime_repo._execute_query(query, (limit,))
        top_anime = []
        
        for row in results:
            anime = AnimeSeries(
                series_id=row[0],
                titel=row[1],
                original_titel=row[2],
                beschreibung=row[3],
                erscheinungsjahr=row[4],
                status=row[5],
                studio=row[6],
                regisseur=row[7],
                aniworld_url=row[8],
                cover_url=row[9],
                letzte_aktualisierung=row[10]
            )
            episode_count = row[11]
            top_anime.append((anime, episode_count))
        
        return top_anime
    
    def get_recent_downloads(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Gibt die zuletzt durchgeführten Downloads zurück
        
        Args:
            limit: Anzahl der zurückzugebenden Downloads
            
        Returns:
            Liste mit Download-Informationen
        """
        query = """
            SELECT d.download_id, d.status, d.zieldatei, d.sprache, d.provider,
                   e.titel as episode_titel, s.titel as season_titel, a.titel as anime_titel
            FROM downloads d
            JOIN episoden e ON d.episode_id = e.episode_id
            JOIN seasons s ON e.season_id = s.season_id
            JOIN anime_series a ON s.series_id = a.series_id
            ORDER BY d.download_datum DESC
            LIMIT %s
        """
        
        results = self.download_repo._execute_query(query, (limit,))
        recent_downloads = []
        
        for row in results:
            download_info = {
                'download_id': row[0],
                'status': row[1],
                'zieldatei': row[2],
                'sprache': row[3],
                'provider': row[4],
                'episode_titel': row[5],
                'season_titel': row[6],
                'anime_titel': row[7]
            }
            recent_downloads.append(download_info)
        
        return recent_downloads
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """
        Sammelt verschiedene Statistiken zu Downloads
        
        Returns:
            Dictionary mit Download-Statistiken
        """
        stats = {}
        
        # Gesamtzahl Downloads nach Status
        query_status = """
            SELECT status, COUNT(*) 
            FROM downloads 
            GROUP BY status
        """
        results = self.download_repo._execute_query(query_status)
        status_counts = {row[0]: row[1] for row in results}
        stats['status_counts'] = status_counts
        
        # Durchschnittliche Dateigröße
        query_size = """
            SELECT AVG(dateigroesse) 
            FROM downloads 
            WHERE dateigroesse IS NOT NULL
        """
        result = self.download_repo._execute_query_one(query_size)
        stats['avg_file_size'] = result[0] if result and result[0] else 0
        
        # Beliebteste Provider
        query_provider = """
            SELECT provider, COUNT(*) as count 
            FROM downloads 
            GROUP BY provider 
            ORDER BY count DESC 
            LIMIT 3
        """
        results = self.download_repo._execute_query(query_provider)
        top_providers = [(row[0], row[1]) for row in results]
        stats['top_providers'] = top_providers
        
        # Beliebteste Sprachen
        query_language = """
            SELECT sprache, COUNT(*) as count 
            FROM downloads 
            GROUP BY sprache 
            ORDER BY count DESC 
            LIMIT 3
        """
        results = self.download_repo._execute_query(query_language)
        top_languages = [(row[0], row[1]) for row in results]
        stats['top_languages'] = top_languages
        
        return stats 