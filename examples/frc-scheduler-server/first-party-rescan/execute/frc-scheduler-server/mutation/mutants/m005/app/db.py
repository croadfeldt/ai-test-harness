"""
Database models using SQLAlchemy 2.x async ORM with PostgreSQL.

Two-stage scheduling model:
  Stage 1 — AbstractSchedule: slot-based structure (no team numbers)
  Stage 2 — AssignedSchedule: maps real team numbers onto an abstract schedule
"""
import os
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://frc:frc@localhost:5432/frc_scheduler')
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True, pool_size=5, max_overflow=10, pool_timeout=30, connect_args={'server_settings': {'application_name': 'frc-scheduler'}, 'command_timeout': 60})
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Event(Base):
    """An FRC event (regional, district, championship, or custom)."""
    __tablename__ = 'events'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(Text)
    year: Mapped[int] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tba_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    branding: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    locked_by_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    teams: Mapped[list['EventTeam']] = relationship(back_populates='event', cascade='all, delete-orphan')
    abstract_schedules: Mapped[list['AbstractSchedule']] = relationship(back_populates='event', cascade='all, delete-orphan')
    assigned_schedules: Mapped[list['AssignedSchedule']] = relationship(back_populates='event', cascade='all, delete-orphan')

class Team(Base):
    """A registered FRC team."""
    __tablename__ = 'teams'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rookie_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    events: Mapped[list['EventTeam']] = relationship(back_populates='team')

class EventTeam(Base):
    """Association between an event and the teams attending it."""
    __tablename__ = 'event_teams'
    __table_args__ = (UniqueConstraint('event_id', 'team_id'),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('events.id', ondelete='CASCADE'))
    team_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('teams.id', ondelete='CASCADE'))
    event: Mapped['Event'] = relationship(back_populates='teams')
    team: Mapped['Team'] = relationship(back_populates='events')

class AbstractSchedule(Base):
    """
    Stage 1 output — a slot-based match structure with no team numbers.

    Matches contain slot indices 1..N (abstract positions).
    Surrogate flags are per-slot. This structure is reusable with any
    roster of the same size.
    """
    __tablename__ = 'abstract_schedules'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('events.id', ondelete='SET NULL'), nullable=True)
    name: Mapped[str] = mapped_column(String(128), default='Abstract Schedule')
    num_teams: Mapped[int] = mapped_column(Integer)
    matches_per_team: Mapped[int] = mapped_column(Integer)
    cooldown: Mapped[int] = mapped_column(Integer)
    seed: Mapped[str | None] = mapped_column(String(16), nullable=True)
    iterations_run: Mapped[int] = mapped_column(Integer)
    best_iteration: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)
    created_by: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    matches: Mapped[Any] = mapped_column(JSON)
    surrogate_count: Mapped[Any] = mapped_column(JSON)
    round_boundaries: Mapped[Any] = mapped_column(JSON)
    day_config: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    weights: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_report: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    quality_weights: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    creation_provenance: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    event: Mapped['Event|None'] = relationship(back_populates='abstract_schedules')
    assigned_schedules: Mapped[list['AssignedSchedule']] = relationship(back_populates='abstract_schedule', cascade='all, delete-orphan')

class AssignedSchedule(Base):
    """
    Stage 2 output — real team numbers mapped onto an abstract schedule.

    slot_map: {slot_index: team_number} for all 1..N slots.
    """
    __tablename__ = 'assigned_schedules'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    abstract_schedule_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('abstract_schedules.id', ondelete='CASCADE'))
    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('events.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(128), default='Schedule')
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    forked_from_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('assigned_schedules.id', ondelete='SET NULL'), nullable=True, index=True)
    slot_map: Mapped[Any] = mapped_column(JSON)
    day_config: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    practice_matches: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    assign_seed: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    locked_by_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    official_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    official_by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    official_by_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    competition_approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    audit_trail: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    abstract_schedule: Mapped['AbstractSchedule'] = relationship(back_populates='assigned_schedules')
    event: Mapped['Event'] = relationship(back_populates='assigned_schedules')
    match_rows: Mapped[list['MatchRow']] = relationship(back_populates='assigned_schedule', cascade='all, delete-orphan')
    history_rows: Mapped[list['AssignedScheduleHistory']] = relationship(back_populates='assigned_schedule', cascade='all, delete-orphan')
    lock_events: Mapped[list['AssignedScheduleLockEvent']] = relationship(back_populates='assigned_schedule', cascade='all, delete-orphan')

