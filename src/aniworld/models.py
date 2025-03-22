from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AnimeSeries(Base):
    __tablename__ = "anime_series"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    cover_image = Column(String, nullable=True)
    genres = Column(String, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    seasons = relationship("Season", back_populates="anime", cascade="all, delete-orphan")

    def __repr__(self):
        return f"AnimeSeries(id={self.id}, title={self.title})"


class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True)
    anime_id = Column(Integer, ForeignKey("anime_series.id"), nullable=False)
    season_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    anime = relationship("AnimeSeries", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Season(id={self.id}, anime_id={self.anime_id}, season_id={self.season_id})"


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False)
    episode_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    season = relationship("Season", back_populates="episodes")
    downloads = relationship("Download", back_populates="episode", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Episode(id={self.id}, season_id={self.season_id}, episode_id={self.episode_id}, title={self.title})"


class Download(Base):
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False)
    hoster = Column(String, nullable=False)
    resolution = Column(String, nullable=True)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    episode = relationship("Episode", back_populates="downloads")

    def __repr__(self):
        return f"Download(id={self.id}, episode_id={self.episode_id}, hoster={self.hoster})" 