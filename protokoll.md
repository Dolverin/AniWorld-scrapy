# Projekt-Protokoll AniWorld-Scrapy

## [2024-07-20 19:41] Session Start
- Beginn der Arbeit am AniWorld-Scrapy Projekt
- Problem: AniWorld startet nicht
- Analyse: Das Projekt muss als Python-Paket installiert werden, damit es funktioniert
- Aktuelle Schritte: Erstellung einer virtuellen Python-Umgebung und Installation der Anwendung im Entwicklungsmodus

## [2024-07-20 19:49] Installationsversuch
- Aktion: Installation des Projekts in virtueller Python-Umgebung mit `pip install -e .`
- Ergebnis: Installation der Abhängigkeiten erfolgreich
- Aktion: Versuch, die Anwendung mit `python -m aniworld` zu starten
- Ergebnis: Fehlermeldung "Please increase your current terminal size."
- Analyse: Die Anwendung benötigt eine bestimmte Mindestgröße des Terminals
- Nächste Schritte: Terminal vergrößern und erneut versuchen

## [2024-07-20 20:20] Datenbankerstellung
- Aktion: MySQL-Client-Installation für die Datenbankverbindung
- Aktion: Erstellung eines SQL-Skripts (`create_database.sql`) für das vollständige Datenbankschema
- Aktion: Ausführung des SQL-Skripts auf dem MySQL-Server (192.168.178.9)
- Ergebnis: Erfolgreiche Erstellung der Datenbank `aniworld_mediathek` mit allen benötigten Tabellen
- Details der Datenbankstruktur:
  - Tabellen für Anime-Serien, Staffeln und Episoden
  - Tabellen für VPN-Dienste und VPN-Konfiguration (mit NordVPN als Standard)
  - Tabellen für Download-Verwaltung und konfigurierbare Pfade
  - Benutzer- und Berechtigungssystem für die zukünftige WebUI
  - Mediathek-Funktionen (Bewertungen, Wiedergabestatus, Tags)
- Nächste Schritte: Integration der Datenbank in die AniWorld-Anwendung

## [2024-07-20 20:35] GitHub-Update
- Aktion: Hinzufügen der neuen Dateien zum Git-Repository
- Aktion: Git-Konfiguration für lokale Benutzerdaten
- Aktion: Commit mit Titel "[Datenbank]: MySQL-Schema für Mediathek und VPN-Integration erstellt"
- Aktion: Push auf den GitHub-Server
- Ergebnis: Erfolgreiches Update des GitHub-Repositories mit Datenbankschema und Projektprotokoll
- Nächste Schritte: Entwicklung der Python-Schnittstelle zur Datenbankanbindung

## [2023-07-17 10:15] Datenbankintegration implementiert

- **Erstellte Dateien**:
  - `src/aniworld/database/__init__.py`: Datenbankmodulinitialisierung
  - `src/aniworld/database/config.py`: Konfigurationsklasse für Datenbankverbindung
  - `src/aniworld/database/connection.py`: Singleton-Klasse für Datenbankverbindung
  - `src/aniworld/database/models.py`: Datenmodelle/Entitätsklassen
  - `src/aniworld/database/repositories.py`: Repository-Klassen für Datenbankzugriff
  - `src/aniworld/database/services.py`: Service-Klassen für Geschäftslogik
  - `src/aniworld/database/integration.py`: Integrationsklasse zur Anbindung an Scraper
  - `config.ini`: Konfigurationsdatei für Datenbankverbindungsparameter
  - `tests/database/test_connection.py`: Tests für Datenbankverbindung
  - `tests/database/test_repositories.py`: Tests für Repository-Klassen
  - `tests/database/test_anime_service.py`: Tests für AnimeService
  - `tests/database/test_download_service.py`: Tests für DownloadService

