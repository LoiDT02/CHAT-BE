import json
import logging
import re
from datetime import datetime, date
from enum import Enum
from typing import Dict, Any, List
from urllib.parse import unquote

import unicodedata
from rapidfuzz import fuzz, process

from constant import AppStatus
from core import error_exception_handler

logger = logging.getLogger(__name__)


def convert_to_DMY_date(date_str: str) -> date:
    return datetime.strptime(date_str, '%d/%m/%Y').date()


def convert_to_DMY_str(date_value) -> str:
    if date_value is not None:
        return date_value.strftime('%d/%m/%Y')

def convert_str_to_param(param: str):
    try:
        decoded_param = unquote(param)
        param_data = json.loads(decoded_param)
        return param_data
    except (json.JSONDecodeError, TypeError, ValueError):
        msg = "Chuỗi không được mã hóa hợp lệ hoặc không thể giải mã."
        logger.error(msg, exc_info=ValueError(AppStatus.ERROR_400_INVALID_DATA))
        raise error_exception_handler(app_status=AppStatus.ERROR_400_INVALID_DATA, description=msg)


def convert_date_to_datetime(date_value: date) -> datetime:
    return datetime(date_value.year, date_value.month, date_value.day)


def convert_dates(notification: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    for field in fields:
        date_value = notification.get(field)
        if date_value:
            notification[field] = convert_to_DMY_str(date_value)
    return notification


def convert_datetime_to_str(datetime_value: datetime) -> str:
    return datetime_value.strftime("%H:%M:%S %d/%m/%Y")


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text


def convert_approximate_value_to_enum(value: str, enum: Enum, threshold: int = 80):
    if not value or not isinstance(value, str):
        return None

    enum_mapping = {normalize_text(e.value): e for e in enum}
    normalized_value = normalize_text(value)
    if normalized_value in enum_mapping:
        return enum_mapping[normalized_value]

    choices = list(enum_mapping.keys())
    best_match = process.extractOne(normalized_value, choices, scorer=fuzz.token_set_ratio)

    if best_match and best_match[1] >= threshold:
        return enum_mapping[best_match[0]]
    return None


def convert_str_to_datetime(datetime_str: str) -> datetime:
    return datetime.strptime(datetime_str, '%H:%M:%S %d/%m/%Y')

def convert_value_template_to_dict(text: str, template: str) -> dict | None:
    regex_pattern = re.escape(template)
    regex_pattern = re.sub(r'\\{(\w+)\\}', r'(?P<\1>.+?)', regex_pattern)

    match = re.match(regex_pattern, text)
    if not match:
        return None

    return match.groupdict()
