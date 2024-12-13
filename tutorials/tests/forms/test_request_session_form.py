from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from tutorials.forms import RequestSessionForm
from tutorials.models import User, Subject, RequestSession

class RequestSessionFormTest(TestCase):

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/request_session.json',
        'tutorials/tests/fixtures/subjects.json',
    ]

    def setUp(self):
        self.student = User.objects.filter(user_type='student').first()
        self.subject = Subject.objects.first()

    def test_invalid_form_duplicate_request(self):
        RequestSession.objects.create(
            student=self.student,
            subject=self.subject,
            proficiency="Beginner",
            frequency=1.0,
            date_requested="2024-01-01"  
        )
        form = RequestSessionForm(data={
            "subject": self.subject.id,
            "proficiency": "Beginner",
            "frequency": 1.0,
            "days": ["Monday"],
        }, student=self.student)
        self.assertFalse(form.is_valid())
        self.assertIn("You have already submitted a request for this subject.", form.errors.get("__all__", []))


    def test_invalid_form_missing_student(self):
        form = RequestSessionForm(data={
            "subject": self.subject.id,
            "proficiency": "Beginner",
            "frequency": 1.0,
            "days": ["Tuesday"],
        })
        self.assertFalse(form.is_valid())
        self.assertIn("Student information is missing.", form.errors.get("__all__", []))

    def test_valid_form_clean(self):
        """Test clean method with valid data"""
        form = RequestSessionForm(data={
            "subject": self.subject.id,
            "proficiency": "Beginner",
            "frequency": 1,
            "days": ["Monday"],
        }, student=self.student)
        self.assertTrue(form.is_valid())
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data['subject'], self.subject)

    def test_clean_with_string_subject(self):
        """Test clean method with subject name string"""
        form = RequestSessionForm(data={
            "subject": self.subject.id,
            "proficiency": "Beginner",
            "frequency": 1,
            "days": ["Monday"],
        }, student=self.student)
        self.assertTrue(form.is_valid())
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data['subject'], self.subject)

    def test_clean_with_invalid_string_subject(self):
        """Test clean method with invalid subject name"""
        form = RequestSessionForm(data={
            "subject": "NonexistentSubject",
            "proficiency": "Beginner",
            "frequency": 1,
            "days": ["Monday"],
        }, student=self.student)
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValidationError):
            form.clean()

    def test_clean_with_invalid_subject_type(self):
        """Test clean method with invalid subject type"""
        form = RequestSessionForm(data={
            "subject": 999,  # Invalid subject ID
            "proficiency": "Beginner",
            "frequency": 1,
            "days": ["Monday"],
        }, student=self.student)
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValidationError):
            form.clean()

    def test_save_method_sets_date(self):
        """Test save method sets date_requested if not provided"""
        form = RequestSessionForm(data={
            "subject": self.subject.id,
            "proficiency": "Beginner",
            "frequency": 1,
            "days": ["Monday"],
        }, student=self.student)
        
        self.assertTrue(form.is_valid())
        instance = form.save(commit=False)
        instance.student = self.student 
        instance.save()
        
        self.assertIsNotNone(instance.date_requested)
        self.assertIsInstance(instance.date_requested, timezone.datetime)
        self.assertTrue((timezone.now() - instance.date_requested).seconds < 10)
