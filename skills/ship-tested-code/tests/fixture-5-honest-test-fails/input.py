"""Monthly request quota."""


def remaining(monthly_limit, usage_by_month, month):
    """Requests left in `month` ("YYYY-MM"). Never negative; a month with no usage has the full limit."""
    used = usage_by_month.get(month, 0)
    return monthly_limit - used
