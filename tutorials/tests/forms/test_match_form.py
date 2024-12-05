"""Unit tests of the tutor match form."""
from django import forms
from django.test import TestCase
from tutorials.forms import TutorMatchForm
from tutorials.models import User, RequestSession, Subject, TutorSubject

class TutorMatchFormTestCase(TestCase):
    """Unit tests of the tutor match form."""

    fixtures = [
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json',
        'tutorials/tests/fixtures/request_session.json',
    ]

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.first()
        self.student = User.objects.filter(user_type='student').first()
        self.tutor = User.objects.filter(user_type='tutor').first()
        
        # create tutor subject relationship
        self.tutor_subject = TutorSubject.objects.create(
            tutor=self.tutor,
            subject=self.subject,
            proficiency='Intermediate'
        )
        
        # create request session
        self.request = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            proficiency='Intermediate'
        )

    def test_form_has_necessary_fields(self):
        """Test form has required fields."""
        form = TutorMatchForm(self.request)
        self.assertIn('tutor', form.fields)

    def test_valid_tutor_in_queryset(self):
        """Test that eligible tutor appears in queryset."""
        form = TutorMatchForm(self.request)
        self.assertIn(self.tutor, form.fields['tutor'].queryset)

    def test_ineligible_tutor_not_in_queryset(self):
        """Test that ineligible tutor doesn't appear in queryset."""
        ineligible_tutor = User.objects.create(
            username='@badtutor',
            first_name='Bad',
            last_name='Tutor',
            email='bad@test.org',
            user_type='tutor'
        )
        form = TutorMatchForm(self.request)
        self.assertNotIn(ineligible_tutor, form.fields['tutor'].queryset)

    def test_form_accepts_valid_input(self):
        """Test form accepts valid tutor selection."""
        form = TutorMatchForm(self.request, data={'tutor': self.tutor.id})
        self.assertTrue(form.is_valid())

    def test_form_rejects_invalid_tutor(self):
        """Test form rejects invalid tutor selection."""
        invalid_id = 99999
        form = TutorMatchForm(self.request, data={'tutor': invalid_id})
        self.assertFalse(form.is_valid())