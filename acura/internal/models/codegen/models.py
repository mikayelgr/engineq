from typing import Any, List, Optional

from pgvector.sqlalchemy.vector import VECTOR
from sqlalchemy import ARRAY, Boolean, Column, Date, DateTime, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, String, Table, Text, UniqueConstraint, Uuid, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import uuid

class Base(DeclarativeBase):
    pass


class SchemaMigrations(Base):
    __tablename__ = 'schema_migrations'
    __table_args__ = (
        PrimaryKeyConstraint('version', name='schema_migrations_pkey'),
    )

    version: Mapped[str] = mapped_column(String, primary_key=True)


class Subscribers(Base):
    __tablename__ = 'subscribers'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='subscribers_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    license: Mapped[uuid.UUID] = mapped_column(Uuid, server_default=text('gen_random_uuid()'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    note: Mapped[Optional[str]] = mapped_column(Text)

    suggestion: Mapped[List['Suggestions']] = relationship('Suggestions', secondary='playback', back_populates='subscriber')
    playlists: Mapped[List['Playlists']] = relationship('Playlists', back_populates='subscribers')
    prompts: Mapped[List['Prompts']] = relationship('Prompts', back_populates='subscribers')


class Tracks(Base):
    __tablename__ = 'tracks'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='tracks_pkey'),
        UniqueConstraint('title', 'artist', name='tracks_title_artist_key'),
        Index('tracks_search_embedding_idx', 'search_embedding')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    artist: Mapped[str] = mapped_column(String)
    duration: Mapped[int] = mapped_column(Integer)
    uri: Mapped[str] = mapped_column(Text)
    explicit: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    image: Mapped[Optional[str]] = mapped_column(Text)
    search_embedding: Mapped[Optional[Any]] = mapped_column(VECTOR(1024))
    genres: Mapped[Optional[list]] = mapped_column(ARRAY(Text()))

    suggestions: Mapped[List['Suggestions']] = relationship('Suggestions', back_populates='tracks')


class Playlists(Base):
    __tablename__ = 'playlists'
    __table_args__ = (
        ForeignKeyConstraint(['sid'], ['subscribers.id'], ondelete='CASCADE', name='playlists_sid_fkey'),
        PrimaryKeyConstraint('id', name='playlists_pkey'),
        UniqueConstraint('sid', 'created_at', name='playlists_sid_created_at_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sid: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.date]] = mapped_column(Date, server_default=text('now()'))

    subscribers: Mapped[Optional['Subscribers']] = relationship('Subscribers', back_populates='playlists')
    suggestions: Mapped[List['Suggestions']] = relationship('Suggestions', back_populates='playlists')


class Prompts(Base):
    __tablename__ = 'prompts'
    __table_args__ = (
        ForeignKeyConstraint(['sid'], ['subscribers.id'], ondelete='CASCADE', name='prompts_sid_fkey'),
        PrimaryKeyConstraint('id', name='prompts_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt: Mapped[str] = mapped_column(Text)
    sid: Mapped[int] = mapped_column(Integer)
    active_when: Mapped[Optional[str]] = mapped_column(Text)

    subscribers: Mapped['Subscribers'] = relationship('Subscribers', back_populates='prompts')


class Suggestions(Base):
    __tablename__ = 'suggestions'
    __table_args__ = (
        ForeignKeyConstraint(['pid'], ['playlists.id'], ondelete='CASCADE', name='suggestions_pid_fkey'),
        ForeignKeyConstraint(['tid'], ['tracks.id'], ondelete='CASCADE', name='suggestions_tid_fkey'),
        PrimaryKeyConstraint('id', name='suggestions_pkey')
    )

    pid: Mapped[int] = mapped_column(Integer)
    tid: Mapped[int] = mapped_column(Integer)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    added_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    subscriber: Mapped[List['Subscribers']] = relationship('Subscribers', secondary='playback', back_populates='suggestion')
    playlists: Mapped['Playlists'] = relationship('Playlists', back_populates='suggestions')
    tracks: Mapped['Tracks'] = relationship('Tracks', back_populates='suggestions')


t_playback = Table(
    'playback', Base.metadata,
    Column('subscriber_id', Integer, primary_key=True),
    Column('suggestion_id', Uuid),
    ForeignKeyConstraint(['subscriber_id'], ['subscribers.id'], ondelete='CASCADE', name='playback_sid_fkey'),
    ForeignKeyConstraint(['suggestion_id'], ['suggestions.id'], ondelete='CASCADE', name='playback_suggestion_id_fkey'),
    PrimaryKeyConstraint('subscriber_id', name='playback_pkey')
)
