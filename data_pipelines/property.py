import logging
import time

from dotenv import load_dotenv

from data_pipelines import BasePipeline
from database import AddressDB, PropertyDB, build_session
from models.property import PropertyStruct, AddressStruct
from utils.helpers import log_time_elapsed
from utils.paths import get_root_directory

logging.basicConfig(level=logging.INFO)


class PropertyPipeline(BasePipeline):

    def __init__(self, max_records=None, after_date=None, offset=None):
        """
            Initialize PropertyPipeline with specific model and database model.
            Sets up a specific bucket for the connection.
        """
        super() \
            .__init__(
            model=PropertyStruct,
            db_model=PropertyDB,
            max_records=max_records,
            after_date=after_date,
            offset=offset
        )
        self.con.set_bucket('artifex-property-data-sandbox', 'realtor')

    def run(self):
        """
          Run the pipeline:
          1. Load data from a checkpoint.
          2. Parse the data.
          3. Fetch address ids.
          4. Write the processed data to the database.
        """
        start = time.time()
        self.load_data(checkpoint_path=f'{get_root_directory()}/data/property_checkpoint.pkl')
        self.parse_data()
        log_time_elapsed(start, 'parsing and loading data')
        self.fetch_address_id()
        log_time_elapsed(start, 'fetched address ids')

        self.write_to_db()

    def fetch_address_id(self):
        """
            Fetch the address_id for each property if the address exists in the database
        """
        lookup_strs = [s.address.st_lookup_str for s in self.data]

        with build_session() as sess:
            address_record = sess.query(AddressDB.address_id, AddressDB.st_lookup_str).filter(
                AddressDB.st_lookup_str.in_(lookup_strs)).all()
        address_lookup = {i[1]: i[0] for i in address_record}
        new_addresses = []

        for p in self.data:
            p.address_id = address_lookup.get(p.address.st_lookup_str) if not p.address_id else p.address_id
            if not p.address_id:
                new_addresses.append(p)
                continue

        lookup_strs = [s.address.st_lookup_str for s in new_addresses]
        new_addresses = [AddressDB(**AddressStruct.parse_obj(s.address).dict()) for s in new_addresses]
        # dedupe by st_lookup_str
        new_addresses = list({v.st_lookup_str: v for v in new_addresses}.values())
        sess = build_session()
        res = sess.bulk_save_objects(new_addresses)
        sess.commit()
        print('type res: ', type(res))
        address_record = sess.query(AddressDB.address_id, AddressDB.st_lookup_str).filter(
            AddressDB.st_lookup_str.in_(lookup_strs)).all()
        sess.close()

        address_lookup = {i[1]: i[0] for i in address_record}

        for p in self.data:
            if p.address_id:
                continue
            p.address_id = address_lookup.get(p.address.st_lookup_str)
            if not p.address_id:
                print('Failed to generate address id for, ', p.address.st_lookup_str)
                continue
            p.address = None

    def run_from_pickle(self, path):
        """
        Run the pipeline using pickle file
        """
        start = time.time()

        self.load_from_pickle(path)
        self.parse_data()
        log_time_elapsed(start, 'parsing and loading data')

        self.fetch_address_id()
        log_time_elapsed(start, 'fetched address ids')

        self.write_to_db()


if __name__ == "__main__":
    load_dotenv()
    listing_pipeline = PropertyPipeline(max_records=100000)

    # To run data from s3 instances
    # listing_pipeline.run()

    # Data can be optionally run from a checkpoint like this
    listing_pipeline.run_from_pickle(f'{get_root_directory()}/data/property_checkpoint.pkl')
