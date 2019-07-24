from django.conf import settings

from .exceptions import NonExistingTicketToRemove
from .models import Ticket, Event, Order


class Basket:
    """
    Basket class to store reserved tickets within basket per user anonymous session.
    """
    def __init__(self, request) -> None:
        self.session = request.session
        basket = self.session.get(settings.BASKET_SESSION_ID, {})
        self.basket = basket
        self._remove_expired_tickets()

    def buy(self, name, surname) -> None:
        """
        Lock all ticket within the basket and create order object about transaction.
        :param name: name of person who buy tickets.
        :param surname: surname of person who buy tickets.
        """
        if self.basket.keys():
            order = Order.objects.create(name=name, surname=surname)
            tickets = self._get_tickets_ob_by_tickets_id_in_basket()
            for ticket in tickets:
                ticket.buy(order)
            self.save()

    def add(self, ticket) -> None:
        """
        Add given ticket objects to basket. Ticket will be release from the basket within next 15 minutes.
        Before that, user has opportunity to buy it.
        :param ticket: Ticket object for given event.
        """
        ticket.event.increase_reservations_counter()
        if str(ticket.id) not in self.basket:
            self.basket[str(ticket.id)] = {
                'price': str(ticket.price),
                'category': ticket.category,
            }
        ticket.reserve()
        self.save()

    def save(self) -> None:
        """
        Save current basket in session.
        """
        self.session[settings.BASKET_SESSION_ID] = self.basket

    def remove(self, event_id, category) -> None:
        """
        Remove last ticket from given event and by category if such ticket exist in cart.
        :param event_id: event of ticket to remove.
        :param category: category of ticket to remove.
        """
        try:
            ticket_ids = self.basket.keys()
            event = Event.objects.get(id=int(event_id))
            ticket = Ticket.objects.filter(id__in=ticket_ids, event=event, category=category).last()
            ticket.release()
        except:
            raise NonExistingTicketToRemove(event_id, category)
        del self.basket[str(ticket.id)]
        self.save()

    def get_total_price(self) -> float:
        """
        Get a cost of all tickets from the basket.
        :return: Amount in float format.
        """
        return sum([float(ticket['price']) for ticket in self.basket.values()])

    def _remove_expired_tickets(self) -> None:
        """
        Private method, launched every time when Basket object is created.
        Check is there is any expired ticket in basket and in case of True - remove them.
        """
        tickets = self._get_tickets_ob_by_tickets_id_in_basket()
        for ticket in tickets:
            if ticket.is_reservation_expired():
                self.remove(ticket.event.id, ticket.category)

    def _get_tickets_ob_by_tickets_id_in_basket(self):
        """
        Make query for Ticket objects according with ticket ids from basket.
        :return: Container with Tickets objects.
        """
        ticket_ids = self.basket.keys()
        return Ticket.objects.filter(id__in=ticket_ids)

    def __iter__(self):
        """
        Overload iteration operator. Return lines with information about number of ticket and total cost,
         grouped by event.
        :return: yield of 'events' dictionary.
        """
        tickets = self._get_tickets_ob_by_tickets_id_in_basket()
        events = {}
        for ticket in tickets:
            event_key = ticket.event
            if not events.get(ticket.event):
                events[event_key] = {c[1]: 0 for c in Ticket.CATEGORY}
                events[event_key]['total_price'] = 0

            events[event_key][ticket.category] += 1
            events[event_key]['total_price'] += ticket.price

            expired_time_label = f'{ticket.category}_expired_time'
            if not events[event_key].get(expired_time_label):
                events[event_key][expired_time_label] = ticket.reservation_time
            else:
                if events[event_key][expired_time_label] < ticket.reservation_time:
                    events[event_key][expired_time_label] = ticket.reservation_time

        for item in events.items():
            yield item

    def __len__(self):
        """
        Overload length operator. Return a total number of tickets in basket.
        :return: integer with number of total tickets in basket.
        """
        return len(self.basket)
