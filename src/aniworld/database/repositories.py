"""
Repository-Klassen für den Datenbankzugriff
Jede Repository-Klasse ist für eine Entität zuständig und stellt CRUD-Operationen bereit
"""

import logging
from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime

from .connection import DatabaseConnection
from .models import (
    AnimeSeries, Season, Episode, Download, Provider, 
    Language, Genre, Tag, VpnService, DownloadPfad, Benutzer
)

class BaseRepository:
    """Basisklasse für alle Repositories mit gemeinsamen Funktionen"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def _execute_query(self, query: str, params: Tuple = None, fetch_one: bool = False) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """
        Führt eine SQL-Abfrage aus und gibt das Ergebnis zurück
        
        Args:
            query: SQL-Abfrage
            params: Parameter für die Abfrage
            fetch_one: Gibt nur einen Datensatz zurück, wenn True
            
        Returns:
            Liste von Dictionaries oder ein Dictionary, wenn fetch_one=True
            None, wenn kein Ergebnis gefunden wurde
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch_one:
                return cursor.fetchone()
            
            return cursor.fetchall()
    
    def _execute_update(self, query: str, params: Tuple = None) -> int:
        """
        Führt ein SQL-UPDATE, INSERT oder DELETE aus und gibt die Anzahl der betroffenen Zeilen zurück
        
        Args:
            query: SQL-Abfrage
            params: Parameter für die Abfrage
            
        Returns:
            Anzahl der betroffenen Zeilen oder die letzte eingefügte ID
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            
            if cursor.lastrowid:
                return cursor.lastrowid
            
            return cursor.rowcount


class AnimeRepository(BaseRepository):
    """Repository für Anime-Serien"""
    
    def save(self, anime: AnimeSeries) -> int:
        """
        Speichert eine Anime-Serie in der Datenbank
        Führt ein Update durch, wenn series_id vorhanden ist, sonst ein Insert
        
        Args:
            anime: Die zu speichernde Anime-Serie
            
        Returns:
            Die ID der gespeicherten Anime-Serie
        """
        if anime.series_id:
            # Update bestehenden Anime
            query = """
            UPDATE anime_series 
            SET titel = %s, original_titel = %s, beschreibung = %s, 
                cover_url = %s, erscheinungsjahr = %s, status = %s,
                studio = %s, regisseur = %s, zielgruppe = %s, fsk = %s,
                bewertung = %s, aniworld_url = %s
            WHERE series_id = %s
            """
            self._execute_update(query, (
                anime.titel, anime.original_titel, anime.beschreibung,
                anime.cover_url, anime.erscheinungsjahr, anime.status,
                anime.studio, anime.regisseur, anime.zielgruppe, anime.fsk,
                anime.bewertung, anime.aniworld_url, anime.series_id
            ))
            return anime.series_id
        else:
            # Füge neuen Anime hinzu
            query = """
            INSERT INTO anime_series 
            (titel, original_titel, beschreibung, cover_url, 
             erscheinungsjahr, status, studio, regisseur, 
             zielgruppe, fsk, bewertung, aniworld_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            return self._execute_update(query, (
                anime.titel, anime.original_titel, anime.beschreibung,
                anime.cover_url, anime.erscheinungsjahr, anime.status,
                anime.studio, anime.regisseur, anime.zielgruppe, anime.fsk,
                anime.bewertung, anime.aniworld_url
            ))
    
    def save_cover_data(self, series_id: int, cover_data: bytes) -> bool:
        """
        Speichert die Cover-Bilddaten für eine Anime-Serie
        
        Args:
            series_id: ID der Anime-Serie
            cover_data: Binärdaten des Cover-Bilds
            
        Returns:
            True, wenn erfolgreich, sonst False
        """
        query = "UPDATE anime_series SET cover_data = %s WHERE series_id = %s"
        affected = self._execute_update(query, (cover_data, series_id))
        return affected > 0
    
    def find_by_id(self, series_id: int) -> Optional[AnimeSeries]:
        """
        Sucht eine Anime-Serie anhand ihrer ID
        
        Args:
            series_id: ID der Anime-Serie
            
        Returns:
            AnimeSeries-Objekt oder None, wenn nicht gefunden
        """
        query = "SELECT * FROM anime_series WHERE series_id = %s"
        result = self._execute_query(query, (series_id,), fetch_one=True)
        
        if result:
            return AnimeSeries(
                series_id=result['series_id'],
                titel=result['titel'],
                original_titel=result['original_titel'],
                beschreibung=result['beschreibung'],
                cover_url=result['cover_url'],
                cover_data=result['cover_data'],
                erscheinungsjahr=result['erscheinungsjahr'],
                status=result['status'],
                studio=result['studio'],
                regisseur=result['regisseur'],
                zielgruppe=result['zielgruppe'],
                fsk=result['fsk'],
                bewertung=result['bewertung'],
                aniworld_url=result['aniworld_url'],
                erstellt_am=result['erstellt_am'],
                aktualisiert_am=result['aktualisiert_am']
            )
        return None
    
    def find_by_url(self, aniworld_url: str) -> Optional[AnimeSeries]:
        """
        Sucht eine Anime-Serie anhand ihrer AniWorld-URL
        
        Args:
            aniworld_url: AniWorld-URL der Serie
            
        Returns:
            AnimeSeries-Objekt oder None, wenn nicht gefunden
        """
        query = "SELECT * FROM anime_series WHERE aniworld_url = %s"
        result = self._execute_query(query, (aniworld_url,), fetch_one=True)
        
        if result:
            return AnimeSeries(
                series_id=result['series_id'],
                titel=result['titel'],
                original_titel=result['original_titel'],
                beschreibung=result['beschreibung'],
                cover_url=result['cover_url'],
                cover_data=result['cover_data'],
                erscheinungsjahr=result['erscheinungsjahr'],
                status=result['status'],
                studio=result['studio'],
                regisseur=result['regisseur'],
                zielgruppe=result['zielgruppe'],
                fsk=result['fsk'],
                bewertung=result['bewertung'],
                aniworld_url=result['aniworld_url'],
                erstellt_am=result['erstellt_am'],
                aktualisiert_am=result['aktualisiert_am']
            )
        return None
    
    def find_all(self) -> List[AnimeSeries]:
        """
        Gibt alle Anime-Serien zurück
        
        Returns:
            Liste von AnimeSeries-Objekten
        """
        query = "SELECT * FROM anime_series ORDER BY titel"
        results = self._execute_query(query)
        
        anime_list = []
        for result in results:
            anime_list.append(AnimeSeries(
                series_id=result['series_id'],
                titel=result['titel'],
                original_titel=result['original_titel'],
                beschreibung=result['beschreibung'],
                cover_url=result['cover_url'],
                cover_data=result['cover_data'],
                erscheinungsjahr=result['erscheinungsjahr'],
                status=result['status'],
                studio=result['studio'],
                regisseur=result['regisseur'],
                zielgruppe=result['zielgruppe'],
                fsk=result['fsk'],
                bewertung=result['bewertung'],
                aniworld_url=result['aniworld_url'],
                erstellt_am=result['erstellt_am'],
                aktualisiert_am=result['aktualisiert_am']
            ))
        return anime_list
    
    def delete(self, series_id: int) -> bool:
        """
        Löscht eine Anime-Serie anhand ihrer ID
        
        Args:
            series_id: ID der Anime-Serie
            
        Returns:
            True, wenn erfolgreich, sonst False
        """
        query = "DELETE FROM anime_series WHERE series_id = %s"
        affected = self._execute_update(query, (series_id,))
        return affected > 0


class SeasonRepository(BaseRepository):
    """Repository für Staffeln"""
    
    def save(self, season: Season) -> int:
        """
        Speichert eine Staffel in der Datenbank
        Führt ein Update durch, wenn season_id vorhanden ist, sonst ein Insert
        
        Args:
            season: Die zu speichernde Staffel
            
        Returns:
            Die ID der gespeicherten Staffel
        """
        if season.season_id:
            # Update bestehende Staffel
            query = """
            UPDATE seasons 
            SET series_id = %s, staffel_nummer = %s, titel = %s, 
                beschreibung = %s, erscheinungsjahr = %s, 
                anzahl_episoden = %s, aniworld_url = %s
            WHERE season_id = %s
            """
            self._execute_update(query, (
                season.series_id, season.staffel_nummer, season.titel,
                season.beschreibung, season.erscheinungsjahr,
                season.anzahl_episoden, season.aniworld_url, season.season_id
            ))
            return season.season_id
        else:
            # Füge neue Staffel hinzu
            query = """
            INSERT INTO seasons 
            (series_id, staffel_nummer, titel, beschreibung, 
             erscheinungsjahr, anzahl_episoden, aniworld_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            return self._execute_update(query, (
                season.series_id, season.staffel_nummer, season.titel,
                season.beschreibung, season.erscheinungsjahr,
                season.anzahl_episoden, season.aniworld_url
            ))
    
    def find_by_id(self, season_id: int) -> Optional[Season]:
        """
        Sucht eine Staffel anhand ihrer ID
        
        Args:
            season_id: ID der Staffel
            
        Returns:
            Season-Objekt oder None, wenn nicht gefunden
        """
        query = "SELECT * FROM seasons WHERE season_id = %s"
        result = self._execute_query(query, (season_id,), fetch_one=True)
        
        if result:
            return Season(
                season_id=result['season_id'],
                series_id=result['series_id'],
                staffel_nummer=result['staffel_nummer'],
                titel=result['titel'],
                beschreibung=result['beschreibung'],
                erscheinungsjahr=result['erscheinungsjahr'],
                anzahl_episoden=result['anzahl_episoden'],
                aniworld_url=result['aniworld_url']
            )
        return None
    
    def find_by_series_id(self, series_id: int) -> List[Season]:
        """
        Sucht alle Staffeln zu einer Anime-Serie
        
        Args:
            series_id: ID der Anime-Serie
            
        Returns:
            Liste von Season-Objekten
        """
        query = "SELECT * FROM seasons WHERE series_id = %s ORDER BY staffel_nummer"
        results = self._execute_query(query, (series_id,))
        
        season_list = []
        for result in results:
            season_list.append(Season(
                season_id=result['season_id'],
                series_id=result['series_id'],
                staffel_nummer=result['staffel_nummer'],
                titel=result['titel'],
                beschreibung=result['beschreibung'],
                erscheinungsjahr=result['erscheinungsjahr'],
                anzahl_episoden=result['anzahl_episoden'],
                aniworld_url=result['aniworld_url']
            ))
        return season_list
    
    def find_by_url(self, aniworld_url: str) -> Optional[Season]:
        """
        Sucht eine Staffel anhand ihrer AniWorld-URL
        
        Args:
            aniworld_url: AniWorld-URL der Staffel
            
        Returns:
            Season-Objekt oder None, wenn nicht gefunden
        """
        query = "SELECT * FROM seasons WHERE aniworld_url = %s"
        result = self._execute_query(query, (aniworld_url,), fetch_one=True)
        
        if result:
            return Season(
                season_id=result['season_id'],
                series_id=result['series_id'],
                staffel_nummer=result['staffel_nummer'],
                titel=result['titel'],
                beschreibung=result['beschreibung'],
                erscheinungsjahr=result['erscheinungsjahr'],
                anzahl_episoden=result['anzahl_episoden'],
                aniworld_url=result['aniworld_url']
            )
        return None


class EpisodeRepository(BaseRepository):
    """Repository für Episoden"""
    
    def save(self, episode: Episode) -> int:
        """
        Speichert eine Episode in der Datenbank
        Führt ein Update durch, wenn episode_id vorhanden ist, sonst ein Insert
        
        Args:
            episode: Die zu speichernde Episode
            
        Returns:
            Die ID der gespeicherten Episode
        """
        if episode.episode_id:
            # Update bestehende Episode
            query = """
            UPDATE episodes 
            SET season_id = %s, episode_nummer = %s, titel = %s, 
                beschreibung = %s, laufzeit = %s, luftdatum = %s, 
                aniworld_url = %s
            WHERE episode_id = %s
            """
            self._execute_update(query, (
                episode.season_id, episode.episode_nummer, episode.titel,
                episode.beschreibung, episode.laufzeit, episode.luftdatum,
                episode.aniworld_url, episode.episode_id
            ))
            return episode.episode_id
        else:
            # Füge neue Episode hinzu
            query = """
            INSERT INTO episodes 
            (season_id, episode_nummer, titel, beschreibung, 
             laufzeit, luftdatum, aniworld_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            return self._execute_update(query, (
                episode.season_id, episode.episode_nummer, episode.titel,
                episode.beschreibung, episode.laufzeit, episode.luftdatum,
                episode.aniworld_url
            ))
    
    def find_by_id(self, episode_id: int) -> Optional[Episode]:
        """
        Sucht eine Episode anhand ihrer ID
        
        Args:
            episode_id: ID der Episode
            
        Returns:
            Episode-Objekt oder None, wenn nicht gefunden
        """
        query = "SELECT * FROM episodes WHERE episode_id = %s"
        result = self._execute_query(query, (episode_id,), fetch_one=True)
        
        if result:
            return Episode(
                episode_id=result['episode_id'],
                season_id=result['season_id'],
                episode_nummer=result['episode_nummer'],
                titel=result['titel'],
                beschreibung=result['beschreibung'],
                laufzeit=result['laufzeit'],
                luftdatum=result['luftdatum'],
                aniworld_url=result['aniworld_url']
            )
        return None
    
    def find_by_season_id(self, season_id: int) -> List[Episode]:
        """
        Sucht alle Episoden zu einer Staffel
        
        Args:
            season_id: ID der Staffel
            
        Returns:
            Liste von Episode-Objekten
        """
        query = "SELECT * FROM episodes WHERE season_id = %s ORDER BY episode_nummer"
        results = self._execute_query(query, (season_id,))
        
        episode_list = []
        for result in results:
            episode_list.append(Episode(
                episode_id=result['episode_id'],
                season_id=result['season_id'],
                episode_nummer=result['episode_nummer'],
                titel=result['titel'],
                beschreibung=result['beschreibung'],
                laufzeit=result['laufzeit'],
                luftdatum=result['luftdatum'],
                aniworld_url=result['aniworld_url']
            ))
        return episode_list
    
    def find_by_url(self, aniworld_url: str) -> Optional[Episode]:
        """
        Sucht eine Episode anhand ihrer AniWorld-URL
        
        Args:
            aniworld_url: AniWorld-URL der Episode
            
        Returns:
            Episode-Objekt oder None, wenn nicht gefunden
        """
        query = "SELECT * FROM episodes WHERE aniworld_url = %s"
        result = self._execute_query(query, (aniworld_url,), fetch_one=True)
        
        if result:
            return Episode(
                episode_id=result['episode_id'],
                season_id=result['season_id'],
                episode_nummer=result['episode_nummer'],
                titel=result['titel'],
                beschreibung=result['beschreibung'],
                laufzeit=result['laufzeit'],
                luftdatum=result['luftdatum'],
                aniworld_url=result['aniworld_url']
            )
        return None


class DownloadRepository(BaseRepository):
    """Repository für Downloads"""
    
    def save(self, download: Download) -> int:
        """
        Speichert einen Download in der Datenbank
        Führt ein Update durch, wenn download_id vorhanden ist, sonst ein Insert
        
        Args:
            download: Der zu speichernde Download
            
        Returns:
            Die ID des gespeicherten Downloads
        """
        if download.download_id:
            # Update bestehenden Download
            query = """
            UPDATE downloads 
            SET episode_id = %s, provider_id = %s, language_id = %s, 
                speicherlink = %s, lokaler_pfad = %s, dateigroesse = %s, 
                qualitaet = %s, format = %s, hash_wert = %s, status = %s, 
                notizen = %s, download_pfad_id = %s, vpn_genutzt = %s,
                vpn_id = %s, vpn_server_id = %s, download_geschwindigkeit = %s,
                benutzer_id = %s
            WHERE download_id = %s
            """
            self._execute_update(query, (
                download.episode_id, download.provider_id, download.language_id,
                download.speicherlink, download.lokaler_pfad, download.dateigroesse,
                download.qualitaet, download.format, download.hash_wert, download.status,
                download.notizen, download.download_pfad_id, download.vpn_genutzt,
                download.vpn_id, download.vpn_server_id, download.download_geschwindigkeit,
                download.benutzer_id, download.download_id
            ))
            return download.download_id
        else:
            # Füge neuen Download hinzu
            query = """
            INSERT INTO downloads 
            (episode_id, provider_id, language_id, speicherlink, 
             lokaler_pfad, dateigroesse, qualitaet, format, 
             hash_wert, status, notizen, download_pfad_id, 
             vpn_genutzt, vpn_id, vpn_server_id, download_geschwindigkeit, benutzer_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            return self._execute_update(query, (
                download.episode_id, download.provider_id, download.language_id,
                download.speicherlink, download.lokaler_pfad, download.dateigroesse,
                download.qualitaet, download.format, download.hash_wert, download.status,
                download.notizen, download.download_pfad_id, download.vpn_genutzt,
                download.vpn_id, download.vpn_server_id, download.download_geschwindigkeit,
                download.benutzer_id
            ))
    
    def find_by_id(self, download_id: int) -> Optional[Download]:
        """
        Sucht einen Download anhand seiner ID
        
        Args:
            download_id: ID des Downloads
            
        Returns:
            Download-Objekt oder None, wenn nicht gefunden
        """
        query = "SELECT * FROM downloads WHERE download_id = %s"
        result = self._execute_query(query, (download_id,), fetch_one=True)
        
        if result:
            return Download(
                download_id=result['download_id'],
                episode_id=result['episode_id'],
                provider_id=result['provider_id'],
                language_id=result['language_id'],
                speicherlink=result['speicherlink'],
                lokaler_pfad=result['lokaler_pfad'],
                dateigroesse=result['dateigroesse'],
                qualitaet=result['qualitaet'],
                download_datum=result['download_datum'],
                format=result['format'],
                hash_wert=result['hash_wert'],
                status=result['status'],
                notizen=result['notizen'],
                download_pfad_id=result['download_pfad_id'],
                vpn_genutzt=result['vpn_genutzt'],
                vpn_id=result['vpn_id'],
                vpn_server_id=result['vpn_server_id'],
                download_geschwindigkeit=result['download_geschwindigkeit'],
                benutzer_id=result['benutzer_id']
            )
        return None
    
    def find_by_episode_id(self, episode_id: int) -> List[Download]:
        """
        Sucht alle Downloads zu einer Episode
        
        Args:
            episode_id: ID der Episode
            
        Returns:
            Liste von Download-Objekten
        """
        query = "SELECT * FROM downloads WHERE episode_id = %s ORDER BY download_datum DESC"
        results = self._execute_query(query, (episode_id,))
        
        download_list = []
        for result in results:
            download_list.append(Download(
                download_id=result['download_id'],
                episode_id=result['episode_id'],
                provider_id=result['provider_id'],
                language_id=result['language_id'],
                speicherlink=result['speicherlink'],
                lokaler_pfad=result['lokaler_pfad'],
                dateigroesse=result['dateigroesse'],
                qualitaet=result['qualitaet'],
                download_datum=result['download_datum'],
                format=result['format'],
                hash_wert=result['hash_wert'],
                status=result['status'],
                notizen=result['notizen'],
                download_pfad_id=result['download_pfad_id'],
                vpn_genutzt=result['vpn_genutzt'],
                vpn_id=result['vpn_id'],
                vpn_server_id=result['vpn_server_id'],
                download_geschwindigkeit=result['download_geschwindigkeit'],
                benutzer_id=result['benutzer_id']
            ))
        return download_list
    
    def find_active_downloads(self) -> List[Download]:
        """
        Sucht alle aktiven Downloads (Status: geplant oder läuft)
        
        Returns:
            Liste von Download-Objekten
        """
        query = "SELECT * FROM downloads WHERE status IN ('geplant', 'läuft') ORDER BY download_datum"
        results = self._execute_query(query)
        
        download_list = []
        for result in results:
            download_list.append(Download(
                download_id=result['download_id'],
                episode_id=result['episode_id'],
                provider_id=result['provider_id'],
                language_id=result['language_id'],
                speicherlink=result['speicherlink'],
                lokaler_pfad=result['lokaler_pfad'],
                dateigroesse=result['dateigroesse'],
                qualitaet=result['qualitaet'],
                download_datum=result['download_datum'],
                format=result['format'],
                hash_wert=result['hash_wert'],
                status=result['status'],
                notizen=result['notizen'],
                download_pfad_id=result['download_pfad_id'],
                vpn_genutzt=result['vpn_genutzt'],
                vpn_id=result['vpn_id'],
                vpn_server_id=result['vpn_server_id'],
                download_geschwindigkeit=result['download_geschwindigkeit'],
                benutzer_id=result['benutzer_id']
            ))
        return download_list 