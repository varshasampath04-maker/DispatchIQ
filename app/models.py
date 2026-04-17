from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    id          = Column(Integer, primary_key=True, index=True)
    driver_name = Column(String, nullable=False)
    status      = Column(String, default="pending")   # pending | in_transit | delivered
    eta         = Column(DateTime, nullable=True)
    score       = Column(Float, nullable=True)
    decision    = Column(String, nullable=True)
