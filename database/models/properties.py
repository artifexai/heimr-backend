from typing import List, Optional

from sqlalchemy import String, Integer, Float, ForeignKey, Date, Column, BigInteger
from sqlalchemy.orm import mapped_column, relationship, Mapped

from database import ModelUtils, Base
from database.models.listings import ListingDB
from database.models.taxes import TaxDB


class AddressDB(Base, ModelUtils):
    __tablename__ = "address"
    __table_args__ = {"schema": "prod"}
    address_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    street_name: Mapped[str] = mapped_column(String(50), index=True)
    street_number: Mapped[str] = mapped_column(String(30), index=True)
    city: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    zip_code: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    street_suffix: Mapped[str] = mapped_column(String(30))
    st_lookup_str: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    unit = mapped_column(String(30))
    lat = mapped_column(Float)
    lon = mapped_column(Float)

    permits = relationship("PermitDB", back_populates="address", uselist=True)


class PropertyDB(Base, ModelUtils):
    __tablename__ = "property"
    __table_args__ = {"schema": "prod"}

    property_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    realtor_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    url = mapped_column(String(500))
    image = mapped_column(String(500))
    street_view = mapped_column(String(500))

    baths: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    beds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sqft: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lot_sqft: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    address_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('prod.address.address_id'), nullable=False)

    address: Mapped[Optional[AddressDB]] = relationship(
        "AddressDB", uselist=False, lazy="joined"
    )

    tax: Mapped[Optional[List[TaxDB]]] = relationship(
        "TaxDB", backref="property",
        cascade="all, delete-orphan",
        uselist=True
    )

    listing: Mapped[Optional[List[ListingDB]]] = relationship(
        "ListingDB", backref="property",
        cascade="all, delete-orphan", uselist=True
    )


class Properties(Base, ModelUtils):
    __tablename__ = "properties"
    property_id = Column(String(50), primary_key=True)
    state = Column(String(2), index=True, nullable=False)
    city = Column(String(20), index=True, nullable=False)
    zip_code = Column(String(5), index=True, nullable=False)
    street_address = Column(String(50), index=True)
    listing_status = Column(String(15))
    last_sold_date = Column(Date)
    last_sold_price = Column(Integer)
    list_price = Column(Integer)
    estimate = Column(Integer)
