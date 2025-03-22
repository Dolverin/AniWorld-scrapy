"""
Tests für die Repository-Klassen
"""

import unittest
from unittest.mock import patch, MagicMock

from src.aniworld.database.repositories import BaseRepository, AnimeRepository, SeasonRepository, EpisodeRepository, DownloadRepository
from src.aniworld.database.models import AnimeSeries, Season, Episode, Download


class TestBaseRepository(unittest.TestCase):
    """Testklasse für die BaseRepository-Klasse"""
    
    def setUp(self):
        """Test-Setup"""
        # Patch für die DatabaseConnection-Klasse
        self.connection_patcher = patch('src.aniworld.database.connection.DatabaseConnection')
        self.mock_connection_class = self.connection_patcher.start()
        
        # Mock für die Connection-Instanz
        self.mock_connection = MagicMock()
        self.mock_connection_class.instance.return_value.get_connection.return_value.__enter__.return_value = self.mock_connection
        
        # Mock für den Cursor
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor
        
        # Repository-Instanz erstellen
        self.repo = BaseRepository()
    
    def tearDown(self):
        """Test-Teardown"""
        self.connection_patcher.stop()
    
    def test_execute_query(self):
        """Test für _execute_query Methode"""
        # Mock-Daten einrichten
        self.mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'Test'}]
        
        # Methode aufrufen
        result = self.repo._execute_query("SELECT * FROM test WHERE id = %s", (1,))
        
        # Ergebnis prüfen
        self.assertEqual(result, [{'id': 1, 'name': 'Test'}])
        self.mock_cursor.execute.assert_called_once_with("SELECT * FROM test WHERE id = %s", (1,))
        self.mock_cursor.fetchall.assert_called_once()
    
    def test_execute_query_with_error(self):
        """Test für _execute_query Methode mit Fehler"""
        # Mock für execute einrichten, um einen Fehler zu werfen
        self.mock_cursor.execute.side_effect = Exception("Datenbank-Fehler")
        
        # Methode aufrufen und Ausnahme erwarten
        with self.assertRaises(Exception):
            self.repo._execute_query("SELECT * FROM test WHERE id = %s", (1,))
    
    def test_execute_update_insert(self):
        """Test für _execute_update Methode (INSERT)"""
        # Mock-Daten einrichten
        self.mock_cursor.lastrowid = 42
        
        # Methode aufrufen
        result = self.repo._execute_update(
            "INSERT INTO test (name) VALUES (%s)",
            ("Test",)
        )
        
        # Ergebnis prüfen
        self.assertEqual(result, 42)
        self.mock_cursor.execute.assert_called_once_with(
            "INSERT INTO test (name) VALUES (%s)",
            ("Test",)
        )
        self.mock_connection.commit.assert_called_once()
    
    def test_execute_update_update(self):
        """Test für _execute_update Methode (UPDATE)"""
        # Mock-Daten einrichten
        self.mock_cursor.rowcount = 1
        
        # Methode aufrufen
        result = self.repo._execute_update(
            "UPDATE test SET name = %s WHERE id = %s",
            ("Neuer Name", 1)
        )
        
        # Ergebnis prüfen
        self.assertEqual(result, 1)  # Anzahl der betroffenen Zeilen
        self.mock_cursor.execute.assert_called_once_with(
            "UPDATE test SET name = %s WHERE id = %s",
            ("Neuer Name", 1)
        )
        self.mock_connection.commit.assert_called_once()
    
    def test_execute_update_with_error(self):
        """Test für _execute_update Methode mit Fehler"""
        # Mock für execute einrichten, um einen Fehler zu werfen
        self.mock_cursor.execute.side_effect = Exception("Datenbank-Fehler")
        
        # Methode aufrufen und Ausnahme erwarten
        with self.assertRaises(Exception):
            self.repo._execute_update("INSERT INTO test (name) VALUES (%s)", ("Test",))
        
        # Prüfen, dass kein Commit aufgerufen wurde
        self.mock_connection.commit.assert_not_called()


