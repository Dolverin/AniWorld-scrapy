"""
Konfigurationsmodul für die Datenbankverbindung
"""

import os
import configparser
import logging
from pathlib import Path
from typing import Dict, Any


class DatabaseConfig:
    """
    Konfigurationsklasse für die Datenbankverbindung.
    
    Diese Klasse lädt Konfigurationsparameter aus drei Quellen (in dieser Prioritätsreihenfolge):
    1. Umgebungsvariablen
    2. Konfigurationsdatei (config.ini)
    3. Standardwerte
    """
    
    # Standardwerte für die Konfiguration
    DEFAULT_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'aniworld',
        'password': 'password',
        'database': 'aniworld_db',
        'charset': 'utf8mb4',
        'use_pure': True,
        'autocommit': False,
        'pool_size': 5,
    }
    
    # Umgebungsvariablen-Mapping
    ENV_MAPPING = {
        'host': 'DB_HOST',
        'port': 'DB_PORT',
        'user': 'DB_USER',
        'password': 'DB_PASSWORD',
        'database': 'DB_DATABASE',
    }
    
    # Konfigurationsdatei-Abschnitt
    CONFIG_SECTION = 'database'
    
    def __init__(self, config_file: str = None):
        """
        Initialisiert die Datenbankkonfiguration.
        
        Args:
            config_file: Optionaler Pfad zur Konfigurationsdatei (default: Sucht nach config.ini)
        """
        self.logger = logging.getLogger('aniworld.db.config')
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Wenn keine Konfigurationsdatei angegeben ist, suchen wir in üblichen Verzeichnissen
        if config_file is None:
            possible_paths = [
                'config.ini',  # Aktuelles Verzeichnis
                'src/aniworld/config.ini',  # Anwendungsverzeichnis
                str(Path.home() / '.aniworld' / 'config.ini'),  # Home-Verzeichnis
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config_file = path
                    self.logger.info(f"Konfigurationsdatei gefunden: {path}")
                    break
        
        # Laden der Konfigurationsdatei, falls vorhanden
        if config_file and os.path.exists(config_file):
            self._load_from_config_file(config_file)
        
        # Laden von Umgebungsvariablen (höchste Priorität)
        self._load_from_environment()
        
        # Typkonvertierung für numerische Werte
        self._convert_types()
        
        self.logger.debug(f"Datenbankkonfiguration initialisiert: {self.get_sanitized_config()}")
    
    def _load_from_config_file(self, config_file: str) -> None:
        """
        Lädt Konfigurationsparameter aus einer Konfigurationsdatei.
        
        Args:
            config_file: Pfad zur Konfigurationsdatei
        """
        try:
            parser = configparser.ConfigParser()
            parser.read(config_file)
            
            if self.CONFIG_SECTION in parser:
                for key in self.config:
                    if key in parser[self.CONFIG_SECTION]:
                        self.config[key] = parser[self.CONFIG_SECTION][key]
                        self.logger.debug(f"Konfiguration aus Datei geladen: {key}")
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Konfigurationsdatei: {e}")
    
    def _load_from_environment(self) -> None:
        """
        Lädt Konfigurationsparameter aus Umgebungsvariablen.
        """
        for key, env_var in self.ENV_MAPPING.items():
            if env_var in os.environ:
                self.config[key] = os.environ[env_var]
                self.logger.debug(f"Konfiguration aus Umgebungsvariable geladen: {key}")
    
    def _convert_types(self) -> None:
        """
        Konvertiert Konfigurationsparameter in die richtigen Typen.
        """
        # Port muss eine Ganzzahl sein
        if isinstance(self.config['port'], str):
            try:
                self.config['port'] = int(self.config['port'])
            except ValueError:
                self.logger.warning(f"Ungültiger Port-Wert: {self.config['port']}, verwende Standard: {self.DEFAULT_CONFIG['port']}")
                self.config['port'] = self.DEFAULT_CONFIG['port']
        
        # Pool-Größe muss eine Ganzzahl sein
        if isinstance(self.config['pool_size'], str):
            try:
                self.config['pool_size'] = int(self.config['pool_size'])
            except ValueError:
                self.logger.warning(f"Ungültige Pool-Größe: {self.config['pool_size']}, verwende Standard: {self.DEFAULT_CONFIG['pool_size']}")
                self.config['pool_size'] = self.DEFAULT_CONFIG['pool_size']
        
        # Autocommit und use_pure müssen Booleans sein
        for key in ['autocommit', 'use_pure']:
            if isinstance(self.config[key], str):
                if self.config[key].lower() in ['true', '1', 'yes', 'y']:
                    self.config[key] = True
                elif self.config[key].lower() in ['false', '0', 'no', 'n']:
                    self.config[key] = False
    
    def get_config(self) -> Dict[str, Any]:
        """
        Gibt die aktuelle Konfiguration zurück.
        
        Returns:
            Dict mit allen Konfigurationsparametern
        """
        return self.config.copy()
    
    def get_sanitized_config(self) -> Dict[str, Any]:
        """
        Gibt eine gesäuberte Version der Konfiguration zurück (ohne Passwort).
        
        Returns:
            Dict mit Konfigurationsparametern ohne sensible Daten
        """
        config = self.config.copy()
        config['password'] = '******'  # Passwort verbergen
        return config
    
    def get_connection_params(self) -> Dict[str, Any]:
        """
        Gibt die Parameter für die Datenbankverbindung zurück.
        
        Returns:
            Dict mit den Parametern für mysql.connector.connect()
        """
        return {
            'host': self.config['host'],
            'port': self.config['port'],
            'user': self.config['user'],
            'password': self.config['password'],
            'database': self.config['database'],
            'charset': self.config['charset'],
            'use_pure': self.config['use_pure'],
            'autocommit': self.config['autocommit'],
            'pool_size': self.config['pool_size'],
        }


# Singleton-Instanz der Konfiguration
_config_instance = None


def get_config(config_file: str = None) -> DatabaseConfig:
    """
    Gibt die Singleton-Instanz der Datenbankkonfiguration zurück.
    
    Args:
        config_file: Optionaler Pfad zur Konfigurationsdatei
    
    Returns:
        DatabaseConfig-Instanz
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = DatabaseConfig(config_file)
    return _config_instance


# Beispiel für eine Konfigurationsdatei (config.ini):
"""
[database]
host = localhost
port = 3306
user = aniworld
password = sicheres_passwort
database = aniworld_db
charset = utf8mb4
use_pure = true
autocommit = false
pool_size = 5
""" 