class AssignedScheduleHistory(Base):
    """Snapshot of an assigned schedule taken before each mutation.

    Copy-on-write recovery: every PATCH (or restore) writes a row
    here BEFORE applying changes, so the previous state is preserved.
    Restoring is `POST /api/assigned-schedules/{id}/restore/{history_id}`
    which copies the named row back onto the live schedule and inserts
    a new history row with action='restore'.

    is_active and lock state are intentionally NOT in the snapshot —
    they're operational metadata, not "content". A restore preserves
    the live schedule's lock state and active status.
    """
    __tablename__ = 'assigned_schedule_history'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assigned_schedule_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('assigned_schedules.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(128))
    day_config: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    slot_map: Mapped[Any] = mapped_column(JSON)
    practice_matches: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    action: Mapped[str] = mapped_column(String(16))
    actor_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    actor_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    assigned_schedule: Mapped['AssignedSchedule'] = relationship(back_populates='history_rows')

class AssignedScheduleLockEvent(Base):
    """One row per lock or unlock action.

    The live `assigned_schedules.locked_at` column carries the
    *current* state. This audit table preserves the history so
    diagnostics can answer "when was this unlocked, and by whom"
    after the fact — without it, that history is lost the instant
    `locked_at` is reset to NULL.
    """
    __tablename__ = 'assigned_schedule_lock_events'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assigned_schedule_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('assigned_schedules.id', ondelete='CASCADE'), index=True)
    action: Mapped[str] = mapped_column(String(16))
    actor_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    actor_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    assigned_schedule: Mapped['AssignedSchedule'] = relationship(back_populates='lock_events')

class User(Base):
    """OAuth user — created on first login via Google or Apple."""
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sub: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class PersonalAccessToken(Base):
    """Long-lived API token for programmatic access.

    Mint flow:
      1. User authenticates via OAuth (JWT issued)
      2. User calls POST /api/me/tokens with a name (and optional expiry)
      3. Server generates a 32-byte random secret, returns the PLAINTEXT
         token ONCE, stores only sha256(plaintext) in token_hash
      4. Client persists the plaintext (it cannot be retrieved later;
         losing it = revoke + reissue)

    Use flow:
      1. Client sends `Authorization: Bearer frc_pat_<plaintext>` on
         every request
      2. app/auth.py:get_current_user routes by prefix:
         - Starts with `frc_pat_` → verify via DB lookup (this table)
         - Otherwise → decode as JWT
      3. DB lookup is a single indexed query by token_hash; last_used_at
         updated asynchronously (not blocking the request)

    Why SHA-256 and not bcrypt:
      PATs are 256-bit cryptographically random secrets, not passwords.
      No bruteforce concern. SHA-256 is fast (sub-millisecond per
      verification) which matters when every authenticated API request
      hits this path. bcrypt would add ~100ms per request — unacceptable
      for an API.

    Admin status:
      Captured into is_admin at mint time. Means: if a user is promoted
      to admin AFTER they minted a token, the token does NOT gain admin
      privileges retroactively. Revoke + reissue to pick up new status.
      Symmetric: if admin status is revoked, existing tokens DO retain
      admin until manually revoked. This mirrors the JWT behavior
      (is_admin embedded in claims, takes effect on next login).
    """
    __tablename__ = 'personal_access_tokens'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    token_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    scopes: Mapped[Any] = mapped_column(JSON, nullable=False, server_default='["*"]')
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

class PdfImport(Base):
    """Cache of LLM-parsed schedule PDFs.

    Same PDF (by SHA-256) → same parsed result. Stops repeat LLM calls when
    users re-upload the same file (very common during testing or iterating).

    Cache entries are NOT tied to a specific event — a PDF that gets imported
    for one event might also be reusable for another. We keep them separate
    from AssignedSchedule and only materialize into AssignedSchedule on the
    user's explicit confirmation.
    """
    __tablename__ = 'pdf_imports'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pdf_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    byte_size: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int] = mapped_column(Integer)
    parsed: Mapped[Any] = mapped_column(JSON)
    validation: Mapped[Any] = mapped_column(JSON)
    format_detected: Mapped[str | None] = mapped_column(String, nullable=True)
    method: Mapped[str] = mapped_column(String, default='llm')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class MatchRow(Base):
    """
    Denormalised match row for queryable team lookups.
    Stores real team numbers after Stage 2 assignment.
    """
    __tablename__ = 'match_rows'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assigned_schedule_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('assigned_schedules.id', ondelete='CASCADE'))
    match_num: Mapped[int] = mapped_column(Integer)
    red1: Mapped[int] = mapped_column(Integer)
    red2: Mapped[int] = mapped_column(Integer)
    red3: Mapped[int] = mapped_column(Integer)
    blue1: Mapped[int] = mapped_column(Integer)
    blue2: Mapped[int] = mapped_column(Integer)
    blue3: Mapped[int] = mapped_column(Integer)
    red1_surrogate: Mapped[bool] = mapped_column(Boolean, default=False)
    red2_surrogate: Mapped[bool] = mapped_column(Boolean, default=False)
    red3_surrogate: Mapped[bool] = mapped_column(Boolean, default=True)
    blue1_surrogate: Mapped[bool] = mapped_column(Boolean, default=False)
    blue2_surrogate: Mapped[bool] = mapped_column(Boolean, default=False)
    blue3_surrogate: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_schedule: Mapped['AssignedSchedule'] = relationship(back_populates='match_rows')

