from django.test import TestCase
from tutorials.forms import UpdateProficiencyForm
from tutorials.models import TutorSubject

class UpdateProficiencyFormTest(TestCase):
    def test_valid_data(self):
        form = UpdateProficiencyForm(data={"proficiency": "Advanced"})
        self.assertTrue(form.is_valid())

    def test_missing_data(self):
        form = UpdateProficiencyForm(data={})
        self.assertFalse(form.is_valid())
