import logging
import os
import re
from typing import ByteString, List, Optional, Union, Dict, cast

import arrow
import emoji
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import Column, Date, DateTime, String, VARCHAR, create_engine, inspect, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session as _Session
from sqlalchemy.orm.state import InstanceState
from sqlalchemy.sql.base import ColumnCollection

# Create type hints for SQLAlchemy
DBSessionType = _Session
SessFactoryType = sessionmaker

load_dotenv()
url = os.getenv('DATABASE_URL')

if not url:
    raise Exception('DATABASE_URL does not exist in environment')

engine = create_engine(url, isolation_level="REPEATABLE READ", pool_pre_ping=True)
# Type is cast because SQLAlchemy uses Any for the return type
DEFAULT_SESSION_FACTORY: SessFactoryType = cast(
    SessFactoryType,
    scoped_session(sessionmaker(bind=engine))
)


def build_session():
    global DEFAULT_SESSION_FACTORY
    return DEFAULT_SESSION_FACTORY()


def rebuild_session_factory_for_testing():
    global DEFAULT_SESSION_FACTORY
    global engine
    # Testing DB is hardcoded so that tests cannot be accidentally run against production
    engine = create_engine(
        'postgresql://test:test@localhost:999/postgres',
        isolation_level="REPEATABLE READ",
        pool_pre_ping=True)
    DEFAULT_SESSION_FACTORY = scoped_session(sessionmaker(bind=engine))


Base = declarative_base()


class ModelUtils:
    """
    Model Utils is inherited by SQLAlchemy columns to provide helper methods
    """

    def strings_to_date(self):
        """
        Method to identify all date columns and ensure they are datetime and not string

        :return:
        :rtype: None
        """
        ins: InstanceState = inspect(self)
        cols: List[Column] = list(ins.mapper.columns)

        for c in cols:
            if isinstance(c.type, DateTime) or isinstance(c.type, Date):
                val = getattr(self, c.name)
                if val:
                    try:
                        parsed_date = arrow.get(val).datetime
                        setattr(self, c.name, parsed_date)
                    except:
                        setattr(self, c.name, None)

    def parse(self):
        """
        Method to enforce data types of a model
        If parsing fails, the value is set to None
        :return:
        """

        ins: InstanceState = inspect(self)
        cols: List[Column] = list(ins.mapper.columns)
        self.strings_to_date()

        for c in cols:
            sql_type = c.type
            val = getattr(self, c.name)
            if is_null(val):
                setattr(self, c.name, None)
                continue

            if isinstance(sql_type, Integer):
                try:
                    setattr(self, c.name, int(val))
                except:
                    setattr(self, c.name, None)

            if isinstance(sql_type, Float):
                try:
                    setattr(self, c.name, float(val))
                except:
                    setattr(self, c.name, None)

    def sanitize_strings(self):
        """
        Method to decode UTF-8 strings, trim whitespace, encode emojis, and enforce column string character limits

        :return:
        :rtype: None
        """
        ins: InstanceState = inspect(self)
        cols: List[Column] = list(ins.mapper.columns)

        for c in cols:
            if isinstance(c.type, String) or isinstance(c.type, VARCHAR):
                val: Optional[Union[str, ByteString]] = getattr(self, c.name)
                if val:
                    #  Decode byte strings if exist
                    sanitized_string = val.decode("utf-8", 'ignore') if isinstance(val, ByteString) else val
                    #  Strip leading/training whitespace, and replace double spaces with single
                    sanitized_string = str(sanitized_string).strip().replace('  ', ' ')
                    #  Encode emojis
                    sanitized_string = emoji.demojize(sanitized_string)
                    sanitized_string = re.sub(r'[^\x00-\x7f]', r'', sanitized_string)
                    #  Ensure number of characters is less than max characters by truncating
                    max_char: int = c.type.length
                    if len(sanitized_string) >= max_char:
                        logging.warning(f'Field {c.name} exceeds maximum character count of {max_char} '
                                        f'for {type(self).__name__} record and will be truncated')
                        sanitized_string = sanitized_string[:max_char - 1]
                    setattr(self, c.name, sanitized_string)

    def to_dict(self) -> Dict:

        inspector: InstanceState = inspect(self)
        columns: ColumnCollection = inspector.mapper.columns

        rec: Dict = {}
        self.parse()

        for col, _ in columns.items():
            val = getattr(self, col)

            # Falsy values should be serialized, by None values should be skipped
            if val is not None:
                rec.update({col: val})

        return rec


def is_null(v):
    if v is None:
        return True

    if isinstance(v, bool):
        return False

    if isinstance(v, str):
        if not v:
            return True
        if v.lower() == 'nan':
            return True
        if v == 'NaN':
            return True
        if v == 'None':
            return True
        return False

    if isinstance(v, float):
        if np.isnan(v):
            return True

    return False


from database.models.taxes import Tax, TaxDB
from database.models.listings import Listing, ListingDB, ListingEventDB
from database.models.permits import Permit, PermitDB
from database.models.properties import Properties, PropertyDB, AddressDB
from database.models.account import Account, UserSession
