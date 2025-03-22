"""
Datenbankverbindungsmodul für AniWorld-Scrapy
"""

import logging
import mysql.connector
from contextlib import contextmanager
from typing import Optional, ContextManager

from src.aniworld.database.config import get_config


class DatabaseConnection:
    """
    Singleton-Klasse für die Verwaltung der MySQL-Datenbankverbindung.
    
    Diese Klasse implementiert das Singleton-Pattern, um sicherzustellen,
    dass nur eine Datenbankverbindungsinstanz existiert. Sie bietet Methoden
    zur Verwaltung und zum Testen der Verbindung zur MySQL-Datenbank.
    """
    
    _instance = None
    
    def __new__(cls):
        """
        Implementiert das Singleton-Pattern für die Datenbankverbindung.
        
        Returns:
            Die einzige Instanz der DatabaseConnection-Klasse
        """
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Initialisiert die Datenbankverbindung, aber nur einmal.
        """
        if self._initialized:
            return
        
        self.logger = logging.getLogger('aniworld.db.connection')
        self.logger.info("Initialisiere Datenbankverbindung")
        
        # Datenbankkonfiguration aus Config-Klasse laden
        self.config = get_config()
        self.connection_params = self.config.get_connection_params()
        
        self.logger.debug(f"Datenbankparameter: {self.config.get_sanitized_config()}")
        
        self._initialized = True
    
    @classmethod
    def instance(cls) -> 'DatabaseConnection':
        """
        Gibt die Singleton-Instanz der Datenbankverbindung zurück.
        
        Returns:
            Die einzige Instanz der DatabaseConnection-Klasse
        """
        return cls()
    
    @contextmanager
    def get_connection(self) -> ContextManager[mysql.connector.MySQLConnection]:
        """
        Stellt eine Datenbankverbindung her und gibt sie als Context-Manager zurück.
        
        Diese Methode stellt sicher, dass die Verbindung nach der Verwendung
        ordnungsgemäß geschlossen wird.
        
        Yields:
            Eine MySQL-Verbindung
            
        Raises:
            mysql.connector.Error: Bei Problemen mit der Datenbankverbindung
        """
        connection = None
        try:
            # Verbindung herstellen
            self.logger.debug("Stelle Datenbankverbindung her")
            connection = mysql.connector.connect(**self.connection_params)
            
            # Verbindung zurückgeben
            yield connection
            
        except mysql.connector.Error as e:
            self.logger.error(f"Fehler bei der Datenbankverbindung: {e}")
            raise
        
        finally:
            # Verbindung schließen, falls sie existiert
            if connection is not None and connection.is_connected():
                self.logger.debug("Schließe Datenbankverbindung")
                connection.close()
    
    def test_connection(self) -> bool:
        """
        Testet die Datenbankverbindung.
        
        Diese Methode versucht, eine Verbindung zur Datenbank herzustellen
        und eine einfache Abfrage auszuführen.
        
        Returns:
            True, wenn die Verbindung erfolgreich ist, sonst False
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT VERSION() AS version")
                    result = cursor.fetchone()
                    version = result.get('version', 'unbekannt')
                    self.logger.info(f"Datenbankverbindung erfolgreich getestet. MySQL-Version: {version}")
                    return True
        
        except Exception as e:
            self.logger.error(f"Datenbankverbindungstest fehlgeschlagen: {e}")
            return False 