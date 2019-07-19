from django.db import models


class Event(models.Model):
    """
    Main Event model for ticket platform.
    Fields:
        name - field with name of the event.
        time_and_date - field with date and time of event.

    Methods:
        get_time - return only hour and minute in nice, readable format '<h>:<m>'
        get_url - return url of event (url contain only pk argument)
    """
    name = models.CharField(max_length=30)
    time_and_date = models.DateTimeField()

    def get_time(self) -> str:
        return f"{self.time_and_date.hour}:{self.time_and_date.minute}"

    def get_url(self) -> int:
        return self.pk