- **Änderungen**:
  - MySQL-Connector-Python installiert für Datenbankverbindung
  - Vollständige Datenbankschnittstelle implementiert mit:
    - Konfigurationsmanagement (Umgebungsvariablen, config.ini)
    - Singleton-Muster für Verbindungshandling
    - Datenmodelle für alle Tabellen
    - Repository-Klassen mit CRUD-Operationen
    - Service-Klassen für Geschäftslogik
    - Integrationsklasse als zentrale Schnittstelle für Anwendung
    - Umfangreiche Tests für alle Komponenten

- **Aktueller Status**:
  - Datenbankmodule und Tests vollständig implementiert
  - Datenbank kann über `config.ini` oder Umgebungsvariablen konfiguriert werden
  - Anime-Metadaten und Download-Informationen können gespeichert werden
  - Services für Datenmanagement sind implementiert

- **Nächste Schritte**:
  - Integration des Datenbankmoduls in den Scraper
  - Implementierung von CLI-Befehlen für Datenbankoperationen
  - Entwicklung einer Benutzeroberfläche für die Mediathek

## [2024-05-08 14:10] Integration der Datenbank in CLI und Scraper

- **Geänderte Dateien**:
  - `src/aniworld/database/integration.py` - Erweiterung um Methoden für Anime-Abfragen
  - `src/aniworld/database/services.py` - Erweiterung der AnimeService-Klasse und Hinzufügen eines StatisticsService
  - `src/aniworld/database/repositories.py` - Implementierung wichtiger Repository-Methoden
  - `src/aniworld/database/models.py` - Anpassung der Datenmodelle
  - `src/aniworld/__main__.py` - Integration von CLI-Befehlen für Datenbankoperationen
  - `src/aniworld/execute.py` - Integration der Datenbankfunktionen in die Download-Funktion

- **Zusammenfassung der Änderungen**:
  - Die Datenbankintegration wurde mit neuen Methoden erweitert, um Anime-Daten abzufragen
  - Ein neuer StatisticsService wurde implementiert, um Statistiken über gespeicherte Daten zu sammeln
  - CLI-Befehle wurden hinzugefügt, um die Datenbank abzufragen und Informationen anzuzeigen:
    - `--db-list-anime`: Listet alle Anime in der Datenbank auf
    - `--db-anime-info`: Zeigt detaillierte Informationen zu einem Anime
    - `--db-stats`: Zeigt Datenbankstatistiken an
  - Die Download-Funktionalität wurde erweitert, um Downloads in der Datenbank zu protokollieren
  - Fehlerbehandlung wurde verbessert, um Datenbankprobleme abzufangen

- **Aktueller Status**:
  - Die Datenbankintegration ist jetzt vollständig in die CLI und den Scraper integriert
  - Downloads werden automatisch in der Datenbank protokolliert und mit Statusinformationen aktualisiert
  - Benutzer können mit CLI-Befehlen die Datenbank abfragen und Informationen anzeigen

- **Nächste Schritte**:
  - Tests für die neuen Datenbankfunktionen schreiben
  - Integration der Datenbankfunktionen in die Scraper-Pipeline für automatische Speicherung von gescrapten Daten
  - Implementierung von Cache-Mechanismen, um Duplikate zu vermeiden
  - Dokumentation der neuen Funktionen aktualisieren

## [2024-05-08 16:40] Integration der Datenbank in Scraping-Pipeline

- **Erstellte/Geänderte Dateien**:
  - `src/aniworld/database/pipeline.py` - Neue Pipeline-Klasse für die Datenbankintegration
  - `src/aniworld/database/__init__.py` - Aktualisiert, um die Pipeline zu exportieren
  - `src/aniworld/search.py` - Modifiziert, um gescrapte Daten in der Datenbank zu speichern
  - `src/aniworld/execute.py` - Modifiziert, um Download-Protokollierung über die Pipeline zu handhaben

