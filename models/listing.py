from copy import deepcopy
from datetime import date
from typing import Optional, Dict, List

import arrow
from pydantic import BaseModel, Field, root_validator

from utils.helpers import fetch_nested_key, drop_keys, first_element_of_list, rename
from utils.helpers import try_parse_date


class ListingEventStruct(BaseModel):
    source_listing_id: int = Field()
    price: int = Field()
    event_date: date = Field()
    event_type: str = Field()
    source_name: Optional[str] = Field()

    # there are cases where the data returns an event and no listing. So this is optional.
    listing_id: Optional[int] = Field()

    # join fields
    property_id: Optional[int] = Field()
    realtor_id: Optional[str] = Field()

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
        from_attributes = True

    @root_validator(pre=True)
    def preprocess(cls, data):
        sid = data.get('source_listing_id')
        if not sid:
            data['source_listing_id'] = data.get('listing_id')
        return data


class ListingStruct(BaseModel):
    listing_id: int = Field()
    price: int = Field(..., alias='list_price')
    status: str = Field()

    listing_date: Optional[date] = Field()
    description: Optional[str] = Field()
    last_updated: Optional[date] = Field()
    last_status_change: Optional[date] = Field()

    events: Optional[List[ListingEventStruct]] = Field()

    # join fields
    property_id: Optional[int] = Field()
    realtor_id: Optional[str] = Field()

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
        from_attributes = True

    @staticmethod
    def from_raw(data: List[Dict], property_id: int, realtor_id: str) -> List['ListingStruct']:
        data = deepcopy(data)
        listings = []
        events = []

        for li in data:
            rec = li.pop('listing')
            li = rename(li, {'date': 'event_date', 'event_name': 'event_type'})
            li.update({
                'listing_id': fetch_nested_key(rec, ['listing_id']),
                'event_date': arrow.get(li['event_date']).to('UTC').date(),
                'property_id': property_id,
                'realtor_id': realtor_id
            })
            events.append(li)

            if not rec or not rec.get('listing_id'):
                # TODO: update this logic to return orphaned events
                #   currently we are dropping orphaned events because they are only returned when joined to a listing
                continue

            rec.update({'property_id': property_id, 'realtor_id': realtor_id})
            rec = rename(rec,
                         {
                             'list_date': 'listing_date',
                             'last_update_date': 'last_updated',
                             'last_status_change_date': 'last_status_change'
                         })
            # if the event is a listing, format and add it to the list
            rec['listing_date'] = try_parse_date(rec.get('listing_date'), utc=True)
            last_updated = rec.get('last_updated')
            last_status_change = rec.get('last_status_change')
            last_updated = last_updated or last_status_change
            last_status_change = last_status_change or last_updated

            if last_updated and last_status_change:
                rec['last_updated'] = arrow.get(last_updated).to('UTC').date()
                rec['last_status_change'] = arrow.get(last_status_change).to('UTC').date()

            photos: Optional[List[Dict]] = rec.pop('photos')

            if photos:
                rec['photos'] = [fetch_nested_key(p, ['href']) for p in photos]
                rec['photos'] = [p for p in rec['photos'] if p]

            rec['source_listing_id'] = li.get('source_listing_id')
            rec['description'] = fetch_nested_key(rec.pop('description'), ['text'])

            rec = drop_keys(
                rec,
                ['suppression_flags', 'advertisers', 'source']
            )

            listings.append(rec)

        # Select first listing per date
        listing_ids = list(set([li['listing_id'] for li in listings]))
        distinct_listings = []
        # Dedupe by taking the most recent record for each listing
        for i in listing_ids:
            matches = []
            for li in listings:
                if li['listing_id'] == i:
                    li['listing_date'] = li.get('listing_date') or li.get('last_updated')
                    if not li.get('listing_date'):
                        continue
                    matches.append(li)

            match = first_element_of_list(sorted(matches, key=lambda x: x.get('listing_date')))
            distinct_listings.append(match)

        list_struct = []
        for li in distinct_listings:
            try:
                list_struct.append(ListingStruct.parse_obj(li))
            except Exception as e:
                print(e)

        event_struct = [ListingEventStruct.parse_obj(e) for e in events if e.get('source_listing_id')]

        for li in list_struct:
            li.events = [e for e in event_struct if e.listing_id == li.listing_id]

        return list_struct
