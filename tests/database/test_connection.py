"""
Tests für die Datenbankverbindungsklasse
"""

import unittest
from unittest.mock import patch, MagicMock, call
import os

from src.aniworld.database.connection import DatabaseConnection


class TestDatabaseConnection(unittest.TestCase):
    """Testklasse für die Datenbankverbindung"""
    
    def setUp(self):
        """Test-Setup: Entferne eventuell vorhandene Instanz"""
        # Zurücksetzen der Singleton-Instanz vor jedem Test
        DatabaseConnection._instance = None
    
    def test_singleton_pattern(self):
        """Test, ob das Singleton-Muster korrekt funktioniert"""
        connection1 = DatabaseConnection()
        connection2 = DatabaseConnection()
        
        # Beide Instanzen sollten identisch sein
        self.assertIs(connection1, connection2)
    
    @patch('src.aniworld.database.connection.mysql.connector.connect')
    def test_get_connection(self, mock_connect):
        """Test, ob die Verbindung korrekt hergestellt wird"""
        # Mock-Objekte einrichten
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Context Manager testen
        db = DatabaseConnection()
        with db.get_connection() as conn:
            self.assertEqual(conn, mock_conn)
        
        # Verbindung sollte mit den korrekten Parametern hergestellt werden
        mock_connect.assert_called_once_with(
            host=db.host,
            user=db.user,
            password=db.password,
            database=db.database
        )
        
        # close sollte aufgerufen werden, nachdem der Context Manager verlassen wurde
        mock_conn.close.assert_called_once()
    
    @patch('src.aniworld.database.connection.mysql.connector.connect')
    def test_get_connection_with_error(self, mock_connect):
        """Test, ob Fehler korrekt behandelt werden"""
        # Mock-Objekte einrichten
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Fehler simulieren
        mock_conn.commit.side_effect = Exception("Testfehler")
        
        # Context Manager testen
        db = DatabaseConnection()
        with self.assertRaises(Exception):
            with db.get_connection() as conn:
                conn.commit()  # Dies sollte den Fehler auslösen
        
        # close sollte trotz Fehler aufgerufen werden
        mock_conn.close.assert_called_once()
    
    @patch('src.aniworld.database.connection.mysql.connector.connect')
    def test_test_connection(self, mock_connect):
        """Test, ob die Verbindungsprüfung korrekt funktioniert"""
        # Mock-Objekte einrichten
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ["5.7.32"]
        
        # Verbindungstest durchführen
        db = DatabaseConnection()
        result = db.test_connection()
        
        # Ergebnis prüfen
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once_with("SELECT VERSION()")
    
    @patch('src.aniworld.database.connection.mysql.connector.connect')
    def test_test_connection_failure(self, mock_connect):
        """Test, ob Fehler bei der Verbindungsprüfung korrekt behandelt werden"""
        # Mock-Fehler einrichten
        mock_connect.side_effect = Exception("Verbindungsfehler")
        
        # Verbindungstest durchführen
        db = DatabaseConnection()
        result = db.test_connection()
        
        # Ergebnis prüfen
        self.assertFalse(result)
    
    @patch.dict(os.environ, {
        "DB_HOST": "test-host",
        "DB_USER": "test-user",
        "DB_PASSWORD": "test-password",
        "DB_NAME": "test-db"
    })
    def test_environment_variables(self):
        """Test, ob Umgebungsvariablen korrekt verwendet werden"""
        # Neue Instanz erstellen
        db = DatabaseConnection()
        
        # Umgebungsvariablen sollten verwendet werden
        self.assertEqual(db.host, "test-host")
        self.assertEqual(db.user, "test-user")
        self.assertEqual(db.password, "test-password")
        self.assertEqual(db.database, "test-db")


if __name__ == '__main__':
    unittest.main() 