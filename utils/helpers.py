import inspect
import json
import logging
import re
import sys
import time
from datetime import date
from typing import Optional, Any, List, Union, Dict

import arrow

from utils.types import T, DateType


# noinspection PyBroadException
def try_parse_date(d: Any, utc: bool = False) -> Optional[date]:
    if not d:
        return
    try:
        val = arrow.get(d)
        if not val:
            return
        return val.to('UTC').date() if utc else val.date()

    except Exception:
        return


def pick_keys(d: Dict, fields: List[str]) -> Dict:
    rec = {}
    for k, v in d.items():
        if v and (k in fields):
            rec.update({k: v})

    return rec


def drop_keys(d: Dict, fields: List[str]) -> Dict:
    rec = {}
    for k, v in d.items():
        if v and (k not in fields):
            rec.update({k: v})

    return rec


def rename(d: Dict, mapping: Dict) -> Dict:
    res = {}
    for k, v in d.items():
        new_name = mapping.get(k)
        if new_name:
            res.update({new_name: v})
        else:
            res.update({k: v})

    return res


def drop_empty_keys(d: Dict) -> Dict:
    res = {}
    for k, v in d.items():
        if v:
            res.update({k: v})
    return res


def from_camel_case_to_snake_case(data):
    return [{string_to_camel(k): v for k, v in d.items()} for d in data]


def dict_keys_to_snake_case(data):
    res = {}
    for k, v in data.items():
        if v:
            key = string_to_camel(k)
            res.update({key: v})
    return res


def string_to_camel(s: str):
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', s).lower().replace('-', '_')


def first_element_of_list(l: List[T]) -> Optional[T]:
    return next(iter(l), None)


def unwrap_if_one(l: List[T]) -> Optional[Union[List[T], T]]:
    if not l:
        return
    if len(l) > 1:
        return l
    return first_element_of_list(l)


def ms_timestamp(d: DateType) -> int:
    ts = arrow.get(d).to('UTC').timestamp() * 1000
    return int(ts)


def log_time_elapsed(start, activity):
    elapsed_time = time.time() - start
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = elapsed_time % 60
    logging.info(f'Finished {activity} in {hours}:{minutes:02}:{seconds:05.2f}')


def fetch_nested_key(d: Dict, key_path: List[Any]) -> Any:
    """
    Read a nested value from a dictionary.

    If a key doesn't exist, it will return None

    Do you ever get tired of writing a million (x.get('y') or {}).get('z') statements? Well, this is the fix

    Example:
        data = {'first_key': {'second_key': 10}}
        fetch_nested_key(data, ['first_key']) => {'second_key': 10}
        fetch_nested_key(data, ['first_key', 'second_key']) => 10
        fetch_nested_key(data, ['first_key', 'third_key', 'fourth_key']) => None

    :param d:
    :param key_path:
    :return:
    """
    rec: Any = d
    for key in key_path:
        rec = (rec or {}).get(key)
    return rec


def pretty_print(d: Dict):
    """
    Print a dictionary in a pretty format
    """
    print(json.dumps(d, indent=4, sort_keys=True))


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


def print_top_memory_usage(n: int = 10):
    _vars = dict(inspect.getmembers(inspect.stack()[1][0]))["f_globals"]
    by_memory = sorted(((name, sys.getsizeof(value)) for name, value in _vars.items()), key=lambda x: -x[1])
    for name, size in by_memory[:n]:
        print("{:>30}: {:>8}".format(name, sizeof_fmt(size)))


def try_pop(d: Dict, key: str) -> Optional[Any]:
    """
    Try to pop a key from a dictionary, if it doesn't exist, return None

    """
    if not d or not isinstance(d, dict):
        return None
    try:
        return d.pop(key)
    except KeyError:
        return None
