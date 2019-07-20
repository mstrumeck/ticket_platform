import datetime

from django.test import TestCase
from django.utils import timezone

from .models import Ticket, Event
from .views import event_list_view, event_detail_view
from django.http import HttpRequest


class BaseSetUp(TestCase):

    def setUp(self):
        self.test_datetime = timezone.now()
        self.test_event = Event.objects.create(name="Test Event", time_and_date=self.test_datetime)


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
            self.test_event.get_available_tickets_num_by_categories(),
            {"Normal": 0, "Premium": 0, "VIP": 0}
        )

    def test_get_available_tickets_num_by_categories_with_tickets(self):
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[0][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[1][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[2][1])
        self.assertEqual(
            self.test_event.get_available_tickets_num_by_categories(),
            {"Normal": 1, "Premium": 1, "VIP": 1}
        )


class ListOfEventViewTest(TestCase):
    def setUp(self):
        self.test_datetime = timezone.now()

    def test_main_view_without_data(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_of_content_for_view_without_data(self):
        response = event_list_view(HttpRequest())
        self.assertTrue("No events available. Stay tuned!" in response.content.decode())

    def test_of_content_for_view_with_data(self):
        Event.objects.create(name="Test Event", time_and_date=self.test_datetime)
        response = event_list_view(HttpRequest())
        decoded_response = response.content.decode()
        self.assertTrue("Event name: Test Event" in decoded_response)
        self.assertTrue("SOLD OUT!" in decoded_response)

    def test_main_view_with_data(self):
        Event.objects.create(name="Test Event", time_and_date=timezone.now())
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class EventDetailViewTest(BaseSetUp):

    def test_detail_event_view_positive_scenario(self):
        response = self.client.get("/1")
        self.assertEqual(response.status_code, 200)

    def test_detail_view_content_without_ticket_positive_scenario(self):
        response = event_detail_view(HttpRequest(), self.test_event.id)
        decoded_response = response.content.decode()
        self.assertTrue("Name of event: Test Event" in decoded_response)
        self.assertTrue("All ticket was sold out!" in decoded_response)

    def test_detail_view_content_with_tickets_positive_scenario(self):
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[0][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[1][1])
        Ticket.objects.create(event=self.test_event, category=Ticket.CATEGORY[2][1])
        response = event_detail_view(HttpRequest(), self.test_event.id)
        decoded_response = response.content.decode()
        self.assertTrue("Name of event: Test Event" in decoded_response)
        self.assertTrue("Available tickets:" in decoded_response)
        self.assertTrue("Normal: 1" in decoded_response)
        self.assertTrue("Premium: 1" in decoded_response)
        self.assertTrue("VIP: 1" in decoded_response)
        self.assertTrue(decoded_response)

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

    def test_is_remove_ticet_not_remove_event(self):
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(Event.objects.count(), 1)
        self.test_ticket.delete()
        self.assertEqual(Ticket.objects.count(), 0)
        self.assertEqual(Event.objects.count(), 1)
