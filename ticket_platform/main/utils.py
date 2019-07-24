import datetime
from collections import namedtuple

EventAndTickets = namedtuple("EventAndTickets", ("event", "num_of_tickets"))
EventSummary = namedtuple("EventSummary", ("event", "total_tickets", "reservations", "sold_tickets", "profit", "possible_profit"))


def payment_error_message(currency, amount):
    """
    Function to throw message about error during payment.
    """
    return f"{amount} {currency} is not valid amount. Please, provide a proper amount in {currency}."


def turn_none_into_zero(value):
    """
    Used to refine plot data from Django aggregations functions.
    :param value: check is values is none. If not, will return value back.
    :return: 0 if value is 'None'
    """
    if value is None:
        return 0
    return value


def time_between(start, end):
    """
    Get all days between start and end date. Needed to generate a full chart from first object occurence to last.
    :param start: start date in datetime.datetime.date format
    :param end: end date in datetime.datetime.date format
    :return: yield start plus one day till end.
    """
    while start < end:
        yield start
        start += datetime.timedelta(days=1)
