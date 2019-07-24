from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.html import mark_safe

from .basket import Basket
from .forms import PaymentForm
from .line_chart_plotter import OrderPlotter
from .models import Event, Ticket
from .utils import EventAndTickets, payment_error_message, EventSummary
from .models import Order


def stats(request):
    """
    Generate a several stats about tickets, event and incomes.
    """
    total_num_of_events = Event.objects.all().count()
    total_num_of_tickets = Ticket.objects.all().count()
    total_reservations = Event.objects.all().aggregate(Sum('reservations'))['reservations__sum']
    total_sold_tickets = Ticket.objects.filter(is_sold=True).count()
    total_profit = Ticket.objects.filter(is_sold=True).aggregate(Sum('price'))['price__sum']
    total_possible_profit = Ticket.objects.all().aggregate(Sum('price'))['price__sum']

    if not total_num_of_events:
        context = {'total_num_of_events': total_num_of_events}
    else:
        events_summary = (EventSummary(
            event=e,
            total_tickets=e.ticket_set.all().count(),
            reservations=e.reservations,
            sold_tickets=e.ticket_set.filter(is_sold=True).count(),
            profit=e.ticket_set.filter(is_sold=True).aggregate(Sum('price'))['price__sum'],
            possible_profit=e.ticket_set.all().aggregate(Sum('price'))['price__sum'])
            for e in Event.objects.all())

        context = {
            'total_num_of_events': total_num_of_events,
            'total_num_of_tickets': total_num_of_tickets,
            'total_reservation': total_reservations,
            'total_sold_tickets': total_sold_tickets,
            'total_profit': total_profit,
            'total_possible_profit': total_possible_profit,
            'events_summary': events_summary,
        }

    if Order.objects.count():
        op = OrderPlotter()
        orders_per_day = op.get_chart_with_number_of_orders_per_day()
        profits_per_day = op.get_chart_with_profits_per_day()
        context['orders_per_day'] = mark_safe(orders_per_day)
        context['profits_per_day'] = mark_safe(profits_per_day)

    return render(request, 'main/stats.html', context)


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
    return render(request, "main/basket/buy.html", {'form': form, 'payment_error': payment_error})


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
    return render(request, "main/basket/list.html")


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