class TestAnimeRepository(unittest.TestCase):
    """Testklasse für die AnimeRepository-Klasse"""
    
    def setUp(self):
        """Test-Setup"""
        # Patch für die BaseRepository-Klasse
        self.base_patcher = patch('src.aniworld.database.repositories.BaseRepository')
        self.mock_base = self.base_patcher.start()
        
        # Repository-Instanz erstellen
        self.repo = AnimeRepository()
        
        # Mock-Methoden für _execute_query und _execute_update
        self.repo._execute_query = MagicMock()
        self.repo._execute_update = MagicMock()
    
    def tearDown(self):
        """Test-Teardown"""
        self.base_patcher.stop()
    
    def test_save_new_anime(self):
        """Test für save-Methode mit neuem Anime (ohne series_id)"""
        # Mock-Daten einrichten
        anime = AnimeSeries(
            titel="Test Anime",
            beschreibung="Eine Testbeschreibung",
            status="laufend",
            aniworld_url="https://aniworld.to/anime/test-anime"
        )
        self.repo._execute_update.return_value = 42  # Neue ID
        
        # Methode aufrufen
        result = self.repo.save(anime)
        
        # Ergebnis prüfen
        self.assertEqual(result, 42)
        self.repo._execute_update.assert_called_once()  # INSERT-Anweisung
        
        # Prüfen, dass die SQL-Anweisung ein INSERT ist
        sql = self.repo._execute_update.call_args[0][0]
        self.assertIn("INSERT INTO anime_series", sql)
    
    def test_save_existing_anime(self):
        """Test für save-Methode mit bestehendem Anime (mit series_id)"""
        # Mock-Daten einrichten
        anime = AnimeSeries(
            series_id=42,
            titel="Test Anime",
            beschreibung="Eine aktualisierte Beschreibung",
            status="abgeschlossen",
            aniworld_url="https://aniworld.to/anime/test-anime"
        )
        self.repo._execute_update.return_value = 1  # Anzahl aktualisierter Zeilen
        
        # Methode aufrufen
        result = self.repo.save(anime)
        
        # Ergebnis prüfen
        self.assertEqual(result, 42)  # Bestehende ID
        self.repo._execute_update.assert_called_once()  # UPDATE-Anweisung
        
        # Prüfen, dass die SQL-Anweisung ein UPDATE ist
        sql = self.repo._execute_update.call_args[0][0]
        self.assertIn("UPDATE anime_series", sql)
    
    def test_find_by_id(self):
        """Test für find_by_id-Methode"""
        # Mock-Daten einrichten
        mock_results = [{
            'series_id': 42,
            'titel': 'Test Anime',
            'beschreibung': 'Eine Testbeschreibung',
            'status': 'laufend',
            'aniworld_url': 'https://aniworld.to/anime/test-anime'
        }]
        self.repo._execute_query.return_value = mock_results
        
        # Methode aufrufen
        result = self.repo.find_by_id(42)
        
        # Ergebnis prüfen
        self.assertIsNotNone(result)
        self.assertEqual(result.series_id, 42)
        self.assertEqual(result.titel, 'Test Anime')
        self.assertEqual(result.beschreibung, 'Eine Testbeschreibung')
        self.assertEqual(result.status, 'laufend')
        self.assertEqual(result.aniworld_url, 'https://aniworld.to/anime/test-anime')
        
        # Prüfen, dass _execute_query mit der richtigen ID aufgerufen wurde
        self.repo._execute_query.assert_called_once()
        sql, params = self.repo._execute_query.call_args[0]
        self.assertIn("SELECT * FROM anime_series WHERE series_id = %s", sql)
        self.assertEqual(params, (42,))
    
    def test_find_by_id_not_found(self):
        """Test für find_by_id-Methode, wenn kein Eintrag gefunden wird"""
        # Mock-Daten einrichten
        self.repo._execute_query.return_value = []
        
        # Methode aufrufen
        result = self.repo.find_by_id(42)
        
        # Ergebnis prüfen
        self.assertIsNone(result)
        self.repo._execute_query.assert_called_once()
    
    def test_find_by_url(self):
        """Test für find_by_url-Methode"""
        # Mock-Daten einrichten
        mock_results = [{
            'series_id': 42,
            'titel': 'Test Anime',
            'beschreibung': 'Eine Testbeschreibung',
            'status': 'laufend',
            'aniworld_url': 'https://aniworld.to/anime/test-anime'
        }]
        self.repo._execute_query.return_value = mock_results
        
        # Methode aufrufen
        result = self.repo.find_by_url("https://aniworld.to/anime/test-anime")
        
        # Ergebnis prüfen
        self.assertIsNotNone(result)
        self.assertEqual(result.series_id, 42)
        
        # Prüfen, dass _execute_query mit der richtigen URL aufgerufen wurde
        self.repo._execute_query.assert_called_once()
        sql, params = self.repo._execute_query.call_args[0]
        self.assertIn("SELECT * FROM anime_series WHERE aniworld_url = %s", sql)
        self.assertEqual(params, ("https://aniworld.to/anime/test-anime",))
    
    def test_find_all(self):
        """Test für find_all-Methode"""
        # Mock-Daten einrichten
        mock_results = [
            {
                'series_id': 1,
                'titel': 'Anime 1',
                'beschreibung': 'Beschreibung 1',
                'status': 'laufend',
                'aniworld_url': 'https://aniworld.to/anime/anime-1'
            },
            {
                'series_id': 2,
                'titel': 'Anime 2',
                'beschreibung': 'Beschreibung 2',
                'status': 'abgeschlossen',
                'aniworld_url': 'https://aniworld.to/anime/anime-2'
            }
        ]
        self.repo._execute_query.return_value = mock_results
        
        # Methode aufrufen
        result = self.repo.find_all()
        
        # Ergebnis prüfen
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].series_id, 1)
        self.assertEqual(result[0].titel, 'Anime 1')
        self.assertEqual(result[1].series_id, 2)
        self.assertEqual(result[1].titel, 'Anime 2')
        
        # Prüfen, dass _execute_query ohne Parameter aufgerufen wurde
        self.repo._execute_query.assert_called_once()
        sql = self.repo._execute_query.call_args[0][0]
        self.assertIn("SELECT * FROM anime_series", sql)
    
    def test_delete(self):
        """Test für delete-Methode"""
        # Mock-Daten einrichten
        self.repo._execute_update.return_value = 1  # Eine Zeile gelöscht
        
        # Methode aufrufen
        result = self.repo.delete(42)
        
        # Ergebnis prüfen
        self.assertTrue(result)
        self.repo._execute_update.assert_called_once()
        sql, params = self.repo._execute_update.call_args[0]
        self.assertIn("DELETE FROM anime_series WHERE series_id = %s", sql)
        self.assertEqual(params, (42,))
    
    def test_delete_not_found(self):
        """Test für delete-Methode, wenn kein Eintrag gefunden wird"""
        # Mock-Daten einrichten
        self.repo._execute_update.return_value = 0  # Keine Zeile gelöscht
        
        # Methode aufrufen
        result = self.repo.delete(42)
        
        # Ergebnis prüfen
        self.assertFalse(result)
        self.repo._execute_update.assert_called_once()


