from datetime import date
from typing import Optional, List

from sqlalchemy import Column, Integer, String, ForeignKey, Float, BigInteger, Date
from sqlalchemy import DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship

from database import Base, ModelUtils


class ListingEventDB(Base, ModelUtils):
    __tablename__ = 'listing_event'
    __table_args__ = {'schema': 'prod'}

    listing_event_id: Mapped[int] = Column(BigInteger, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("prod.listing.listing_id"))
    property_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("prod.property.property_id"))
    realtor_id: Mapped[str] = mapped_column(String(50))
    source_listing_id: Mapped[str] = mapped_column(String(50))

    event_date: Mapped[date] = Column(Date)
    event_type: Mapped[str] = Column(String(100))
    price: Mapped[int] = Column(Integer)
    source_name: Mapped[str] = Column(String(100))


class ListingDB(Base, ModelUtils):
    __tablename__ = 'listing'
    __table_args__ = {'schema': 'prod'}

    listing_id: Mapped[int] = Column(BigInteger, primary_key=True)
    property_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("prod.property.property_id"))
    realtor_id: Mapped[str] = mapped_column(String(50))

    description: Mapped[str] = Column(String(3000), index=True, nullable=True)
    price: Mapped[int] = Column(Integer)
    status: Mapped[str] = Column(String(100))
    listing_date: Mapped[date] = Column(Date)
    last_updated: Mapped[date] = Column(Date)
    last_status_change: Mapped[date] = Column(Date)

    events: Mapped[Optional[List[ListingEventDB]]] = relationship(
        "ListingEventDB",
        backref="listing",
        cascade="all, delete-orphan",
        uselist=True
    )


class Listing(Base, ModelUtils):
    __tablename__ = 'listing'

    listing_id = Column(Integer, primary_key=True)
    list_price = Column(Integer)
    last_price_change = Column(Float)
    price_per_square_feet = Column(Float)
    listing_date = Column(DateTime)
    hoa_fee = Column(Float)
    listing_name = Column(String(300))
    listing_type = Column(String(300))

    num_bedrooms = Column(Integer)
    num_full_baths = Column(Integer)
    num_half_baths = Column(Integer)
    num_features = Column(Integer)
    parcel_number = Column(String(300))
    zoning_type = Column(String(300))
    property_primary_type = Column(String(300))
    property_secondary_type = Column(String(300))
    estimated_annual_tax = Column(String(300))
    year_built = Column(Integer)
    building_area = Column(Float)
    building_area_units = Column(String(300))
    foundation_type = Column(String(300))
    construction_materials = Column(String(300))
    roof_type = Column(String(300))
    house_type = Column(String(300))
    lot_description = Column(String(300))
    lot_size_acres = Column(Float)
    lot_size_sqft = Column(Float)
    address_line = Column(String(300), index=True, nullable=False)
    address_street_number = Column(Integer)
    address_street_name = Column(String(300))
    address_street_suffix = Column(String(300))
    unit_number = Column(String(300))
    city = Column(String(300))
    state = Column(String(300))
    zip_code = Column(Integer)
    county = Column(String(300))
    latitude = Column(Float)
    longitude = Column(Float)
    property_image = Column(String(300))
