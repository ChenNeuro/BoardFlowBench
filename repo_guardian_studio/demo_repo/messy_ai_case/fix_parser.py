from parser_final import normalize_date_patch


def wrapper_parse(value):
    return normalize_date_patch(value)


def quick_parse(value):
    return wrapper_parse(value)


def unused_final_helper():
    return None

