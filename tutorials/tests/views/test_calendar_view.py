from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import User, RequestSession, Subject, RequestSessionDay, Match
from tutorials.views import get_calendar_context, get_recurring_dates
from datetime import date

class CalendarViewTestCase(TestCase):
    """Unit tests for the calendar view."""

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json',
        'tutorials/tests/fixtures/request_session.json'
    ]

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('calendar_view')
        self.student = User.objects.filter(user_type='student').first()
        self.tutor = User.objects.filter(user_type='tutor').first()
        self.admin = User.objects.filter(user_type='admin').first()
        self.subject = Subject.objects.first()
        self.request = RequestSession.objects.first()

    def test_calendar_url(self):
        """Test calendar URL."""
        self.assertEqual(self.url, '/calendar/')

    def test_get_calendar_not_logged_in(self):
        """Test calendar redirects when not logged in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/log_in/?next=/calendar/')

    def test_get_calendar_as_admin(self):
        """Test calendar shows admin view."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')

    def test_get_calendar_as_tutor(self):
        """Test calendar shows regular view."""
        self.client.force_login(self.tutor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')

    def test_get_calendar_as_student(self):
        """Test calendar shows regular view."""
        self.client.force_login(self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')

    def test_calendar_search_filters_sessions(self):
        """Test calendar search filters sessions correctly."""
        # Create test sessions
        request_session1 = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            proficiency='Beginner',
            frequency=1.0,
            date_requested=date(2024, 1, 1)
        )
        
        request_session2 = RequestSession.objects.create(
            student=User.objects.create(
                username='@otherstudent',
                password='Password123',
                user_type='student'
            ),
            subject=Subject.objects.create(name='Physics'),
            proficiency='Advanced',
            frequency=1.0,
            date_requested=date(2024, 1, 1)
        )
        Match.objects.create(
            request_session=request_session1,
            tutor=self.tutor,
            tutor_approved=True
        )
        Match.objects.create(
            request_session=request_session2,
            tutor=self.tutor,
            tutor_approved=True
        )

        self.client.force_login(self.admin)
        
        # Search by student username
        response = self.client.get(self.url + f'?search={self.student.username}')
        self.assertEqual(len(response.context['sessions']), 1)
        self.assertEqual(response.context['sessions'][0].student, self.student)
        
        # Search by subject
        response = self.client.get(self.url + '?search=Physics')
        self.assertEqual(len(response.context['sessions']), 1)
        self.assertEqual(response.context['sessions'][0].subject.name, 'Physics')
        
        # Search by proficiency
        response = self.client.get(self.url + '?search=Advanced')
        self.assertEqual(len(response.context['sessions']), 1)
        self.assertEqual(response.context['sessions'][0].proficiency, 'Advanced')

    def test_get_calendar_context_recurring_dates(self):
        """Test recurring dates are generated correctly for calendar context."""
        request_session = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            frequency=1.0, 
            date_requested=date(2024, 8, 10)
        )
        RequestSessionDay.objects.create(
            request_session=request_session,
            day_of_week='Monday'
        )
        Match.objects.create(
            request_session=request_session,
            tutor=self.tutor,
            tutor_approved=True
        )
        calendar_context = get_calendar_context(self.admin, month=1, year=2025)
        self.assertTrue(hasattr(calendar_context['sessions'][0], 'recurring_dates'))
        session = calendar_context['sessions'][0]
        self.assertTrue(all(
            date in calendar_context['highlighted_dates'] 
            for date in session.recurring_dates
        ))
        expected_dates = [7, 14, 21, 28]
        self.assertEqual(sorted(session.recurring_dates), expected_dates)

    def test_get_recurring_dates(self):
        """Test recurring dates are calculated correctly."""
        request_session = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            frequency=1.0,
            date_requested=date(2024, 8, 10),
            proficiency='Beginner'
        )
        RequestSessionDay.objects.create(
            request_session=request_session,
            day_of_week='Monday'
        )
        
        dates = get_recurring_dates(request_session, 2025, 1)
        
        expected_dates = [7, 14, 21, 28] 
        self.assertEqual(sorted(dates), expected_dates)
        
    def test_biweekly_recurring_dates(self):
        """Test biweekly frequency generates correct dates."""
        request_session = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            frequency=2.0, 
            date_requested=date(2024, 8, 10),
            proficiency='Beginner'
        )
        RequestSessionDay.objects.create(
            request_session=request_session,
            day_of_week='Monday'
        )
        RequestSessionDay.objects.create(
            request_session=request_session,
            day_of_week='Thursday'
        )
        
        dates = get_recurring_dates(request_session, 2025, 1)
        expected_dates = [7, 10, 14, 17, 21, 24, 28, 31] 
        self.assertEqual(sorted(dates), expected_dates)

    def test_term_boundaries(self):
        """Test dates respect term boundaries."""
        request_session = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            frequency=1.0,
            date_requested=date(2024, 8, 1),
            proficiency='Beginner'
        )
        
        RequestSessionDay.objects.create(
            request_session=request_session,
            day_of_week='Wednesday'
        )
        
        dec_dates = get_recurring_dates(request_session, 2024, 12)
        self.assertTrue(max(dec_dates) <= 20)
        
        jan_dates = get_recurring_dates(request_session, 2025, 1)
        self.assertTrue(min(jan_dates) >= 4)