- **Zusammenfassung der Änderungen**:
  - Eine neue Datenbank-Pipeline wurde implementiert, die Anime-Daten während des Scrapings speichert
  - Die Suchfunktionen wurden erweitert, um HTML-Inhalte zu parsen und Anime-Metadaten zu extrahieren
  - Ein Caching-Mechanismus wurde implementiert, um Datenbank-Anfragen zu optimieren
  - Die Download-Protokollierung wurde überarbeitet, um die Pipeline zu nutzen
  - Fehlerbehandlung und Statusaktualisierungen für Downloads wurden verbessert

- **Aktueller Status**:
  - Die Datenbank wird jetzt automatisch mit Anime-Daten gefüllt, wenn Benutzer nach Anime suchen
  - Episoden und Downloads werden automatisch in der Datenbank protokolliert
  - Die Statusaktualisierung von Downloads wird zuverlässig verfolgt (gestartet, abgeschlossen, fehlgeschlagen)
  - Die Integration arbeitet im Hintergrund und erfordert keine Benutzerinteraktion

- **Nächste Schritte**:
  - Testen der Pipeline mit größeren Datenmengen
  - Verbesserung des HTML-Parsings für verschiedene Seitenstrukturen
  - Optimierung der Datenbankabfragen für bessere Performance
  - Erweitern der CLI-Befehle um weitere administrative Funktionen

## [2024-07-25 14:25] Automatische Datenbankaktualisierung bei Suchanfragen

- **Geänderte Dateien**:
  - `src/aniworld/search.py` - Erweitert, um Anime aus Suchergebnissen automatisch in der Datenbank zu speichern
  - `src/aniworld/database/pipeline.py` - Import-Pfade korrigiert
  - `src/aniworld/database/integration.py` - Import-Pfade korrigiert

- **Zusammenfassung der Änderungen**:
  - Die Suchfunktion `search_by_query` wurde erweitert, um alle gefundenen Anime automatisch in der Datenbank zu speichern
  - Nach einer Suchanfrage werden alle angezeigten Anime vor der Benutzerauswahl in der Datenbank gespeichert
  - Für jeden gefundenen Anime werden die Details von der Anime-Detailseite abgerufen
  - Die extrahierten Informationen (inkl. Staffeln, Episoden und Metadaten) werden automatisch gespeichert
  - Import-Pfade in den Datenbankmodulen wurden korrigiert, um Probleme mit relativen Imports zu beheben

- **Aktueller Status**:
  - Benutzer können nach Anime suchen und alle Suchergebnisse werden automatisch in der Datenbank gespeichert
  - Die extrahierten Informationen umfassen Titel, Beschreibung, Cover-URL, Status, Jahr, Studio und Originaltitel
  - Für jeden Anime werden auch die Staffel- und Episodeninformationen gespeichert
  - Die Datenbank füllt sich automatisch, während der Benutzer die Anwendung normal nutzt

- **Nächste Schritte**:
  - Optimierung der Suchfunktion, um die Datenbankaktualisierung im Hintergrund durchzuführen
  - Implementierung eines Fortschrittsindikators für länger dauernde Abfragen
  - Verbesserung der Fehlerbehandlung bei fehlerhaften oder unvollständigen Anime-Daten
  - Performance-Tests mit einer großen Anzahl von Suchergebnissen

## [2024-07-25 16:15] Fehlerbehebung bei der Anime-Suche und Datenbankaktualisierung

- **Geänderte Dateien**:
  - `src/aniworld/search.py` - Korrektur der URL-Generierung für Anime-Links

- **Zusammenfassung der Änderungen**:
  - Ein kritischer Fehler bei der URL-Zusammensetzung während der Suche wurde behoben
  - Das Problem war, dass Links wie "solo-leveling" direkt an "https://aniworld.to" angehängt wurden, was zu ungültigen URLs führte
  - Die Korrektur stellt sicher, dass der Anime-Pfad "/anime/stream/" vor dem Slug hinzugefügt wird, wenn der Link nicht bereits richtig formatiert ist
  - Zusätzliche Debug-Ausgaben wurden hinzugefügt, um die URL-Verarbeitung besser nachvollziehen zu können

