from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
from logger import logger

Base = declarative_base()

class SignalRecord(Base):
    __tablename__ = "signal_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    symbol = Column(String, nullable=False)
    bias = Column(String, nullable=False)
    confluence_score = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    tp1 = Column(Float, nullable=False)
    tp2 = Column(Float, nullable=False)
    tp3 = Column(Float, nullable=False)
    passed_filters = Column(Boolean, nullable=False)
    narrative = Column(String, nullable=True)

engine = create_engine("sqlite:///sekwaila_omega_x.db", echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    logger.info("Database initialized successfully.")

def save_signal(data: dict):
    session = SessionLocal()
    try:
        record = SignalRecord(
            symbol=data.get("symbol", "XAUUSD"),
            bias=data["bias"],
            confluence_score=data["probability"],
            entry_price=data["entry"],
            stop_loss=data["stop_loss"],
            tp1=data["tp1"],
            tp2=data["tp2"],
            tp3=data["tp3"],
            passed_filters=data["passed_filters"],
            narrative=data.get("ai_narrative", "")
        )
        session.add(record)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to persist signal record: {e}")
    finally:
        session.close()
