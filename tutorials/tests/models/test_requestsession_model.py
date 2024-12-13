"""Unit tests for the RequestSession model."""
from django.test import TestCase
from django.core.exceptions import ValidationError
from tutorials.models import User, Subject, RequestSession
from datetime import date

class RequestSessionModelTestCase(TestCase):
    """Unit tests for the RequestSession model."""

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/subjects.json'
    ]

    def setUp(self):
        """Set up test data for the RequestSession model."""

        self.student = User.objects.get(username='@johndoe')
        self.student.user_type = 'student'
        self.student.save()
        
        self.subject = Subject.objects.first()
        
        self.request_session = RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            frequency = 1,
            proficiency = "Intermediate",
            date_requested = date.today()
        )

    def test_request_session_creation(self):
        """Test that a RequestSession instance is created correctly."""
        self.assertIsNotNone(self.request_session)
        
        self.assertEqual(self.request_session.student, self.student)
        self.assertEqual(self.request_session.subject, self.subject)
        self.assertEqual(self.request_session.frequency, 1)
        self.assertEqual(self.request_session.proficiency, "Intermediate")
        
        self.assertTrue(RequestSession.objects.filter(
            student=self.student,
            subject=self.subject
        ).exists())

    def test_request_session_str(self):
        """Test the string representation."""
        expected = f"{self.student.username} - {self.subject.name}"
        self.assertEqual(str(self.request_session), expected)
    
    def test_unique_request_session_combination(self):
        """Test that a student cannot have duplicate subjects."""
        duplicate = RequestSession(
            student=self.student,
            subject=self.subject
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_invalid_proficiency(self):
        """Test that an invalid proficiency level raises a validation error."""
        with self.assertRaises(ValidationError):
            self.request_session.proficiency = "Expert"
            self.request_session.full_clean()
    
    def test_invalid_frequency(self):
        """Test that an invalid frequency raises a validation error."""
        with self.assertRaises(ValidationError):
            self.request_session.frequency = -1
            self.request_session.full_clean()

    def test_invalid_subject(self):
        """Test that an invalid subject raises a validation error."""
        with self.assertRaises(ValidationError):
            self.request_session.subject = None
            self.request_session.full_clean()

    def test_invalid_student(self):
        """Test that an invalid student raises a validation error."""
        with self.assertRaises(ValidationError):
            self.request_session.student = None
            self.request_session.full_clean()