from sqlalchemy import Column, Integer, String, ForeignKey, Float, BigInteger
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.schema import UniqueConstraint

from database import Base, ModelUtils


class TaxDB(Base, ModelUtils):
    __tablename__ = 'tax'
    __table_args__ = {'schema': 'prod'}

    tax_id = Column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("prod.property.property_id"))
    realtor_id: Mapped[str] = mapped_column(String(50))

    year: Mapped[int] = Column(Integer, nullable=False, index=True)
    tax: Mapped[int] = Column(Integer)
    building: Mapped[int] = Column(Integer)
    land: Mapped[int] = Column(Integer)
    assessment: Mapped[int] = Column(Integer)

    # each property can only have one tax record per year. The proerty_id and year are unique together
    UniqueConstraint('property_id', 'year', name='_property_year_uc')


class Tax(Base, ModelUtils):
    __tablename__ = 'tax'

    tax_id = Column(Integer, primary_key=True, autoincrement=True)

    year = Column(Integer)
    tax = Column(Integer)
    assessment_building = Column(Float)
    assessment_land = Column(Float)
    assessment_total = Column(Integer)
    market_building = Column(Integer)
    market_land = Column(Integer)
    market_total = Column(Integer)
    listing_id = Column(Integer)
