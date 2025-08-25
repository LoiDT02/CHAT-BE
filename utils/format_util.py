import re
from datetime import date

from unidecode import unidecode


def acronym_format(acronym_str: str) -> str:
    return unidecode(''.join(word[0] for word in acronym_str.split()).lower())


def unsigned_format(unsigned_str: str) -> str:
    return unidecode(unsigned_str.lower())


def username_format(full_name: str, date_of_birth: date) -> str | None:
    parts = full_name.split()
    last_middle_name = " ".join(parts[:-1])
    first_name = parts[-1]

    last_middle_name_acronym = acronym_format(last_middle_name)
    first_name_unsigned = unsigned_format(first_name)
    date_of_birth_short = date_of_birth.strftime("%d%m%y")

    regex = "".join([last_middle_name_acronym, first_name_unsigned, date_of_birth_short])
    return regex

