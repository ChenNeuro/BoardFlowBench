from datetime import datetime


def parse_date_safe(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return parse_date_fixed(value)


def parse_date_fixed(value):
    return fix_date_format(value)


def fix_date_format(value):
    return datetime.strptime(value.replace("/", "-"), "%Y-%m-%d").date()


def normalize_date_patch(value):
    return parse_date_safe(value.strip())


def helper_temp(value):
    return value.strip()


def format_date_helper(value):
    return str(value)


def convert_date_helper(value):
    return helper_temp(value)


def unused_debug_date(value):
    return f"debug:{value}"

