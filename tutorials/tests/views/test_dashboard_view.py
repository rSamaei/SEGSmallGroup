from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import User, RequestSession, Subject
from datetime import date

class DashboardViewTestCase(TestCase):
    """Unit tests for the dashboard view."""

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json'
    ]

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('dashboard')
        self.student = User.objects.filter(user_type='student').first()
        self.admin = User.objects.filter(user_type='admin').first()
        self.subject = Subject.objects.first()
        self.request = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            proficiency='Beginner',
            frequency='1.0',
            date_requested=date.today()
        )

    def test_dashboard_url(self):
        """Test dashboard URL."""
        self.assertEqual(self.url, '/dashboard/')

    def test_get_dashboard_not_logged_in(self):
        """Test dashboard redirects when not logged in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/log_in/?next=/dashboard/')

    def test_get_dashboard_as_admin(self):
        """Test dashboard shows admin view."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertTrue(response.context['is_admin_view'])
        self.assertEqual(response.context['unmatched_count'], 1)

    def test_get_dashboard_as_regular_user(self):
        """Test dashboard shows regular view."""
        self.client.force_login(self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertNotIn('is_admin_view', response.context)
        self.assertNotIn('unmatched_count', response.context)