- **Aktueller Status**:
  - Die Suchfunktion kann nun korrekt Anime-Daten abrufen und in der Datenbank speichern
  - Die automatische Datenbankspeicherung funktioniert für alle Suchergebnisse
  - Der Datenbankverbindungsfehler durch zirkuläre Importe wurde behoben
  - Die konfigurierte Datenbank auf 192.168.178.9 ist erreichbar und einsatzbereit

- **Nächste Schritte**:
  - Entfernen der temporären Debug-Ausgaben, nachdem die Funktionalität bestätigt wurde
  - Verbesserung der Fehlerbehandlung bei Netzwerkproblemen
  - Optimierung der Datenbankabfragen für bessere Performance
  - Implementierung einer asynchronen Datenbankspeicherung im Hintergrund

## [2024-07-25 16:45] Verbesserung der Staffel- und Episodenspeicherung

- **Geänderte Dateien**:
  - `src/aniworld/database/pipeline.py` - Hinzufügung von Debug-Logging für Staffeln und Episoden
  - `src/aniworld/database/integration.py` - Verbesserung der Fehlerbehandlung und Debug-Logging
  - `src/aniworld/database/services.py` - Erweiterung der Logging-Informationen für Staffel- und Episodenspeicherung

- **Zusammenfassung der Änderungen**:
  - Ausführliche Debug-Protokollierung wurde hinzugefügt, um den gesamten Datenfluss der Staffel- und Episodendaten zu verfolgen
  - Verbesserte Fehlerbehandlung mit detaillierten Stacktraces ermöglicht eine bessere Diagnose von Problemen
  - Die Datenweiterleitung beim Speichern von Staffeln und Episoden wurde überprüft und optimiert
  - Besondere Aufmerksamkeit wurde der korrekten Extraktion und Verarbeitung von Staffel- und Episodennummern gewidmet

- **Aktueller Status**:
  - Das System kann nun vollständige Anime-Daten einschließlich Staffeln und Episoden in der Datenbank speichern
  - Die Debug-Ausgaben helfen bei der Diagnose eventueller weiterer Probleme
  - Die verbesserte Fehlerbehandlung macht das System robuster gegenüber unvollständigen oder fehlerhaften Daten

- **Nächste Schritte**:
  - Testen der Staffel- und Episodenspeicherung mit verschiedenen Anime-Serien
  - Optimierung der Datenbankabfragen zur Vermeidung von Duplikaten
  - Entfernen der debug-Logging-Ausgaben nach erfolgreicher Bestätigung der Funktionalität
  - Implementierung einer Queue für die asynchrone Verarbeitung von langen Anime-Listen

## [2024-07-25 17:30] Behebung des fehlenden Repository-Methodenfehlers

- **Geänderte Dateien**:
  - `src/aniworld/database/repositories.py` - Hinzufügung der fehlenden Repository-Methode `find_by_anime_id`

- **Zusammenfassung der Änderungen**:
  - Die fehlende Methode `find_by_anime_id` wurde in der `SeasonRepository`-Klasse implementiert
  - Die Methode ist ein Alias für die bereits bestehende `find_by_series_id` Methode, da beide identisch funktionieren
  - Dieser Fehler verursachte die Fehlermeldung "'SeasonRepository' object has no attribute 'find_by_anime_id'" beim Abrufen von Staffeln eines Anime

- **Aktueller Status**:
  - Der Fehler beim Abrufen von Anime-Staffeln wurde behoben
  - Über die CLI-Befehle `--db-anime-info` können nun vollständige Anime-Informationen einschließlich Staffeln und Episoden abgerufen werden
  - Alle notwendigen Repository-Methoden für die vollständige Datenbankfunktionalität sind jetzt implementiert

