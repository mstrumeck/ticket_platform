from collections import namedtuple

EventAndTickets = namedtuple("EventAndTickets", ("event", "num_of_tickets"))


def payment_error_message(currency, amount):
    return f"{amount} {currency} is not valid amount. Please, provide a proper amount in {currency}."
