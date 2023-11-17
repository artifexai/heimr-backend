from copy import deepcopy
from typing import Dict, List, Optional

from pydantic import BaseModel, Extra, Field

from database.models.listings import ListingDB, ListingEventDB
from database.models.properties import AddressDB, PropertyDB
from database.models.taxes import TaxDB
from models.listing import ListingStruct
from models.shared import AddressStruct
from models.tax import TaxStruct
from utils.helpers import fetch_nested_key, first_element_of_list


class PropertyStruct(BaseModel):
    property_id: int = Field()
    realtor_id: str = Field()
    address: AddressStruct = Field()

    url: Optional[str] = Field()
    image: Optional[str] = Field()
    street_view: Optional[str] = Field()

    baths: Optional[float] = Field()
    beds: Optional[int] = Field()
    sqft: Optional[int] = Field()
    lot_sqft: Optional[int] = Field()
    address_id: Optional[int]

    listings: Optional[List[ListingStruct]] = Field(alias='listing')
    taxes: Optional[List[TaxStruct]] = Field(alias='tax')

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
        from_attributes = True
        extra = Extra.ignore

    def to_orm_obj(self) -> PropertyDB:
        rec = self.dict()
        _address = rec.pop('address')
        _taxes = rec.pop('taxes') or []
        _listings = rec.pop('listings') or []
        _listing_events = []

        listings = []

        for li in _listings:
            _e = li.pop('events')
            db_listing = ListingDB(**li)
            if _e:
                event_recs = [ListingEventDB(**e) for e in _e]
                _listing_events.extend(event_recs)
                db_listing.events = event_recs
            listings.append(db_listing)

        prop = PropertyDB(**rec)
        if _address:
            address = AddressDB(**_address)
            prop.address = address

        taxes = [TaxDB(**t) for t in _taxes]
        prop.tax = taxes
        prop.listing = listings
        return prop

    @staticmethod
    def from_raw(file, street_suffix_lookup) -> 'PropertyStruct':
        details: Dict = fetch_nested_key(file, ['props', 'pageProps', 'initialReduxState', 'propertyDetails'])
        if not details:
            raise ValueError('Missing details in query')
        # copy details to avoid side effects that mutate the original
        details = deepcopy(details)

        slug = fetch_nested_key(file, ['query', 'slug']) or fetch_nested_key(file, ['query', 'detailSlug'])
        if not slug:
            raise ValueError('Missing slug in query')
        realtor_id: str = ''
        if isinstance(slug, str):
            realtor_id = slug.replace('-', '')
        elif isinstance(slug, list):
            realtor_id = (first_element_of_list(slug) or '').replace('-', '')

        property_id = details.pop('property_id')
        url = details.pop('href')

        location: Dict = details.pop('location')
        street_view = location.pop('street_view_url')

        address = AddressStruct.from_raw(location.pop('address'), street_suffix_dict=street_suffix_lookup)
        address.property_id = property_id
        # address.realtor_id = realtor_id

        description = details.pop('description') or {}

        property_history = details.pop('property_history')
        tax_history = details.pop('tax_history')

        listings = taxes = None

        if property_history:
            listings = ListingStruct.from_raw(property_history, property_id, realtor_id)
        if tax_history:
            taxes = TaxStruct.from_raw_list(tax_history, property_id, realtor_id)

        try:

            rec = PropertyStruct.parse_obj({
                'property_id': property_id,
                'realtor_id': realtor_id,
                'address': address,
                'url': url,
                'street_view': street_view,
                'baths': description.get('baths'),
                'beds': description.get('beds'),
                'sqft': description.get('sqft'),
                'lot_sqft': description.get('lot_sqft'),
                'listings': listings,
                'taxes': taxes
            })

            return rec
        except Exception as e:
            print(e)
            print(details)
            print(property_history)
            raise e
