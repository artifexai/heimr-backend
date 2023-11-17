from datetime import date
from typing import Optional

from sqlalchemy import BigInteger, Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, mapped_column, Mapped

from database import Base, ModelUtils


class PermitDB(Base, ModelUtils):

    """
    This class will be populated when the permit -> address -> property join logic has been developed
    """
    __tablename__ = 'permit'
    __table_args__ = {"schema": "prod"}

    permit_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    location_id: Mapped[int] = mapped_column(BigInteger)
    permit_type_name: Mapped[str] = mapped_column(String(100))
    occupancy_type = mapped_column(String(100))
    date_created: Mapped[date] = Column(Date)
    date_submitted: Mapped[date] = Column(Date)
    address_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('prod.address.address_id'), nullable=False)

    address = relationship("AddressDB", back_populates="permits", foreign_keys=[address_id])

    applicant_full_name: Mapped[Optional[str]] = Column(String(100))

    property_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('prod.property.property_id'))


class Permit(Base, ModelUtils):
    __tablename__ = 'permit'

    permit_id = Column(Integer, primary_key=True, autoincrement=True)

    listing_id = Column(Integer)
    standardized_address = Column(String(300))
    application_date = Column(DateTime)
    issue_date = Column(DateTime)
    expiry_date = Column(DateTime)
    permit_number = Column(String(300))
    property_address = Column(String(300))
    zone = Column(String(300))
    unit_number = Column(String(300))
    applicant_name = Column(String(300))
    city = Column(String(300))
    applicant_email = Column(String(300))
    applicant_phone = Column(String(300))
    owner_name = Column(String(300))
    owner_street_number = Column(String(300))
    owner_street_name = Column(String(300))
    owner_city = Column(String(300))
    owner_email = Column(String(300))
    owner_phone = Column(String(300))
    owner_fax = Column(String(300))
    business_owner_name = Column(String(300))
    business_owner_street_number = Column(String(300))
    business_owner_street_name = Column(String(300))
    business_owner_city = Column(String(300))
    business_owner_email = Column(String(300))
    business_owner_phone = Column(String(300))
    mailing_address = Column(String(300))
    start_date = Column(DateTime)
    description = Column(String(300))
    estimated_cost = Column(Float)
    status = Column(String(300))
    inspection = Column(String(300))
    state = Column(String(300))
    zipcode = Column(Integer)
    key = Column(Integer)
    street_number = Column(Integer)
    street_name = Column(String(300))
    street_type = Column(String(300))
    street_direction = Column(String(300))
    permit_standardized_description = Column(String(300))
