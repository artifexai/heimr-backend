import re
import unicodedata
from copy import deepcopy
from typing import Dict, Optional

from pydantic import BaseModel, Extra, Field

from utils.helpers import try_pop


class AddressStruct(BaseModel):
    state: str = Field()
    city: str = Field()
    street_name: str = Field()
    street_number: str = Field()
    zip_code: int = Field(..., alias='postal_code')  # alias allows parsing of raw data with key 'postal_code'

    street_suffix: Optional[str] = Field()
    st_lookup_str: Optional[str] = Field()

    unit: Optional[str] = Field()
    lat: Optional[float] = Field()
    lon: Optional[float] = Field()

    # join fields
    property_id: Optional[int] = Field()

    @staticmethod
    def process_street_number(street_number):
        if isinstance(street_number, (float, int)):
            return str(int(street_number))
        elif isinstance(street_number, int):
            return str(street_number)
        return street_number

    @staticmethod
    def remove_accents(input_str: str) -> str:
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
        return only_ascii

    @staticmethod
    def get_suffix_lookup(street_suffix: str, street_suffix_dict: Dict) -> str:
        sfx_lookup = street_suffix_dict.get(street_suffix.lower())
        if sfx_lookup:
            return sfx_lookup.title()

    @staticmethod
    def remove_special_chars_except_accents(s: str) -> str:
        pattern = re.compile(r'[^a-zA-Z0-9\s\u00C0-\u017F]')
        return pattern.sub('', s)

    @staticmethod
    def identify_suffix_in_street(street_name, street_suffix_dict):
        last_token_pattern = re.compile(r'\s(\w+)$')
        last_token_match = last_token_pattern.search(street_name)
        if last_token_match:
            last_token = last_token_match.group(1)
            if street_name.endswith(last_token) and last_token.lower() in street_suffix_dict:
                return last_token, street_name, True
        return None, street_name, False

    @staticmethod
    def check_if_suffix_match(street_name, street_suffix, street_suffix_dict):
        suffix, street_name, suffix_found = AddressStruct.identify_suffix_in_street(street_name, street_suffix_dict)
        if suffix_found:
            tmp_suffix = AddressStruct.get_suffix_lookup(suffix, street_suffix_dict)
            if tmp_suffix == street_suffix:
                street_name = street_name.replace(suffix, '').strip()
        return street_name

    @staticmethod
    def standardize_data(data: Dict, street_suffix_dict: Dict):
        if data.get('st_lookup_str'):
            return data

        street_number = AddressStruct.process_street_number(data.get('street_number') or data.get('street_no'))
        data['street_number'] = street_number
        street_name = AddressStruct.remove_special_chars_except_accents(data.get('street_name')).title()
        street_suffix = data.get('street_suffix')
        unit = data.get('unit')
        data['city'] = data['city'].title()
        if data['state'] == 'Massachusetts':
            data['state'] = 'MA'

        if street_suffix:
            street_suffix = AddressStruct.get_suffix_lookup(street_suffix, street_suffix_dict)
            street_name = AddressStruct.check_if_suffix_match(street_name, street_suffix, street_suffix_dict)
        else:
            suffix, street_name, found = AddressStruct.identify_suffix_in_street(street_name, street_suffix_dict)
            if found:
                street_name = street_name.replace(suffix, '').strip()
                street_suffix = AddressStruct.get_suffix_lookup(suffix, street_suffix_dict)

        data['street_name'] = street_name
        data['street_suffix'] = street_suffix
        standard_street_name = AddressStruct.remove_accents(street_name)
        zip_code = data.get('postal_code') or data.get('zip_code')

        data['st_lookup_str'] = f'{street_number.lower()} {standard_street_name.lower()} '

        if street_suffix and str(street_suffix).lower() != 'nan':
            data['st_lookup_str'] += f'{street_suffix.lower()}, '
        if unit and str(unit).lower() != 'nan':
            if isinstance(unit, (int, float)):
                unit = str(int(unit))
            data['st_lookup_str'] += f'{unit.lower().strip()}, '

        data['st_lookup_str'] += f'{AddressStruct.format_zip(zip_code)}'

        return data


    @staticmethod
    def from_raw(address: Dict, street_suffix_dict: Dict):
        address = deepcopy(address)
        coords = try_pop(address, 'coordinates')
        if coords:
            address['lat'] = try_pop(coords, 'lat')
            address['lon'] = try_pop(coords, 'lon')

        validated_data = AddressStruct.standardize_data(address, street_suffix_dict)
        return AddressStruct.parse_obj(validated_data)

    @staticmethod
    def format_zip(zip_code):
        return str(int(zip_code)).zfill(5)

    def get_formatted_address(self, street_suffix_dict):
        """
        Address displayed as human-readable format
        """
        data = AddressStruct.standardize_data(self.dict(), street_suffix_dict)
        original_street_name = data.get('street_name')
        street_num = data.get('street_number')
        street_suffix = data.get('street_suffix')
        city = data.get('city')
        state = data.get('state')
        zipcode = data.get('postal_code') or data.get('zip_code')

        return f'{street_num}, {original_street_name.title()} {street_suffix.title()},' \
               f' {city.title()}, {state} {AddressStruct.format_zip(zipcode)}'

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
        from_attributes = True
        extra = Extra.ignore
