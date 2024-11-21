from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import User, RequestSession, Subject, Match
from tutorials.forms import TutorMatchForm

class AdminRequestedSessionHighlightedViewTestCase(TestCase):

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json'
    ]

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create admin
        self.admin = User.objects.filter(user_type='admin').first()

        # create tutor
        self.tutor = User.objects.filter(user_type='tutor').first()
        
        # Create student
        self.student = User.objects.filter(user_type='student').first()
        
        # Create subject and request
        self.subject = Subject.objects.first()
        self.request = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            proficiency='Beginner'
        )

        self.url = reverse('admin_requested_session_highlighted', args=[self.request.pk])

    def test_url(self):
        """Test URL."""
        expected_url = f'/requests/{self.request.id}/'
        self.assertEqual(self.url, expected_url)

    def test_get_request_redirects_when_not_logged_in(self):
        """Test view redirects when user not logged in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        expected_redirect = f'/log_in/?next=/requests/{self.request.id}/'
        self.assertRedirects(response, expected_redirect)

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
        self.assertTemplateUsed(response, 'admin_requested_session_highlighted.html')

    def test_context_data(self):
        """Test context data."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.context['request'], self.request)

    def test_form_in_context(self):
        """Test form in context."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertIn('form', response.context)
    
    def test_selected_tutor_in_context(self):
        """Test selected tutor in context."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertIn('selected_tutor', response.context)
    
    def test_selected_tutor(self):
        """Test selected tutor."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertIsNone(response.context['selected_tutor'])