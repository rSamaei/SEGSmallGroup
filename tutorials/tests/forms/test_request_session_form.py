from django.test import TestCase
from tutorials.forms import RequestSessionForm
from tutorials.models import User, Subject, RequestSession

class RequestSessionFormTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username="student1", user_type="student")
        self.subject = Subject.objects.create(name="Physics")

    def test_valid_request(self):
        form = RequestSessionForm(data={
            "subject": self.subject.id,
            "proficiency": "Intermediate",
            "frequency": 1.0,
            "days": ["Monday", "Wednesday"],
        }, student=self.student)
        self.assertTrue(form.is_valid())

    def test_duplicate_request(self):
        RequestSession.objects.create(student=self.student, subject=self.subject)
        form = RequestSessionForm(data={
            "subject": self.subject.id,
            "proficiency": "Intermediate",
            "frequency": 1.0,
            "days": ["Monday", "Wednesday"],
        }, student=self.student)
        self.assertFalse(form.is_valid())
        self.assertIn("You have already submitted a request for this subject.", form.errors["__all__"])
