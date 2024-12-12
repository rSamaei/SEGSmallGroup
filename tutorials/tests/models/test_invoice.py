from django.core.exceptions import ValidationError
from django.test import TestCase
from tutorials.models import User, Match, RequestSession, TutorSubject, Subject, Invoice

class InvoiceTest(TestCase):
    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json',
        'tutorials/tests/fixtures/subjects.json',
        'tutorials/tests/fixtures/tutor_subjects.json',
        'tutorials/tests/fixtures/request_session.json'
    ]

    def setUp(self):
        self.tutor = TutorSubject.objects.first().tutor 
        self.session = RequestSession.objects.first() 
        self.match = Match.objects.create( 
            request_session=self.session,
            tutor=self.tutor,
            tutor_approved=True
        )
        self.invoice = Invoice.objects.create(
            payment = 1.00,
            match = self.match
        )
    
    def test_status_check(self):
        self.assertEqual(self.invoice.payment_status, 'unpaid')