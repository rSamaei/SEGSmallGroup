from django.test import TestCase
from tutorials.forms import RequestSessionForm
from tutorials.models import User, Subject, RequestSession
from decimal import Decimal

class RequestSessionFormTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username="@student1", password="password123", user_type="student")
        self.subject = Subject.objects.create(name="Science")

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
