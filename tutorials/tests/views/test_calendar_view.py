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
        self.assertIsNotNone(response.context['users'])
        self.assertTrue(len(response.context['users']) > 0)  # check it's not empty as admins should see all users

    def test_get_calendar_as_tutor(self):
        """Test calendar shows regular view."""
        self.client.force_login(self.tutor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')
        self.assertIsNone(response.context.get('users'))  # users list should not exist as non-admins should not see it

    def test_get_calendar_as_student(self):
        """Test calendar shows regular view."""
        self.client.force_login(self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')
        self.assertIsNone(response.context.get('users'))  # users list should not exist as non-admins should not see it

    def test_get_calendar_context_recurring_dates(self):
        """Test recurring dates are generated correctly for calendar context."""
        request_session = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            frequency=1.0,  # Weekly
            date_requested=date(2024, 8, 10)  # Start of Spring term
        )
        RequestSessionDay.objects.create(
            request_session=request_session,
            day_of_week='Monday'
        )
        match = Match.objects.create(
            request_session=request_session,
            tutor=self.tutor,
            tutor_approved=True
        )
        # Get calendar context for January 2024
        calendar_context = get_calendar_context(self.admin, month=1, year=2025)
        # Check session has recurring_dates attribute
        self.assertTrue(hasattr(calendar_context['sessions'][0], 'recurring_dates'))
        # Check recurring dates are in highlighted_dates
        session = calendar_context['sessions'][0]
        self.assertTrue(all(
            date in calendar_context['highlighted_dates'] 
            for date in session.recurring_dates
        ))
        # Check dates are correct (all Mondays in January 2024)
        expected_dates = [7, 14, 21, 28]  # All Mondays
        self.assertEqual(sorted(session.recurring_dates), expected_dates)

    def test_get_recurring_dates(self):
        """Test recurring dates are calculated correctly."""
        # Create request session with specific date and frequency
        request_session = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            frequency=1.0,  # Weekly
            date_requested=date(2024, 8, 10),  # Start of Spring term
            proficiency='Beginner'
        )
        
        # Add Monday as session day
        RequestSessionDay.objects.create(
            request_session=request_session,
            day_of_week='Monday'
        )
        
        # Test January dates (Spring term)
        dates = get_recurring_dates(request_session, 2025, 1)
        
        # Should include all Mondays in January 2024 within term
        expected_dates = [7, 14, 21, 28]  # All Mondays in January 2024
        self.assertEqual(sorted(dates), expected_dates)
        
    def test_biweekly_recurring_dates(self):
        """Test biweekly frequency generates correct dates."""
        request_session = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            frequency=2.0,  # Biweekly
            date_requested=date(2024, 8, 10),
            proficiency='Beginner'
        )
        
        # Add two days
        RequestSessionDay.objects.create(
            request_session=request_session,
            day_of_week='Monday'
        )
        RequestSessionDay.objects.create(
            request_session=request_session,
            day_of_week='Thursday'
        )
        
        dates = get_recurring_dates(request_session, 2025, 1)
        expected_dates = [7, 10, 14, 17, 21, 24, 28, 31]  # Mondays and Thursdays
        self.assertEqual(sorted(dates), expected_dates)

    def test_term_boundaries(self):
        """Test dates respect term boundaries."""
        # Create session that spans term break
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
        
        # Check December dates
        dec_dates = get_recurring_dates(request_session, 2024, 12)
        # Should only include Wednesdays until Dec 20
        self.assertTrue(max(dec_dates) <= 20)
        
        # Check January dates
        jan_dates = get_recurring_dates(request_session, 2025, 1)
        # Should only include Wednesdays after Jan 4
        self.assertTrue(min(jan_dates) >= 4)

    def test_admin_calendar_filter_by_student(self):
        """Test admin can filter calendar by student."""
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
        calendar_context = get_calendar_context(
            self.admin, 
            month=1, 
            year=2024,
            selected_user=self.student.username
        )
        # Should only show student's sessions
        self.assertEqual(len(calendar_context['sessions']), 1)
        self.assertEqual(calendar_context['sessions'][0].student, self.student)
    
    def test_admin_calendar_filter_by_tutor(self):
        """Test admin can filter calendar by tutor."""
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
        calendar_context = get_calendar_context(
            self.admin,
            month=1,
            year=2024,
            selected_user=self.tutor.username
        )
        # Should only show tutor's sessions
        self.assertEqual(len(calendar_context['sessions']), 1)
        self.assertEqual(calendar_context['sessions'][0].match.tutor, self.tutor)