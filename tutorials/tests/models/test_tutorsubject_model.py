"""Unit tests for the TutorSubject model."""
from django.test import TestCase
from tutorials.models import User, Subject, TutorSubject

class TutorSubjectModelTestCase(TestCase):
    """Unit tests for the TutorSubject model."""

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/subjects.json'
    ]

    def setUp(self):
        """Set up test data for the TutorSubject model."""

        self.tutor = User.objects.get(username='@johndoe')
        self.tutor.user_type = 'tutor'
        self.tutor.save()
        
        self.subject = Subject.objects.get(name='Mathematics')
        
        self.tutor_subject = TutorSubject.objects.create(
            tutor=self.tutor,
            subject=self.subject,
            proficiency_level = "Advanced"
        )

    def test_tutor_subject_creation(self):
        """Test that a TutorSubject instance is created correctly."""
        self.assertEqual(self.tutor_subject.tutor, self.tutor)
        self.assertEqual(self.tutor_subject.subject, self.subject)
        self.assertEqual(self.tutor_subject.proficiency_level, "Advanced")

    def test_tutor_subject_str(self):
        """Test the string representation."""
        expected = f"{self.tutor.username} - {self.subject.name}"
        self.assertEqual(str(self.tutor_subject), expected)

    def test_unique_tutor_subject_combination(self):
        """Test that a tutor cannot have duplicate subjects."""
        duplicate = TutorSubject(
            tutor=self.tutor,
            subject=self.subject
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    