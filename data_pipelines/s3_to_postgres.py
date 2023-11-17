import logging
import pickle
from typing import List, Dict, Optional

import arrow
from dotenv import load_dotenv

from aws.s3_handler import S3
from database import build_session
from database.models.properties import PropertyDB
from models.property import PropertyStruct
from utils.types import DateType


class PropertyPipeline:
    """
    Pipeline to load property data from S3, transform, validate, enforce types, and write to DB

    Attributes
    ----------

        con: S3 connection object
        max_records: Maximum number of records to load from S3
            NOTE: records are limiting by the first n records by date
        after_date: Only load records after this date
        data: Raw data from S3
        properties: List of PropertyStruct objects
        db_records: List of PropertyDB objects

    """
    con: S3

    max_records: Optional[int]
    after_date: Optional[DateType]
    offset: Optional[int]
    data: Optional[List[Dict]]
    properties: Optional[List[PropertyStruct]]
    db_records: Optional[List[PropertyDB]]

    def __init__(self,
                 max_records: Optional[int] = None,
                 after_date: Optional[DateType] = None,
                 offset: Optional[int] = None
                 ):
        logging.info('Starting property pipeline')
        self.max_records = max_records
        self.after_date = after_date
        self.offset = offset

        self.con = S3()
        self.con.set_bucket('artifex-property-data-sandbox', 'realtor')

    def run(self):
        """
        Run the pipeline. All orchestration is done here.

        """
        s = arrow.now()
        print(f'Starting pipeline at {s}')
        logging.info('Loading property data')
        self.load_data()
        logging.info('Writing property data to DB')
        self.write_to_db()

        e = arrow.now()
        print(f'Pipeline finished at {e}')
        print(f'Pipeline took {e - s}')

    def load_data(self, from_pickle: Optional[str] = None):
        """
        Load data from S3, parse with pydantic, and convert to DB objects

        """

        if from_pickle:
            self.data = pickle.load(open(from_pickle, 'rb'))

        else:
            self.data = self.con.load_files_after_date(
                date=self.after_date,
                limit=self.max_records,
                offset=self.offset
            )
            pickle.dump(self.data, open('../data/s3_dump.pkl', 'wb'))

        self.properties = []
        problem_records = []

        for d in self.data:
            try:
                self.properties.append(PropertyStruct.from_raw(d))
            except Exception as e:
                logging.error(f'Error parsing property: {e}')
                problem_records.append(d)
                continue

        if problem_records:
            logging.warning(f'Problem records: {len(problem_records)}')

        self.db_records = [_p.to_orm_obj() for _p in self.properties]

    def write_to_db(self):
        """
        Write the validated DB objects to Postgres

        """
        problems = []
        with build_session() as sess:
            for p in self.db_records:
                try:
                    sess.merge(p)
                    sess.commit()
                except Exception as e:
                    sess.rollback()
                    logging.error(f'Error writing to DB')
                    problems.append((p, e))

        print(f'DB Write complete. {len(problems)} problems')


if __name__ == '__main__':
    load_dotenv()

    logging.basicConfig(level=logging.INFO)
    # listing_pipeline = PropertyPipeline()
    # listing_pipeline.load_data(from_pickle='../data/s3_dump.pkl')
    # listing_pipeline.write_to_db()

    # # Load permit data
    s3 = S3()
    s3.set_bucket('artifex-permit-data-sandbox')
    permit_data = s3.load_files_after_date(date='2021-01-01', limit=10)
    #
    # # Load deed data
    # s3.set_bucket('artifex-deed-data-sandbox')
    # objects = s3.objects_in_bucket()
    # deed_data = s3.read_many_objects_json(objects)
