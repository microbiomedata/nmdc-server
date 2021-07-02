from datetime import datetime
from enum import Enum
from math import floor
from typing import List, TypeVar

from dateutil.relativedelta import SU, relativedelta

BinnableValue = TypeVar("BinnableValue", float, int, datetime)


class DateBinResolution(Enum):
    day = "day"
    week = "week"
    month = "month"
    year = "year"


def range_bins(min_: BinnableValue, max_: BinnableValue, num_bins: int) -> List[BinnableValue]:
    """Get equal length bins for a given numeric range."""
    if max_ <= min_:
        raise ValueError("expected min_ < max_")
    if num_bins <= 0:
        raise ValueError("expected positive number of bins")
    step = (max_ - min_) / num_bins
    if isinstance(min_, int):
        step = floor(step)
        if step <= 0:
            raise ValueError("num_bins too large for numeric range")
    return [min_ + step * i for i in range(num_bins)] + [max_]


def datetime_bins(min_: datetime, max_: datetime, resolution: DateBinResolution) -> List[datetime]:
    """Get date range bins of various size."""
    min_date = min_.date()
    max_date = max_.date() + relativedelta(days=1)

    # expand min/max date to be a round value at the binning resultion requested
    if resolution == DateBinResolution.day:
        delta = relativedelta(days=1)
    elif resolution == DateBinResolution.week:
        min_date += relativedelta(weekday=SU(-1))
        max_date += relativedelta(weekday=SU)
        delta = relativedelta(weeks=1, weekday=SU)
    elif resolution == DateBinResolution.month:
        min_date += relativedelta(day=1)
        max_date += relativedelta(months=1, day=1)
        delta = relativedelta(months=1, day=1)
    elif resolution == DateBinResolution.year:
        min_date += relativedelta(month=1, day=1)
        max_date += relativedelta(years=1, month=1, day=1)
        delta = relativedelta(years=1, day=1, month=1)
    else:
        raise ValueError("Invalid date bin category")

    if max_date <= min_date:
        raise ValueError("expected non-empty date range")

    d = min_date
    dates = []
    min_time = datetime.min.time()
    while d <= max_date:
        dates.append(datetime.combine(d, min_time))
        d += delta
    return dates
