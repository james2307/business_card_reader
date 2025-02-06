from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from datetime import datetime
import json

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

# Create SQLAlchemy engine with SSL requirements
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "sslmode": "require"
    },
    pool_pre_ping=True,  # Verify connection before using
    json_serializer=lambda obj: json.dumps(obj),
    json_deserializer=lambda obj: json.loads(obj)
)

# Create declarative base
Base = declarative_base()

class BusinessCard(Base):
    __tablename__ = 'business_cards'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    company_name = Column(String)
    company_details = Column(JSON)  # Stores all extracted data as JSON
    image_path = Column(String)  # Store S3 path to the image

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'upload_date': self.upload_date.isoformat(),
            'company_name': self.company_name,
            'company_details': self.company_details,
            'image_path': self.image_path
        }

# Create all tables
Base.metadata.create_all(engine)

# Create session factory
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_card_info(filename: str, company_name: str, details: dict, image_path: str):
    """Save business card information to database"""
    db = SessionLocal()
    try:
        # Ensure details is properly serialized
        if isinstance(details, str):
            details = json.loads(details)

        card = BusinessCard(
            filename=filename,
            company_name=company_name,
            company_details=details,  # SQLAlchemy will handle JSON serialization
            image_path=image_path
        )
        db.add(card)
        db.commit()
        return card.id
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to save card info: {str(e)}")
    finally:
        db.close()

def get_all_cards():
    """Retrieve all business cards"""
    db = SessionLocal()
    try:
        cards = db.query(BusinessCard).all()
        return [card.to_dict() for card in cards]
    finally:
        db.close()

def get_card_by_id(card_id: int):
    """Retrieve a specific business card"""
    db = SessionLocal()
    try:
        card = db.query(BusinessCard).filter(BusinessCard.id == card_id).first()
        return card.to_dict() if card else None
    finally:
        db.close()