class TestSeasonRepository(unittest.TestCase):
    """Testklasse für die SeasonRepository-Klasse"""
    
    def setUp(self):
        """Test-Setup"""
        # Patch für die BaseRepository-Klasse
        self.base_patcher = patch('src.aniworld.database.repositories.BaseRepository')
        self.mock_base = self.base_patcher.start()
        
        # Repository-Instanz erstellen
        self.repo = SeasonRepository()
        
        # Mock-Methoden für _execute_query und _execute_update
        self.repo._execute_query = MagicMock()
        self.repo._execute_update = MagicMock()
    
    def tearDown(self):
        """Test-Teardown"""
        self.base_patcher.stop()
    
    def test_find_by_series_id(self):
        """Test für find_by_series_id-Methode"""
        # Mock-Daten einrichten
        mock_results = [
            {
                'season_id': 1,
                'series_id': 42,
                'staffel_nummer': 1,
                'titel': 'Staffel 1',
                'aniworld_url': 'https://aniworld.to/anime/test-anime/staffel-1'
            },
            {
                'season_id': 2,
                'series_id': 42,
                'staffel_nummer': 2,
                'titel': 'Staffel 2',
                'aniworld_url': 'https://aniworld.to/anime/test-anime/staffel-2'
            }
        ]
        self.repo._execute_query.return_value = mock_results
        
        # Methode aufrufen
        result = self.repo.find_by_series_id(42)
        
        # Ergebnis prüfen
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].season_id, 1)
        self.assertEqual(result[0].staffel_nummer, 1)
        self.assertEqual(result[1].season_id, 2)
        self.assertEqual(result[1].staffel_nummer, 2)
        
        # Prüfen, dass _execute_query mit der richtigen series_id aufgerufen wurde
        self.repo._execute_query.assert_called_once()
        sql, params = self.repo._execute_query.call_args[0]
        self.assertIn("SELECT * FROM seasons WHERE series_id = %s", sql)
        self.assertEqual(params, (42,))


