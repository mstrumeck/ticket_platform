from django.shortcuts import render, get_object_or_404

from .models import Event
from .utils import EventAndTickets


def event_detail_view(request, event_id):
    """
    Main view for single event.
    """
    event_id = int(event_id)
    event = get_object_or_404(Event, id=event_id)
    context = {"event": event}
    context.update(event.get_available_tickets_num_by_categories())
    return render(request, "main/event/detail.html", context)


def event_list_view(request):
    """
    Main view for all events in database, sorted by time.
    """
    events = Event.objects.order_by('-time_and_date')
    events_with_tickets = [EventAndTickets(e, e.get_sum_of_available_tickets()) for e in events]
    return render(request, "main/event/list.html", {"events": events_with_tickets})
