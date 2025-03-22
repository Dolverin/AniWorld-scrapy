-- Erstelle Datenbank
CREATE DATABASE IF NOT EXISTS aniworld_mediathek CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE aniworld_mediathek;

-- Tabelle für Sprachen
CREATE TABLE languages (
    language_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    code VARCHAR(10) NOT NULL UNIQUE
);

-- Tabelle für Provider
CREATE TABLE providers (
    provider_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(255),
    aktiv BOOLEAN DEFAULT TRUE
);

-- Tabelle für Genres/Kategorien
CREATE TABLE genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    beschreibung TEXT
);

-- Haupttabelle für Anime-Serien
CREATE TABLE anime_series (
    series_id INT AUTO_INCREMENT PRIMARY KEY,
    titel VARCHAR(255) NOT NULL,
    original_titel VARCHAR(255),
    beschreibung TEXT,
    cover_url VARCHAR(255),
    cover_data MEDIUMBLOB,
    erscheinungsjahr YEAR,
    status ENUM('laufend', 'abgeschlossen', 'angekündigt') DEFAULT 'laufend',
    studio VARCHAR(100),
    regisseur VARCHAR(100),
    zielgruppe ENUM('Shonen', 'Seinen', 'Shojo', 'Josei', 'Kodomo', 'Allgemein'),
    fsk VARCHAR(10),
    bewertung DECIMAL(3,1),
    aniworld_url VARCHAR(255) UNIQUE,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Verknüpfungstabelle zwischen Anime und Genres (n:m)
CREATE TABLE anime_genres (
    series_id INT,
    genre_id INT,
    PRIMARY KEY (series_id, genre_id),
    FOREIGN KEY (series_id) REFERENCES anime_series(series_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
);

-- Tabelle für Staffeln
CREATE TABLE seasons (
    season_id INT AUTO_INCREMENT PRIMARY KEY,
    series_id INT NOT NULL,
    staffel_nummer INT NOT NULL,
    titel VARCHAR(255),
    beschreibung TEXT,
    erscheinungsjahr YEAR,
    anzahl_episoden INT,
    aniworld_url VARCHAR(255),
    FOREIGN KEY (series_id) REFERENCES anime_series(series_id) ON DELETE CASCADE,
    UNIQUE KEY (series_id, staffel_nummer)
);

-- Tabelle für Episoden
CREATE TABLE episodes (
    episode_id INT AUTO_INCREMENT PRIMARY KEY,
    season_id INT NOT NULL,
    episode_nummer INT NOT NULL,
    titel VARCHAR(255),
    beschreibung TEXT,
    laufzeit INT COMMENT 'Laufzeit in Minuten',
    luftdatum DATE,
    aniworld_url VARCHAR(255) UNIQUE,
    FOREIGN KEY (season_id) REFERENCES seasons(season_id) ON DELETE CASCADE,
    UNIQUE KEY (season_id, episode_nummer)
);

-- Tabelle für VPN-Dienste
CREATE TABLE vpn_services (
    vpn_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT 'z.B. NordVPN, ExpressVPN, etc.',
    aktiv BOOLEAN DEFAULT FALSE,
    standard_service BOOLEAN DEFAULT FALSE,
    api_basis_url VARCHAR(255),
    beschreibung TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabelle für VPN-Zugangsdaten (mit Verschlüsselung)
CREATE TABLE vpn_credentials (
    credential_id INT AUTO_INCREMENT PRIMARY KEY,
    vpn_id INT NOT NULL,
    benutzername VARCHAR(255) NOT NULL,
    passwort_verschluesselt VARBINARY(512) NOT NULL,
    initialisierungsvektor VARBINARY(255) COMMENT 'Für Verschlüsselungsalgorithmen',
    api_token_verschluesselt VARBINARY(512),
    api_token_ablauf DATETIME,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (vpn_id) REFERENCES vpn_services(vpn_id) ON DELETE CASCADE
);

-- Tabelle für VPN-Server
CREATE TABLE vpn_servers (
    server_id INT AUTO_INCREMENT PRIMARY KEY,
    vpn_id INT NOT NULL,
    server_name VARCHAR(255) NOT NULL,
    server_adresse VARCHAR(255) NOT NULL,
    land VARCHAR(100),
    stadt VARCHAR(100),
    protokoll ENUM('UDP', 'TCP', 'IKEv2', 'OpenVPN', 'WireGuard', 'SOCKS5') DEFAULT 'UDP',
    port INT,
    last_ping INT COMMENT 'Latenz in ms',
    last_ping_time TIMESTAMP,
    max_geschwindigkeit INT COMMENT 'in Mbps',
    belastung DECIMAL(5,2) COMMENT 'Serverauslastung in Prozent',
    favorit BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (vpn_id) REFERENCES vpn_services(vpn_id) ON DELETE CASCADE
);

-- Tabelle für Pfade (Download-Verzeichnisse)
CREATE TABLE download_pfade (
    pfad_id INT AUTO_INCREMENT PRIMARY KEY,
    pfad VARCHAR(255) NOT NULL,
    beschreibung VARCHAR(255),
    standard_pfad BOOLEAN DEFAULT FALSE,
    verfuegbar BOOLEAN DEFAULT TRUE,
    freier_speicherplatz BIGINT COMMENT 'in Bytes, wird periodisch aktualisiert',
    gesamter_speicherplatz BIGINT COMMENT 'in Bytes',
    aktiv BOOLEAN DEFAULT TRUE,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabelle für Downloads
CREATE TABLE downloads (
    download_id INT AUTO_INCREMENT PRIMARY KEY,
    episode_id INT NOT NULL,
    provider_id INT NOT NULL,
    language_id INT NOT NULL,
    speicherlink VARCHAR(255) NOT NULL,
    lokaler_pfad VARCHAR(255),
    dateigroesse BIGINT COMMENT 'Größe in Bytes',
    qualitaet VARCHAR(20) COMMENT 'z.B. 1080p, 720p',
    download_datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    format VARCHAR(10) COMMENT 'z.B. MP4, MKV',
    hash_wert VARCHAR(64) COMMENT 'Für Integritätsprüfung',
    status ENUM('geplant', 'läuft', 'abgeschlossen', 'fehlgeschlagen') DEFAULT 'geplant',
    notizen TEXT,
    download_pfad_id INT,
    vpn_genutzt BOOLEAN DEFAULT FALSE,
    vpn_id INT,
    vpn_server_id INT,
    download_geschwindigkeit DECIMAL(10,2) COMMENT 'in MB/s',
    benutzer_id INT,
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id) ON DELETE RESTRICT,
    FOREIGN KEY (language_id) REFERENCES languages(language_id) ON DELETE RESTRICT,
    FOREIGN KEY (download_pfad_id) REFERENCES download_pfade(pfad_id) ON DELETE SET NULL,
    FOREIGN KEY (vpn_id) REFERENCES vpn_services(vpn_id) ON DELETE SET NULL,
    FOREIGN KEY (vpn_server_id) REFERENCES vpn_servers(server_id) ON DELETE SET NULL
);

-- Tabelle für Tags (zusätzliche Schlagwörter)
CREATE TABLE tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Verknüpfungstabelle zwischen Anime und Tags (n:m)
CREATE TABLE anime_tags (
    series_id INT,
    tag_id INT,
    PRIMARY KEY (series_id, tag_id),
    FOREIGN KEY (series_id) REFERENCES anime_series(series_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
);

-- Tabelle für Benutzer (für WebUI)
CREATE TABLE benutzer (
    benutzer_id INT AUTO_INCREMENT PRIMARY KEY,
    benutzername VARCHAR(50) NOT NULL UNIQUE,
    passwort_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    vorname VARCHAR(100),
    nachname VARCHAR(100),
    rolle ENUM('admin', 'poweruser', 'normal', 'gast') DEFAULT 'normal',
    aktiv BOOLEAN DEFAULT TRUE,
    letzter_login TIMESTAMP,
    api_token VARCHAR(255),
    api_token_ablauf DATETIME,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabelle für Benutzereinstellungen
CREATE TABLE benutzer_einstellungen (
    einstellung_id INT AUTO_INCREMENT PRIMARY KEY,
    benutzer_id INT NOT NULL,
    standard_download_pfad_id INT,
    bevorzugte_sprache_id INT,
    bevorzugter_provider_id INT,
    standard_qualitaet VARCHAR(20),
    vpn_nutzen BOOLEAN DEFAULT FALSE,
    bevorzugter_vpn_id INT,
    bevorzugter_vpn_server_id INT,
    benachrichtigungen_aktiv BOOLEAN DEFAULT TRUE,
    dark_mode BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (benutzer_id) REFERENCES benutzer(benutzer_id) ON DELETE CASCADE,
    FOREIGN KEY (standard_download_pfad_id) REFERENCES download_pfade(pfad_id) ON DELETE SET NULL,
    FOREIGN KEY (bevorzugte_sprache_id) REFERENCES languages(language_id) ON DELETE SET NULL,
    FOREIGN KEY (bevorzugter_provider_id) REFERENCES providers(provider_id) ON DELETE SET NULL,
    FOREIGN KEY (bevorzugter_vpn_id) REFERENCES vpn_services(vpn_id) ON DELETE SET NULL,
    FOREIGN KEY (bevorzugter_vpn_server_id) REFERENCES vpn_servers(server_id) ON DELETE SET NULL
);

-- Tabelle für Benutzer-Bewertungen und Kommentare
CREATE TABLE user_ratings (
    rating_id INT AUTO_INCREMENT PRIMARY KEY,
    series_id INT,
    bewertung DECIMAL(3,1) NOT NULL CHECK (bewertung BETWEEN 0 AND 10),
    kommentar TEXT,
    benutzer_name VARCHAR(100) NOT NULL,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (series_id) REFERENCES anime_series(series_id) ON DELETE CASCADE
);

-- Tabelle für Wiedergabestatus
CREATE TABLE playback_status (
    status_id INT AUTO_INCREMENT PRIMARY KEY,
    episode_id INT NOT NULL,
    benutzer_name VARCHAR(100) NOT NULL,
    position INT COMMENT 'Position in Sekunden',
    abgeschlossen BOOLEAN DEFAULT FALSE,
    letzter_zugriff TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE,
    UNIQUE KEY (episode_id, benutzer_name)
);

-- Tabelle für allgemeine Systemkonfiguration
CREATE TABLE konfiguration (
    config_id INT AUTO_INCREMENT PRIMARY KEY,
    schluessel VARCHAR(100) NOT NULL UNIQUE,
    wert TEXT,
    beschreibung TEXT,
    kategorie VARCHAR(100) NOT NULL,
    typ ENUM('text', 'zahl', 'boolean', 'json', 'pfad') NOT NULL,
    bearbeitbar BOOLEAN DEFAULT TRUE,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Standarddaten für Sprachen einfügen
INSERT INTO languages (name, code) VALUES 
('German Dub', 'de_dub'),
('German Sub', 'de_sub'),
('English Sub', 'en_sub');

-- Standarddaten für Provider einfügen
INSERT INTO providers (name, base_url) VALUES 
('Vidoza', 'https://vidoza.net'),
('VOE', 'https://voe.sx'),
('Doodstream', 'https://dood.to'),
('Vidmoly', 'https://vidmoly.to'),
('Streamtape', 'https://streamtape.com'),
('SpeedFiles', NULL);

-- Eintrag für NordVPN
INSERT INTO vpn_services (name, aktiv, standard_service, api_basis_url, beschreibung) VALUES
('NordVPN', true, true, 'https://api.nordvpn.com', 'NordVPN-Dienst für sichere Downloads');

-- Standardwerte für Konfiguration
INSERT INTO konfiguration (schluessel, wert, beschreibung, kategorie, typ) VALUES
('standard_download_pfad', '/home/media/downloads', 'Standardpfad für Downloads', 'downloads', 'pfad'),
('max_gleichzeitige_downloads', '3', 'Maximale Anzahl gleichzeitiger Downloads', 'downloads', 'zahl'),
('download_geschwindigkeit_limit', '0', '0 = unbegrenzt, sonst in KB/s', 'downloads', 'zahl'),
('vpn_immer_nutzen', 'true', 'VPN für alle Downloads aktivieren', 'sicherheit', 'boolean'),
('automatisches_tagging', 'true', 'Automatische Erstellung von Tags basierend auf Metadaten', 'metadaten', 'boolean'),
('webui_port', '8080', 'Port für die WebUI', 'server', 'zahl'),
('api_token_lebensdauer', '86400', 'Lebensdauer von API-Tokens in Sekunden (24h)', 'sicherheit', 'zahl');

-- Standardpfad für Downloads einfügen
INSERT INTO download_pfade (pfad, beschreibung, standard_pfad) VALUES
('/home/media/downloads', 'Standard-Download-Verzeichnis', true);

-- Admin-Benutzer für WebUI erstellen
INSERT INTO benutzer (benutzername, passwort_hash, email, vorname, nachname, rolle) VALUES
('admin', '$2y$10$3eJwbj.XgmpjR5zF4UCdje1wxKymVjXWU2ipFXZOfrUfTjC5jBgEW', 'admin@example.com', 'Admin', 'User', 'admin');
-- Passwort-Hash für 'admin123' 