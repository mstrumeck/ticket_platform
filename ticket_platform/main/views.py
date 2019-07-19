from django.views.generic import ListView, DetailView

from .models import Event


class EventDetail(DetailView):
    """
    Main class view for single event.
    """
    model = Event
    template_name = "main/event/detail.html"


class EventsListView(ListView):
    """
    Main class view for all events in database, sorted by time.
    """
    queryset = Event.objects.order_by('-time_and_date')
    context_object_name = 'events'
    template_name = "main/event/list.html"
