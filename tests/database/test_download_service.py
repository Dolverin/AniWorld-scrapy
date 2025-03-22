"""
Tests für die DownloadService-Klasse
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.aniworld.database.services import DownloadService, LookupService
from src.aniworld.database.models import Download


class TestDownloadService(unittest.TestCase):
    """Testklasse für den DownloadService"""
    
    def setUp(self):
        """Test-Setup"""
        # Patches für die Repository-Klasse und Lookup-Service
        self.download_repo_patcher = patch('src.aniworld.database.repositories.DownloadRepository')
        self.lookup_service_patcher = patch('src.aniworld.database.services.LookupService')
        self.anime_service_patcher = patch('src.aniworld.database.services.AnimeService')
        
        self.mock_download_repo = self.download_repo_patcher.start()
        self.mock_lookup_service = self.lookup_service_patcher.start()
        self.mock_anime_service = self.anime_service_patcher.start()
        
        # Service-Instanz erstellen
        self.service = DownloadService()
        
        # Mock-Rückgabewerte für Repository-Methoden
        self.service.download_repo = self.mock_download_repo.return_value
        self.service.lookup_service = self.mock_lookup_service.return_value
        self.service.anime_service = self.mock_anime_service.return_value
    
    def tearDown(self):
        """Test-Teardown"""
        self.download_repo_patcher.stop()
        self.lookup_service_patcher.stop()
        self.anime_service_patcher.stop()
    
    def test_record_download_success(self):
        """Test für record_download mit erfolgreicher Ausführung"""
        # Mocks für Methoden einrichten
        episode_url = "https://aniworld.to/anime/test-anime/staffel-1/episode-1"
        
        # Mock für AnimeService.get_episode_by_url
        mock_anime = MagicMock()
        mock_anime.series_id = 1
        mock_season = MagicMock()
        mock_season.season_id = 5
        mock_episode = MagicMock()
        mock_episode.episode_id = 10
        self.service.anime_service.get_episode_by_url.return_value = (mock_anime, mock_season, mock_episode)
        
        # Mock für LookupService
        self.service.lookup_service.get_provider_id.return_value = 2
        self.service.lookup_service.get_language_id.return_value = 3
        
        # Mock für Download-Repository
        self.service.download_repo.save.return_value = 42  # Neue Download-ID
        
        # Methode aufrufen
        result = self.service.record_download(
            episode_url=episode_url,
            provider_name="Streamtape",
            language_name="Deutsch",
            download_pfad="/downloads/test.mp4",
            qualitaet="1080p"
        )
        
        # Ergebnis prüfen
        self.assertEqual(result, 42)  # Download ID
        self.service.anime_service.get_episode_by_url.assert_called_once_with(episode_url)
        self.service.lookup_service.get_provider_id.assert_called_once_with("Streamtape")
        self.service.lookup_service.get_language_id.assert_called_once_with("Deutsch")
        self.service.download_repo.save.assert_called_once()
        
        # Prüfen, dass das Download-Objekt korrekt erstellt wurde
        download_arg = self.service.download_repo.save.call_args[0][0]
        self.assertEqual(download_arg.episode_id, 10)
        self.assertEqual(download_arg.provider_id, 2)
        self.assertEqual(download_arg.language_id, 3)
        self.assertEqual(download_arg.download_pfad, "/downloads/test.mp4")
        self.assertEqual(download_arg.qualitaet, "1080p")
        self.assertEqual(download_arg.status, "abgeschlossen")
        self.assertIsNotNone(download_arg.download_datum)
    
    def test_record_download_episode_not_found(self):
        """Test für record_download, wenn die Episode nicht gefunden wird"""
        # Mock für AnimeService.get_episode_by_url
        self.service.anime_service.get_episode_by_url.return_value = None
        
        # Methode aufrufen
        result = self.service.record_download(
            episode_url="https://aniworld.to/anime/test-anime/staffel-1/episode-1",
            provider_name="Streamtape",
            language_name="Deutsch",
            download_pfad="/downloads/test.mp4"
        )
        
        # Ergebnis prüfen
        self.assertEqual(result, 0)  # Keine Download-ID, da Episode nicht gefunden
        self.service.anime_service.get_episode_by_url.assert_called_once()
        self.service.lookup_service.get_provider_id.assert_not_called()
        self.service.lookup_service.get_language_id.assert_not_called()
        self.service.download_repo.save.assert_not_called()
    
    def test_record_download_provider_not_found(self):
        """Test für record_download, wenn der Provider nicht gefunden wird"""
        # Mock für AnimeService.get_episode_by_url
        mock_anime = MagicMock()
        mock_season = MagicMock()
        mock_episode = MagicMock()
        mock_episode.episode_id = 10
        self.service.anime_service.get_episode_by_url.return_value = (mock_anime, mock_season, mock_episode)
        
        # Mock für LookupService - Provider nicht gefunden
        self.service.lookup_service.get_provider_id.return_value = 0
        
        # Methode aufrufen
        result = self.service.record_download(
            episode_url="https://aniworld.to/anime/test-anime/staffel-1/episode-1",
            provider_name="UnbekannterProvider",
            language_name="Deutsch",
            download_pfad="/downloads/test.mp4"
        )
        
        # Ergebnis prüfen
        self.assertEqual(result, 0)  # Keine Download-ID, da Provider nicht gefunden
        self.service.anime_service.get_episode_by_url.assert_called_once()
        self.service.lookup_service.get_provider_id.assert_called_once_with("UnbekannterProvider")
        self.service.lookup_service.get_language_id.assert_not_called()
        self.service.download_repo.save.assert_not_called()
    
    def test_update_download_status(self):
        """Test für update_download_status"""
        # Mock für Download-Repository
        self.service.download_repo.update_status.return_value = True
        
        # Methode aufrufen
        result = self.service.update_download_status(
            download_id=42,
            status="fehler",
            fehler_details="Verbindungsfehler"
        )
        
        # Ergebnis prüfen
        self.assertTrue(result)
        self.service.download_repo.update_status.assert_called_once_with(
            42, "fehler", "Verbindungsfehler"
        )
    
    def test_get_active_downloads(self):
        """Test für get_active_downloads"""
        # Mock für Download-Repository
        mock_downloads = [
            Download(
                download_id=1,
                episode_id=10,
                provider_id=2,
                language_id=3,
                download_pfad="/downloads/test1.mp4",
                status="aktiv"
            ),
            Download(
                download_id=2,
                episode_id=11,
                provider_id=2,
                language_id=3,
                download_pfad="/downloads/test2.mp4",
                status="aktiv"
            )
        ]
        self.service.download_repo.find_active.return_value = mock_downloads
        
        # Methode aufrufen
        result = self.service.get_active_downloads()
        
        # Ergebnis prüfen
        self.assertEqual(result, mock_downloads)
        self.service.download_repo.find_active.assert_called_once()


if __name__ == '__main__':
    unittest.main() 