class TestEpisodeRepository(unittest.TestCase):
    """Testklasse für die EpisodeRepository-Klasse"""
    
    def setUp(self):
        """Test-Setup"""
        # Patch für die BaseRepository-Klasse
        self.base_patcher = patch('src.aniworld.database.repositories.BaseRepository')
        self.mock_base = self.base_patcher.start()
        
        # Repository-Instanz erstellen
        self.repo = EpisodeRepository()
        
        # Mock-Methoden für _execute_query und _execute_update
        self.repo._execute_query = MagicMock()
        self.repo._execute_update = MagicMock()
    
    def tearDown(self):
        """Test-Teardown"""
        self.base_patcher.stop()
    
    def test_find_by_season_id(self):
        """Test für find_by_season_id-Methode"""
        # Mock-Daten einrichten
        mock_results = [
            {
                'episode_id': 1,
                'season_id': 5,
                'episode_nummer': 1,
                'titel': 'Episode 1',
                'aniworld_url': 'https://aniworld.to/anime/test-anime/staffel-1/episode-1'
            },
            {
                'episode_id': 2,
                'season_id': 5,
                'episode_nummer': 2,
                'titel': 'Episode 2',
                'aniworld_url': 'https://aniworld.to/anime/test-anime/staffel-1/episode-2'
            }
        ]
        self.repo._execute_query.return_value = mock_results
        
        # Methode aufrufen
        result = self.repo.find_by_season_id(5)
        
        # Ergebnis prüfen
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].episode_id, 1)
        self.assertEqual(result[0].episode_nummer, 1)
        self.assertEqual(result[1].episode_id, 2)
        self.assertEqual(result[1].episode_nummer, 2)
        
        # Prüfen, dass _execute_query mit der richtigen season_id aufgerufen wurde
        self.repo._execute_query.assert_called_once()
        sql, params = self.repo._execute_query.call_args[0]
        self.assertIn("SELECT * FROM episodes WHERE season_id = %s", sql)
        self.assertEqual(params, (5,))


class TestDownloadRepository(unittest.TestCase):
    """Testklasse für die DownloadRepository-Klasse"""
    
    def setUp(self):
        """Test-Setup"""
        # Patch für die BaseRepository-Klasse
        self.base_patcher = patch('src.aniworld.database.repositories.BaseRepository')
        self.mock_base = self.base_patcher.start()
        
        # Repository-Instanz erstellen
        self.repo = DownloadRepository()
        
        # Mock-Methoden für _execute_query und _execute_update
        self.repo._execute_query = MagicMock()
        self.repo._execute_update = MagicMock()
    
    def tearDown(self):
        """Test-Teardown"""
        self.base_patcher.stop()
    
    def test_find_active(self):
        """Test für find_active-Methode"""
        # Mock-Daten einrichten
        mock_results = [
            {
                'download_id': 1,
                'episode_id': 10,
                'provider_id': 2,
                'language_id': 3,
                'download_pfad': '/downloads/test1.mp4',
                'status': 'aktiv'
            },
            {
                'download_id': 2,
                'episode_id': 11,
                'provider_id': 2,
                'language_id': 3,
                'download_pfad': '/downloads/test2.mp4',
                'status': 'aktiv'
            }
        ]
        self.repo._execute_query.return_value = mock_results
        
        # Methode aufrufen
        result = self.repo.find_active()
        
        # Ergebnis prüfen
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].download_id, 1)
        self.assertEqual(result[0].status, 'aktiv')
        self.assertEqual(result[1].download_id, 2)
        self.assertEqual(result[1].status, 'aktiv')
        
        # Prüfen, dass _execute_query mit dem richtigen Status aufgerufen wurde
        self.repo._execute_query.assert_called_once()
        sql, params = self.repo._execute_query.call_args[0]
        self.assertIn("SELECT * FROM downloads WHERE status = %s", sql)
        self.assertEqual(params, ('aktiv',))
    
    def test_update_status(self):
        """Test für update_status-Methode"""
        # Mock-Daten einrichten
        self.repo._execute_update.return_value = 1  # Eine Zeile aktualisiert
        
        # Methode aufrufen
        result = self.repo.update_status(42, "fehler", "Verbindungsfehler")
        
        # Ergebnis prüfen
        self.assertTrue(result)
        self.repo._execute_update.assert_called_once()
        sql, params = self.repo._execute_update.call_args[0]
        self.assertIn("UPDATE downloads SET status = %s, fehler_details = %s WHERE download_id = %s", sql)
        self.assertEqual(params, ("fehler", "Verbindungsfehler", 42))
    
    def test_update_status_not_found(self):
        """Test für update_status-Methode, wenn kein Eintrag gefunden wird"""
        # Mock-Daten einrichten
        self.repo._execute_update.return_value = 0  # Keine Zeile aktualisiert
        
        # Methode aufrufen
        result = self.repo.update_status(42, "fehler", "Verbindungsfehler")
        
        # Ergebnis prüfen
        self.assertFalse(result)
        self.repo._execute_update.assert_called_once()


if __name__ == '__main__':
    unittest.main() 