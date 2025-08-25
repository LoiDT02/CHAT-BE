import re


def check_DMY_date_format(value):
    regex_pattern = r'^\d{2}/\d{2}/\d{4}$'
    return True if re.match(regex_pattern, value) else False


def check_datetime_format(value):
    regex_pattern = r'^\d{2}:\d{2}:\d{2} \d{2}/\d{2}/\d{4}$'
    return True if re.match(regex_pattern, value) else False