class MatchResult(Base):
    """Result for a single played match. Sourced from TBA. One row per match
    per event."""
    __tablename__ = 'match_results'
    __table_args__ = (UniqueConstraint('event_id', 'comp_level', 'match_number', 'set_number', name='uix_match_result_key'),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('events.id', ondelete='CASCADE'), index=True)
    comp_level: Mapped[str] = mapped_column(String(8))
    match_number: Mapped[int] = mapped_column(Integer)
    set_number: Mapped[int] = mapped_column(Integer, default=1)
    actual_time: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    predicted_time: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    post_result_time: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    red_teams: Mapped[list] = mapped_column(JSON, default=list)
    blue_teams: Mapped[list] = mapped_column(JSON, default=list)
    red_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blue_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    winning_alliance: Mapped[str | None] = mapped_column(String(8), nullable=True)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    videos: Mapped[list | None] = mapped_column(JSON, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class TeamRanking(Base):
    """Current event ranking for a team. Sourced from TBA's rankings endpoint."""
    __tablename__ = 'team_rankings'
    __table_args__ = (UniqueConstraint('event_id', 'team_number', name='uix_team_ranking_key'),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('events.id', ondelete='CASCADE'), index=True)
    team_number: Mapped[int] = mapped_column(Integer, index=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    ties: Mapped[int] = mapped_column(Integer, default=0)
    matches_played: Mapped[int] = mapped_column(Integer, default=0)
    ranking_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    extra_stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class QueueStatus(Base):
    """Current queueing status for a match. Sourced from Nexus webhooks.

    Status values match Nexus's terminology:
      'queueing_soon', 'now_queueing', 'on_deck', 'on_field', 'completed'
    """
    __tablename__ = 'queue_status'
    __table_args__ = (UniqueConstraint('event_id', 'comp_level', 'match_number', 'set_number', name='uix_queue_status_key'),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('events.id', ondelete='CASCADE'), index=True)
    comp_level: Mapped[str] = mapped_column(String(8))
    match_number: Mapped[int] = mapped_column(Integer)
    set_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32))
    queue_time: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class EventLiveSync(Base):
    """Tracks per-event sync state — when we last refreshed TBA, errors, etc.
    Used to throttle TBA API calls and surface freshness to clients."""
    __tablename__ = 'event_live_sync'
    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('events.id', ondelete='CASCADE'), primary_key=True)
    tba_last_fetched: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tba_last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    nexus_last_event: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    nexus_last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sim_started_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sim_speedup: Mapped[float | None] = mapped_column(Float, nullable=True)

async def init_db(retries: int=10, delay: float=2.0) -> None:
    """Create all tables (idempotent). Retries for slow Postgres start."""
    import asyncio
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                from sqlalchemy import text
                await conn.execute(text('ALTER TABLE events ADD COLUMN IF NOT EXISTS branding JSONB'))
                await conn.execute(text('ALTER TABLE assigned_schedules ADD COLUMN IF NOT EXISTS practice_matches JSONB'))
                await conn.execute(text('ALTER TABLE abstract_schedules ADD COLUMN IF NOT EXISTS weights JSONB'))
                await conn.execute(text('ALTER TABLE abstract_schedules ADD COLUMN IF NOT EXISTS source VARCHAR(32)'))
                await conn.execute(text('ALTER TABLE abstract_schedules ADD COLUMN IF NOT EXISTS source_url TEXT'))
                await conn.execute(text('ALTER TABLE abstract_schedules ADD COLUMN IF NOT EXISTS quality_report JSONB'))
                await conn.execute(text('ALTER TABLE abstract_schedules ADD COLUMN IF NOT EXISTS quality_weights JSONB'))
                await conn.execute(text('ALTER TABLE abstract_schedules ADD COLUMN IF NOT EXISTS creation_provenance JSONB'))
                await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE'))
                await conn.execute(text('ALTER TABLE assigned_schedules ADD COLUMN IF NOT EXISTS forked_from_id BIGINT REFERENCES assigned_schedules(id) ON DELETE SET NULL'))
                await conn.execute(text('CREATE INDEX IF NOT EXISTS assigned_schedules_forked_from_idx ON assigned_schedules(forked_from_id) WHERE forked_from_id IS NOT NULL'))
            return
        except Exception as e:
            last_error = e
            if attempt < retries:
                import logging
                logging.getLogger(__name__).warning('DB not ready (attempt %d/%d): %s — retrying in %.0fs', attempt, retries, e, delay)
                await asyncio.sleep(delay)
    raise RuntimeError(f'Could not connect to database after {retries} attempts') from last_error

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session