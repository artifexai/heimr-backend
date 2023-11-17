import json
import logging
import pickle
from typing import List
from typing import Optional
from typing import Type
from typing import Union

from aws.s3_handler import S3
from database import PermitDB
from database import PropertyDB
from database import build_session
from models.permit import PermitStruct
from models.property import PropertyStruct
from utils.paths import get_root_directory
from utils.types import DateType

PipelineModel = Type[Union[PropertyStruct, PermitStruct]]
PipelineData = Union[PropertyStruct, PermitStruct]
PipelineDBModel = Type[Union[PropertyDB, PermitDB]]


class BasePipeline:
    con: S3
    model: PipelineModel
    db_model: PipelineDBModel
    max_records: Optional[int]
    after_date: Optional[DateType]
    offset: Optional[int]
    data: Optional[List[PipelineData]]
    raw_data: Optional[List[dict]]

    def __init__(self,
                 model: PipelineModel,
                 db_model: PipelineDBModel,
                 max_records: Optional[int] = None,
                 after_date: Optional[DateType] = None,
                 offset: Optional[int] = None
                 ):

        self.model = model
        self.db_model = db_model

        self.max_records = max_records
        self.after_date = after_date
        self.offset = offset
        self.street_suffix_lookup = json.load(open(f'{get_root_directory()}/data/street_suffix_lookup.json'))

        self.con = S3()

    def load_data(self, checkpoint_path: Optional[str] = None):
        """
        Load data from S3, parse with pydantic

        If checkpoint_path is provided, the data will be saved to that path as a pickle file

        Args:
            checkpoint_path: Optional[str]: Path to save the data to as a pickle file

        """
        if not self.con.bucket:
            raise Exception('An S3 bucket must be set before you can call the load_data method')

        self.raw_data = self.con.load_files_after_date(
            date=self.after_date,
            limit=self.max_records,
            offset=self.offset,
            parallel=True
        )
        if checkpoint_path:
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(self.raw_data, f)

    def load_from_pickle(self, path):
        """
        Load data from a pickle file
        Args:
            path: str: Path to the pickle file
        """
        with open(path, 'rb') as f:
            self.raw_data = pickle.load(f)

    def parse_data(self):
        """
        Parse the raw data into pydantic objects and validate
        """
        records: List[PipelineData] = []
        problem_records = []
        for d in self.raw_data:
            try:
                mod = self.model.from_raw(d, self.street_suffix_lookup)
                if isinstance(mod, List):
                    records.extend(mod)
                else:
                    records.append(mod)
            except Exception as e:
                logging.error(f'Error parsing: {e}')
                problem_records.append(d)
                continue

        self.data = records

        if problem_records:
            logging.warning(f'Problem records: {len(problem_records)}')

    def write_to_db(self):
        """
        Write the validated DB objects to Postgres

        """

        db_records = [d.to_orm_obj() for d in self.data]
        chunked_records = [db_records[i:i + 1000] for i in range(0, len(db_records), 1000)]

        problems = []
        with build_session() as sess:
            for c in chunked_records:
                try:
                    sess.bulk_save_objects(c)
                    sess.commit()
                except Exception as e:
                    sess.rollback()
                    logging.error(f'Error writing to DB')
                    problems.append((c, e))
            for p in db_records:
                try:
                    sess.merge(p)
                    sess.commit()
                except Exception as e:
                    sess.rollback()
                    logging.error(f'Error writing to DB')
                    problems.append((p, e))

        print(f'DB Write complete. {len(problems)} problems')
