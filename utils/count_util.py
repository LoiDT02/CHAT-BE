def count_digits(value_str: str) -> int:
    count = 0
    for char in value_str:
        if char.isdigit():
            count += 1
    return count
