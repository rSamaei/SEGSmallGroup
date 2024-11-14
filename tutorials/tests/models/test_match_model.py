"""Unit tests for the Match model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db import IntegrityError, transaction
from tutorials.models import User, Match, RequestSession, TutorSubject, Subject

class MatchModelTestCase(TestCase):
    """Unit tests for the Match model."""

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json',
        'tutorials/tests/fixtures/tutor_subjects.json',
        'tutorials/tests/fixtures/request_session.json'
    ]

    def setUp(self):
        self.tutor = TutorSubject.objects.first().tutor # get the tutor linked in the tutor subjects fixture
        self.session = RequestSession.objects.first() # get the request session created in the request session fixture
        self.match = Match.objects.create(  # these should now have the same subject and proficiency
            request_session=self.session,
            tutor=self.tutor
        )

    def test_match_creation(self):
        """Test match is created correctly."""
        self.assertIsNotNone(self.match)
        self.assertEqual(self.match.tutor, self.tutor)
        self.assertEqual(self.match.request_session, self.session)

    def test_match_str(self):
        """Test string representation."""
        expected = f"Match: {self.session} with Tutor {self.tutor.username}"
        self.assertEqual(str(self.match), expected)

    def test_unique_match_per_request(self):
        """Test that a request session can only have one match (OneToOne relationship)."""
        self.assertTrue(Match.objects.filter(request_session=self.session).exists())
        
        duplicate_match = Match(
            request_session=self.session,
            tutor=self.tutor
        )
        
        # Use atomic transaction to rollback after test
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                duplicate_match.save()
        
        # Verify only one match exists
        self.assertEqual(Match.objects.filter(request_session=self.session).count(), 1)

    def test_invalid_tutor_assignment(self):
        """Test that only users with tutor type can be assigned."""
        student = User.objects.filter(user_type='student').first()
        with self.assertRaises(ValidationError):
            invalid_match = Match(
                request_session=self.session,
                tutor=student
            )
            invalid_match.full_clean()

    def test_cascade_deletion(self):
        """Test that deleting a request session deletes the match."""
        session_id = self.session.id
        self.session.delete()
        self.assertFalse(Match.objects.filter(request_session_id=session_id).exists())

    def subject_is_the_same(self):
        """Test that the subject of the request session and tutor subject match."""
        self.assertEqual(self.session.subject, self.tutor.tutor_subjects.first().subject)

    def test_tutor_subject_match(self):
        """Test tutor is qualified for subject."""
        self.assertTrue(
            self.tutor.tutor_subjects.filter(
                subject=self.session.subject
            ).exists()
        )