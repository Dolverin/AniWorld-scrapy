"""
Tests für die AnimeService-Klasse
"""

import unittest
from unittest.mock import patch, MagicMock

from src.aniworld.database.services import AnimeService
from src.aniworld.database.models import AnimeSeries, Season, Episode


class TestAnimeService(unittest.TestCase):
    """Testklasse für den AnimeService"""
    
    def setUp(self):
        """Test-Setup"""
        # Patches für die Repository-Klassen
        self.anime_repo_patcher = patch('src.aniworld.database.repositories.AnimeRepository')
        self.season_repo_patcher = patch('src.aniworld.database.repositories.SeasonRepository')
        self.episode_repo_patcher = patch('src.aniworld.database.repositories.EpisodeRepository')
        
        self.mock_anime_repo = self.anime_repo_patcher.start()
        self.mock_season_repo = self.season_repo_patcher.start()
        self.mock_episode_repo = self.episode_repo_patcher.start()
        
        # Service-Instanz erstellen
        self.service = AnimeService()
        
        # Mock-Rückgabewerte für Repository-Methoden
        self.service.anime_repo = self.mock_anime_repo.return_value
        self.service.season_repo = self.mock_season_repo.return_value
        self.service.episode_repo = self.mock_episode_repo.return_value
    
    def tearDown(self):
        """Test-Teardown"""
        self.anime_repo_patcher.stop()
        self.season_repo_patcher.stop()
        self.episode_repo_patcher.stop()
    
    def test_get_or_create_anime_existing(self):
        """Test für get_or_create_anime mit existierendem Anime"""
        # Mock für find_by_url einrichten
        existing_anime = AnimeSeries(
            series_id=1,
            titel="Test Anime",
            aniworld_url="https://aniworld.to/anime/test-anime"
        )
        self.service.anime_repo.find_by_url.return_value = existing_anime
        
        # Methode aufrufen
        result = self.service.get_or_create_anime(
            aniworld_url="https://aniworld.to/anime/test-anime",
            titel="Test Anime"
        )
        
        # Ergebnis prüfen
        self.assertEqual(result, existing_anime)
        self.service.anime_repo.find_by_url.assert_called_once_with("https://aniworld.to/anime/test-anime")
        self.service.anime_repo.save.assert_not_called()  # Sollte nicht gespeichert werden, da existiert
    
    def test_get_or_create_anime_new(self):
        """Test für get_or_create_anime mit neuem Anime"""
        # Mock für find_by_url einrichten
        self.service.anime_repo.find_by_url.return_value = None
        self.service.anime_repo.save.return_value = 42  # Neue ID
        
        # Methode aufrufen
        result = self.service.get_or_create_anime(
            aniworld_url="https://aniworld.to/anime/test-anime",
            titel="Test Anime"
        )
        
        # Ergebnis prüfen
        self.assertEqual(result.series_id, 42)
        self.assertEqual(result.titel, "Test Anime")
        self.assertEqual(result.aniworld_url, "https://aniworld.to/anime/test-anime")
        self.service.anime_repo.find_by_url.assert_called_once_with("https://aniworld.to/anime/test-anime")
        self.service.anime_repo.save.assert_called_once()
    
    def test_get_or_create_season_existing(self):
        """Test für get_or_create_season mit existierender Staffel"""
        # Mock für find_by_series_id einrichten
        existing_season = Season(
            season_id=5,
            series_id=1,
            staffel_nummer=2,
            titel="Staffel 2"
        )
        self.service.season_repo.find_by_series_id.return_value = [existing_season]
        
        # Methode aufrufen
        result = self.service.get_or_create_season(
            series_id=1,
            staffel_nummer=2
        )
        
        # Ergebnis prüfen
        self.assertEqual(result, existing_season)
        self.service.season_repo.find_by_series_id.assert_called_once_with(1)
        self.service.season_repo.save.assert_not_called()  # Sollte nicht gespeichert werden, da existiert
    
    def test_get_or_create_season_new(self):
        """Test für get_or_create_season mit neuer Staffel"""
        # Mock für find_by_series_id einrichten
        self.service.season_repo.find_by_series_id.return_value = []
        self.service.season_repo.save.return_value = 5  # Neue ID
        
        # Methode aufrufen
        result = self.service.get_or_create_season(
            series_id=1,
            staffel_nummer=2,
            aniworld_url="https://aniworld.to/anime/test-anime/staffel-2"
        )
        
        # Ergebnis prüfen
        self.assertEqual(result.season_id, 5)
        self.assertEqual(result.series_id, 1)
        self.assertEqual(result.staffel_nummer, 2)
        self.assertEqual(result.aniworld_url, "https://aniworld.to/anime/test-anime/staffel-2")
        self.service.season_repo.find_by_series_id.assert_called_once_with(1)
        self.service.season_repo.save.assert_called_once()
    
    def test_get_or_create_episode_existing(self):
        """Test für get_or_create_episode mit existierender Episode"""
        # Mock für find_by_season_id einrichten
        existing_episode = Episode(
            episode_id=10,
            season_id=5,
            episode_nummer=3,
            titel="Episode 3"
        )
        self.service.episode_repo.find_by_season_id.return_value = [existing_episode]
        
        # Methode aufrufen
        result = self.service.get_or_create_episode(
            season_id=5,
            episode_nummer=3
        )
        
        # Ergebnis prüfen
        self.assertEqual(result, existing_episode)
        self.service.episode_repo.find_by_season_id.assert_called_once_with(5)
        self.service.episode_repo.save.assert_not_called()  # Sollte nicht gespeichert werden, da existiert
    
    def test_get_or_create_episode_new(self):
        """Test für get_or_create_episode mit neuer Episode"""
        # Mock für find_by_season_id einrichten
        self.service.episode_repo.find_by_season_id.return_value = []
        self.service.episode_repo.save.return_value = 10  # Neue ID
        
        # Methode aufrufen
        result = self.service.get_or_create_episode(
            season_id=5,
            episode_nummer=3,
            aniworld_url="https://aniworld.to/anime/test-anime/staffel-2/episode-3"
        )
        
        # Ergebnis prüfen
        self.assertEqual(result.episode_id, 10)
        self.assertEqual(result.season_id, 5)
        self.assertEqual(result.episode_nummer, 3)
        self.assertEqual(result.aniworld_url, "https://aniworld.to/anime/test-anime/staffel-2/episode-3")
        self.service.episode_repo.find_by_season_id.assert_called_once_with(5)
        self.service.episode_repo.save.assert_called_once()
    
    @patch('src.aniworld.database.services.requests.get')
    def test_save_from_scraper_data(self, mock_requests_get):
        """Test für save_from_scraper_data"""
        # Mocks für Repositories einrichten
        self.service.anime_repo.find_by_url.return_value = None
        self.service.anime_repo.save.return_value = 1
        self.service.season_repo.find_by_series_id.return_value = []
        self.service.season_repo.save.return_value = 5
        self.service.episode_repo.find_by_season_id.return_value = []
        self.service.episode_repo.save.return_value = 10
        
        # Mock für die HTTP-Anfrage
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_image_data"
        mock_requests_get.return_value = mock_response
        
        # Scraped Daten einrichten
        anime_data = {
            "url": "https://aniworld.to/anime/test-anime",
            "title": "Test Anime",
            "description": "Eine Testbeschreibung",
            "cover_url": "https://aniworld.to/img/test.jpg",
            "original_title": "テストアニメ",
            "year": 2023,
            "status": "laufend",
            "studio": "Test Studio",
            "director": "Test Director",
            "seasons": [
                {
                    "number": 1,
                    "title": "Staffel 1",
                    "url": "https://aniworld.to/anime/test-anime/staffel-1",
                    "episode_count": 2,
                    "episodes": [
                        {
                            "number": 1,
                            "title": "Episode 1",
                            "url": "https://aniworld.to/anime/test-anime/staffel-1/episode-1",
                            "description": "Erste Episode"
                        },
                        {
                            "number": 2,
                            "title": "Episode 2",
                            "url": "https://aniworld.to/anime/test-anime/staffel-1/episode-2",
                            "description": "Zweite Episode"
                        }
                    ]
                }
            ]
        }
        
        # Methode aufrufen
        result = self.service.save_from_scraper_data(anime_data)
        
        # Ergebnis prüfen
        self.assertEqual(result, 1)  # Series ID
        self.service.anime_repo.save.assert_called()
        self.service.anime_repo.save_cover_data.assert_called_once_with(1, b"fake_image_data")
        self.service.season_repo.save.assert_called()
        self.assertEqual(self.service.episode_repo.save.call_count, 2)  # 2 Episoden
        
        # Prüfen der Cover-Bildabfrage
        mock_requests_get.assert_called_once_with("https://aniworld.to/img/test.jpg", timeout=10)
    
    def test_get_episode_by_url_found(self):
        """Test für get_episode_by_url, wenn die Episode gefunden wird"""
        # Mock-Objekte einrichten
        mock_episode = Episode(episode_id=10, season_id=5, episode_nummer=3)
        mock_season = Season(season_id=5, series_id=1, staffel_nummer=2)
        mock_anime = AnimeSeries(series_id=1, titel="Test Anime")
        
        self.service.episode_repo.find_by_url.return_value = mock_episode
        self.service.season_repo.find_by_id.return_value = mock_season
        self.service.anime_repo.find_by_id.return_value = mock_anime
        
        # Methode aufrufen
        result = self.service.get_episode_by_url("https://aniworld.to/anime/test-anime/staffel-2/episode-3")
        
        # Ergebnis prüfen
        self.assertIsNotNone(result)
        self.assertEqual(result, (mock_anime, mock_season, mock_episode))
        self.service.episode_repo.find_by_url.assert_called_once_with(
            "https://aniworld.to/anime/test-anime/staffel-2/episode-3"
        )
        self.service.season_repo.find_by_id.assert_called_once_with(5)
        self.service.anime_repo.find_by_id.assert_called_once_with(1)
    
    def test_get_episode_by_url_not_found(self):
        """Test für get_episode_by_url, wenn die Episode nicht gefunden wird"""
        # Mock-Objekte einrichten
        self.service.episode_repo.find_by_url.return_value = None
        
        # Methode aufrufen
        result = self.service.get_episode_by_url("https://aniworld.to/anime/test-anime/staffel-2/episode-3")
        
        # Ergebnis prüfen
        self.assertIsNone(result)
        self.service.episode_repo.find_by_url.assert_called_once_with(
            "https://aniworld.to/anime/test-anime/staffel-2/episode-3"
        )
        self.service.season_repo.find_by_id.assert_not_called()
        self.service.anime_repo.find_by_id.assert_not_called()


if __name__ == '__main__':
    unittest.main() 