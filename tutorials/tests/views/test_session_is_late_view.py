from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import User, RequestSession, Subject, RequestSessionDay
from tutorials.forms import TutorMatchForm
from tutorials.views import is_request_late
from datetime import date

class IsRequestLateTestCase(TestCase):
    """Unit tests for the is_request_late view."""

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json'
    ]

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.admin = User.objects.filter(user_type='admin').first()
        self.tutor = User.objects.filter(user_type='tutor').first()
        self.student = User.objects.filter(user_type='student').first()
        self.subject = Subject.objects.first()
        
        # Create request with days and date
        self.request = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            proficiency='Beginner',
            frequency=1.0,
            date_requested=date(2024, 8, 29)
        )
        # Add request day
        RequestSessionDay.objects.create(
            request_session=self.request,
            day_of_week='Monday'
        )

    def test_get_true_when_late(self):
        """Test view returns True when request is late."""
        self.assertTrue(is_request_late(self.request.date_requested))

    def test_get_false_when_not_late(self):
        """Test view returns False when request is not late."""
        self.request.date_requested = date(2024, 8, 10)
        self.assertFalse(is_request_late(self.request.date_requested))
        