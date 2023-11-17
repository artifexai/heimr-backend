import logging
from datetime import date
from typing import Dict, List, Optional

import arrow
from pydantic import BaseModel, Field

from database import AddressDB, build_session, PermitDB
from models.shared import AddressStruct


class PermitStruct(BaseModel):
    permit_id: int = Field()
    location_id: int = Field()
    permit_type_name: str = Field()
    occupancy_type: str = Field()
    address: AddressStruct = Field()
    date_created: date = Field()
    date_submitted: date = Field()
    address_id: Optional[int] = Field()

    applicant_full_name: Optional[str] = Field()
    property_id: Optional[int] = Field()

    @staticmethod
    def _create_address(data: Dict, street_suffix_lookup: Dict) -> AddressStruct:
        address = {'state': data.pop('state'), 'city': data.pop("city"), 'street_number': data.pop('street_no'),
                   'street_name': data.pop('street_name'), 'postal_code': data.pop('postal_code'),
                   'lat': data.pop('latitude'), 'lon': data.pop('longitude')}
        return AddressStruct.from_raw(address, street_suffix_dict=street_suffix_lookup)

    @staticmethod
    def from_raw(data: Dict, street_suffix_lookup: Dict) -> List['PermitStruct']:

        location_id = data.get('location_id')

        permits = data.get('permits')

        records = []
        for p in permits:

            p['address'] = PermitStruct._create_address(p, street_suffix_lookup)

            p['location_id'] = location_id
            p['date_created'] = arrow.get(p['date_created']).to('UTC').date()
            p['date_submitted'] = arrow.get(p['date_submitted']).to('UTC').date()
            p['permit_id'] = p['record_id']
            p['permit_type_name'] = p['record_type_name']

            try:
                rec = PermitStruct.parse_obj(p)
                records.append(rec)
            except Exception as e:
                logging.error("Failed to parse record. Error: %s", e)
        return records

    @classmethod
    def find_property_id(cls, permit_rec):
        with build_session() as sess:
            res = sess.query(AddressDB.property_id).where(
                (AddressDB.street_name == permit_rec.address.street_name) &
                (AddressDB.zip_code == permit_rec.address.zip_code) &
                (AddressDB.street_number == permit_rec.address.street_number)
            ).first()

        if res:
            return res[0]
        else:
            return None

    def to_orm_obj(self):
        rec = self.dict()
        _address = rec.pop('address')
        permit = PermitDB(**rec)
        if _address:
            address = AddressDB(**_address)
            permit.address = address
        return permit

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
        from_attributes = True
