from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import User, RequestSession, Subject, Match, RequestSessionDay
from tutorials.forms import TutorMatchForm
from datetime import date

class AdminRequestedSessionsViewTestCase(TestCase):
    """Unit tests for the admin requested sessions view."""

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json'
    ]

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('admin_requested_sessions')
        
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
            date_requested=date.today()
        )
        # Add request day
        RequestSessionDay.objects.create(
            request_session=self.request,
            day_of_week='Monday'
        )

    def test_url(self):
        """Test URL."""
        self.assertEqual(self.url, '/requests/')

    def test_get_request_redirects_when_not_logged_in(self):
        """Test view redirects when user not logged in."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/log_in/?next={self.url}')

    def test_get_request_redirects_when_not_admin(self):
        """Test view redirects when user is not admin."""
        self.client.force_login(self.student)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('dashboard'))

    def test_get_request_success_when_admin(self):
        """Test view succeeds for admin user."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_requested_sessions.html')

    def test_shows_only_unmatched_requests(self):
        """Test view only shows unmatched requests."""
        another_student = User.objects.filter(
            user_type='student'
        ).exclude(pk=self.student.pk).first()
        
        matched_request = RequestSession.objects.create(
            student=another_student,
            subject=self.subject,
            proficiency='Intermediate',
            frequency=1.0,
            date_requested=date.today()
        )
        Match.objects.create(
            request_session=matched_request,
            tutor=self.tutor
        )
        
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        
        requests_with_forms = response.context['requests_with_forms']
        self.assertEqual(len(requests_with_forms), 1)
        self.assertEqual(requests_with_forms[0]['request'], self.request)

    def test_creates_form_for_each_request(self):
        """Test view creates a form for each unmatched request."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        
        requests_with_forms = response.context['requests_with_forms']
        self.assertTrue(isinstance(requests_with_forms[0]['form'], TutorMatchForm))

    def test_context_contains_admin_flag(self):
        """Test context contains admin view flag."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertTrue(response.context['is_admin_view'])