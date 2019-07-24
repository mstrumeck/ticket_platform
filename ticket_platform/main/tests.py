import datetime
from unittest import mock

from django.http import HttpRequest
from django.test import TestCase
from django.utils import timezone

from .basket import Basket
from .exceptions import NonExistingTicketToRemove
from .line_chart_plotter import LineChartAbstract, OrderPlotter
from .models import Ticket, Event, Order
from .views import event_list_view, event_detail_view
from .utils import time_between, payment_error_message, turn_none_into_zero


class BaseSetUp(TestCase):

    def setUp(self):
        self.test_datetime = timezone.now()
        self.test_event = Event.objects.create(name="Test Event", time_and_date=self.test_datetime)


class PlotterTestSetup(TestCase):

    def setUp(self):
        self.test_order_one = Order.objects.create(name="test1", surname="test1")
        self.mocked = timezone.now() + timezone.timedelta(days=3)
        with mock.patch('django.utils.timezone.now', mock.Mock(return_value=self.mocked)):
            self.test_order_two = Order.objects.create(name="test2", surname="test2")


class EventObjectTest(BaseSetUp):

    def test_event_creation(self):
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(self.test_event.name, "Test Event")
        datetime_now = datetime.datetime.now()
        self.assertEqual(self.test_datetime.date(), datetime_now.date())
        self.assertEqual(self.test_datetime.hour, datetime_now.hour)
        self.assertEqual(self.test_datetime.minute, datetime_now.minute)
        self.assertEqual(self.test_datetime.second, datetime_now.second)

    def test_get_url(self):
        self.assertEqual(self.test_event.get_url(), 1)

    def test_get_time(self):
        event_time = self.test_event.time_and_date
        self.assertEqual(self.test_event.get_time(), f"{event_time.hour}:{event_time.minute}")

    def test_get_sum_of_available_tickets_with_no_tickets(self):
        self.assertEqual(self.test_event.get_sum_of_available_tickets(), 0)

    def test_get_sum_of_available_tickets_with_tickets(self):
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[0][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[1][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[2][1])
        self.assertEqual(self.test_event.get_sum_of_available_tickets(), 3)

    def test_get_available_tickets_num_by_categories_with_no_tickets(self):
        self.assertEqual(
            list(self.test_event.get_available_tickets_num_by_categories()),
            [("Normal", 0), ("Premium", 0), ("VIP", 0)]
        )

    def test_get_available_tickets_num_by_categories_with_tickets(self):
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[0][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[1][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[2][1])
        self.assertEqual(
            list(self.test_event.get_available_tickets_num_by_categories()),
            [("Normal", 1), ("Premium", 1), ("VIP", 1)]
        )

    def test_get_available_tickets_num_by_categories_if_one_is_reserved(self):
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[0][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[1][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[2][1])
        Ticket.objects.last().reserve()

        self.assertEqual(
            list(self.test_event.get_available_tickets_num_by_categories()),
            [("Normal", 1), ("Premium", 1), ("VIP", 0)]
        )


class ListOfEventViewTest(TestCase):
    def setUp(self):
        self.test_datetime = timezone.now()
        session = self.client.get("/")
        self.request = HttpRequest()
        self.request.session = session

    def test_main_view_without_data(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_of_content_for_view_without_data(self):
        response = event_list_view(self.request)
        self.assertTrue("No events available. Stay tuned!" in response.content.decode())

    def test_of_content_for_view_with_data(self):
        Event.objects.create(name="Test Event", time_and_date=self.test_datetime + timezone.timedelta(minutes=1))
        response = event_list_view(self.request)
        decoded_response = response.content.decode()
        self.assertTrue("Event name: Test Event." in decoded_response)
        self.assertTrue("SOLD OUT!" in decoded_response)

    def test_main_view_with_data(self):
        Event.objects.create(name="Test Event", time_and_date=timezone.now())
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_main_view_with_two_events_including_one_from_past(self):
        Event.objects.create(name="Test Event Future", time_and_date=timezone.now() + timezone.timedelta(days=1))
        Event.objects.create(name="Test Event Past", time_and_date=timezone.now() - timezone.timedelta(days=1))
        response = event_list_view(self.request)
        decoded_response = response.content.decode()
        self.assertTrue("Event name: Test Event Future." in decoded_response)
        self.assertFalse("Event name: Test Event Past." in decoded_response)


class EventDetailViewTest(BaseSetUp):
    def setUp(self):
        super().setUp()
        session = self.client.get(f"{self.test_event.id}")
        self.request = HttpRequest()
        self.request.session = session

    def test_detail_event_view_positive_scenario(self):
        response = self.client.get("/1")
        self.assertEqual(response.status_code, 200)

    def test_detail_view_content_without_ticket_positive_scenario(self):
        response = event_detail_view(self.request, self.test_event.id)
        decoded_response = response.content.decode()
        self.assertTrue("Detail for Test Event." in decoded_response)

    def test_detail_view_content_with_tickets_positive_scenario(self):
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[0][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[1][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[2][1])
        response = event_detail_view(self.request, self.test_event.id)
        decoded_response = response.content.decode()
        self.assertTrue("Detail for Test Event." in decoded_response)
        self.assertTrue("Available tickets:" in decoded_response)
        self.assertTrue("Normal: 1" in decoded_response)
        self.assertTrue("Premium: 1" in decoded_response)
        self.assertTrue("VIP: 1" in decoded_response)
        self.assertEqual(decoded_response.count("Reserve"), 3)

    def test_detail_view_content_with_tickets_if_one_types_of_tickets_non_exist(self):
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[0][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[1][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[2][1], is_sold=True)
        response = event_detail_view(self.request, self.test_event.id)
        decoded_response = response.content.decode()
        self.assertEqual(decoded_response.count("Reserve"), 2)
        self.assertTrue("Normal: 1" in decoded_response)
        self.assertTrue("Premium: 1" in decoded_response)
        self.assertFalse("VIP: 0" in decoded_response)

    def test_detail_view_content_with_tickets_if_one_types_of_tickets_sold_out(self):
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[0][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[1][1])
        response = event_detail_view(self.request, self.test_event.id)
        decoded_response = response.content.decode()
        self.assertEqual(decoded_response.count("Reserve"), 2)
        self.assertTrue("Normal: 1" in decoded_response)
        self.assertTrue("Premium: 1" in decoded_response)
        self.assertFalse("VIP: 0" in decoded_response)

    def test_detail_view_content_with_tickets_if_one_types_of_tickets_was_reserved(self):
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[0][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[1][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[2][1])
        Ticket.objects.last().reserve()
        response = event_detail_view(self.request, self.test_event.id)
        decoded_response = response.content.decode()
        self.assertEqual(decoded_response.count("Reserve"), 2)
        self.assertTrue("Normal: 1" in decoded_response)
        self.assertTrue("Premium: 1" in decoded_response)
        self.assertFalse("VIP" in decoded_response)

    def test_detail_event_view_negative_scenario(self):
        self.test_event.delete()
        response = self.client.get("/1")
        self.assertEqual(response.status_code, 404)


class TicketObjectsTest(BaseSetUp):
    def setUp(self):
        super().setUp()
        self.test_ticket = Ticket.objects.create(event=self.test_event)

    def test_ticket_creation(self):
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertFalse(self.test_ticket.is_sold)
        self.assertEqual(self.test_ticket.category, "Normal")

    def test_is_remove_ticket_not_remove_event(self):
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(Event.objects.count(), 1)
        self.test_ticket.delete()
        self.assertEqual(Ticket.objects.count(), 0)
        self.assertEqual(Event.objects.count(), 1)

    def test_ticket_reserve(self):
        ticket_reservation_time_before = self.test_ticket.reservation_time
        self.test_ticket.reserve()
        ticket_reservation_time_after = self.test_ticket.reservation_time
        # self.assertEqual(60 - (ticket_reservation_time_before.minute - ticket_reservation_time_after.minute), 15)

    def test_ticket_release(self):
        self.test_ticket.reserve()
        self.assertNotEqual(timezone.now().minute, self.test_ticket.reservation_time.minute)
        self.test_ticket.release()
        self.assertEqual(timezone.now().minute, self.test_ticket.reservation_time.minute)

    def test_is_reservation_expired_positive(self):
        self.assertTrue(self.test_ticket.is_reservation_expired())

    def test_is_reservation_expired_negative(self):
        self.test_ticket.reservation_time += timezone.timedelta(minutes=5)
        self.assertFalse(self.test_ticket.is_reservation_expired())

    def test_buy_ticket(self):
        test_order = Order.objects.create(name="test_name", surname="test_surname")
        self.test_ticket.buy(test_order)
        self.assertTrue(self.test_ticket.is_sold)
        self.assertEqual(self.test_ticket.order, test_order)
        datetime_now = datetime.datetime.now()
        self.assertEqual(self.test_datetime.date(), datetime_now.date())
        self.assertEqual(self.test_datetime.hour, datetime_now.hour)
        self.assertEqual(self.test_datetime.minute, datetime_now.minute)
        self.assertEqual(self.test_datetime.second, datetime_now.second)


class TestOrderObject(BaseSetUp):
    def test_order_creation(self):
        test_order = Order.objects.create(name="test_name", surname="test_surname")
        self.assertEqual(test_order.name, "test_name")
        self.assertEqual(test_order.surname, "test_surname")
        datetime_now = datetime.datetime.now()
        self.assertEqual(test_order.time_and_date.date(), datetime_now.date())
        self.assertEqual(test_order.time_and_date.hour, datetime_now.hour)
        self.assertEqual(test_order.time_and_date.minute, datetime_now.minute)
        self.assertEqual(test_order.time_and_date.second, datetime_now.second)


class TestBasketObject(BaseSetUp):
    def setUp(self):
        super().setUp()
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[0][1], price=10)
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[1][1], price=20)
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[2][1], price=30)
        session = self.client.get('/')
        request = HttpRequest()
        request.session = session
        self.test_basket = Basket(request)

    def test_buy_with_empty_basket(self):
        self.test_basket.buy("test_name", "test_surname")
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Ticket.objects.filter(is_sold=True).count(), 0)
        self.assertEqual(Ticket.objects.filter(order=None).count(), 3)
        self.assertEqual(Ticket.objects.filter(reservation_time__minute=timezone.now().minute).count(), 3)

    def test_buy_with_non_empty_basket(self):
        for t in Ticket.objects.all():
            self.test_basket.add(t)

        self.test_basket.buy("test_name", "test_surname")
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Ticket.objects.filter(is_sold=True).count(), 3)
        self.assertEqual(Ticket.objects.filter(order=None).count(), 0)
        self.assertEqual(Ticket.objects.filter(reservation_time__minute=timezone.now().minute).count(), 3)

    def test_add_ticket_to_basket(self):
        self.assertEqual(self.test_basket.basket, {})
        self.test_basket.add(Ticket.objects.last())
        self.assertEqual(self.test_basket.basket, {'3': {'price': '30.00', 'category': 'VIP'}})

    def test_remove_non_existing_ticket_from_basket(self):
        self.assertEqual(self.test_basket.basket, {})
        self.assertRaises(NonExistingTicketToRemove, self.test_basket.remove, event_id=self.test_event.id, category='Normal')

    def test_remove_existing_ticket_from_basket(self):
        self.test_basket.add(Ticket.objects.last())
        self.assertEqual(self.test_basket.basket, {'3': {'price': '30.00', 'category': 'VIP'}})
        self.test_basket.remove(self.test_event.id, "VIP")
        self.assertEqual(self.test_basket.basket, {})

    def test_get_total_price(self):
        self.assertEqual(self.test_basket.get_total_price(), 0)
        for t in Ticket.objects.all():
            self.test_basket.add(t)
        self.assertEqual(self.test_basket.get_total_price(), 60)

    def test_remove_expired_tickets_with_ticket_to_remove(self):
        for t in Ticket.objects.all():
            self.test_basket.add(t)

        self.assertNotEqual(self.test_basket.basket, {})

        for t in Ticket.objects.all():
            t.reservation_time = timezone.now()
            t.save()

        self.test_basket._remove_expired_tickets()
        self.assertEqual(self.test_basket.basket, {})

    def test_get_tickets_ob_by_tickets_id_in_basket(self):
        self.assertEqual(len(self.test_basket._get_tickets_ob_by_tickets_id_in_basket()), 0)
        for t in Ticket.objects.all():
            self.test_basket.add(t)
        self.assertEqual(len(self.test_basket._get_tickets_ob_by_tickets_id_in_basket()), 3)

    def test_overload_iter_empty_scenario(self):
        self.assertEqual(list(self.test_basket), [])

    def test_overload_iter_non_empty_scenario(self):
        for t in Ticket.objects.all():
            self.test_basket.add(t)

        for item in self.test_basket:
            self.assertEqual(item[1]['Normal'], 1)
            self.assertEqual(item[1]['Premium'], 1)
            self.assertEqual(item[1]['VIP'], 1)
            self.assertEqual(item[1]['total_price'], 60)

    def test_overload_len(self):
        self.assertEqual(len(self.test_basket), 0)

        for t in Ticket.objects.all():
            self.test_basket.add(t)

        self.assertEqual(len(self.test_basket), 3)


class LineCharPlotterTest(PlotterTestSetup):

    def setUp(self):
        super().setUp()
        self.line_plotter = LineChartAbstract(Order)

    def test_get_first_date_of_occurence(self):
        self.assertEqual(self.line_plotter.get_first_date_of_occurence().date(), timezone.now().date())

    def test_get_last_date_of_occurence(self):
        test_value = self.mocked + timezone.timedelta(days=1)
        self.assertEqual(self.line_plotter.get_last_date_of_occurence().date(), test_value.date())

    def test_get_number_of_objects_per_day(self):
        self.assertEqual(len(self.line_plotter.get_number_of_objects_per_day()), 5)
        self.assertEqual(sum(self.line_plotter.get_number_of_objects_per_day()), 2)

    def test_get_days_range(self):
        self.assertEqual(len(self.line_plotter.get_days_range()), 5)
        for day in self.line_plotter.get_days_range():
            self.assertEqual(type(day), int)


class OrderPlotterTest(PlotterTestSetup):

    def setUp(self):
        super().setUp()
        self.order_plotter = OrderPlotter()
        self.test_event = Event.objects.create(name="Test Event", time_and_date=timezone.now())
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[0][1], price=10)
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[1][1], price=20,  order=self.test_order_one, is_sold=True)
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[2][1], price=30,  order=self.test_order_two)

    def test_get_number_of_sold_tickets_by_category(self):
        self.assertEqual(self.order_plotter.get_number_of_sold_tickets_by_category('Normal'), [0, 0, 0, 0, 0])
        self.assertEqual(self.order_plotter.get_number_of_sold_tickets_by_category('VIP'), [0, 0, 0, 1, 0])

    def test_get_sold_tickets_per_day(self):
        self.assertEqual(self.order_plotter.get_sold_tickets_per_day(), [1, 0, 0, 1, 0])

    def test_get_amount_of_cash_from_tickets_per_day_total(self):
        self.assertEqual(self.order_plotter.get_amount_of_cash_from_tickets_per_day_total(), [20, 0, 0, 30, 0])

    def test_get_amount_of_cash_from_ticket_per_day_for_category(self):
        self.assertEqual(self.order_plotter.get_amount_of_cash_from_ticket_per_day_for_category('Premium'), [20, 0, 0, 0, 0])


class TestUtils(PlotterTestSetup):

    def setUp(self):
        super().setUp()
        self.line_plotter = LineChartAbstract(Order)

    def test_time_between(self):
        result = list(time_between(self.line_plotter.get_first_date_of_occurence(), self.line_plotter.get_last_date_of_occurence()))
        self.assertEqual(len(result), 5)

    def test_payment_error_message(self):
        self.assertEqual(payment_error_message(30, "USD"), "USD 30 is not valid amount. Please, provide a proper amount in 30.")

    def test_turn_none_into_zero(self):
        self.assertEqual(turn_none_into_zero(None), 0)
