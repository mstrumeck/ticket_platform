from django.db import models
from django.db.models import F
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
    reservations = models.IntegerField(default=0)

    def increase_reservations_counter(self) -> None:
        """
        Mark if someone click on the reservation button for this event.
        """
        self.reservations = F('reservations') + 1
        self.save()

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


class Order(models.Model):
    """
    Class with Order object where is stored all data about transaction.
    """
    CURRENCY = (
        ("EUR", "Euro"),
    )
    name = models.CharField(max_length=30)
    surname = models.CharField(max_length=30)
    time_and_date = models.DateTimeField(auto_now=True)


class Ticket(models.Model):
    """
    Class with Ticket Model.

    Fields:
        CATEGORY - constant list of tickets type.
        event - show us for what event ticket is.
        category - char field with category selected according to CATEGORY field.
        is_sold - information is ticket already sold.
        reservation_time - time until ticket will be lock for other users
        price - price of ticket in decimal
    """
    CATEGORY = (
        ("N", "Normal"),
        ("P", "Premium"),
        ("V", "VIP")
    )
    event = models.ForeignKey(to=Event, on_delete=models.PROTECT)
    order = models.ForeignKey(to=Order, on_delete=models.PROTECT, null=True)
    category = models.CharField(max_length=10, choices=CATEGORY, default="Normal")
    is_sold = models.BooleanField(default=False)
    reservation_time = models.DateTimeField(default=timezone.now())
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def reserve(self, minutes=15) -> None:
        """
        Increase 'reservation_time' according to 'minutes' parameter. If reservation_time is bigger than current time,
        ticket will be lock for other users.
        :param minutes: integer value needed to increase 'reservation_time'
        """
        self.reservation_time = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save()

    def release(self) -> None:
        """
        Set back 'reservation_time' to current. Ticket is now visible for rest of users.
        """
        self.reservation_time = timezone.now()
        self.save()

    def is_reservation_expired(self) -> bool:
        """
        Give information if ticket is still reserved by other user
        :return: bool
        """
        return self.reservation_time <= timezone.now()

    def buy(self, order) -> None:
        """
        Change ticket status to permanent invisible for other users, and assign ticket to suitable order.
        :param order: Order object with information about transaction.
        """
        self.is_sold = True
        self.order = order
        self.release()
