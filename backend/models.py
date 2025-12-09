# models.py
"""SQLAlchemy database models for Nidar C2 system"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Vehicle(Base):
    """Vehicle information table"""
    __tablename__ = 'vehicles'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100))
    sysid = Column(Integer)
    compid = Column(Integer)
    port = Column(Integer)
    last_seen = Column(Integer)  # timestamp in ms
    last_pos_lat = Column(Float)
    last_pos_lon = Column(Float)
    last_pos_alt = Column(Float)
    battery = Column(Integer)
    status = Column(String(50))
    
    # Relationships
    detections = relationship("Detection", back_populates="vehicle")
    missions = relationship("Mission", back_populates="vehicle")

class Detection(Base):
    """Object detection records"""
    __tablename__ = 'detections'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String(50), ForeignKey('vehicles.vehicle_id'), nullable=False)
    lat = Column(Float)
    lon = Column(Float)
    conf = Column(Float)  # confidence score
    img_path = Column(String(500))
    ts = Column(Integer)  # timestamp in ms
    approved = Column(Boolean, default=False)
    delivered = Column(Boolean, default=False)
    delivered_mission_id = Column(Integer, ForeignKey('missions.id'))
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="detections")

class Mission(Base):
    """Mission records"""
    __tablename__ = 'missions'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String(50), ForeignKey('vehicles.vehicle_id'), nullable=False)
    items_json = Column(Text)  # JSON string of mission items
    status = Column(String(50))  # pending, active, completed, aborted
    created_ts = Column(Integer)
    started_ts = Column(Integer)
    finished_ts = Column(Integer)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="missions")
    logs = relationship("MissionLog", back_populates="mission")

class MissionLog(Base):
    """Mission execution logs"""
    __tablename__ = 'mission_logs'
    
    id = Column(Integer, primary_key=True)
    mission_id = Column(Integer, ForeignKey('missions.id'), nullable=False)
    ts = Column(Integer)
    step = Column(String(50))
    details = Column(Text)
    
    # Relationships
    mission = relationship("Mission", back_populates="logs")

# Database setup
DATABASE_URL = "sqlite:///./nidar.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
