from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

SCALE = 1000  # exact thousandths of IQD; UI precision is independent


def decimal(value):
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('Invalid numeric value') from exc
    if not result.is_finite():
        raise ValueError('Number must be finite')
    return result


def units(value):
    return int((decimal(value) * SCALE).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def amount(value):
    return Decimal(value) / SCALE


def money(value, precision=0):
    return f'{amount(value):,.{precision}f} IQD'


def percentage(value, rate):
    rate = decimal(rate)
    if not 0 <= rate <= 100:
        raise ValueError('Percentage must be between 0 and 100')
    return int((Decimal(value) * rate / 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
