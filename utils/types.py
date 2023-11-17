from datetime import date, datetime
from typing import List, TypeVar, Union, Dict

import arrow

T = TypeVar("T")
DateType = Union[arrow.Arrow, date, datetime, str]
ListDict = List[Dict]
