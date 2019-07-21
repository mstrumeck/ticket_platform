from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .models import Event, Ticket
from .utils import EventAndTickets


def reserve_ticket_for_event(request, event_id, category) -> redirect:
    """
    Function to launch 'reserve_ticet' method for last ticket in given category for given event.
    :param event_id: event for given ticket.
    :param category: category of ticket (from Normal, Premium and VIP).
    :return: redirect object to 'event_detail_view'.
    """
    event_id = int(event_id)
    event = get_object_or_404(Event, id=event_id)
    last_ticket = Ticket.objects.filter(
        category=category,
        event=event
    ).exclude(
        reservation_time__gte=timezone.now()
    ).last()
    last_ticket.reserve_ticket()

    return redirect('event_detail', event_id)


def event_detail_view(request, event_id) -> render:
    """
    Main view for single event.
    """
    event_id = int(event_id)
    event = get_object_or_404(Event, id=event_id)

    return render(request, "main/event/detail.html", {
        "event": event,
        "tickets": event.get_available_tickets_num_by_categories(),
    })


def event_list_view(request) -> render:
    """
    Main view for all events in database, sorted by time.
    """
    events = Event.objects.order_by('-time_and_date').exclude(time_and_date__lte=timezone.now())
    events_with_tickets = [EventAndTickets(e, e.get_sum_of_available_tickets()) for e in events]
    return render(request, "main/event/list.html", {"events": events_with_tickets})
