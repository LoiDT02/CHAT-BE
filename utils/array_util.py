from typing import List


def unique_elements_in_two_array(arr1, arr2):
    set1 = set(arr1)
    set2 = set(arr2)

    unique_in_arr1 = set1 - set2
    unique_in_arr2 = set2 - set1

    unique_elements = list(unique_in_arr1) + list(unique_in_arr2)
    return unique_elements


def merge_and_remove_duplicates_in_two_array(arr1, arr2):
    return list(set(arr1).union(arr2))


def elements_in_first_array_not_in_second_array(arr1, arr2):
    set1 = set(arr1)
    set2 = set(arr2)
    return list(set1 - set2)


def remove_duplicate_in_array_obj(arr, attrs: List[str]):
    seen = set()
    unique_results = []

    for obj in arr:
        identifier = tuple(getattr(obj, attr) for attr in attrs)
        if identifier not in seen:
            seen.add(identifier)
            unique_results.append(obj)

    return unique_results


def remove_duplicate_in_array(arr):
    return list(set(arr))
