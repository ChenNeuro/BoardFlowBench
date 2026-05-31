from calculator import add_amount


def total_amount(values):
    """Return the total for a sequence of values."""
    total = 0
    for value in values:
        total = add_amount(total, value)
    return total


def format_total(values):
    total = total_amount(values)
    return f"Total: {total:.2f}"