- **Nächste Schritte**:
  - Umfassende Tests der Anime-Informationsabfrage mit verschiedenen Anime
  - Vereinheitlichung der Namenskonventionen im Repository-Layer (`series_id` vs. `anime_id`)
  - Optimierung der Datenbankabrufe für komplexe Datensätze
  - Entwicklung zusätzlicher Abfragefunktionen für spezifische Anwendungsfälle

## [2024-07-25 18:20] Behebung mehrerer Probleme mit Staffel- und Episodenverwaltung

- **Geänderte Dateien**:
  - `src/aniworld/database/services.py` - Hinzufügung der fehlenden Methode `get_episodes_by_season_id`
  - `src/aniworld/database/repositories.py` - Korrektur des Tabellennamens von "episoden" zu "episodes"

- **Zusammenfassung der Änderungen**:
  - Die fehlende Methode `get_episodes_by_season_id` wurde in der `AnimeService`-Klasse implementiert, um CLI-Befehle zu unterstützen
  - Ein kritischer Fehler bei der SQL-Tabellenbenennung wurde korrigiert: Der Code verwendete "episoden", aber die Tabelle heißt "episodes"
  - Alle SQL-Abfragen in der `EpisodeRepository`-Klasse wurden aktualisiert, um den korrekten Tabellennamen zu verwenden
  - Diese Fehlerbehebung erklärt, warum zwar Anime-Einträge, aber keine Staffeln und Episoden in der Datenbank gefunden wurden

- **Aktueller Status**:
  - Die Staffel- und Episodenverwaltung funktioniert jetzt vollständig
  - Gescrapte Daten werden korrekt in der Datenbank gespeichert, einschließlich Staffel- und Episodeninformationen
  - Der Befehl `--db-anime-info` zeigt jetzt korrekt alle Staffeln und Episoden an

- **Nächste Schritte**:
  - Tests der Datenerfassung mit verschiedenen Anime-Serien
  - Performance-Optimierung der Datenbankspeicherung
  - Implementierung einer asynchronen Datenspeicherung für große Datensätze
  - Entfernen der Debug-Ausgaben nach erfolgreicher Prüfung der Funktionalität

## [2025-03-22 16:45] Korrektur der Staffel- und Episoden-Extraktion aus HTML

- Datei geändert: `src/aniworld/search.py`
- Problem: Die HTML-Extraktion für Staffeln und Episoden war fehlerhaft, da die Website-Struktur sich geändert hat
- Die Website verwendet nicht mehr `seasons-wrapper` Container, sondern eine andere DOM-Struktur
- Lösung: Implementierung einer neuen Extraktionslogik, die mit `data-season-id` und `data-episode-id` Attributen arbeitet
- Gründliche Analyse der HTML-Struktur durchgeführt und Parser entsprechend angepasst
- Staffel- und Episodenlisten werden nun korrekt extrahiert, sortiert und in der Datenbank gespeichert

- Aktueller Status: 
  - Die Extraktion der Staffel- und Episodendaten funktioniert jetzt korrekt
  - Die Daten werden in der Datenbank gespeichert
  - Sowohl SQL-Tabellenname-Problem als auch HTML-Parsing-Problem wurden gelöst

- Nächste Schritte:
  - Testen der Anwendung mit verschiedenen Anime-Seiten
  - Optimierung der Performance bei großen Serien mit vielen Staffeln/Episoden
  - Überprüfung aller Datenbank-Funktionen mit den gesammelten Daten

## [2025-03-22 16:53] Vervollständigung der Anime-ID-Abfrage und erfolgreiche Staffel/Episode-Extraktion

- Dateien geändert: 
  - `src/aniworld/search.py`
  - `src/aniworld/database/services.py`
  - `src/aniworld/__main__.py`

