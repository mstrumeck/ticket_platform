from django.test import TestCase
from .views import Event
import datetime


class EventObjectTest(TestCase):

    def setUp(self):
        self.test_event = Event.objects.create(name="Test Event")

    def test_event_creation(self):
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(self.test_event.name, "Test Event")
        test_event_time = self.test_event.time_and_date
        datetime_now = datetime.datetime.now()
        self.assertEqual(test_event_time.date(), datetime_now.date())
        self.assertEqual(test_event_time.hour, datetime_now.hour)
        self.assertEqual(test_event_time.minute, datetime_now.minute)
        self.assertEqual(test_event_time.second, datetime_now.second)

    def test_get_url(self):
        self.assertEqual(self.test_event.get_url(), 1)

    def test_get_time(self):
        event_time = self.test_event.time_and_date
        self.assertEqual(self.test_event.get_time(), f"{event_time.hour}:{event_time.minute}")


class EventViewTest(TestCase):
    def test_main_view(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_detail_event_view_positive_scenario(self):
        Event.objects.create(name="Test Event")
        response = self.client.get("/1")
        self.assertEqual(response.status_code, 200)

    def test_detail_event_view_negative_scenario(self):
        response = self.client.get("/1")
        self.assertEqual(response.status_code, 404)
