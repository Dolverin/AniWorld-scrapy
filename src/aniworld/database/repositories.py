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
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('aniworld.db.repo.anime')
    
    def save(self, anime: AnimeSeries) -> int:
        """
        Speichert oder aktualisiert eine Anime-Serie
        
        Args:
            anime: Das zu speichernde AnimeSeries-Objekt
            
        Returns:
            ID der gespeicherten/aktualisierten Anime-Serie
        """
        if anime.series_id is None or anime.series_id <= 0:
            # Neuer Anime - Insert
            query = """
                INSERT INTO anime_series 
                (titel, original_titel, beschreibung, erscheinungsjahr, status, 
                studio, regisseur, aniworld_url, cover_url, cover_data, aktualisiert_am)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            params = (
                anime.titel, 
                anime.original_titel, 
                anime.beschreibung, 
                anime.erscheinungsjahr,
                anime.status,
                anime.studio,
                anime.regisseur,
                anime.aniworld_url,
                anime.cover_url,
                anime.cover_data
            )
            
            anime.series_id = self._execute_update(query, params)
            self.logger.info(f"Neue Anime-Serie angelegt: {anime.titel} (ID: {anime.series_id})")
        else:
            # Bestehender Anime - Update
            query = """
                UPDATE anime_series 
                SET titel = %s, 
                    original_titel = %s, 
                    beschreibung = %s, 
                    erscheinungsjahr = %s, 
                    status = %s, 
                    studio = %s, 
                    regisseur = %s, 
                    aniworld_url = %s, 
                    cover_url = %s,
                    aktualisiert_am = NOW()
                WHERE series_id = %s
            """
            params = (
                anime.titel, 
                anime.original_titel, 
                anime.beschreibung, 
                anime.erscheinungsjahr,
                anime.status,
                anime.studio,
                anime.regisseur,
                anime.aniworld_url,
                anime.cover_url,
                anime.series_id
            )
            
            self._execute_update(query, params)
            self.logger.debug(f"Anime-Serie aktualisiert: {anime.titel} (ID: {anime.series_id})")
        
        return anime.series_id
    
    def find_by_id(self, series_id: int) -> Optional[AnimeSeries]:
        """
        Findet einen Anime anhand seiner ID
        
        Args:
            series_id: ID des zu findenden Anime
            
        Returns:
            Das AnimeSeries-Objekt oder None, wenn nicht gefunden
        """
        query = """
            SELECT series_id, titel, original_titel, beschreibung, erscheinungsjahr, 
                   status, studio, regisseur, aniworld_url, cover_url, 
                   aktualisiert_am
            FROM anime_series
            WHERE series_id = %s
        """
        
        row = self._execute_query(query, (series_id,), fetch_one=True)
        if row:
            return AnimeSeries(
                series_id=row['series_id'],
                titel=row['titel'],
                original_titel=row['original_titel'],
                beschreibung=row['beschreibung'],
                erscheinungsjahr=row['erscheinungsjahr'],
                status=row['status'],
                studio=row['studio'],
                regisseur=row['regisseur'],
                aniworld_url=row['aniworld_url'],
                cover_url=row['cover_url'],
                aktualisiert_am=row['aktualisiert_am']
            )
        
        return None
    
    def find_by_url(self, url: str) -> Optional[AnimeSeries]:
        """
        Findet einen Anime anhand seiner Aniworld-URL
        
        Args:
            url: Die Aniworld-URL des zu findenden Anime
            
        Returns:
            Das AnimeSeries-Objekt oder None, wenn nicht gefunden
        """
        query = """
            SELECT series_id, titel, original_titel, beschreibung, erscheinungsjahr, 
                   status, studio, regisseur, aniworld_url, cover_url, 
                   aktualisiert_am
            FROM anime_series
            WHERE aniworld_url = %s
        """
        
        row = self._execute_query(query, (url,), fetch_one=True)
        if row:
            return AnimeSeries(
                series_id=row['series_id'],
                titel=row['titel'],
                original_titel=row['original_titel'],
                beschreibung=row['beschreibung'],
                erscheinungsjahr=row['erscheinungsjahr'],
                status=row['status'],
                studio=row['studio'],
                regisseur=row['regisseur'],
                aniworld_url=row['aniworld_url'],
                cover_url=row['cover_url'],
                aktualisiert_am=row['aktualisiert_am']
            )
        
        return None
    
    def find_all(self) -> List[AnimeSeries]:
        """
        Gibt alle Anime-Serien zurück
        
        Returns:
            Liste aller Anime-Serien in der Datenbank
        """
        query = """
            SELECT series_id, titel, original_titel, beschreibung, erscheinungsjahr, 
                   status, studio, regisseur, aniworld_url, cover_url, 
                   aktualisiert_am
            FROM anime_series
            ORDER BY titel
        """
        
        results = self._execute_query(query)
        animes = []
        
        for row in results:
            animes.append(AnimeSeries(
                series_id=row['series_id'],
                titel=row['titel'],
                original_titel=row['original_titel'],
                beschreibung=row['beschreibung'],
                erscheinungsjahr=row['erscheinungsjahr'],
                status=row['status'],
                studio=row['studio'],
                regisseur=row['regisseur'],
                aniworld_url=row['aniworld_url'],
                cover_url=row['cover_url'],
                aktualisiert_am=row['aktualisiert_am']
            ))
        
        return animes
    
    def save_cover_data(self, series_id: int, cover_data: bytes) -> bool:
        """
        Speichert das Cover-Bild eines Anime
        
        Args:
            series_id: ID des Anime
            cover_data: Binärdaten des Cover-Bildes
            
        Returns:
            True, wenn erfolgreich gespeichert
        """
        query = """
            UPDATE anime_series 
            SET cover_data = %s
            WHERE series_id = %s
        """
        
        return self._execute_update(query, (cover_data, series_id)) > 0
    
    def delete(self, series_id: int) -> bool:
        """
        Löscht einen Anime aus der Datenbank
        
        Args:
            series_id: ID des zu löschenden Anime
            
        Returns:
            True, wenn erfolgreich gelöscht
        """
        query = "DELETE FROM anime_series WHERE series_id = %s"
        return self._execute_update(query, (series_id,)) > 0


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
    
    def find_by_anime_id(self, series_id: int) -> List[Season]:
        """
        Findet alle Staffeln eines Anime anhand der Anime-ID
        
        Args:
            series_id: Die ID der Anime-Serie
            
        Returns:
            Liste der Staffeln für den Anime
        """
        return self.find_by_series_id(series_id)
    
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
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('aniworld.db.repo.episode')
    
    def save(self, episode: Episode) -> int:
        """
        Speichert oder aktualisiert eine Episode
        
        Args:
            episode: Das zu speichernde Episode-Objekt
            
        Returns:
            ID der gespeicherten/aktualisierten Episode
        """
        if episode.episode_id is None or episode.episode_id <= 0:
            # Neue Episode - Insert
            query = """
                INSERT INTO episoden 
                (season_id, episode_nummer, titel, beschreibung, laufzeit, luftdatum, aniworld_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                episode.season_id, 
                episode.episode_nummer, 
                episode.titel, 
                episode.beschreibung, 
                episode.laufzeit,
                episode.luftdatum,
                episode.aniworld_url
            )
            
            episode.episode_id = self._execute_update(query, params)
            self.logger.info(f"Neue Episode angelegt: {episode.titel} (ID: {episode.episode_id})")
        else:
            # Bestehende Episode - Update
            query = """
                UPDATE episoden 
                SET season_id = %s, 
                    episode_nummer = %s, 
                    titel = %s, 
                    beschreibung = %s, 
                    laufzeit = %s, 
                    luftdatum = %s, 
                    aniworld_url = %s
                WHERE episode_id = %s
            """
            params = (
                episode.season_id, 
                episode.episode_nummer, 
                episode.titel, 
                episode.beschreibung, 
                episode.laufzeit,
                episode.luftdatum,
                episode.aniworld_url,
                episode.episode_id
            )
            
            self._execute_update(query, params)
            self.logger.debug(f"Episode aktualisiert: {episode.titel} (ID: {episode.episode_id})")
        
        return episode.episode_id
    
    def find_by_id(self, episode_id: int) -> Optional[Episode]:
        """
        Findet eine Episode anhand ihrer ID
        
        Args:
            episode_id: ID der zu findenden Episode
            
        Returns:
            Das Episode-Objekt oder None, wenn nicht gefunden
        """
        query = """
            SELECT episode_id, season_id, episode_nummer, titel, beschreibung, 
                   laufzeit, luftdatum, aniworld_url
            FROM episoden
            WHERE episode_id = %s
        """
        
        row = self._execute_query(query, (episode_id,), fetch_one=True)
        if row:
            return Episode(
                episode_id=row['episode_id'],
                season_id=row['season_id'],
                episode_nummer=row['episode_nummer'],
                titel=row['titel'],
                beschreibung=row['beschreibung'],
                laufzeit=row['laufzeit'],
                luftdatum=row['luftdatum'],
                aniworld_url=row['aniworld_url']
            )
        
        return None
    
    def find_by_url(self, url: str) -> Optional[Episode]:
        """
        Findet eine Episode anhand ihrer Aniworld-URL
        
        Args:
            url: Die Aniworld-URL der zu findenden Episode
            
        Returns:
            Das Episode-Objekt oder None, wenn nicht gefunden
        """
        query = """
            SELECT episode_id, season_id, episode_nummer, titel, beschreibung, 
                   laufzeit, luftdatum, aniworld_url
            FROM episoden
            WHERE aniworld_url = %s
        """
        
        row = self._execute_query(query, (url,), fetch_one=True)
        if row:
            return Episode(
                episode_id=row['episode_id'],
                season_id=row['season_id'],
                episode_nummer=row['episode_nummer'],
                titel=row['titel'],
                beschreibung=row['beschreibung'],
                laufzeit=row['laufzeit'],
                luftdatum=row['luftdatum'],
                aniworld_url=row['aniworld_url']
            )
        
        return None
    
    def find_by_season_id(self, season_id: int) -> List[Episode]:
        """
        Findet alle Episoden einer Staffel
        
        Args:
            season_id: ID der Staffel
            
        Returns:
            Liste der Episoden der Staffel
        """
        query = """
            SELECT episode_id, season_id, episode_nummer, titel, beschreibung, 
                   laufzeit, luftdatum, aniworld_url
            FROM episoden
            WHERE season_id = %s
            ORDER BY episode_nummer
        """
        
        results = self._execute_query(query, (season_id,))
        episodes = []
        
        for row in results:
            episodes.append(Episode(
                episode_id=row['episode_id'],
                season_id=row['season_id'],
                episode_nummer=row['episode_nummer'],
                titel=row['titel'],
                beschreibung=row['beschreibung'],
                laufzeit=row['laufzeit'],
                luftdatum=row['luftdatum'],
                aniworld_url=row['aniworld_url']
            ))
        
        return episodes
    
    def delete(self, episode_id: int) -> bool:
        """
        Löscht eine Episode aus der Datenbank
        
        Args:
            episode_id: ID der zu löschenden Episode
            
        Returns:
            True, wenn erfolgreich gelöscht
        """
        query = "DELETE FROM episoden WHERE episode_id = %s"
        return self._execute_update(query, (episode_id,)) > 0


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