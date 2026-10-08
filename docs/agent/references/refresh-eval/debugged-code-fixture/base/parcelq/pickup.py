from datetime import datetime, timedelta

from parcelq import clock

CUTOFF_HOUR_UTC = 16


def pickup_date():
    """The date the courier collects: today if booked before the cutoff, otherwise tomorrow."""
    today = clock.now().date()
    if datetime.now().hour < CUTOFF_HOUR_UTC:
        return today
    return today + timedelta(days=1)