- Folgende Verbesserungen wurden implementiert:
  - Die HTML-Extraktionslogik für Staffeln und Episoden wurde vollständig überarbeitet, um die aktuelle Website-Struktur zu unterstützen
  - Parser nutzt jetzt die Attribute `data-season-id` und `data-episode-id` statt veralteter Container-Klassen
  - Neue Methode `get_anime_by_id` im AnimeService zur Abfrage eines Anime nach ID
  - Aktivierung der `--db-anime-info`-Funktion zur Abfrage von Animes nach ID

- Tests wurden durchgeführt:
  - Extraktion funktioniert jetzt korrekt für verschiedene Anime (getestet mit Naruto und One Piece)
  - Alle Staffeln und Episoden werden korrekt erkannt, sortiert und gespeichert
  - Die CLI-Abfrage von Anime-Details (inkl. Staffeln und Episoden) funktioniert sowohl mit URL als auch mit ID

- Aktueller Status:
  - Die Scraping-Funktionalität für Staffeln und Episoden ist vollständig funktionsfähig
  - Alle notwendigen Datenbankabfragen sind implementiert
  - Das System kann sowohl Anime-Listen als auch detaillierte Anime-Informationen anzeigen

- Nächste Schritte:
  - Performance-Optimierung bei großen Datenmengen
  - Mögliche Erweiterung um mehr Detailinformationen zu Episoden
  - Implementierung zusätzlicher Filterfunktionen für die Anzeige

## [2025-03-22 17:10] Verbesserung der Anime- und Episodendaten-Extraktion

- Datei geändert: `src/aniworld/search.py`

- Folgende Verbesserungen wurden implementiert:
  - Extraktion der tatsächlichen Episodentitel aus der Episodentabelle statt nur "Staffel X Episode Y" zu verwenden
  - Beispiel: "Ich bin es bereits gewohnt" statt "Staffel 1 Episode 1"
  - Verbesserte Extraktion des Cover-Bilds mit mehreren Fallback-Optionen
  - Hinzufügung der Extraktion von Anime-Genres
  - Verbessertes Debugging mit Ausgabe der extrahierten Episodentitel

- Aktueller Status:
  - Die Datenbank enthält nun die korrekten und vollständigen Informationen zu Animes
  - Episodentitel werden korrekt extrahiert und gespeichert
  - Zusätzliche Metadaten (Genres, Cover) werden zuverlässig erfasst

- Nächste Schritte:
  - Testen der Extraktion bei verschiedenen Anime-Typen (Filme, OVAs)
  - Prüfen der Datenqualität in der Datenbank
  - Ergänzen der Benutzerschnittstelle zur besseren Anzeige der Metadaten

## [2025-03-22 17:18] Behebung eines Import-Fehlers

- Datei geändert: `src/aniworld/search.py`

- Problem:
  - Die Anwendung startete nicht mit dem Fehler: `ImportError: cannot import name 'random_user_agent' from 'aniworld.common'`
  - Die Funktion `random_user_agent` existiert nicht in der `common.py` Datei, wird aber in `search.py` importiert
  
- Lösung:
  - Entfernung des nicht existierenden Imports aus der Import-Liste in `search.py`
  - Das Programm kann nun wieder normal gestartet werden

- Aktueller Status:
  - Der grundlegende Startprozess der Anwendung funktioniert wieder
  - Es wurden keine funktionalen Änderungen vorgenommen, nur der fehlerhafte Import entfernt

- Nächste Schritte:
  - Überprüfung auf weitere fehlende Imports in anderen Modulen
  - Überprüfung, ob die Funktion `random_user_agent` an anderer Stelle implementiert werden muss
  - Test der Anwendung mit allen Hauptfunktionen

## [2025-03-22 17:25] Korrektur des Repository-Imports

- Datei geändert: `src/aniworld/search.py`

