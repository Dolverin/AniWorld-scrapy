"""
Datenmodelle für die Datenbankentitäten
Verwendet Dataclasses für eine einfache Serialisierung/Deserialisierung
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Union

@dataclass
class AnimeSeries:
    """Repräsentiert eine Anime-Serie in der Datenbank"""
    series_id: Optional[int] = None
    titel: str = ""
    original_titel: Optional[str] = None
    beschreibung: Optional[str] = None
    cover_url: Optional[str] = None
    cover_data: Optional[bytes] = None
    erscheinungsjahr: Optional[int] = None
    status: str = "laufend"
    studio: Optional[str] = None
    regisseur: Optional[str] = None
    zielgruppe: Optional[str] = None
    fsk: Optional[str] = None
    bewertung: Optional[float] = None
    aniworld_url: Optional[str] = None
    erstellt_am: Optional[datetime] = None
    aktualisiert_am: Optional[datetime] = None

@dataclass
class Season:
    """Repräsentiert eine Staffel einer Anime-Serie"""
    season_id: Optional[int] = None
    series_id: int = 0
    staffel_nummer: int = 0
    titel: Optional[str] = None
    beschreibung: Optional[str] = None
    erscheinungsjahr: Optional[int] = None
    anzahl_episoden: Optional[int] = None
    aniworld_url: Optional[str] = None
    
@dataclass
class Episode:
    """Repräsentiert eine Episode einer Anime-Staffel"""
    episode_id: Optional[int] = None
    season_id: int = 0
    episode_nummer: int = 0
    titel: Optional[str] = None
    beschreibung: Optional[str] = None
    laufzeit: Optional[int] = None
    luftdatum: Optional[datetime] = None
    aniworld_url: Optional[str] = None
    
@dataclass
class Download:
    """Repräsentiert einen Download einer Episode"""
    download_id: Optional[int] = None
    episode_id: int = 0
    provider_id: int = 0
    language_id: int = 0
    speicherlink: str = ""
    lokaler_pfad: Optional[str] = None
    dateigroesse: Optional[int] = None
    qualitaet: Optional[str] = None
    download_datum: Optional[datetime] = None
    format: Optional[str] = None
    hash_wert: Optional[str] = None
    status: str = "geplant"
    notizen: Optional[str] = None
    download_pfad_id: Optional[int] = None
    vpn_genutzt: bool = False
    vpn_id: Optional[int] = None
    vpn_server_id: Optional[int] = None
    download_geschwindigkeit: Optional[float] = None
    benutzer_id: Optional[int] = None

@dataclass
class Provider:
    """Repräsentiert einen Content-Provider (VOE, Vidoza, etc.)"""
    provider_id: Optional[int] = None
    name: str = ""
    base_url: Optional[str] = None
    aktiv: bool = True

@dataclass
class Language:
    """Repräsentiert eine Sprache (German Dub, English Sub, etc.)"""
    language_id: Optional[int] = None
    name: str = ""
    code: str = ""

@dataclass
class Genre:
    """Repräsentiert ein Genre (Action, Comedy, etc.)"""
    genre_id: Optional[int] = None
    name: str = ""
    beschreibung: Optional[str] = None

@dataclass
class Tag:
    """Repräsentiert ein Tag für eine Anime-Serie"""
    tag_id: Optional[int] = None
    name: str = ""

@dataclass
class VpnService:
    """Repräsentiert einen VPN-Dienst"""
    vpn_id: Optional[int] = None
    name: str = ""
    aktiv: bool = False
    standard_service: bool = False
    api_basis_url: Optional[str] = None
    beschreibung: Optional[str] = None
    erstellt_am: Optional[datetime] = None
    aktualisiert_am: Optional[datetime] = None

@dataclass
class DownloadPfad:
    """Repräsentiert einen Pfad für Downloads"""
    pfad_id: Optional[int] = None
    pfad: str = ""
    beschreibung: Optional[str] = None
    standard_pfad: bool = False
    verfuegbar: bool = True
    freier_speicherplatz: Optional[int] = None
    gesamter_speicherplatz: Optional[int] = None
    aktiv: bool = True
    erstellt_am: Optional[datetime] = None
    aktualisiert_am: Optional[datetime] = None

@dataclass
class Benutzer:
    """Repräsentiert einen Benutzer des Systems"""
    benutzer_id: Optional[int] = None
    benutzername: str = ""
    passwort_hash: str = ""
    email: Optional[str] = None
    vorname: Optional[str] = None
    nachname: Optional[str] = None
    rolle: str = "normal"
    aktiv: bool = True
    letzter_login: Optional[datetime] = None
    api_token: Optional[str] = None
    api_token_ablauf: Optional[datetime] = None
    erstellt_am: Optional[datetime] = None
    aktualisiert_am: Optional[datetime] = None 