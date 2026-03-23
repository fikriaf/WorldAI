from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    BigInteger,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class WorldRun(Base):
    __tablename__ = "world_runs"

    id = Column(String(36), primary_key=True)
    seed_id = Column(String(255), nullable=False)
    genesis_mode = Column(String(50), nullable=False)
    grid_width = Column(Integer, nullable=False)
    grid_height = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    final_tick = Column(Integer, nullable=True)
    final_population = Column(Integer, nullable=True)

    agents = relationship("Agent", back_populates="world_run")
    events = relationship("Event", back_populates="world_run")
    species = relationship("Species", back_populates="world_run")
    metrics = relationship("MetricsSnapshot", back_populates="world_run")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True)
    world_run_id = Column(String(36), ForeignKey("world_runs.id"), nullable=False)
    genome_hash = Column(String(16), nullable=False)
    genes_count = Column(Integer, nullable=False)
    birth_tick = Column(Integer, nullable=False)
    death_tick = Column(Integer, nullable=True)
    parent_ids = Column(JSON, server_default="[]")
    species_label = Column(String(100), nullable=True)
    final_energy = Column(Float, nullable=True)
    final_health = Column(Float, nullable=True)
    final_mass = Column(Float, nullable=True)

    world_run = relationship("WorldRun", back_populates="agents")


class Event(Base):
    __tablename__ = "events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    world_run_id = Column(String(36), ForeignKey("world_runs.id"), nullable=False)
    tick = Column(Integer, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    source_id = Column(String(36), nullable=True)
    target_id = Column(String(36), nullable=True)
    data = Column(JSON, server_default="{}")
    created_at = Column(DateTime, server_default=datetime.utcnow)

    world_run = relationship("WorldRun", back_populates="events")


class Species(Base):
    __tablename__ = "species"

    id = Column(Integer, primary_key=True, autoincrement=True)
    world_run_id = Column(String(36), ForeignKey("world_runs.id"), nullable=False)
    name = Column(String(100), nullable=False)
    first_seen_tick = Column(Integer, nullable=False)
    peak_population = Column(Integer, server_default="0")
    total_born = Column(Integer, server_default="0")
    total_died = Column(Integer, server_default="0")

    world_run = relationship("WorldRun", back_populates="species")


class MetricsSnapshot(Base):
    __tablename__ = "metrics_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    world_run_id = Column(String(36), ForeignKey("world_runs.id"), nullable=False)
    tick = Column(Integer, nullable=False, index=True)
    population = Column(Integer, nullable=False)
    total_energy = Column(Float, nullable=False)
    shannon_entropy = Column(Float, nullable=True)
    genome_diversity = Column(Float, nullable=True)
    avg_neural_complexity = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=datetime.utcnow)

    world_run = relationship("WorldRun", back_populates="metrics")
