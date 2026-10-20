"""Restaurant reporting dates, in Iraq local time (UTC+03:00, no daylight saving)."""
from datetime import date, datetime, time, timedelta, timezone
import unicodedata

BUSINESS_TZ = timezone(timedelta(hours=3), 'Asia/Baghdad')


def business_today():
    return datetime.now(BUSINESS_TZ).date()


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = ''.join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in str(value).strip())
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError('Enter a valid date: YYYY-MM-DD or DD/MM/YYYY')


def utc_midnight(value):
    return datetime.combine(parse_date(value), time.min, BUSINESS_TZ).astimezone(timezone.utc).isoformat(timespec='microseconds')


def period_dates(reference=None):
    anchor = parse_date(reference) if reference is not None else business_today()
    week = anchor - timedelta(days=(anchor.weekday() - 5) % 7)
    month = anchor.replace(day=1)
    following = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
    return {'day': (anchor, anchor), 'week': (week, week + timedelta(days=6)),
            'month': (month, following - timedelta(days=1))}
