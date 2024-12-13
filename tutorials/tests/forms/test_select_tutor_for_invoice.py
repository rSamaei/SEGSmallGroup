from django.test import TestCase
from tutorials.forms import SelectTutorForInvoice
from tutorials.forms import TutorMatchForm
from tutorials.models import User, RequestSession, Subject, TutorSubject, Match

class TutorSelectTest(TestCase):

    fixtures = [
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json',
        'tutorials/tests/fixtures/request_session.json',
    ]
    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.first()
        self.student = User.objects.filter(user_type='student').first()
        self.tutor = User.objects.filter(user_type='tutor').first()
        self.request = RequestSession.objects.first()
        

        # Create tutor subject relationship
        self.tutor_subject = TutorSubject.objects.create(
            tutor=self.tutor,
            subject=self.subject,
            proficiency='Intermediate'
        )
        self.match = Match.objects.create(
            request_session = self.request,
            tutor = self.tutor,
            tutor_approved = True
        )

    def test_valid_data(self):
        form = SelectTutorForInvoice(data={
            "tutor":self.tutor,
        })
        self.assertTrue(form.is_valid())

    
