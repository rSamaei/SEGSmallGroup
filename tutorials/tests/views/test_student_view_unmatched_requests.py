from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from tutorials.models import RequestSession, Subject, RequestSessionDay

User = get_user_model()

class StudentViewUnmatchedRequestsTests(TestCase):

    def setUp(self):
        # Create a student user
        self.student_user = User.objects.create_user(
            username='@student', 
            password='password', 
            email='student@example.com', 
            user_type='student'
        )

        # Create a non-student user
        self.non_student_user = User.objects.create_user(
            username='@teacher', 
            password='password', 
            email='teacher@example.com', 
            user_type='tutor'
        )

        # Create a subject
        self.subject = Subject.objects.create(name='Mathematics')

        # Create unmatched requests for the student
        self.unmatched_request = RequestSession.objects.create(
            student=self.student_user,
            subject=self.subject,
            proficiency='Beginner',
            frequency=1.0,
            date_requested=now().date()
        )

        # Create associated days for the request
        self.day_monday = RequestSessionDay.objects.create(request_session=self.unmatched_request, day_of_week='Monday')
        self.day_tuesday = RequestSessionDay.objects.create(request_session=self.unmatched_request, day_of_week='Tuesday')

        # URL for the view
        self.url = reverse('student_view_unmatched_requests')


    def test_view_requires_login(self):
        """Ensure the view redirects unauthenticated users to the login page."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('log_in')}?next={self.url}")

    def test_view_redirects_non_students(self):
        """Ensure non-student users are redirected to the dashboard."""
        self.client.login(username='@teacher', password='password')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('dashboard'))

    def test_view_displays_unmatched_requests(self):
        """Ensure the view displays unmatched requests for the logged-in student."""
        self.client.login(username='@student', password='password')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_view_unmatched_requests.html')

        # Verify the request data is in the context
        unmatched_requests = response.context['unmatched_requests']
        self.assertIn(self.unmatched_request, unmatched_requests)

        # Verify the request details are rendered
        self.assertContains(response, 'Mathematics')
        self.assertContains(response, 'Beginner')
        self.assertContains(response, 'Weekly')
        self.assertContains(response, 'Monday')
        self.assertContains(response, 'Tuesday')
        self.assertContains(response, self.unmatched_request.date_requested.strftime('%b. %d, %Y'))

    def test_view_actions_are_rendered(self):
        """Ensure the delete and modify actions are rendered correctly."""
        self.client.login(username='@student', password='password')
        response = self.client.get(self.url)

        delete_url = reverse('delete_request', args=[self.unmatched_request.id])
        modify_url = reverse('modify_request', args=[self.unmatched_request.id])

        # Verify the delete button
        self.assertContains(response, f"action=\"{delete_url}\"")
        self.assertContains(response, 'btn-danger')

        # Verify the modify link
        self.assertContains(response, f"href=\"{modify_url}\"")
        self.assertContains(response, 'btn-warning')

    def test_submit_new_request_button(self):
        """Ensure the Submit New Request button is rendered."""
        self.client.login(username='@student', password='password')
        response = self.client.get(self.url)

        submit_url = reverse('student_submits_request')
        self.assertContains(response, f"href=\"{submit_url}\"")
        self.assertContains(response, 'btn-primary')
