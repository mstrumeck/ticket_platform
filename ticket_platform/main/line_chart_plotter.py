from abc import ABC

from django.db.models import Sum, Min, Max
from django.utils import timezone
from plotly import graph_objects, offline

from .models import Order, Ticket
from .utils import turn_none_into_zero, time_between


class LineChartAbstract(ABC):
    """Base abstract class for all plotter classes."""
    def __init__(self, object_to_plot):
        self.object_to_plot = object_to_plot

    def get_first_date_of_occurence(self):
        """
        Get all objects within database and try find the yearliest date among them.
        :return: datetime.date
        """
        return self.object_to_plot.objects.order_by(
            'time_and_date'
        ).aggregate(
            Min(
                'time_and_date'
            ))['time_and_date__min']

    def get_last_date_of_occurence(self):
        """
        Get all objects within database and try find the latest date among them.
        :return: datetime.date
        """
        return self.object_to_plot.objects.order_by(
            'time_and_date'
        ).aggregate(
            Max(
                'time_and_date'
            ))['time_and_date__max'] + timezone.timedelta(days=1)

    def get_number_of_objects_per_day(self):
        """
        Query to find every occurency of object and group them per days range, from the first object to last.
        :return: list with numbers of objects per day.
        """
        return [
            self.object_to_plot.objects.filter(
                time_and_date__date=time.date()
            ).count() for time in time_between(
                self.get_first_date_of_occurence(), self.get_last_date_of_occurence()
            )
        ]

    def get_days_range(self):
        """
        List with dates between first and the last date of object existing. Default value for x axis in all charts.
        :return: list of dates in datetime.date() format.
        """
        return [
            d.date() for d in time_between(
                self.get_first_date_of_occurence(), self.get_last_date_of_occurence()
            )
        ]

    def add_trace_to_fig(self, fig, y, name):
        """
        Add additional line to existing figure
        :param fig: Figure to plot
        :param y: y_axis with data to present
        :param name: title of the generated plot
        :return:
        """
        fig.add_trace(graph_objects.Scatter(x=self.get_days_range(), y=y, name=name))
        return fig


class OrderPlotter(LineChartAbstract):
    """
    Dedicated plotter of 'Order' object, based on LineChartAbstract.
    """
    def __init__(self):
        self.object_to_plot = Order

    def get_number_of_sold_tickets_by_category(self, category) -> list:
        """
        Get list with all sold ticket by category per day.
        :param category: ticket category (normal, premium, vip)
        :return: list with number of ticket by category per day.
        """
        return [
            self.object_to_plot.objects.filter(
                time_and_date__date=time.date(), ticket__category=category
            ).count() for time in time_between(
                self.get_first_date_of_occurence(), self.get_last_date_of_occurence()
            )
        ]

    def get_chart_with_number_of_orders_per_day(self) -> offline.plot:
        """
        Create chart with statistic about orders per each day, from the first order to last one.
        :return: chart save as plot object.
        """
        fig = graph_objects.Figure()
        self.add_trace_to_fig(fig, self.get_number_of_objects_per_day(), "Number of Orders per day.")
        self.add_trace_to_fig(fig, self.get_sold_tickets_per_day(), "Sold tickets per day.")
        for category in Ticket.CATEGORY:
            self.add_trace_to_fig(
                fig,
                self.get_number_of_sold_tickets_by_category(category[1]),
                f"Solved ticket for {category[1]} category."
            )
        return offline.plot(fig, output_type="div")

    def get_sold_tickets_per_day(self) -> list:
        """
        Return a list of tickets per day with 'sold' status. Each ticket is marked as sold during creation of
        order object.
        :return: list with number of solved tickets per day.
        """
        return [
            self.object_to_plot.objects.filter(
                time_and_date__date=time.date()
            ).values('ticket').count() for time in time_between(
                self.get_first_date_of_occurence(), self.get_last_date_of_occurence()
            )
        ]

    def get_amount_of_cash_from_tickets_per_day_total(self) -> list:
        """
        Return a total profits from all tickets grouped by each day.
        :return: list with amounts of profits in days range.
        """
        data = [
            self.object_to_plot.objects.filter(
                time_and_date__date=time.date()
            ).values('ticket__price'
                     ).aggregate(Sum('ticket__price'))['ticket__price__sum'] for time in time_between(
                self.get_first_date_of_occurence(), self.get_last_date_of_occurence()
            )
        ]
        data = list(map(turn_none_into_zero, data))
        return data

    def get_amount_of_cash_from_ticket_per_day_for_category(self, category) -> list:
        """
        Show amount of cash per day group by each day and category
        :param category: category of ticket to query
        :return: list of amount of cash per day
        """
        data = [self.object_to_plot.objects.filter(
            time_and_date__date=time.date(),
            ticket__category=category
        ).values('ticket__price'
                 ).aggregate(Sum('ticket__price', default=0))['ticket__price__sum'] for time in time_between(
            self.get_first_date_of_occurence(), self.get_last_date_of_occurence()
        )
                ]
        data = list(map(turn_none_into_zero, data))
        return data

    def get_chart_with_profits_per_day(self) -> offline.plot:
        """
        Gather and calculate a all income from day, in total and per category as well.
        """
        fig = graph_objects.Figure()
        self.add_trace_to_fig(
            fig,
            self.get_amount_of_cash_from_tickets_per_day_total(),
            "Amount of cash from tickets per day."
        )
        for category in Ticket.CATEGORY:
            self.add_trace_to_fig(
                fig,
                self.get_amount_of_cash_from_ticket_per_day_for_category(category[1]),
                f"Solved ticket for {category[1]} category."
            )
        return offline.plot(fig, output_type="div")
