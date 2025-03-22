"""
Datenbankmodul für AniWorld-Scrapy
Enthält Klassen und Funktionen für den Zugriff auf die MySQL-Datenbank
"""

# Importiere Hauptklassen für einfache Verfügbarkeit
from .connection import DatabaseConnection
from .models import AnimeSeries, Season, Episode, Download
from .repositories import AnimeRepository, SeasonRepository, EpisodeRepository, DownloadRepository
from .services import AnimeService, DownloadService
from .integration import DatabaseIntegration
from .pipeline import DatabasePipeline, get_pipeline

# Exportiere Funktionsnamen für "from aniworld.database import *"
__all__ = [
    'DatabaseConnection',
    'AnimeSeries', 'Season', 'Episode', 'Download',
    'AnimeRepository', 'SeasonRepository', 'EpisodeRepository', 'DownloadRepository',
    'AnimeService', 'DownloadService',
    'DatabaseIntegration',
    'DatabasePipeline', 'get_pipeline'
] 