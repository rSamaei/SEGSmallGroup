from django.test import TestCase
from tutorials.forms import SelectTutorForInvoice
from tutorials.models import User, Match

class SelectTutorForInvoiceTest(TestCase):
    def setUp(self):
        self.tutor = User.objects.create_user(username="tutor1", user_type="tutor")
        Match.objects.create(tutor=self.tutor, tutor_approved=True)

    def test_valid_selection(self):
        form = SelectTutorForInvoice(data={"tutor": self.tutor.id})
        self.assertTrue(form.is_valid())

    def test_invalid_selection(self):
        form = SelectTutorForInvoice(data={"tutor": None})
        self.assertFalse(form.is_valid())
