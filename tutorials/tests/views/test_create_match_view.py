from django.test import TestCase, Client
from django.contrib.messages import get_messages
from django.urls import reverse
from tutorials.models import User, RequestSession, Subject, Match, TutorSubject
from unittest.mock import patch

class CreateMatchViewTestCase(TestCase):
    """Unit tests for the create match view."""

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json',
        'tutorials/tests/fixtures/request_session.json'
    ]

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.admin = User.objects.filter(user_type='admin').first()
        self.tutor = User.objects.filter(user_type='tutor').first()
        self.student = User.objects.filter(user_type='student').first()
        self.subject = Subject.objects.first()
        self.request = RequestSession.objects.first()
        TutorSubject.objects.update_or_create(
            tutor=self.tutor,
            subject=self.request.subject,
            defaults={'proficiency': self.request.proficiency}
        )
        self.url = reverse('create_match', args=[self.request.id])
    
    def test_url(self):
        """Test URL."""
        expected_url = f'/match/{self.request.id}/'
        self.assertEqual(self.url, expected_url)

    def test_post_request_creates_match_and_redirects(self):
        """Test post request creates match and redirects."""
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {'tutor': self.tutor.id})
        # Update: redirect to admin_requested_sessions
        expected_url = reverse('admin_requested_sessions')
        self.assertRedirects(response, expected_url)

    def test_post_request_match_created(self):
        """Test post request match created."""
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {'tutor': self.tutor.id})
        # Update: redirect to admin_requested_sessions
        self.assertRedirects(response, reverse('admin_requested_sessions'))
        # Check match creation
        self.assertTrue(Match.objects.filter(
            request_session=self.request,
            tutor=self.tutor
        ).exists())
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Match created successfully')

    def test_post_request_match_not_created_for_student(self):
        """Test post request match not created for student."""
        self.client.force_login(self.student)
        response = self.client.post(self.url, {'tutor': self.tutor.id})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Match.objects.filter(
            request_session=self.request,
            tutor=self.tutor
        ).exists())

    def test_post_request_match_not_created_for_tutor(self):
        """Test post request match not created for tutor."""
        self.client.force_login(self.tutor)
        response = self.client.post(self.url, {'tutor': self.tutor.id})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Match.objects.filter(
            request_session=self.request,
            tutor=self.tutor
        ).exists())
    
    def test_post_request_invalid_form(self):
        """Test post request invalid form."""
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Match.objects.filter(
            request_session=self.request,
            tutor=self.tutor
        ).exists())
    
    def test_post_request_invalid_tutor(self):
        """Test post request invalid tutor."""
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {'tutor': 999})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Match.objects.filter(
            request_session=self.request,
            tutor=self.tutor
        ).exists())

    def test_match_creation_exception_handling(self):
        """Test exception handling during match creation."""
        self.client.force_login(self.admin)
        
        # Mock Match.objects.create to raise an exception
        with patch('tutorials.models.Match.objects.create') as mock_create:
            mock_create.side_effect = Exception('Database error')
            
            # Make the request
            response = self.client.post(self.url, {'tutor': self.tutor.id})
            
            # Check redirect
            self.assertRedirects(response, reverse('admin_requested_session_highlighted', args=[self.request.id]))
            
            # Check error message
            messages = list(get_messages(response.wsgi_request))
            self.assertEqual(str(messages[0]), 'Error creating match: Database error')
            
            # Verify no match was created
            self.assertFalse(Match.objects.exists())