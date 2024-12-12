from django.test import TestCase
from tutorials.forms import SelectStudentsForInvoice
from tutorials.models import User, Match, RequestSession

class SelectStudentsForInvoiceTest(TestCase):
    def setUp(self):
        self.tutor = User.objects.create_user(username="tutor1", user_type="tutor")
        self.student = User.objects.create_user(username="student1", user_type="student")
        self.request_session = RequestSession.objects.create(student=self.student, subject="Math")
        Match.objects.create(request_session=self.request_session, tutor=self.tutor)

    def test_valid_selection(self):
        form = SelectStudentsForInvoice(data={"student": self.student.id}, selfTutor=self.tutor)
        self.assertTrue(form.is_valid())

    def test_no_student_available(self):
        form = SelectStudentsForInvoice(data={"student": None}, selfTutor=self.tutor)
        self.assertFalse(form.is_valid())
