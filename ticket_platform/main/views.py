from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .basket import Basket
from .forms import PaymentForm
from .models import Event, Ticket
from .utils import EventAndTickets, payment_error_message


def buy_tickets(request) -> render:
    """
    View with all reserved tickets and semi-payment gateway. In case of lack any reserved ticket, user will get
    suitable message.
    :return: render object with buy form and basket.
    """
    payment_error = None
    basket = Basket(request)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            amount = cd['amount']
            currency = cd['currency']
            name = cd['name']
            surname = cd['surname']
            if amount == basket.get_total_price():
                basket.buy(name, surname)
            else:
                payment_error = payment_error_message(currency, amount)
    else:
        form = PaymentForm()
    return render(request, "main/buy.html", {'basket': basket, 'form': form, 'payment_error': payment_error})


def release_ticket_from_basket(request, event_id, category) -> redirect:
    """
    Redirected view needed to release ticket data for others users.
    :param event_id: id of tickets event.
    :param category: user select from which category want release ticket.
    :return: redirect object with basket view (updated by released ticket)
    """
    basket = Basket(request)
    basket.remove(event_id, category)
    return redirect('basket_view')


def basket_view(request):
    """
    View with the data from the session basket.
    :return: render template with data from basket and rendered request.'.
    """
    basket = Basket(request)
    return render(request, "main/basket.html", {'basket': basket})


def reserve_ticket_for_event(request, event_id, category) -> redirect:
    """
    Function to launch 'reserve_ticket' method for last ticket in given category for given event.
    :param event_id: event for given ticket.
    :param category: category of ticket (from Normal, Premium and VIP).
    :return: redirect object to 'event_detail_view'.
    """
    basket = Basket(request)
    event_id = int(event_id)
    event = get_object_or_404(Event, id=event_id)
    last_ticket = Ticket.objects.filter(
        category=category,
        event=event
    ).exclude(
        reservation_time__gte=timezone.now()
    ).last()
    basket.add(last_ticket)
    return redirect('event_detail', event_id)


def event_detail_view(request, event_id) -> render:
    """
    Main view for single event.
    """
    event_id = int(event_id)
    event = get_object_or_404(Event, id=event_id)
    basket = Basket(request)
    return render(request, "main/event/detail.html", {
        "event": event,
        "tickets": event.get_available_tickets_num_by_categories(),
        "basket": basket
    })


def event_list_view(request) -> render:
    """
    Main view for all events in database, sorted by time.
    """
    basket = Basket(request)
    events = Event.objects.order_by('-time_and_date').exclude(time_and_date__lte=timezone.now())
    events_with_tickets = [EventAndTickets(e, e.get_sum_of_available_tickets()) for e in events]
    return render(request, "main/event/list.html", {"events": events_with_tickets, "basket": basket})
