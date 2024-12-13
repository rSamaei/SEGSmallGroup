from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from tutorials.models import Match, RequestSession, Frequency, Subject
from unittest.mock import patch

class ViewMatchedRequestsTests(TestCase):
    def setUp(self):
        # Get the custom User model
        User = get_user_model()

        # Create users
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='password123',
            first_name='Admin',
            last_name='User',
            email='adminuser@example.com',
            user_type='admin'  # Set user_type to admin
        )
        
        self.tutor_user = User.objects.create_user(
            username='tutoruser',
            password='password123',
            first_name='Tutor',
            last_name='User',
            email='tutoruser@example.com',
            user_type='tutor'
        )
        
        self.student_user = User.objects.create_user(
            username='studentuser',
            password='password123',
            first_name='Student',
            last_name='User',
            email='studentuser@example.com',
            user_type='student'
        )

        # Create Subjects
        self.math_subject = Subject.objects.create(name="Math")

        # Create RequestSession and Matched Requests
        self.request_session = RequestSession.objects.create(
            student=self.student_user,
            subject=self.math_subject,
            proficiency="Intermediate",
            date_requested="2024-01-01",
            frequency=1.0
        )

        self.match = Match.objects.create(
            tutor=self.tutor_user,
            request_session=self.request_session,
            tutor_approved=True
        )

        # Set URLs for the view
        self.url = reverse('view_matched_requests')

    def test_admin_can_view_all_matched_requests(self):
        """Test that the admin can view all matched requests."""
        self.client.login(username='adminuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matched Requests')
        self.assertContains(response, 'Tutor')
        self.assertContains(response, 'Student')
        self.assertContains(response, self.tutor_user.username)
        self.assertContains(response, self.student_user.username)
        self.assertContains(response, 'Math')

    def test_tutor_can_view_only_their_matched_requests(self):
        """Test that a tutor can view only their matched requests."""
        self.client.login(username='tutoruser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matched Requests')
        self.assertContains(response, self.student_user.username)
        self.assertContains(response, 'Math')
        self.assertContains(response, 'Tutor')
        self.assertNotContains(response, 'No matched requests found.')

    def test_student_can_view_only_their_matched_requests(self):
        """Test that a student can view only their matched requests."""
        self.client.login(username='studentuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matched Requests')
        self.assertContains(response, self.tutor_user.username)
        self.assertContains(response, 'Math')
        self.assertNotContains(response, 'No matched requests found.')

    def test_search_functionality(self):
        """Test that the search functionality works correctly."""
        # Test as admin
        self.client.login(username='adminuser', password='password123')
        response = self.client.get(self.url, {'search': 'tutoruser'})
        self.assertContains(response, self.tutor_user.username)
        self.assertNotContains(response, 'No matched requests found.')
        
        # Test as tutor
        self.client.login(username='tutoruser', password='password123')
        response = self.client.get(self.url, {'search': 'studentuser'})
        self.assertContains(response, self.student_user.username)
        self.assertNotContains(response, 'No matched requests found.')

    def test_no_matched_requests_found(self):
        """Test that the 'No matched requests found' message appears when there are no requests."""
        # Delete the match and test
        self.match.delete()
        self.client.login(username='adminuser', password='password123')
        response = self.client.get(self.url)
        self.assertContains(response, 'No matched requests found')

    def test_admin_can_delete_matched_request(self):
        """Test that the admin can delete a matched request."""
        self.client.login(username='adminuser', password='password123')
        response = self.client.post(reverse('delete_matched_request', kwargs={'match_id': self.match.id}), follow=True)
        self.assertRedirects(response, self.url)
        self.assertContains(response, 'Matched request deleted successfully.')
        # Verify match is deleted
        with self.assertRaises(Match.DoesNotExist):
            self.match.refresh_from_db()
