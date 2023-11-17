"""
This file contains the data which will be cached in memory and shared by the endpoints
NOTE: This logic will be moved to a shared cache in production
"""
import logging
from typing import List, Dict, Optional

from database import build_session, AddressDB
from search import Search

property_addresses: Optional[List[Dict]] = None
search_idx = None


def get_addresses():
    """
    Fetches the addresses of all properties from the database.

    Returns
    -------
    property_addresses: list[dict]
        A list of dictionaries where each dictionary represents a property address and
        has the following structure:
        {
            'property_id': <property_id>,
            'full_address': <full_address>
        }
    """
    global property_addresses
    if property_addresses:
        return property_addresses

    try:
        with build_session() as sess:
            data: List[AddressDB] = (
                sess.query(
                    AddressDB.property_id,
                    AddressDB.state,
                    AddressDB.city,
                    AddressDB.street_name,
                    AddressDB.zip_code)
                .filter(AddressDB.property_id.isnot(None))
                .filter(AddressDB.state == 'MA')
                .distinct()
                .all()
            )

        property_addresses = [
            {'property_id': d.property_id,
             'full_address': f"{d.street_name}, {d.city}, {d.state}, {str(d.zip_code).zfill(5)}"}
            for d in data
        ]
        print(f'Loaded {len(property_addresses)} properties')
        return property_addresses
    except Exception as e:
        logging.error(f'Failed to load properties for database with error: {e}')


def get_search_idx():
    """
    Generates a search index on the addresses of the properties

    Returns
    -------
     search_idx- An instance of the Search class with the search index created on the addresses of
        the properties.
    """
    global property_addresses
    global search_idx
    if search_idx:
        return search_idx

    try:
        data = get_addresses()
        if not data:
            logging.warning('No addresses returned from database. Search index not created.')
            return None
        search_idx = Search(data=data, fields_to_search=['full_address'], id_field='property_id')
        return search_idx
    except Exception as e:
        logging.error(f'Failed to load search index with error: {e}')
        property_addresses = None
        search_idx = None
