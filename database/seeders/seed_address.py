import json
import logging
from typing import Dict, List

import pandas as pd

from database import build_session, AddressDB
from models.shared import AddressStruct
from utils.paths import get_root_directory

logging.basicConfig(level=logging.INFO)


def load_and_preprocess_data(file_path: str) -> Dict:
    """
        Loads and preprocess address data
    """

    data = pd.read_pickle(file_path, compression="gzip")[:50000]
    column_mapping = {
        "St_Name": "street_name",
        "St_PosTyp": "street_suffix",
        "Add_Number": "street_number",
        "Zip_Code": "zip_code",
        "Longitude": 'lon',
        "Latitude": 'lat',
        "State": 'state',
        'Uninc_Comm': 'city',
        'Unit': 'unit'
    }
    data.rename(columns=column_mapping, inplace=True)
    relevant_columns = ['street_name', 'street_suffix', 'city', 'zip_code', 'state', 'lon', 'lat', "street_number",
                        "unit"]
    data = data[relevant_columns]
    data.dropna(subset=['street_suffix', 'zip_code'], inplace=True)
    data.drop_duplicates(inplace=True)
    data_dict = data.to_dict(orient='records')
    del data
    return data_dict


def create_address_instances(data_dict: Dict, lookup_dict) -> List[AddressStruct]:
    """
        Creates non-duplicated instances of AddressStruct
    """
    add_instances = [AddressStruct.from_raw(data_dict[i], lookup_dict) for i in range(len(data_dict))]

    address_string = []
    not_duplicated = []

    for i in add_instances:
        if i.st_lookup_str in address_string:
            continue
        address_string.append(i.st_lookup_str)
        not_duplicated.append(i)

    add_instances = not_duplicated
    del address_string, not_duplicated

    return add_instances


def write_to_db(db_records):
    """
        Write the validated DB objects to Postgres.
    """
    problems = []
    with build_session() as sess:
        for p in db_records:
            try:
                sess.merge(p)
                sess.commit()
            except Exception as e:
                sess.rollback()
                logging.error(f'Error writing to DB: {e}')
                problems.append((p, e))
    logging.info(f'DB Write complete. {len(problems)} problems encountered.')


if __name__ == "__main__":
    street_suffix_lookup = json.load(open(f'{get_root_directory()}/data/street_suffix_lookup.json'))

    address_path = f'{get_root_directory()}/data/all_mass_addresses.pkl'

    address_dict = load_and_preprocess_data(address_path)

    address_instances = create_address_instances(address_dict, street_suffix_lookup)

    address_dicts = [address_instance.dict() for address_instance in address_instances]
    print(f"Number of addresses: {len(address_dicts)}")

    with build_session() as sess:
        address_db_instances = [AddressDB(**address_dict) for address_dict in address_dicts]
        sess.bulk_save_objects(address_db_instances)
        sess.commit()
