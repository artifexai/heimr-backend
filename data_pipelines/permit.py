import logging
import time

from dotenv import load_dotenv

from data_pipelines import BasePipeline
from database import build_session, AddressDB, PermitDB
from models.permit import PermitStruct
from utils.helpers import log_time_elapsed
from utils.paths import get_root_directory

logging.basicConfig(level=logging.INFO)


class PermitPipeline(BasePipeline):

    def __init__(self):
        """
           Initialize PermitPipeline with specific model and database model.
           Sets up a specific bucket for the connection.
        """
        super().__init__(model=PermitStruct, db_model=PermitDB)
        self.con.set_bucket('artifex-permit-data-sandbox')

    def find_property_id(self):
        """
            Finds property id based on address_id
        """

        address_ids = list(set([p.address_id for p in self.data]))
        with build_session() as sess:

            res = sess.query(AddressDB.property_id, AddressDB.address_id).filter(
                AddressDB.address_id.in_(address_ids)).all()

        property_lookup = {i[1]: i[0] for i in res}
        for permit in self.data:
            permit.property_id = property_lookup.get(permit.address_id)
            if not permit.property_id:
                continue

    def fetch_address_id(self):
        """
            Fetch the address_id for each permit if the address exists in the database
        """
        lookup_strs = list(set([s.address.st_lookup_str for s in self.data]))

        with build_session() as sess:
            address_record = sess.query(AddressDB.address_id, AddressDB.st_lookup_str).filter(
                AddressDB.st_lookup_str.in_(lookup_strs)).all()
        address_lookup = {i[1]: i[0] for i in address_record}

        for permit in self.data:
            permit.address_id = address_lookup.get(permit.address.st_lookup_str)
            if not permit.address_id:
                continue

            permit.address = None

    def run(self):
        """
           Run the pipeline:
           1. Load data from a checkpoint.
           2. Parse the data.
           3. Assign property ids to the data.
           4. Fetch address ids.
           5. Write the processed data to the database.
        """
        start = time.time()
        self.load_data(checkpoint_path=f'{get_root_directory()}/data/permit_checkpoint.pkl')
        self.parse_data()
        log_time_elapsed(start, 'parsing and loading data')

        self.fetch_address_id()
        log_time_elapsed(start, 'fetched address ids')

        self.find_property_id()
        log_time_elapsed(start, 'assigned property id')

        self.write_to_db()

    def run_from_pickle(self, path):
        """
            Run the pipeline using pickle file to load data
        """
        start = time.time()

        self.load_from_pickle(path)
        self.parse_data()
        log_time_elapsed(start, 'parsing and loading data')

        self.fetch_address_id()
        log_time_elapsed(start, 'fetched address ids')

        self.find_property_id()
        log_time_elapsed(start, 'assigned property id')

        self.write_to_db()


if __name__ == "__main__":
    load_dotenv()

    permit_pipe = PermitPipeline()
    permit_pipe.run()
    # permit_pipe.run_from_pickle(f'{get_root_directory()}/data/permit_checkpoint.pkl')
