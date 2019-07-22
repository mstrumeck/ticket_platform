"""Exceptions for pronto detector."""


class BaseBasketExceptions(Exception):
    """Base repository exception."""


class NonExistingTicketToRemove(BaseBasketExceptions):
    """Wrong range revision exception."""

    template = "Event with id {} hasn't tickets for category: {}."

    def __init__(self, event_id, category) -> None:
        message = self.template.format(event_id, category)
        super().__init__(message)
