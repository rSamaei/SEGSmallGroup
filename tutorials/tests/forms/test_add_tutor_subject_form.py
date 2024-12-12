from django.test import TestCase
from tutorials.forms import AddTutorSubjectForm
from tutorials.models import User, Subject, TutorSubject

class AddTutorSubjectFormTest(TestCase):
    def setUp(self):
        self.tutor = User.objects.create_user(username="tutor1", user_type="tutor")
        self.subject = Subject.objects.create(name="Mathematics")

    def test_valid_data(self):
        form = AddTutorSubjectForm(data={
            "tutor": self.tutor.id,
            "subject": self.subject.id,
            "proficiency": "Intermediate",
        })
        self.assertTrue(form.is_valid())

    def test_missing_proficiency(self):
        form = AddTutorSubjectForm(data={
            "tutor": self.tutor.id,
            "subject": self.subject.id,
        })
        self.assertFalse(form.is_valid())
