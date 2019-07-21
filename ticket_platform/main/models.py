from django.db import models
from django.utils import timezone


class Event(models.Model):
    """
    Main Event model for ticket platform.

    Fields:
        name - field with name of the event.
        time_and_date - field with date and time of event.
    """
    name = models.CharField(max_length=30)
    time_and_date = models.DateTimeField()

    def get_time(self) -> str:
        """
        Method give us a formatted time.
        :return: only hour and minute in nice, readable format '<h>:<m>'
        """
        return f"{self.time_and_date.hour}:{self.time_and_date.minute}"

    def get_url(self) -> int:
        """
        Get a pk of event, usable as url.
        :return: url of event (url contain only pk argument) as int
        """
        return self.pk

    def get_sum_of_available_tickets(self) -> int:
        """
        Count and get a sum of total available ticket sum for event.
        :return: Sum of available tickets.
        """
        return self.ticket_set.filter(
            is_sold=False
        ).exclude(
                reservation_time__gte=timezone.now()
            ).count()

    def get_available_tickets_num_by_categories(self) -> tuple:
        """
        Count and get a amount of total available tickets per category for event.
        :return: Tuple with categories: sum of available ticket.
        """
        return (
            (category[1], self.ticket_set.filter(
                category=category[1],
                is_sold=False
            ).exclude(
                reservation_time__gte=timezone.now()
            ).count()) for category in Ticket.CATEGORY
        )


class Ticket(models.Model):
    """
    Class with Ticket Model.

    Fields:
        CATEGORY = constant list of tickets type.
        event = show us for what event ticket is.
        category = Char field with category selected according to CATEGORY field.
        is_sold = Information is ticket already sold.
    """
    CATEGORY = (
        ("N", "Normal"),
        ("P", "Premium"),
        ("V", "VIP")
    )
    event = models.ForeignKey(to=Event, on_delete=models.PROTECT)
    category = models.CharField(max_length=10, choices=CATEGORY, default="Normal")
    is_sold = models.BooleanField(default=False)
    reservation_time = models.DateTimeField(default=timezone.now())

    def reserve_ticket(self, minutes=15):
        self.reservation_time = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save()