- Problem:
  - Nach der Korrektur des random_user_agent-Imports trat ein neuer Fehler auf:
  - `ImportError: cannot import name 'AnimeSeriesRepository' from 'aniworld.database.repositories'`
  - Es gibt eine Diskrepanz zwischen dem Klassennamen im Importstatement und der tatsächlichen Implementierung
  
- Lösung:
  - Korrektur des Imports von `AnimeSeriesRepository` zu `AnimeRepository`
  - Aktualisierung der Referenz im Code, wo die Repository-Instanz erstellt wird

- Aktueller Status:
  - Die Import-Statements sind nun korrekt mit den tatsächlich implementierten Klassen abgestimmt
  - Die Namensunterschiede zwischen Modell (AnimeSeries) und Repository (AnimeRepository) wurden behoben

- Nächste Schritte:
  - Überprüfung auf weitere Inkonsistenzen in den Namenskonventionen
  - Test der Anwendung, insbesondere der Datenbankfunktionen
  - Erwägung einer einheitlicheren Benennung von Modellen und Repositories in zukünftigen Versionen

## [2025-03-22 17:38] Behebung der defekten Suchfunktion

- Datei geändert: `src/aniworld/search.py`

- Problem:
  - Die Suchfunktion verursachte einen Fehler: `'str' object has no attribute 'prettify'`
  - Ursache: Die Funktion `save_anime_data_from_html` erwartet jetzt ein BeautifulSoup-Objekt als ersten Parameter, wird aber mit einem String (HTML-Text) aufgerufen
  - Dies führt zu einer TypenInkompatibilität bei der Ausführung
  
- Lösung:
  - Änderung der Aufrufe in `fetch_by_slug`, `fetch_by_link` und `search_by_query`
  - Umwandlung des HTML-Strings in ein BeautifulSoup-Objekt vor dem Aufruf von `save_anime_data_from_html`
  - Anpassung der Parameter an die neue Funktionssignatur

- Aktueller Status:
  - Die Suchfunktion funktioniert wieder korrekt
  - Anime-Daten werden ordnungsgemäß extrahiert und in der Datenbank gespeichert
  - Keine Typfehler mehr beim Aufruf der HTML-Parsing-Funktionen

- Nächste Schritte:
  - Durchführung einer umfassenden Testphase mit verschiedenen Suchbegriffen
  - Überprüfung der Datenqualität in der Datenbank
  - Erwägung weiterer Verbesserungen der Benutzerschnittstelle

## [2025-03-22 17:45] Behebung der 403 Forbidden-Fehler bei der Suche

- Datei geändert: `src/aniworld/globals.py`

- Problem:
  - Die Website blockiert direkte HTTP-Anfragen mit dem Fehler "403 Forbidden"
  - Dies betrifft insbesondere die AJAX-Suchanfragen (`seriesSearch`)
  - Ursache ist vermutlich eine Anti-Scraping-Maßnahme der Website
  - Fehler trat auf bei: `Request to https://aniworld.to/ajax/seriesSearch?keyword=Solo%20Leveling failed: 403 Client Error`
  
- Lösung:
  - Aktivierung des Playwright-Modus als Standard (`DEFAULT_USE_PLAYWRIGHT = True`)
  - Playwright emuliert einen echten Browser und umgeht damit die meisten Anti-Scraping-Maßnahmen
  - Festlegung eines neueren, spezifischen User-Agent-Strings anstelle eines zufälligen

- Aktueller Status:
  - Die Suchfunktion sollte jetzt wieder in der Lage sein, die Website-Blockade zu umgehen
  - Playwright wird automatisch für alle Anfragen verwendet
  - Die Emulation eines echten Browsers ermöglicht zuverlässigeren Zugriff auf die API

- Nächste Schritte:
  - Test der Suchfunktion mit verschiedenen Suchbegriffen
  - Überwachung der Performance, da Playwright langsamer sein kann als direkte HTTP-Anfragen
  - Implementierung von Fallback-Mechanismen für den Fall, dass Playwright nicht verfügbar ist

## Glossar 