from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, JSON, Numeric, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json

Base = declarative_base()

class Child(Base):
    __tablename__ = 'children'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    avatar = Column(String(10), nullable=False)  # emoji
    color = Column(String(20), nullable=False)   # CSS color name
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    streak_count = Column(Integer, default=0)
    last_completion_date = Column(Date)
    
    # Relationships
    completions = relationship("TaskCompletion", back_populates="child")
    badges = relationship("Badge", back_populates="child")
    week_summaries = relationship("WeekSummary", back_populates="child")
    
    @property
    def current_level(self):
        return (self.xp // 50) + 1
    
    def __repr__(self):
        return f"<Child {self.name}>"

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    points = Column(Integer, nullable=False)  # XP value
    category = Column(String(20), nullable=False)  # DAILY, BEHAVIOUR, WEEKLY
    is_required = Column(Boolean, default=False)
    streakable = Column(Boolean, default=False)
    active_days = Column(JSON)  # [0,1,2,3,4,5,6] for Mon-Sun
    
    # Relationships
    completions = relationship("TaskCompletion", back_populates="task")
    
    def is_active_today(self, weekday):
        """Check if task is active for given weekday (0=Monday, 6=Sunday)"""
        if self.active_days is None:
            return True
        return weekday in self.active_days
    
    def __repr__(self):
        return f"<Task {self.name}>"

class TaskCompletion(Base):
    __tablename__ = 'task_completions'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    date = Column(Date, nullable=False)
    approved = Column(Boolean, default=True)
    
    # Relationships
    child = relationship("Child", back_populates="completions")
    task = relationship("Task", back_populates="completions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_child_date', 'child_id', 'date'),
        Index('idx_task_date', 'task_id', 'date'),
    )
    
    def __repr__(self):
        return f"<TaskCompletion {self.child.name} - {self.task.name} on {self.date}>"

class Badge(Base):
    __tablename__ = 'badges'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    name = Column(String(50), nullable=False)
    emoji = Column(String(10), nullable=False)
    description = Column(Text)
    earned_date = Column(Date, default=date.today)
    
    # Relationships
    child = relationship("Child", back_populates="badges")
    
    def __repr__(self):
        return f"<Badge {self.name} for {self.child.name}>"

class WeekSummary(Base):
    __tablename__ = 'week_summaries'
    
    id = Column(Integer, primary_key=True)
    week_start_date = Column(Date, nullable=False)  # Monday of the week
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    total_points = Column(Integer, default=0)
    required_tasks_completed = Column(Boolean, default=False)
    payout_amount = Column(Numeric(10, 2), default=0.00)
    
    # Relationships
    child = relationship("Child", back_populates="week_summaries")
    
    def __repr__(self):
        return f"<WeekSummary {self.child.name} week of {self.week_start_date}>"

class Settings(Base):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True, default=1)
    full_payout_amount = Column(Numeric(10, 2), default=Decimal('3.00'))
    threshold_rules = Column(JSON)  # [{"min_points": 40, "amount": 2.0}, ...]
    timezone = Column(String(50), default='Europe/London')
    parent_pin = Column(String(100), default='1234')
    
    def get_threshold_rules(self):
        if self.threshold_rules is not None:
            return self.threshold_rules
        return [
            {"min_points": 40, "amount": 2.0},
            {"min_points": 25, "amount": 1.0}
        ]
    
    def __repr__(self):
        return f"<Settings>"

# Database setup functions
# Database setup functions
# Database setup functions
def create_database():
    """Create engine + session factory using Render's DATABASE_URL if present."""
    import os

    # Read from env var; fall back to local SQLite for dev
    db_url = os.getenv("DATABASE_URL", "sqlite:///chore_champions.db")

    # Normalize legacy 'postgres://' to 'postgresql+psycopg2://'
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)

    engine = create_engine(
        db_url,
        future=True,
        pool_pre_ping=True  # keeps connections healthy after idle/sleep
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    # Create tables if they don't exist
    Base.metadata.create_all(engine)

    return engine, Session

def get_or_create_settings(session):
    """Get settings or create default if none exist"""
    settings = session.query(Settings).filter_by(id=1).first()
    if not settings:
        settings = Settings(
            id=1,
            full_payout_amount=Decimal('3.00'),
            threshold_rules=[
                {"min_points": 40, "amount": 2.0},
                {"min_points": 25, "amount": 1.0}
            ],
            timezone='Europe/London',
            parent_pin='1234'
        )
        session.add(settings)
        session.commit()
    return settings
