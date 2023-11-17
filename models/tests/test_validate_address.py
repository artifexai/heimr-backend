import json

from models.shared import AddressStruct
from utils.paths import get_root_directory

street_suffix_lookup = json.load(open(f'{get_root_directory()}/data/street_suffix_lookup.json'))


def test_street_formatting():
    base_rec = {
        "state": "Massachusetts",
        "city": "Sandwich",
        "street_name": "pond view drv",
        "street_number": "6",
        "street_suffix": "dr",
        "zip_code": "02563",
        "property_id": 4543990551,
        "realtor_id": "M4543990551"}

    cases = ['Pond VIEW', 'POND VIEW DRIVE', 'POND VIEW DR', 'POND VIEW DR.', 'pond view drv']
    for case in cases:
        rec = base_rec.copy()
        rec['street_name'] = case
        result = AddressStruct.standardize_data(rec, street_suffix_lookup)
        assert result.get('street_name') == 'Pond View'
        assert result.get('street_suffix') == 'Drive'


def test_format():
    rec_with_accents = {
        'street_name': 'Jalapeño',
        'street_suffix': 'road',
        "zip_code": 2601,
        'street_number': '54',
        'city': 'Hyannis',
        'state': 'Massachusetts',

    }
    # Test with accent
    expected_str = '54, Jalapeño Road, Hyannis, Massachusetts 02601'

    address = AddressStruct(**rec_with_accents)
    assert address, 'Successfully initialized AddressStruct'
    assert address.get_formatted_address(street_suffix_lookup) == expected_str

    rec_without_accents = {
        'street_name': 'STRUDLEY',
        'street_suffix': 'road',
        "zip_code": '2601',
        'street_number': '54',
        'city': 'Hyannis',
        'state': 'Massachusetts',
    }
    # Test without accent

    expected_str2 = '54, Strudley Road, Hyannis, Massachusetts 02601'
    address = AddressStruct(**rec_without_accents)
    assert address, 'Successfully initialized AddressStruct'
    assert address.get_formatted_address(street_suffix_lookup) == expected_str2

    # Test for case when we have street suffix in the name of the street
    expected_str3 = '6, Herring Run Drive, Sandwich, Massachusetts 02563'

    rec_with_st_suffix_in_name = {
        'street_name': "Herring RUN.",
        "street_number": "6",
        "street_suffix": "dr",
        "zip_code": "02563",
        "property_id": 4543990551,
        "realtor_id": "M4543990551",
        "state": "Massachusetts",
        "city": "Sandwich"
    }
    address = AddressStruct(**rec_with_st_suffix_in_name)
    assert address, 'Successfully initialized AddressStruct'
    assert address.get_formatted_address(street_suffix_lookup) == expected_str3
